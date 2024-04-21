import os 
from config import QUESTION_OUTPUT_FOLDER
from dotenv import load_dotenv, dotenv_values

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from requests import HTTPError
from matplotlib import pyplot as plt
import matplotlib
import easylatex2image
from easylatex2image import latex_to_image

q_path = os.path.join(os.getcwd(), QUESTION_OUTPUT_FOLDER)
assert os.path.exists(q_path), "No questions and answer folder found. Make sure to create them!"
assert len(os.listdir(q_path)) > 0, "Nothing found inside the questions directory. Make sure to add questions!"

load_dotenv()
EMAIL = os.getenv("SENDER_MAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def convert_latex2img(latex_str, image_name="temp_latex_image.png"):
    """Converts LaTeX string to a base64-encoded PNG image."""
    packages_and_commands = r"""\usepackage[parfill]{parskip}
    \usepackage[german]{varioref}
    \usepackage{url}
    \usepackage{amsmath} 
    \usepackage{dcolumn}
    \usepackage{tikz}
    \usetikzlibrary{shapes,arrows}
    \usetikzlibrary{intersections}
    \usepackage[all,cmtip]{xy}
    """

    content = r"""
    \xymatrix{M \ar[d]_\kappa \ar[r]^f & A\\ K \ar[ur]_{f_K}}
    """
    path = os.path.join(os.getcwd(), 'temp', 'output.jpg')
    pillow_image = latex_to_image(packages_and_commands,content,path,dpi=500,img_type="JPEG")
    print(pillow_image)
        


def generate_html_content():
    latex_str = "x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}"
    image_base64 = latex_to_image(latex_str)
    html_content = f'<html><body><img src="data:image/png;base64,{image_base64}"><p>Hopefully something rendered!</p></body></html>'
    return html_content

def send_email():
    sender_email = EMAIL
    receiver_email = os.getenv("RECEIVER_MAIL")
    password = EMAIL_PASSWORD

    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Sending First Mail"

    html_content = generate_html_content()

    part = MIMEText(html_content, "html")
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

# send_email()
latex = "A combination of both text and latex component. Let's see what happens! \(a\neq b\Longleftrightarrow b\neq a\)"
convert_latex2img(latex)
