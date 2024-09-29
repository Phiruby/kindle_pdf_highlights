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

def generate_qa_pairs(content, images=None, model="gpt-4-vision-preview", num_pairs="3-5"):
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    messages = [
        {
            "role": "system",
            "content": f"Generate {num_pairs} question-answer pairs based on the given content and images if provided."
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

    print(messages)
    if not images or len(messages[1]["content"]) <= 1:
        print("No images provided or all image encodings failed")
        return None
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000
        )
        
        if hasattr(response, 'choices') and len(response.choices) > 0:
            qa_pairs = response.choices[0].message.content
            return qa_pairs
        else:
            raise Exception("Unexpected response format from OpenAI API")
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        raise

# Example usage:
# qa_pairs = generate_qa_pairs("Your content here", images=["path/to/image1.png", "path/to/image2.png"])
# print(qa_pairs)