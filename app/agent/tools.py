import datetime
import json
import pickle
from pathlib import Path

from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import BaseTool
from langchain.vectorstores import FAISS

from app.config import settings
from app.integrations.faiss import build_index
from app.integrations.gcal import schedule_event
from app.integrations.gmail import send_message
from app.integrations.google_auth import GoogleService, get_google_service

FAISS_INDEX = build_index("./assets/HR_policies.pdf")


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
        return f"\nA welcome email has been sent to {recipient_email}\n"


class HRPolicyEmailTool(BaseTool):
    name = "HR_policy_email_tool"
    description = "useful to send an email with the HR policies to the new employee. The only input is the email address of the recipient."

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
        return f"\nAn email with the HR policies has been sent to {recipient_email}\n"


class SlackInviteTool(BaseTool):
    name = "slack_invite_tool"
    description = "useful to send a slack invite to a new employee via email. The only input is the email address of the recipient."

    def _run(self, recipient_email: str) -> str:
        service = get_google_service(
            service_name=GoogleService.GMAIL,
            client_config=settings.GOOGLE_CLIENT_CONFIG,
            scopes=settings.GOOGLE_SCOPES,
        )

        send_message(
            service=service,
            recipient=recipient_email,
            subject="Slack invite",
            body=f"Welcome to the company! \n\n Here is your Slack invitation: \n{settings.SLACK_INVITE_URL}",
        )
        return f"\nAn email with a Slack invite has been sent to {recipient_email}\n"


class CreateCalendarEventTool(BaseTool):
    name = "calendar_event_tool"
    description = """useful to send a slack invite to a new employee via email. The input to this tool is a JSON with the following format:
    {
        title: str,
        start_iso_datetime: str,
        end_iso_datetime: str,
        attendees: list[str],
        timezone: Optional[str]  # Defaults to UTC
    }
    Make sure to confirm the details of the event with the user.
    """

    def _run(self, event: str) -> str:
        try:
            event_dict = json.loads(event)
        except json.JSONDecodeError:
            return "The event is not a valid JSON"

        service = get_google_service(
            service_name=GoogleService.GCAL,
            client_config=settings.GOOGLE_CLIENT_CONFIG,
            scopes=settings.GOOGLE_SCOPES,
        )

        # Parse datetime strings into datetime objects
        # Add a UTC to BST correction
        event_dict["start_iso_datetime"] = datetime.datetime.fromisoformat(
            event_dict["start_iso_datetime"]
        ) - datetime.timedelta(hours=1)

        event_dict["end_iso_datetime"] = datetime.datetime.fromisoformat(
            event_dict["end_iso_datetime"]
        ) - datetime.timedelta(hours=1)

        event_id = schedule_event(
            service=service,
            summary=event_dict["title"],
            start_time=event_dict["start_iso_datetime"].isoformat(),
            end_time=event_dict["end_iso_datetime"].isoformat(),
            attendees=event_dict["attendees"],
            timezone=event_dict.get("timezone", "UTC"),
        )
        return f"\nA calendar event has been created with id {event_id}\n"


class HRPolicyQATool(BaseTool):
    name = "HR_policy_QA_tool"
    description = "useful to answer questions about the HR policies. The input to this tool is a string with the question."

    def _run(self, query: str) -> str:
        docs = FAISS_INDEX.similarity_search("what is the holiday policy?", k=5)
        clean_docs = [doc.page_content for doc in docs]

        llm = ChatOpenAI(temperature=0.1, model=settings.OPENAI_MODEL)

        result = llm.predict(
            f"""You are a helpful question-answering assistant. You are asked the following question:\n\n
            "{query}"\n

            You have to answer the question. You can use the following information:\n\n
            {clean_docs}\n

            Answer:"
            """
        )

        return f"\n{result}\n"


if __name__ == "__main__":
    pdf_path_str = "./assets/HR_policies.pdf"
    pdf_path = Path(pdf_path_str).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"File {pdf_path} does not exist")

    pickle_filepath = Path(pdf_path_str.replace(".pdf", ".pickle")).resolve()
    if pickle_filepath.exists():
        with open(pickle_filepath, "rb") as handle_rb:
            faiss_index = pickle.load(handle_rb)
    else:
        loader = PyPDFLoader(pdf_path.as_posix())

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=50)
        all_splits = text_splitter.split_documents(loader.load())

        faiss_index = FAISS.from_documents(all_splits, OpenAIEmbeddings())
        with open(pickle_filepath, "wb") as handle_wb:
            pickle.dump(faiss_index, handle_wb, protocol=pickle.HIGHEST_PROTOCOL)

    query = "what is the holiday policy?"
    docs = faiss_index.similarity_search(query, k=5)

    llm = ChatOpenAI(temperature=0.1, model=settings.OPENAI_MODEL)

    clean_docs = [doc.page_content for doc in docs]
    result = llm.predict(
        f"""You are a helpful question-answering assistant. You are asked the following question:\n\n
        "{query}"\n

        You have to answer the question. You can use the following information:\n\n
        {clean_docs}\n

        Be concise. Answer:"
        """
    )

    print(result)


def get_all_tools() -> list[BaseTool]:
    return [
        RespondTool(),  # type: ignore
        WelcomeEmailTool(),  # type: ignore
        HRPolicyEmailTool(),  # type: ignore
        SlackInviteTool(),  # type: ignore
        CreateCalendarEventTool(),  # type: ignore
        HRPolicyQATool(),  # type: ignore
    ]
