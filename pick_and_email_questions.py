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
import tempfile
import subprocess
from io import BytesIO
from PIL import Image
import html
import matplotlib.pyplot as plt
import io

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
    for cid, image_data in image_dict.items():
        if isinstance(image_data, str):  # It's a file path
            with open(image_data, 'rb') as img:
                img_data = img.read()
            image = MIMEImage(img_data)
            image.add_header('Content-Disposition', 'inline', filename=os.path.basename(image_data))
        else:  # It's binary data
            image = MIMEImage(image_data)
            image.add_header('Content-Disposition', 'inline', filename=f'{cid}.png')
        
        image.add_header('Content-ID', f'<{cid}>')
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

def get_picking_algorithm(algorithm_name):
    try:
        module = importlib.import_module(f"picking_algorithms.{algorithm_name}")
        return module.pick_questions
    except ImportError:
        print(f"Algorithm {algorithm_name} not found. Using least_recently_chosen as default.")
        from picking_algorithms.least_recently_chosen import pick_questions
        return pick_questions

def find_image_file(images_dir, filename):
    for root, dirs, files in os.walk(images_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None

def latex_to_image(latex_content):
    plt.figure(figsize=(10, 10))
    plt.axis('off')

    # Define custom LaTeX-like commands with a preceding space
    def custom_latex_commands(content):
        content = re.sub(r'\\inner\{(.+?)\}\{(.+?)\}', r' \\langle \1, \2 \\rangle ', content)
        content = re.sub(r'\\norm\{(.+?)\}', r' \\|\1\\|', content)
        content = re.sub(r'\\complex', r' \\mathbb{C}', content)
        content = re.sub(r'\\reals', r' \\mathbb{R}', content)
        content = re.sub(r'\\matrixset\{(.+?)\}\{(.+?)\}', r' M_{\1}(\2)', content)
        content = re.sub(r'\\range', r' \\operatorname{range}', content)
        return content

    # Handle LaTeX environments like align*, equation*, etc.
    def handle_environments(content):
        # Convert \begin{align*}...\end{align*} to a display math environment
        content = re.sub(
            r'\\begin\{align\*\}(.*?)\\end\{align\*\}', 
            lambda m: f'\\[\n{m.group(1)}\n\\]', 
            content, flags=re.DOTALL
        )
        # Convert \begin{equation*}...\end{equation*} to a display math environment
        content = re.sub(
            r'\\begin\{equation\*\}(.*?)\\end\{equation\*\}', 
            lambda m: f'\\[\n{m.group(1)}\n\\]', 
            content, flags=re.DOTALL
        )
        return content

    def split_long_equation(match):
        eq = match.group(1)
        if len(eq) > 50:  # Adjust this threshold as needed
            parts = eq.split(',')
            return '$ ' + ' $\n$ '.join(parts) + ' $'
        return f'${eq}$'

    latex_content = custom_latex_commands(latex_content) # add custom commands
    print("=======================")
    print(latex_content)
    print("=======================")
    latex_content = handle_environments(latex_content)
    # matplotlib breaks for some reason if there are double dollar signs
    latex_content = re.sub(r'\$\$(.*?)\$\$', lambda m: f'\n${m.group(1)}$\n', latex_content, flags=re.DOTALL)

    # latex_content = re.sub(r'\$(.+?)\$', split_long_equation, latex_content)

    
    plt.text(0.5, 0.5, latex_content, size=12, ha='center', va='center', wrap=True)
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
    img_buffer.seek(0)
    
    plt.close()
    
    return img_buffer.getvalue()

def process_latex(content):
    # Replace '\\' with '\' in the content
    content = content.replace('\\\\', '\\')
    
    # Process inline LaTeX
    content = re.sub(r'\$(.+?)\$', r'$\1$', content)
    content = re.sub(r'\\\((.+?)\\\)', r'$\1$', content)
    
    # Process display LaTeX
    content = re.sub(r'\$\$(.+?)\$\$', r'\[\1\]', content, flags=re.DOTALL)
    content = re.sub(r'\\\[(.+?)\\\]', r'\[\1\]', content, flags=re.DOTALL)
    
    return content

def format_question_in_latex(question, answer):
    return r"""
\textbf{Question:}
    \n\n
%s
    
\textbf{Answer:}
 \n\n   
%s
""" % (question, answer)

def process_and_send_emails():
    question_sets_dir = QUESTION_SETS_DIR
    for set_dir in os.listdir(question_sets_dir):
        set_path = os.path.join(question_sets_dir, set_dir)
        if os.path.isdir(set_path):
            with open(os.path.join(set_path, "config.json"), 'r') as config_file:
                config = json.load(config_file)
            
            internal_name = config["internal_name"]
            subject_title = config["subject_title"]
            keys_are_questions = config["keys_are_question"]
            qa_pairs_file = os.path.join(set_path, config["qa_pairs_file"])
            num_questions = config.get("num_questions", 2)
            question_algorithm = config.get("question_algorithm", "least_recently_chosen")
            paused = config.get("paused", "false")

            if internal_name != 'lin_alg':
                continue

            if paused == "true":
                print(f"Paused: {internal_name}")
                continue

            print(qa_pairs_file)

            processed_dict = read_processed_files(internal_name)
            
            with open(qa_pairs_file, 'r', encoding='utf-8') as file:
                qa_pairs = json.load(file)
            
            picking_algorithm = get_picking_algorithm(question_algorithm)
            selected_questions = picking_algorithm(qa_pairs, processed_dict, num_questions)
            
            print(selected_questions)
            content = ''
            image_dict = {}
            
            for i, question in enumerate(selected_questions):
                current_content = qa_pairs[question]
                if keys_are_questions == "true":
                    print(f"Processing question: {question}")
                    print(f"Answer: {qa_pairs[question]}")
                    latex_content = f"Question: {question}\n\nAnswer: {qa_pairs[question]}"
                else:
                    latex_content = current_content

                latex_image = latex_to_image(latex_content)
                if latex_image is not None:
                    cid = f"latex_img_{i}"
                    image_dict[cid] = latex_image
                    content += f'<img src="cid:{cid}" alt="LaTeX content"><br><br>'
                else:
                    content += f'<pre>{html.escape(latex_content)}</pre><br><br>'

                # Process [IMAGE_WORD] tags
                parts = re.split(r'(\[IMAGE_WORD\]\(.*?\))', current_content)
                for part in parts:
                    if part.startswith('[IMAGE_WORD]'):
                        image_filename = re.search(r'\((.*?)\)', part).group(1)
                        images_dir = os.path.join(set_path, "images")
                        full_image_path = find_image_file(images_dir, image_filename)
                        if full_image_path:
                            cid = f"img_{len(image_dict)}"
                            image_dict[cid] = full_image_path
                            content += f'<img src="cid:{cid}" alt="{image_filename}"><br><br>'
                        else:
                            print(f"Warning: Image not found: {image_filename}")
            
            send_email(content, f"Question Digest: {subject_title}", image_dict)
            write_processed_files(selected_questions, internal_name)

if __name__ == '__main__':
    process_and_send_emails()
