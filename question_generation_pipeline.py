import os
import json
import openai
from ebooklib import epub
from PyPDF2 import PdfReader

# Set your OpenAI API key here
openai.api_key = os.environ.get("OPEN_AI_KEY")

# Define your list of relevant books
# If empty, all books will be processed
RELEVANT_BOOKS = ["Book Title 1", "Book Title 2"]  # Replace with your book titles

# Define the paths to your Kindle clippings and books directory
CLIPPINGS_FILE_PATH = "path_to_clippings/My Clippings.txt"
BOOKS_DIRECTORY = "path_to_books"  # Path to the directory containing your books
PROCESSED_HIGHLIGHTS_FILE = "processed_highlights.json"

# Load processed highlights
def load_processed_highlights():
    if os.path.exists(PROCESSED_HIGHLIGHTS_FILE):
        with open(PROCESSED_HIGHLIGHTS_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

# Save processed highlights
def save_processed_highlights(processed_highlights):
    with open(PROCESSED_HIGHLIGHTS_FILE, 'w', encoding='utf-8') as file:
        json.dump(processed_highlights, file, indent=4)

def find_book_file(book_title):
    """
    Automatically locates the file path of a book based on its title within the BOOKS_DIRECTORY.
    """
    for root, dirs, files in os.walk(BOOKS_DIRECTORY):
        for file in files:
            if book_title.lower() in file.lower():
                if file.endswith(('.epub', '.pdf')):
                    return os.path.join(root, file)
    return None

def extract_highlights_from_clippings(clippings_file):
    highlights = {}
    with open(clippings_file, 'r', encoding='utf-8') as file:
        content = file.read()

    entries = content.split("==========")
    for entry in entries:
        lines = entry.strip().split('\n')
        if len(lines) < 3:
            continue

        book_title = lines[0].strip()
        highlight = lines[-1].strip()

        # Check if the book is in the relevant books list;
        # If RELEVANT_BOOKS is empty, all books will be processed
        if any(relevant_book.lower() in book_title.lower() for relevant_book in RELEVANT_BOOKS) or RELEVANT_BOOKS == []:
            if book_title not in highlights:
                highlights[book_title] = []
            highlights[book_title].append(highlight)

    return highlights

def extract_context_from_epub(file_path, highlight_text):
    book = epub.read_epub(file_path)
    context = ""
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content().decode('utf-8')
            if highlight_text in content:
                start_index = max(0, content.index(highlight_text) - 500)
                end_index = min(len(content), content.index(highlight_text) + len(highlight_text) + 500)
                context = content[start_index:end_index]
                break
    return context

def extract_context_from_pdf(file_path, highlight_text):
    reader = PdfReader(file_path)
    context = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if highlight_text in page_text:
            start_index = max(0, page_text.index(highlight_text) - 500)
            end_index = min(len(page_text), page_text.index(highlight_text) + len(highlight_text) + 500)
            context = page_text[start_index:end_index]
            break
    return context

def generate_questions(context, highlight):
    prompt = f"""
    Given the following context from a book, generate a list of questions that could be useful for spaced repetition learning. The questions should focus on testing key concepts, important details, and the significance of the highlighted text.

    Context:
    {context}

    Highlight:
    {highlight}

    Please provide 3-5 questions.
    """

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.7,
    )

    return response.choices[0].text.strip()

def process_books():
    processed_highlights = load_processed_highlights()
    highlights = extract_highlights_from_clippings(CLIPPINGS_FILE_PATH)

    for book_title, book_highlights in highlights.items():
        print(f"Processing book: {book_title}")
        
        # Automatically find the book file (either .epub or .pdf)
        book_file_path = find_book_file(book_title)
        
        if not book_file_path:
            print(f"Could not find a file for the book: {book_title}")
            continue

        # Ensure the book is in the processed highlights record
        if book_title not in processed_highlights:
            processed_highlights[book_title] = []

        # Determine the file format and extract context accordingly
        for highlight in book_highlights:
            if highlight in processed_highlights[book_title]:
                print(f"Skipping already processed highlight: {highlight}")
                continue

            if book_file_path.endswith(".epub"):
                context = extract_context_from_epub(book_file_path, highlight)
            elif book_file_path.endswith(".pdf"):
                context = extract_context_from_pdf(book_file_path, highlight)
            else:
                print(f"Unsupported file format for book: {book_title}")
                continue

            if context:
                questions = generate_questions(context, highlight)
                print(f"Generated questions for highlight: {highlight}\n{questions}\n")

                # Mark the highlight as processed
                processed_highlights[book_title].append(highlight)

                # Save the updated processed highlights
                save_processed_highlights(processed_highlights)

if __name__ == "__main__":
    process_books()
