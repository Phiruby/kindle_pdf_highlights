import json
import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from config import PROCESSED_TEXT_FILE, QUESTION_SETS_DIR
import importlib
import re
import base64

to send email
def send_email(content, subject, image_dict):
    sender_email = os.getenv("SENDER_MAIL")
    receiver_email = os.getenv("RECEIVER_MAIL")
    password = os.getenv("EMAIL_PASSWORD")

    message = MIMEMultipart("related")
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Attach the HTML content
    html_part = MIMEText(content, 'html')
    message.attach(html_part)

    # Attach images with Content-ID
    for cid, image_path in image_dict.items():
        with open(image_path, 'rb') as img:
            img_data = img.read()
        image = MIMEImage(img_data)
        image.add_header('Content-ID', f'<{cid}>')
        image.add_header('Content-Disposition', 'inline', filename=os.path.basename(image_path))
        message.attach(image)

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        print(f"Email sent successfully for {subject}!")
    except Exception as e:
        print(f"Failed to send email for {subject}. Error: {e}")
    finally:
        server.quit()

def reauthenticate_error():
    '''
    Sends an email consisting of the content to reauthenticate
    '''
    subject = "Reauthentication Required"
    content = """
    <html>
        <body>
            <h1>Reauthentication Required</h1>
            <p>Hey Vilo,</p>
            <p>Seems as though the google drive pipeline requires reauthentication.</p>
            <p>Follow the steps below to reauthenticate as you did before:</p>
            <ol>
                <li>Open the application.</li>
                <li>Follow the prompts to log in with your Google account.</li>
                <li>Ensure that you grant the necessary permissions.</li>
            </ol>
            <p>If you have any questions or need assistance, please do not hesitate to reach out.</p>
            <p>Thank you for your attention to this matter.</p>
            <p>Best regards,<br>Your Application Team</p>
        </body>
    </html>
    """
    image_dict = {}  # Assuming no images are needed for this email
    send_email(content, subject, image_dict)
