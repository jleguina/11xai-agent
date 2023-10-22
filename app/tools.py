from pathlib import Path

from langchain.tools import BaseTool

from app.config import settings
from app.integrations.gmail import send_message
from app.integrations.google_auth import GoogleService, get_google_service


class RespondTool(BaseTool):
    name = "respond_tool"
    description = "used to give an answer to the human. The input to this tool is a string with your response"

    def _run(self, query: str) -> str:
        return query


class WelcomeEmailTool(BaseTool):
    name = "welcome_email_tool"
    description = "useful to send a welcome email to a new employee. The input is the email address of the recipient."

    def _run(self, recipient_email: str) -> str:
        service = get_google_service(
            service_name=GoogleService.GMAIL,
            client_config=settings.GOOGLE_CLIENT_CONFIG,
            scopes=settings.GOOGLE_SCOPES,
        )

        send_message(
            service=service,
            recipient=recipient_email,
            subject="Welcome to the company!",
            body="Welcome to the company! We are very happy to have you here.",
        )
        return f"An email has been sent to {recipient_email}"


class HRPolicyEmailTool(BaseTool):
    name = "HR_policy_email_tool"
    description = "useful to send an email with the HR policies to the new employee. The input is the email address of the recipient."

    def _run(self, recipient_email: str) -> str:
        service = get_google_service(
            service_name=GoogleService.GMAIL,
            client_config=settings.GOOGLE_CLIENT_CONFIG,
            scopes=settings.GOOGLE_SCOPES,
        )

        send_message(
            service=service,
            recipient=recipient_email,
            subject="HR policies",
            body="Please find attached the HR policies of the company",
            attachments=[Path("./assets/HR_policies.pdf").resolve().as_posix()],
        )
        return f"An email has been sent to {recipient_email}"
