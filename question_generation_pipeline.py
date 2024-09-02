import os
import json
import openai
from openai import OpenAI
from ebooklib import epub
import ebooklib
from PyPDF2 import PdfReader
import unicodedata
import re
from config import OFFSETS_BY_BOOK_NAME
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

openai.api_key = os.getenv("OPENAI_API_KEY")
# Define your list of relevant books
# If empty, all books will be processed
RELEVANT_BOOKS = []  # Replace with your book titles

# Define the paths to your Kindle clippings and books directory
CLIPPINGS_FILE_PATH = "D:\\documents\\My Clippings.txt"
BOOKS_DIRECTORY = "D:\documents\Downloads\Items01"  # Path to the directory containing your books
PROCESSED_HIGHLIGHTS_FILE = "processed_highlights.json"
CACHE_FILE = "highlight_cache.json" #context around highlights are stored here

print(os.getenv("OPENAI_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_cache():
    """Load the cache from the file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Save the cache to the file."""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4)

def clean_text_with_gpt(context):
    """
    Cleans the extracted context using GPT-4.
    
    Args:
        context (str): The extracted text from the PDF.

    Returns:
        str: The cleaned text.
    """
    # prompt = f"Please clean the following text, fixing formatting issues, and making it clear and readable:\n\n{context}"
    prompt = f"""
            The following consists of extracted text from a pdf using python. It is very messy. I want you to clean it up. Convert any mathematical expressions into latex and wrap code snippets around markdown blocks.
            Do not say anything else apart from the cleaned text:
            \n\n
            {context}
            """
    
    response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": prompt},
    ]
    )

    print("CLEANING GPT RESPONSE \n ---------------- \n")
    print(response)
    
    cleaned_text = response.choices[0].message.content
    return cleaned_text

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
        if (any(relevant_book.lower() in book_title.lower() for relevant_book in RELEVANT_BOOKS) or RELEVANT_BOOKS == []) and len(highlight) > 3:
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
    print(context)
    print("EXTRACTING CONTEXT FROM EPUB FOR HIGHLIGHT: ", highlight_text)
    return context

def extract_context_from_pdf(file_path, highlight_text, page_number, book_name):
    """
    Extracts the context from a specific page in a PDF file around a given highlight,
    by searching for the highlight in the specified page and then cleaning the context
    using GPT-4 before returning it.

    Args:
        file_path (str): The path to the PDF file
        highlight_text (str): The highlight text to search for
        page_number (int): The page number to search in
        book_name (str): The name of the book (used for page offset)

    Returns:
        str: The cleaned context around the highlight, or an empty string if the highlight is not found.
    """
    # Load the cache
    cache = load_cache()
    print("EXTRACTING CONTEXT FROM PDF FOR HIGHLIGHT: ", highlight_text)

    # Check if the highlight is already cached
    if highlight_text in cache:
        print("Using cached version")
        return cache[highlight_text]

    reader = PdfReader(file_path)  # Read the PDF file
    context = ""  # Initialize the context string
    highlight_text = highlight_text.replace("\n", "")

    # Adjust page_number to be zero-indexed
    for page_index in range(len(reader.pages)):
        page = reader.pages[page_index]
        page_text = page.extract_text()  # Extract the text from the page

        # print(OFFSETS_BY_BOOK_NAME[book_name])

        if page_index < 0 or page_index >= len(reader.pages):
            print(f"Page number {page_number} is out of range in the PDF.")
            return context
 
        if page_text:
            page_text = page_text.replace("\n", "")
            
            page_text_cleaned = page_text.replace("\n", "").replace(" ", "").lower()

            # check if strings are approximately equal
            # sometimes the strings in highlights are different than the pdf (eg: "field" in pdf -> "feld" in highlight)
            if fuzz.partial_ratio(highlight_text.replace(" ", "").lower(), page_text_cleaned) > 80:
                print("PASSED PARTIAL RATION")

                match_start = process.extractOne(highlight_text, [page_text_cleaned], scorer=fuzz.partial_ratio)[1]

                # Extract the context around the found match
                start_index = max(0, match_start - 2000)
                end_index = min(len(page_text), match_start + len(highlight_text) + 2000)
                context = page_text[start_index:end_index]

                # Clean the context using GPT-4
                cleaned_context = clean_text_with_gpt(context)

                # Store the cleaned context in the cache
                cache[highlight_text] = cleaned_context
                save_cache(cache)

                return cleaned_context

    print("DID NOT FIND CONTEXT FOR THE ABOVE HIGHLIGHT!")
    return context


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
        cleaned_book_title = book_title.lstrip('\ufeff')
        if cleaned_book_title not in processed_highlights:
            
            processed_highlights[cleaned_book_title] = []

        # Determine the file format and extract context accordingly
        for entry in book_highlights:
            highlight = entry["highlight"]
            page_number = entry["page_number"]
            context = None 

            # if highlight in processed_highlights[book_title]:
            #     print(f"Skipping already processed highlight: {highlight}")
            #     continue

            if book_file_path.endswith(".epub"):
                print("Skipping .epub for now")
                # context = extract_context_from_epub(book_file_path, highlight)
            elif book_file_path.endswith(".pdf"):
                context = extract_context_from_pdf(book_file_path, highlight, page_number, book_title)
                # print("SKIPPING PDF FOR NOW")
            else:
                print(f"Unsupported file format for book: {book_title}")
                continue

            if context is not None:
                # questions = generate_questions(context, highlight)
                # print(f"Generated questions for highlight: {highlight}\n{questions}\n")

                # Mark the highlight as processed
                book_title_without_bom = book_title.lstrip('\ufeff')
                processed_highlights[book_title_without_bom].append(highlight)

                # Save the updated processed highlights
                save_processed_highlights(processed_highlights)

if __name__ == "__main__":
    process_books()