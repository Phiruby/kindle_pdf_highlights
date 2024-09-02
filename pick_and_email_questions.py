import json
import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import QUESTION_ANSWER_PAIRS_FILE, PROCESSED_HIGHLIGHTS_FILE

# Function to read the list of files that have been processed
def read_processed_files():
    try:
        with open(PROCESSED_HIGHLIGHTS_FILE, 'r', encoding='utf-8') as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Function to send email
def send_email(content):
    sender_email = os.getenv("SENDER_MAIL")
    receiver_email = os.getenv("RECEIVER_MAIL")
    # see https://support.google.com/accounts/answer/185833?hl=en to create app password
    password = os.getenv("EMAIL_PASSWORD")

    print(sender_email, receiver_email, password)

    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Question Digest"

    part = MIMEText(content, 'html')
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

# Function to pick questions that were least recently sent
def pick_least_recently_sent_questions(qa_pairs, processed_files, num_questions=2):
    unsent_questions = [q for q in qa_pairs if q not in [pf.split('|')[0] for pf in processed_files]]
    
    if len(unsent_questions) < num_questions:
        num_questions = len(unsent_questions)
    
    if num_questions == 0:
        # All questions have been sent, recycle and pick the least recently picked questions
        processed_files.sort(key=lambda x: datetime.strptime(x.split('|')[1], '%Y-%m-%d %H:%M:%S'))
        selected_questions = [pf.split('|')[0] for pf in processed_files[:num_questions]]
    else:
        selected_questions = random.sample(unsent_questions, num_questions)
    
    return selected_questions

def write_processed_files(processed_files):
    path = os.path.join(os.getcwd(),'temp','processed_files.txt')
    with open(path, 'w', encoding='utf-8') as file:
        for item in processed_files:
            file.write(f"{item}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Function to render markdown and latex in HTML
def render_markdown_latex(content):
    import markdown2
    import latex2mathml.converter

    # Convert markdown to HTML
    html_content = markdown2.markdown(content)

    # Convert LaTeX to MathML
    def replace_latex_with_mathml(match):
        latex_code = match.group(1)
        mathml_code = latex2mathml.converter.convert(latex_code)
        return f'<math xmlns="http://www.w3.org/1998/Math/MathML">{mathml_code}</math>'

    import re
    # html_content = re.sub(r'\$(.*?)\$', replace_latex_with_mathml, html_content)

    # Remove markdown ticks around the answer block
    html_content = re.sub(r'```(.*?)```', r'\1', html_content, flags=re.DOTALL)

    return html_content

def process_and_send_emails():
    processed_files = read_processed_files()
    
    # Load the generated QA pairs
    with open(QUESTION_ANSWER_PAIRS_FILE, 'r') as file:
        qa_pairs = json.load(file)
    
    selected_questions = pick_least_recently_sent_questions(qa_pairs, processed_files)
    
    content = ''
    for question in selected_questions:
        content += render_markdown_latex(qa_pairs[question]) + '<br><br>'
        processed_files.append(question)
    
    send_email(content)
    write_processed_files(processed_files)

if __name__ == '__main__':
    process_and_send_emails()
