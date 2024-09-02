import os

RELEVANT_BOOKS = []  # Replace with your book titles

# Define the paths to your Kindle clippings and books directory
CLIPPINGS_FILE_PATH = "D:\\documents\\My Clippings.txt"
BOOKS_DIRECTORY = "D:\documents\Downloads\Items01"  # Path to the directory containing your books
PROCESSED_HIGHLIGHTS_FILE = "processed_highlights.json"
CACHE_FILE = "highlight_cache.json" #context around highlights are stored here
QUESTION_ANSWER_PAIRS_FILE = "generated_qa_pairs.json" # json file where question and answers are stored
PROCESSED_TEXT_FILE = os.path.join(os.getcwd(),'temp','processed_files.txt') # txt file where processed highlights are stored. Used to avoid sending the same highlight multiple times
# the characters around the highlighted text that are used to provide context for gpt to generate the question
HIGHLIGHT_CONTEXT_CHARACTER_WINDOW = 2000


