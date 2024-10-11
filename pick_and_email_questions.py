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
import pdf2image
from io import BytesIO
from PIL import Image

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
    # Prepare the LaTeX document
    latex_document = r"""
    \documentclass{article}
    \usepackage{amsmath}
    \usepackage{amssymb}
    \usepackage{color}
    \usepackage[margin=0.5in]{geometry}
    \begin{document}
    \thispagestyle{empty}
    %s
    \end{document}
    """ % latex_content

    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = os.path.join(tmpdir, "latex_content.tex")
        with open(tex_file, "w") as f:
            f.write(latex_document)

        # Compile LaTeX to PDF
        try:
            result = subprocess.run(["pdflatex", "-output-directory", tmpdir, tex_file], 
                                    check=True, capture_output=True, text=True)
            print(f"LaTeX compilation output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"Error during LaTeX compilation: {e}")
            print(f"LaTeX error output: {e.output}")
            return None

        # Check if PDF file was created
        pdf_file = os.path.join(tmpdir, "latex_content.pdf")
        if not os.path.exists(pdf_file):
            print(f"PDF file was not created at {pdf_file}")
            return None

        # Convert PDF to PNG using pdf2image with lower DPI
        try:
            images = pdf2image.convert_from_path(pdf_file, dpi=150)
        except Exception as e:
            print(f"Error converting PDF to image: {e}")
            return None
        
        # Save the first page as PNG in memory with compression
        img_buffer = BytesIO()
        images[0].save(img_buffer, format='PNG', optimize=True, quality=85)
        
        # Resize the image if it's too large
        img = Image.open(img_buffer)
        max_width = 800  # Set your desired maximum width
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
            
            # Save the resized image
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG', optimize=True, quality=85)
        
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
    
    %s
    
    \textbf{Answer:}
    
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

            if internal_name != "machine_learning":
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
                    print("Keys are questions")
                    current_content = format_question_in_latex(process_latex(question), process_latex(qa_pairs[question]))
                else:
                    current_content = process_latex(current_content)
                
                # Process content and prepare images
                processed_content = ''
                parts = re.split(r'(\[IMAGE_WORD\]\(.*?\))', current_content)
                for part in parts:
                    if part.startswith('[IMAGE_WORD]'):
                        image_filename = re.search(r'\((.*?)\)', part).group(1)
                        images_dir = os.path.join(set_path, "images")
                        full_image_path = find_image_file(images_dir, image_filename)
                        if full_image_path:
                            cid = f"img_{len(image_dict)}"
                            image_dict[cid] = full_image_path
                            processed_content += f'<img src="cid:{cid}" alt="{image_filename}">'
                        else:
                            print(f"Warning: Image not found: {image_filename}")
                    else:
                        # Generate LaTeX image for text content
                        latex_image = latex_to_image(part)
                        if latex_image is not None:
                            cid = f"latex_img_{i}_{len(image_dict)}"
                            image_dict[cid] = latex_image
                            processed_content += f'<img src="cid:{cid}" alt="LaTeX content">'
                        else:
                            print(f"Failed to generate LaTeX image for content: {part}")
                            processed_content += f'<p>Failed to render LaTeX: {part}</p>'
                
                content += processed_content + '<br><br>'
            
            send_email(content, f"Question Digest: {subject_title}", image_dict)
            write_processed_files(selected_questions, internal_name)

if __name__ == '__main__':
    process_and_send_emails()
