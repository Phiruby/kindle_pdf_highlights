import json
import openai
from openai import OpenAI

# Load your OpenAI API key
client = OpenAI()

def generate_question_answer(highlight, context):
    prompt = f"""
    Highlight: {highlight}\n
    
    Context: {context}\n\n
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", "content": """You will be given a highlight and context, and you will need to generate 1-3 question
                 and answer pairs (depending on how many questions are required to cover all the information in the highlight) based 
            on the provided information. The fewer questions you generate, the better. The questions should be primarily knowledge questions. 
            For highlights related to math propositions / theorems / corollary, the question and answer pair
            should be "Prove XYZ" and the answer should be the proof. Do not make questions that rely on the proposition number (for example, I do not memorize each theorem by their numbers).
            Any code snippets should be wrapped around markdown code blocks; any 
            math equations should be in latex. 
            The questions should be in the following format, in markdown format: 
            # Question:\n ```[Question]```\n # Answer:\n ```[Answer]```."""
            },
            {"role": "user", "content": prompt}
        ],
    )
    print(response.choices[0].message.content.strip())
    return response.choices[0].message.content.strip()

# Load the highlight cache
with open('highlight_cache.json', 'r') as file:
    highlight_cache = json.load(file)

# Load the existing question-answer pairs if they exist
try:
    with open('generated_qa_pairs.json', 'r') as file:
        qa_pairs = json.load(file)
except FileNotFoundError:
    print("No existing question-answer pairs found. Creating new file.")
    qa_pairs = {}

# Iterate through each highlight-context pair and generate question-answer pairs
for highlight, context in highlight_cache.items():
    if highlight in qa_pairs:
        print(f"Skipping already processed highlight: {highlight}")
        continue
    qa_pair = generate_question_answer(highlight, context)
    qa_pairs[highlight] = qa_pair

# Optionally, save the generated question-answer pairs to a new JSON file
with open('generated_qa_pairs.json', 'w') as file:
    json.dump(qa_pairs, file, indent=4)
