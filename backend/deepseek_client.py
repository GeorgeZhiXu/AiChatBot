"""
Claude via AWS Bedrock client.
Replaces the previous DeepSeek/OpenAI-compatible client.
Uses the Bedrock HTTP API with bearer token authentication.
"""
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
from typing import List, Dict, Generator

import httpx

BEDROCK_TOKEN = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "")
BEDROCK_MODEL = os.environ.get("BEDROCK_MODEL", "us.anthropic.claude-sonnet-4-20250514-v1:0")
BEDROCK_REGION = "us-west-2"
BEDROCK_URL = f"https://bedrock-runtime.{BEDROCK_REGION}.amazonaws.com/model/{BEDROCK_MODEL}/invoke"


def chat_completion(
    messages: List[Dict[str, str]],
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Synchronous call to Claude via Bedrock.
    Returns the full response text.

    messages: list of {"role": "user"|"assistant", "content": "..."}
              (system messages should be passed via the `system` parameter)
    """
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

    result = resp.json()
    return result["content"][0]["text"]


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
