from config import get_prompt, OUTPUT_DATA_FOLDER, QUESTION_OUTPUT_FOLDER, CONTENT_SPLIT_KEY
import os 

from dotenv import load_dotenv, dotenv_values
from openai import OpenAI

data_path = os.path.join(os.getcwd(), OUTPUT_DATA_FOLDER)
assert os.path.exists(data_path), "The data storage folder is not found. Please make sure the data is loaded"
assert len(os.listdir(data_path)) > 0, "No data found inside the storage"

load_dotenv()
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
NUM_QUESTION_PAIRS = 2

client = OpenAI(api_key = OPEN_AI_KEY)

#make output folder if not there yet
question_folder_path = os.path.join(os.getcwd(), QUESTION_OUTPUT_FOLDER)
if not os.path.exists(question_folder_path):
    os.mkdir(question_folder_path)

def read_file_and_create_question(filename: str, num_questions: int) -> None:
    if filename not in os.listdir(data_path):
        # print(repr(os.listdir(data_path)[-11]))
        raise Exception(f"Could not find the following in the data: {filename}")
    
    file_path = os.path.join(data_path, filename)
    question_answers = ''
    with open(file_path, 'rb') as file:
        file_contents = file.read()
        file_contents = file_contents.decode('utf-8')  # Assuming UTF-8 encoding
        # print(type(file_contents))
        if not file_contents.startswith("HIGHLIGHTED CONTENT"):
            return None #if it is a note, then we dont want to create question-answer pair
        #now split to highlighted and text
        highlight, page_text = file_contents.split(CONTENT_SPLIT_KEY)
        highlight = highlight[20:] #removes the "HIGHLIGHTED CONTENT:"

        completion = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "user", "content": get_prompt(highlight, page_text, num_questions)}
            ],
            frequency_penalty=0.19,
            temperature = 1,
            max_tokens = 400
        )
        question_answers = completion.choices[0].message.content
    
    output_path = os.path.join(os.getcwd(), QUESTION_OUTPUT_FOLDER, filename)
    with open(output_path, 'w', encoding='utf-8') as file:
        print(question_answers)
        file.write(question_answers)
       

# read_file_and_create_question("info_\ufeffalgebraic-number-theory__53 .txt", NUM_QUESTION_PAIRS)

'''
creates question files for all highlights within the books stored in the list books
params
---
    books: the list of book (their names)
'''

def create_question_files(books):
    data_path = os.path.join(os.getcwd(), OUTPUT_DATA_FOLDER)
    for file in os.listdir(data_path):
        if file_is_in_list(file, books):
            print(f"Now creating questions for {file}")
            read_file_and_create_question(file, NUM_QUESTION_PAIRS)

'''
checks if any element in file_list is a substring of file
'''
def file_is_in_list(file: str, file_list: str):
    for filos in file_list:
        if filos in file:
            return True
    return False

BOOKS_I_WANT = ["modern-ml-algo", "main_notes"]
create_question_files(BOOKS_I_WANT)