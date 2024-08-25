import os 
from config import QUESTION_OUTPUT_FOLDER
from dotenv import load_dotenv, dotenv_values

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random


q_path = os.path.join(os.getcwd(), QUESTION_OUTPUT_FOLDER)
assert os.path.exists(q_path), "No questions and answer folder found. Make sure to create them!"
assert len(os.listdir(q_path)) > 0, "Nothing found inside the questions directory. Make sure to add questions!"

load_dotenv()
EMAIL = os.getenv("SENDER_MAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

FILES_PER_EMAIL = 2 # FILES_PER_EMAIL * 2 questions per email

def send_email(text):
    sender_email = EMAIL
    receiver_email = os.getenv("RECEIVER_MAIL")
    password = EMAIL_PASSWORD

    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Question Digest"

    # html_content = generate_html_content()
    html_content = r"\frac{1}{2}+\sum_{i=1}^{n}\frac{a_i}{i}"

    part = MIMEText(text, 'plain')
    message.attach(part)


    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")
    finally:
        server.quit()

# Function to read the list of files that have been processed
def read_processed_files():
    try:
        path = os.path.join(os.getcwd(),'temp','processed_files.txt')
        with open(path, 'r') as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Function to write the list of processed files back to disk
def write_processed_files(processed_files):
    path = os.path.join(os.getcwd(),'temp','processed_files.txt')
    with open(path, 'w',encoding='utf-8') as file:
        file.write('\n'.join(processed_files))

def process_and_send_emails():
    processed_files = read_processed_files()
    qa_path = os.path.join(os.getcwd(), 'question_answers')
    files = [file for file in os.listdir(qa_path) if file.endswith('.txt') and file not in processed_files]
    #reset processed files so the previous emails can show up again!
    processed_path = os.path.join(os.getcwd(), 'temp', 'processed_files.txt')
    with open(processed_path, 'w') as file:
        pass #removes everything there

    processed_files = [] #resset the processed files
    content = ''
    if files:
        selected_files = random.sample(files, min(FILES_PER_EMAIL, len(files)))
        for file in selected_files:
            with open(os.path.join('question_answers', file), 'r') as f:
                content += f.read()
                processed_files.append(file)
            content+='\n'

        send_email(content)
        print(content)
        write_processed_files(processed_files)

if __name__ == '__main__':
    process_and_send_emails()