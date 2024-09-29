from openai import OpenAI

def generate_qa_pairs(content, model="gpt-4o-mini", num_pairs="3-5"):
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"Generate {num_pairs} question-answer pairs based on the following content:"},
            {"role": "user", "content": content}
        ]
    )
    return response.choices[0].message.content