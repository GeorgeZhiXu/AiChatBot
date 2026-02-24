"""
Claude via AWS Bedrock client.
Replaces the previous DeepSeek/OpenAI-compatible client.
Uses the Bedrock HTTP API with bearer token authentication.
Supports Claude tool_use for knowledge base integration.
"""
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import json
import os
from typing import List, Dict, Generator

import httpx

BEDROCK_TOKEN = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "")
BEDROCK_MODEL = os.environ.get("BEDROCK_MODEL", "us.anthropic.claude-sonnet-4-20250514-v1:0")
BEDROCK_REGION = "us-west-2"
BEDROCK_URL = f"https://bedrock-runtime.{BEDROCK_REGION}.amazonaws.com/model/{BEDROCK_MODEL}/invoke"

KB_BASE_URL = os.environ.get("KB_BASE_URL", "http://127.0.0.1:8020")

# Tool definitions for Claude
TOOLS = [
    {
        "name": "query_knowledge_base",
        "description": (
            "Query the Chinese language knowledge base using natural language. "
            "The knowledge base contains: 12 textbooks (人教版 grades 1-6, volumes 上册/下册), "
            "~300 lessons with their characters, ~12,800 characters with corpus frequency data, "
            "~39,000 phrases, and learner test activity tracking. "
            "You can ask questions like '列出一年级上册第一课的生字', "
            "'Ada学了哪些字', '频率排名前100的汉字', '二年级有多少课', "
            "'晨这个字在哪一课' etc. The query is converted to SQL internally."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Natural language question about Chinese characters, lessons, textbooks, learner progress, or phrase frequency"
                }
            },
            "required": ["question"]
        }
    }
]


def _call_bedrock(messages, system="", temperature=0.7, max_tokens=2048, tools=None):
    """Low-level Bedrock API call. Returns the parsed JSON response."""
    token = BEDROCK_TOKEN
    if not token:
        raise RuntimeError("AWS_BEARER_TOKEN_BEDROCK is not set in the environment")

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system:
        body["system"] = system
    if tools:
        body["tools"] = tools

    resp = httpx.post(
        BEDROCK_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=60,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Bedrock API error {resp.status_code}: {resp.text}")

    return resp.json()


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool call and return the result as a string."""
    if tool_name == "query_knowledge_base":
        question = tool_input.get("question", "")
        try:
            resp = httpx.post(
                f"{KB_BASE_URL}/api/v1/ask",
                json={"question": question},
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                return json.dumps({
                    "error": f"Knowledge base returned status {resp.status_code}",
                    "detail": resp.text
                })
        except Exception as e:
            return json.dumps({"error": f"Failed to query knowledge base: {str(e)}"})
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


def _extract_text(content_blocks):
    """Extract text from response content blocks."""
    texts = []
    for block in content_blocks:
        if block.get("type") == "text":
            texts.append(block["text"])
    return "\n".join(texts)


def _extract_tool_uses(content_blocks):
    """Extract tool_use blocks from response content."""
    return [block for block in content_blocks if block.get("type") == "tool_use"]


def chat_completion(
    messages: List[Dict[str, str]],
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Synchronous call to Claude via Bedrock with tool_use support.
    Returns the full response text.

    If Claude decides to use the knowledge base tool, we execute the tool
    and send the result back to Claude for a final response.

    messages: list of {"role": "user"|"assistant", "content": "..."}
              (system messages should be passed via the `system` parameter)
    """
    # First call: include tools so Claude can decide whether to use them
    result = _call_bedrock(
        messages=messages,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=TOOLS,
    )

    content = result.get("content", [])
    stop_reason = result.get("stop_reason", "")

    # If Claude did not request tool use, return text directly
    if stop_reason != "tool_use":
        return _extract_text(content)

    # Claude wants to use tool(s) - execute them and send results back
    tool_uses = _extract_tool_uses(content)

    if not tool_uses:
        # Shouldn't happen, but fall back to text
        return _extract_text(content)

    # Build the assistant message with the full content (text + tool_use blocks)
    assistant_message = {"role": "assistant", "content": content}

    # Build tool_result blocks for each tool use
    tool_results = []
    for tool_use in tool_uses:
        tool_result_content = _execute_tool(tool_use["name"], tool_use["input"])
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": tool_use["id"],
            "content": tool_result_content,
        })

    tool_result_message = {"role": "user", "content": tool_results}

    # Second call: send tool results back to Claude for final response
    follow_up_messages = messages + [assistant_message, tool_result_message]

    result2 = _call_bedrock(
        messages=follow_up_messages,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=TOOLS,  # Keep tools available in case Claude needs another round
    )

    content2 = result2.get("content", [])
    stop_reason2 = result2.get("stop_reason", "")

    # Handle a potential second tool call (unlikely but possible)
    if stop_reason2 == "tool_use":
        tool_uses2 = _extract_tool_uses(content2)
        if tool_uses2:
            assistant_message2 = {"role": "assistant", "content": content2}
            tool_results2 = []
            for tool_use in tool_uses2:
                tool_result_content = _execute_tool(tool_use["name"], tool_use["input"])
                tool_results2.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use["id"],
                    "content": tool_result_content,
                })
            tool_result_message2 = {"role": "user", "content": tool_results2}

            follow_up_messages2 = follow_up_messages + [assistant_message2, tool_result_message2]
            result3 = _call_bedrock(
                messages=follow_up_messages2,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return _extract_text(result3.get("content", []))

    return _extract_text(content2)


def chat_completion_stream(
    messages: List[Dict[str, str]],
    model: str = "",
    temperature: float = 0.7,
    system: str = "",
) -> Generator[str, None, None]:
    """
    Synchronous generator that calls Claude via Bedrock and yields
    the full response as a single chunk.

    Note: Bedrock invoke endpoint does not support streaming in the same way
    as the invokeWithResponseStream endpoint. For simplicity we fetch the
    full response and yield it as one chunk. The frontend already handles
    chunk-by-chunk delivery via the socket emit loop.
    """
    full_text = chat_completion(
        messages=messages,
        system=system,
        temperature=temperature,
    )

    # Yield the full response (the caller in main.py streams it chunk-by-chunk
    # to clients via socket.io with small delays, so UX is still progressive)
    yield full_text
