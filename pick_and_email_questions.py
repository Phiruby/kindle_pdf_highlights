import json
import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import PROCESSED_TEXT_FILE, QUESTION_SETS_DIR

# Function to read the list of files that have been processed
# def read_processed_files(set_name):
#     processed_file = f"{PROCESSED_TEXT_FILE}_{set_name}"
#     try:
#         with open(processed_file, 'r', encoding='utf-8') as file:
#             return file.read().splitlines()
#     except FileNotFoundError:
#         return []
def read_processed_files(set_name):
    path = f"{PROCESSED_TEXT_FILE}_{set_name}.json"
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Error reading {path}. File might be corrupted. Starting with an empty dict.")
        return {}

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
def pick_least_recently_sent_questions(qa_pairs, processed_dict, num_questions=2):
    # Separate never-sent questions and sent questions
    never_sent = [q for q in qa_pairs.keys() if q not in processed_dict]
    sent_questions = [q for q in qa_pairs.keys() if q in processed_dict]
    
    # Sort sent questions by timestamp
    sorted_sent = sorted(sent_questions, key=lambda q: processed_dict[q])
    
    # Combine never-sent questions with sorted sent questions
    all_sorted = never_sent + sorted_sent
    
    # Select the required number of questions
    selected_questions = all_sorted[:num_questions]
    
    return selected_questions

def write_processed_files(processed_files, set_name):
    path = f"{PROCESSED_TEXT_FILE}_{set_name}.json"
    
    # Read existing entries
    existing_entries = read_processed_files(set_name)
    
    # Update timestamps for processed files
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for item in processed_files:
        existing_entries[item] = current_time
    
    # Write updated entries back to the file
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(existing_entries, file, indent=2)
    
    print(f"File {path} has been updated with {len(existing_entries)} entries.")

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
    question_sets_dir = QUESTION_SETS_DIR
    for set_dir in os.listdir(question_sets_dir):
        set_path = os.path.join(question_sets_dir, set_dir)
        if os.path.isdir(set_path):
            with open(os.path.join(set_path, "config.json"), 'r') as config_file:
                config = json.load(config_file)
            
            print(config)
            internal_name = config["internal_name"]
            subject_title = config["subject_title"]
            keys_are_questions = config["keys_are_question"]
            qa_pairs_file = os.path.join(set_path, config["qa_pairs_file"])
            print(qa_pairs_file)

            processed_dict = read_processed_files(internal_name)
            
            with open(qa_pairs_file, 'r', encoding='utf-8') as file:
                qa_pairs = json.load(file)
            
            selected_questions = pick_least_recently_sent_questions(qa_pairs, processed_dict)
            
            print(selected_questions)
            content = ''
            for question in selected_questions:
                current_content = qa_pairs[question]
                if keys_are_questions == "true":
                    print("Keys are questions")
                    current_content = format_question_in_markdown(question, qa_pairs[question])
                    
                content += render_markdown_latex(current_content) + '<br><br>'
            
            send_email(content, f"Question Digest: {subject_title}")
            write_processed_files(selected_questions, internal_name)

if __name__ == '__main__':
    process_and_send_emails()