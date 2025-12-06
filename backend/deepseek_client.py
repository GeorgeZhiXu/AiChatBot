import os
from typing import List, Dict, Generator

from openai import OpenAI


def get_client() -> OpenAI:
    """
    Initialize the DeepSeek/OpenAI-compatible client from environment variables.
    Do NOT hardcode the API key.
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set in the environment")

    base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
    )


def chat_completion_stream(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float = 0.7,
) -> Generator[str, None, None]:
    """
    Synchronous generator that wraps DeepSeek's streaming chat API.
    It yields text chunks (strings) one by one.
    """

    client = get_client()

    # This matches your example:
    # stream = client.chat.completions.create(
    #     model="deepseek-chat",
    #     messages=[{"role": "user", "content": user_message}],
    #     stream=True,
    #     temperature=0.7
    # )

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=temperature,
    )

    full_text = ""
    for chunk in stream:
        # According to your example: chunk.choices[0].delta.content
        delta = chunk.choices[0].delta.content
        if delta:
            full_text += delta
            yield delta
