import json
import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import PROCESSED_TEXT_FILE

# Function to read the list of files that have been processed
def read_processed_files(set_name):
    processed_file = f"{PROCESSED_TEXT_FILE}_{set_name}"
    try:
        with open(processed_file, 'r', encoding='utf-8') as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Function to send email
def send_email(content, subject):
    sender_email = os.getenv("SENDER_MAIL")
    receiver_email = os.getenv("RECEIVER_MAIL")
    password = os.getenv("EMAIL_PASSWORD")

    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    part = MIMEText(content, 'html')
    message.attach(part)

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        print(f"Email sent successfully for {subject}!")
    except Exception as e:
        print(f"Failed to send email for {subject}. Error: {e}")
    finally:
        server.quit()

# Function to pick questions that were least recently sent
def pick_least_recently_sent_questions(qa_pairs, processed_files, num_questions=2):
    # Extract questions from processed_files
    processed_questions = [pf.split('|')[0] for pf in processed_files]
    
    # Find unsent questions
    unsent_questions = [q for q in qa_pairs if q not in processed_questions]
    
    if unsent_questions:
        # If there are unsent questions, randomly select from them
        num_to_select = min(num_questions, len(unsent_questions))
        selected_questions = random.sample(unsent_questions, num_to_select)
    else:
        # If all questions have been sent, sort processed_files by date
        processed_files.sort(key=lambda x: datetime.strptime(x.split('|')[1], '%Y-%m-%d %H:%M:%S'))
        # Select the least recently sent questions
        selected_questions = [pf.split('|')[0] for pf in processed_files[:num_questions]]
    
    return selected_questions

def write_processed_files(processed_files, set_name):
    path = f"{PROCESSED_TEXT_FILE}_{set_name}"
    with open(path, 'w', encoding='utf-8') as file:
        for item in processed_files:
            file.write(f"{item}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Function to render markdown and latex in HTML
def render_markdown_latex(content):
    import markdown2
    import latex2mathml.converter

    html_content = markdown2.markdown(content)

    def replace_latex_with_mathml(match):
        latex_code = match.group(1)
        mathml_code = latex2mathml.converter.convert(latex_code)
        return f'<math xmlns="http://www.w3.org/1998/Math/MathML">{mathml_code}</math>'

    import re
    html_content = re.sub(r'\$(.*?)\$', replace_latex_with_mathml, html_content)
    html_content = re.sub(r'```(.*?)```', r'\1', html_content, flags=re.DOTALL)

    return html_content

def format_question_in_markdown(question, answer):
    return f"# Question:\n```{question}```\n# Answer:\n```{answer}```"

def process_and_send_emails():
    question_sets_dir = "question_sets"
    for set_dir in os.listdir(question_sets_dir):
        set_path = os.path.join(question_sets_dir, set_dir)
        if os.path.isdir(set_path):
            with open(os.path.join(set_path, "config.json"), 'r') as config_file:
                config = json.load(config_file)
            
            print(config)
            internal_name = config["internal_name"]
            subject_title = config["subject_title"]
            keys_are_questions = config["keys_are_questions"]
            qa_pairs_file = os.path.join(set_path, config["qa_pairs_file"])
            print(qa_pairs_file)

            processed_files = read_processed_files(internal_name)
            
            with open(qa_pairs_file, 'r', encoding='utf-8') as file:
                qa_pairs = json.load(file)
            
            selected_questions = pick_least_recently_sent_questions(qa_pairs, processed_files)
            
            content = ''
            for question in selected_questions:
                current_content = qa_pairs[question]
                if keys_are_questions == "true": #if the ksy are the question & values are the answer
                    print("Keys are questions")
                    current_content = format_question_in_markdown(question, qa_pairs[question])
                    
                content += render_markdown_latex(current_content) + '<br><br>'
                processed_files.append(question)
            
            send_email(content, f"Question Digest: {subject_title}")
            write_processed_files(processed_files, internal_name)

if __name__ == '__main__':
    process_and_send_emails()