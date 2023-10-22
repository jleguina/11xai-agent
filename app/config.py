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

    # Google API
    SYSTEM_EMAIL = "javierleguina98@gmail.com"
    GMAIL_SCOPES = ["https://mail.google.com/"]

    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_PROJECT_ID: str = os.getenv("GOOGLE_PROJECT_ID", "")
    GOOGLE_AUTH_URI: str = os.getenv("GOOGLE_AUTH_URI", "")
    GOOGLE_TOKEN_URI: str = os.getenv("GOOGLE_TOKEN_URI", "")
    GOOGLE_AUTH_PROVIDER_X509_CERT_URL: str = os.getenv(
        "GOOGLE_AUTH_PROVIDER_X509_CERT_URL", ""
    )
    GOOGLE_REDIRECT_URIS: str = os.getenv("GOOGLE_REDIRECT_URIS", "")

    @property
    def GOOGLE_CLIENT_CONFIG(self) -> dict[str, dict[str, str | list[str]]]:
        return {
            "installed": {
                "client_id": self.GOOGLE_CLIENT_ID,
                "client_secret": self.GOOGLE_CLIENT_SECRET,
                "project_id": self.GOOGLE_PROJECT_ID,
                "auth_uri": self.GOOGLE_AUTH_URI,
                "token_uri": self.GOOGLE_TOKEN_URI,
                "auth_provider_x509_cert_url": self.GOOGLE_AUTH_PROVIDER_X509_CERT_URL,
                "redirect_uris": [self.GOOGLE_REDIRECT_URIS],
            }
        }


settings = _Settings()

openai.api_key = settings.OPENAI_API_KEY

__all__ = ["settings"]
