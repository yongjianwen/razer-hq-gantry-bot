import base64
import os

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()
DATA_PATH = os.environ.get("DATA_PATH")
SENDER_EMAIL_ADDRESS = os.environ.get("SENDER_EMAIL_ADDRESS")
EMAIL_SUBJECT = os.environ.get("EMAIL_SUBJECT")

# Constants
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    creds = None

    token_path = f"{DATA_PATH}/token.json"
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                f"{DATA_PATH}/credentials.json",
                SCOPES
            )
            # creds = flow.run_local_server(port=0)
            creds = flow.run_local_server(
                access_type="offline",
                prompt="consent"
            )

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def extract_text(payload):
    texts = []

    def walk(part):
        mime = part.get("mimeType", "")
        body = part.get("body", {})
        data = body.get("data")

        if data and mime in ("text/plain", "text/html"):
            decoded = base64.urlsafe_b64decode(data).decode(
                errors="ignore"
            )
            texts.append(decoded)

        for child in part.get("parts", []):
            walk(child)

    walk(payload)
    return "\n".join(texts)


def extract_register_link(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    a = soup.find("a", class_="register-link")
    if not a:
        return None

    return a.get("href")


def get_invitation_link(name):
    service = get_gmail_service()

    razer_emails = service.users().messages().list(
        userId="me",
        maxResults=10,
        q=f"from:{SENDER_EMAIL_ADDRESS} subject:{EMAIL_SUBJECT}"
    ).execute()

    messages = razer_emails.get("messages", [])

    for message in messages:
        msg_id = message["id"]

        msg = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full"
        ).execute()

        html_content = extract_text(msg["payload"])

        if html_content.find(f"Dear {name},") != -1:
            link = extract_register_link(html_content)
            return link

    raise Exception("No email found with given name")


if __name__ == "__main__":
    print("This only runs when executed directly")
    get_invitation_link("Yew Chinn")
