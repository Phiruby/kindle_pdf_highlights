import os
import base64
import requests
from openai import OpenAI
from PIL import Image
import io
import imghdr

def encode_image(image_path):
    try:
        print(os.path.exists(image_path))
        print("^^")
        with Image.open(image_path) as img:
            img = img.convert('RGBA')  # Convert to RGBA to preserve transparency
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(os.path.exists(image_path))
        print(f"Error processing image {image_path}: {str(e)}. Skipping.")
        return None

def generate_qa_pairs(content, images=None, model="gpt-4o-mini", num_pairs="3-5"):
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    SYSTEM_PROMPT = """
    You will be given a markdown file written in Obsidian (possibly with latex and images). For each file, generate a
    question-answer pair in the form of a JSON object with the following schema:
    {
        "question1": "answer1",
        "question2": "answer2",
        "question3": "answer3",
        ...
    }
    And nothing else should be included in the response. The questions should cover key ideas, concepts, and details from
    the notes. This includes equations, definitions, theorems, and important observations. 
    
    Do NOT ask questions that are not knowledge-based questions. For example, do not ask questions such as "What does equation X imply about Y?".
    Rather, ask questions in the form of "What is..." (though not all questions are required to be in this form. This is just an example to clarify that
    the questions should be knowledge-based).

    The number of questions you create is up to you. However, they should be diverse and cover all the important ideas in the file. But if you
    think that the file is not very long, you can generate fewer questions. The fewer questions, the better.

    The answer should be thorough, as though the user has read the file in the past but has forgotten most of the details. This may include
    briefly defining technical terms, summarizing key ideas, or explaining the reasoning behind a particular observation.
    
    Make sure to use latex that uses $ instead of \(. Do NOT use \( or \[. Wrap the required parts in $ latex blocks. And do not add double '\\' before a symbol. Only one is fine, as in overleaf style.

    While generating the questions, DO NOT ASSUME that the user is has read the file recently. So do not generate questions that refer to
    a theorem or fact by their numbers / labels. Always state the theorem / fact in full while generating the questions. Likewise, 
    never refer to the specific document or document title. Assume these notes have never been read by the user. Never ask questions such as "What is XYZ as described in the notes?".
    The reader may have never read the notes before.
    """

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ]
        }
    ]

    # Add images to the message if provided
    if images:
        for image_path in images:
            base64_image = encode_image(image_path)
            if base64_image:
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })
                print(f"Successfully encoded image: {image_path}")


    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000
        )
        
        if hasattr(response, 'choices') and len(response.choices) > 0:
            qa_pairs = response.choices[0].message.content
            print(qa_pairs)
            return qa_pairs
        else:
            raise Exception("Unexpected response format from OpenAI API")
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        raise Exception(f"Error calling OpenAI API: {str(e)}")

# Example usage:
# qa_pairs = generate_qa_pairs("Your content here", images=["path/to/image1.png", "path/to/image2.png"])
# print(qa_pairs)