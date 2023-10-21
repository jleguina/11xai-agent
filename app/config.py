import os
from dataclasses import dataclass

import openai
from dotenv import load_dotenv

load_dotenv()


@dataclass
class _Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    DEBUG: bool = False


settings = _Settings()

openai.api_key = settings.OPENAI_API_KEY

__all__ = ["settings"]
