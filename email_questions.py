import os 
from config import QUESTION_OUTPUT_FOLDER
from dotenv import load_dotenv, dotenv_values

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from requests import HTTPError

q_path = os.path.join(os.getcwd(), QUESTION_OUTPUT_FOLDER)
assert os.path.exists(q_path), "No questions and answer folder found. Make sure to create them!"
assert len(os.listdir(q_path)) > 0, "Nothing found inside the questions directory. Make sure to add questions!"

load_dotenv()
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

import base64
from email.message import EmailMessage

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
import google.auth


def gmail_send_message():
  """Create and send an email message
  Print the returned  message id
  Returns: Message object, including message id

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  client_secret_file = os.path.join(os.getcwd(), 'client_secret_1054281926341-k2m55o2nbp1a4mq4nlka460dlr16afd4.apps.googleusercontent.com.json')
  flow = InstalledAppFlow.from_client_secrets_file(
    client_secret_file,
    scopes=['https://www.googleapis.com/auth/gmail.send']
    )
  
  creds = flow.run_local_server(port=0)
  service = build('gmail.googleapis.com', 'v1', credentials=creds)
  print("PAST")

  message = MIMEText("This is some test email. Ignore")
  message['to'] = os.getenv("RECEIVER_MAIL")
  message['subject'] = 'Test Mail'
  create_message = {'raw': base64.urlsafe_b64decode(message.as_bytes()).decode()}

  try:
    message = (service.users().messages().send(userid="me", body=create_message).execute())
    print("Send Message!")
  except HTTPError as e:
    print(f"An error occured: {e}")
    message = None
  return message



#   try:
#     service = build("gmail", "v1", credentials=creds)
#     message = EmailMessage()

#     message.set_content("This is automated draft mail. Though, let's test it! <h1> Hola </h1>")

#     message["To"] = os.getenv("RECEIVER_MAIL")
#     message["From"] = os.getenv("SENDER_MAIL")
#     message["Subject"] = "Question Digest"

#     # encoded message
#     encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

#     create_message = {"raw": encoded_message}
#     # pylint: disable=E1101
#     send_message = (
#         service.users()
#         .messages()
#         .send(userId="me", body=create_message)
#         .execute()
#     )
#     print(f'Message Id: {send_message["id"]}')
#   except HttpError as error:
#     print(f"An error occurred: {error}")
#     send_message = None
#   return send_message


gmail_send_message()
