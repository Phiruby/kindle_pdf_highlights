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

def generate_qa_pairs(content, file_name, images=None, model="gpt-4o", num_pairs="3-5"):
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    SYSTEM_PROMPT = """
    You will be given a markdown file written in Obsidian (possibly with LaTeX and images). It will contain the topic of the notes in the last line. Based on this topic, generate a question-answer pair in the form of a JSON object with the following schema:
    {
        "question1": "answer1",
        "question2": "answer2",
        "question3": "answer3",
        ...
    }

    ### Response Requirements:
    - Only return the JSON object with the questions and answers. Do not include any extra text.

    ### Question Content:
    - Focus on **key ideas, concepts, equations, definitions, theorems**, and observations directly related to the topic.
    - Avoid vague or overly generic questions.

    ### Number of Questions:
    - Provide as **few questions as possible**, but ensure they cover all critical points.

    ### Answer Requirements:
    - The answers should be **thorough and detailed**, assuming the user has never read the file before.
    - Include brief definitions or explanations of technical terms, equations, and reasoning as necessary.

    ### LaTeX Usage:
    - Use **$ for inline LaTeX** and ensure it can be parsed with **double backslashes (\\\\)** for symbols.

    ### General Instructions:
    - Avoid referring to specific document titles, theorem numbers, or labels.
    - For machine learning algorithms, focus on how the algorithms work (mathematically) alongside its implementation.
        - Avoid asking questions about the definition of a term. Provide the definition in the answer if the answer uses it.
        - Avoid asking vague questions such as "How do transformers work?". Be more specific such as "What is multi-head attention?". The answers should go into the math.
        - The answers should be technical and detailed
    - Avoid asking questions that ask how one thing relates to another. Focus on how the content works.
    - If you are referencing anything in the notes, make sure to include it in the question or answer (eg: code blocks, equations, etc.)
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
                    "text": f"The topic of the notes is: {file_name}\n\n{content}"
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
            max_tokens=8000
        )
        
        if hasattr(response, 'choices') and len(response.choices) > 0:
            qa_pairs = response.choices[0].message.content
            # print(qa_pairs)
            return qa_pairs
        else:
            raise Exception("Unexpected response format from OpenAI API")
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        raise Exception(f"Error calling OpenAI API: {str(e)}")

# Example usage:
# qa_pairs = generate_qa_pairs("Your content here", images=["path/to/image1.png", "path/to/image2.png"])
# print(qa_pairs)