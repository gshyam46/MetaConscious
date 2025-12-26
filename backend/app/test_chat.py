import os
import asyncio
import logging

logger = logging.getLogger(__name__)
from dotenv import load_dotenv

load_dotenv()

class UserMessage:
    def __init__(self, text: str):
        self.text = text


async def run_final_llm(model, messages, api_key, session_id=None):
    """
    REAL LLM call.
    Replace this with your actual Groq / LiteLLM / OpenAI implementation.
    """
    from litellm import acompletion  # example

    response = await acompletion(
        model=model,
        messages=messages,
        api_key=api_key,
    )

    return response


class LlmChat:
    def __init__(
        self,
        system_message: str,
        session_id: str | None = None,
        model: str = "llama-3.3-70b-versatile",
    ):
        self.api_key = os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise RuntimeError("LLM_API_KEY not set")

        self.session_id = session_id
        self.system_message = system_message
        self.model = f"groq/{model}"

    async def send_message(self, user_message: UserMessage) -> str:
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": user_message.text},
        ]

        resp = await run_final_llm(
            model=self.model,
            messages=messages,
            api_key=self.api_key,
            session_id=self.session_id,
        )

        return resp["choices"][0]["message"]["content"]


async def main():
    chat = LlmChat(
        system_message="You are a helpful assistant.",
        session_id="local-run",
    )

    msg = UserMessage(text="What is RAG in LLMs?")
    response = await chat.send_message(msg)
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
