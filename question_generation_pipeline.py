import os
import json
import openai
from ebooklib import epub
import ebooklib
from PyPDF2 import PdfReader
import unicodedata
import re

# Set your OpenAI API key here
openai.api_key = os.environ.get("OPEN_AI_KEY")

# Define your list of relevant books
# If empty, all books will be processed
RELEVANT_BOOKS = []  # Replace with your book titles

# Define the paths to your Kindle clippings and books directory
CLIPPINGS_FILE_PATH = "D:\\documents\\My Clippings.txt"
BOOKS_DIRECTORY = "D:\documents\Downloads\Items01"  # Path to the directory containing your books
PROCESSED_HIGHLIGHTS_FILE = "processed_highlights.json"

# Load processed highlights
def load_processed_highlights():
    if os.path.exists(PROCESSED_HIGHLIGHTS_FILE):
        with open(PROCESSED_HIGHLIGHTS_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    print("No processed highlights json file found! Will create one.")
    return {}

# Save processed highlights
def save_processed_highlights(processed_highlights):
    with open(PROCESSED_HIGHLIGHTS_FILE, 'w', encoding='utf-8') as file:
        json.dump(processed_highlights, file, indent=4)

def normalize_text(text):
    """
    Normalize the text to remove special characters and hidden expressions.
    """
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text.lower().strip()

def find_book_file(book_title):
    """
    Automatically locates the file path of a book based on its title within the BOOKS_DIRECTORY.
    """
    normalized_book_title = normalize_text(book_title)
    if (normalized_book_title != book_title):
        return None # return None if the title has special characters
    
    for file in os.listdir(BOOKS_DIRECTORY):
        normalized_file_name = normalize_text(file)
        if normalized_book_title in normalized_file_name and file.endswith(('.epub', '.pdf')):
            return os.path.join(BOOKS_DIRECTORY, file)
    
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

        # Skip entries that are not highlights
        if "Note" in lines[1] or "Bookmark" in lines[1]:
            continue

        book_title = lines[0].strip()
        highlight = lines[-1].strip()

        # Extract page number if available
        page_number = None
        for line in lines:
            if "Your Highlight on page" in line:
                # Extract page number(s) from the line
                page_number_match = re.search(r'page\s+(\d+)(?:-\d+)?', line)
                if page_number_match:
                    page_number = int(page_number_match.group(1))
                break

        # Check if the book is in the relevant books list;
        # If RELEVANT_BOOKS is empty, all books will be processed
        if any(relevant_book.lower() in book_title.lower() for relevant_book in RELEVANT_BOOKS) or RELEVANT_BOOKS == []:
            if book_title not in highlights:
                highlights[book_title] = []
            highlights[book_title].append({
                "highlight": highlight,
                "page_number": page_number
            })

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

def clean_text(text):
    """
    Cleans the text by removing extra spaces, newlines, and normalizing the encoding.
    """
    text = text.replace('\n', ' ')  # Replace newlines with spaces
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    return text.strip().lower()  # Strip leading/trailing spaces and convert to lowercase

def extract_context_from_pdf(file_path, highlight_text, page_number):
    """
    Extracts the context from a specific page in a PDF file around a given highlight
    by searching for the highlight in the specified page.

    Args:
        file_path (str): The path to the PDF file
        highlight_text (str): The highlight text to search for
        page_number (int): The page number to search in

    Returns:
        str: The context around the highlight, or an empty string if the highlight is not found
    """
    reader = PdfReader(file_path)  # Read the PDF file
    context = ""  # Initialize the context string

    # Adjust page_number to be zero-indexed
    page_index = page_number - 1

    if page_index < 0 or page_index >= len(reader.pages):
        print(f"Page number {page_number} is out of range in the PDF.")
        return context

    page = reader.pages[page_index]
    page_text = page.extract_text()  # Extract the text from the page

    if page_text:
        # Clean the highlight and page text for better matching
        clean_highlight = clean_text(highlight_text)
        clean_page_text = clean_text(page_text)

        # Check if the cleaned highlight is in the cleaned page text
        if clean_highlight in clean_page_text:
            # If it is, find the start and end indices of the highlight in the original text
            original_start_index = page_text.lower().index(clean_highlight)
            start_index = max(0, original_start_index - 500)
            end_index = min(len(page_text), original_start_index + len(highlight_text) + 500)

            # Extract the context from the page text
            context = page_text[start_index:end_index]

    return context  # Return the context, or an empty string if the highlight is not found

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
        for entry in book_highlights:
            highlight = entry["highlight"]
            page_number = entry["page_number"]

            if highlight in processed_highlights[book_title]:
                print(f"Skipping already processed highlight: {highlight}")
                continue

            if book_file_path.endswith(".epub"):
                context = extract_context_from_epub(book_file_path, highlight)
            elif book_file_path.endswith(".pdf"):
                context = extract_context_from_pdf(book_file_path, highlight, page_number)
            else:
                print(f"Unsupported file format for book: {book_title}")
                continue

            if context:
                # questions = generate_questions(context, highlight)
                # print(f"Generated questions for highlight: {highlight}\n{questions}\n")

                # Mark the highlight as processed
                processed_highlights[book_title].append(highlight)

                # Save the updated processed highlights
                save_processed_highlights(processed_highlights)

if __name__ == "__main__":
    process_books()