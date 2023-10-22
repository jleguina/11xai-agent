import copy
import os
import os.path
import pickle
import warnings

# for encoding/decoding messages in base64
from base64 import urlsafe_b64encode
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

# for dealing with attachement MIME types
from email.mime.text import MIMEText
from mimetypes import guess_type as guess_mime_type
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API utils
from googleapiclient.discovery import build

from app.config import settings


def gmail_authenticate() -> Any:
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
                settings.GOOGLE_CLIENT_CONFIG, settings.GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build("gmail", "v1", credentials=creds)


# Adds the attachment with the given filename to the given message
def add_attachment(
    message: MIMEText | MIMEMultipart, filepath: str
) -> MIMEText | MIMEMultipart:
    content_type, encoding = guess_mime_type(filepath)
    if content_type is None or encoding is not None:
        content_type = "application/octet-stream"
    main_type, sub_type = content_type.split("/", 1)

    msg: MIMEText | MIMEImage | MIMEAudio | MIMEApplication | MIMEBase
    with open(filepath, "rb") as fp:
        if main_type == "text":
            msg = MIMEText(fp.read().decode(), _subtype=sub_type)
        elif main_type == "image":
            msg = MIMEImage(fp.read(), _subtype=sub_type)
        elif main_type == "audio":
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
        elif main_type == "application":
            msg = MIMEApplication(fp.read(), _subtype=sub_type)
        else:
            warnings.warn(f"Unknown attachment type {main_type}/{sub_type}")
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())

    filename = os.path.basename(filepath)
    msg.add_header("Content-Disposition", "attachment", filename=filename)

    # Avoid side effects
    message_copy = copy.deepcopy(message)
    message_copy.attach(msg)
    return message_copy


def build_message(
    recipient: str,
    subject: str,
    body: str,
    attachments: list[str] = [],
) -> dict[str, str]:
    message: MIMEText | MIMEMultipart
    if not attachments:
        message = MIMEText(body)
    else:
        message = MIMEMultipart()
        message.attach(MIMEText(body))
        for filepath in attachments:
            # Verify that the file exists
            if not os.path.isfile(filepath):
                raise FileNotFoundError(f"File {filepath} not found")
            message = add_attachment(message, filepath)

    message["to"] = recipient
    message["from"] = settings.SYSTEM_EMAIL
    message["subject"] = subject

    return {"raw": urlsafe_b64encode(message.as_bytes()).decode()}


def send_message(
    service: Any,
    recipient: str,
    subject: str,
    body: str,
    attachments: list[str] = [],
) -> dict[str, str]:
    return (
        service.users()
        .messages()
        .send(
            userId="me",
            body=build_message(recipient, subject, body, attachments),
        )
        .execute()
    )


if __name__ == "__main__":
    service = gmail_authenticate()
    attachment_path = Path("./assets/HR_policies.pdf").resolve().as_posix()
    send_message(
        service=service,
        recipient="javierleguina98@gmail.com",
        subject="This is a subject",
        body="This is the body of the email",
        attachments=["./assets/HR_policies.pdf"],
    )
