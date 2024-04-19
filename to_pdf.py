import os
import re
import PyPDF2
from typing import List, Dict, Union
from config import Note, Highlight

from extractor import extract_highlights
from config import PATH_TO_KINDLE, OUTPUT_DATA_FOLDER, OFFSETS_BY_BOOK_NAME

# Function to extract text from specific page of PDF
'''
pdf_path: the path to the book pdf (inside kindle)
page_numbers: a list storing the page numbers we want to read. If it is not a list of int, converts it to an int
'''
def extract_text_from_pdf(pdf_path: str, page_numbers: List, book_name: None, highlighted_content: None):
    # Open the PDF file
    if pdf_path is None:
        print("The following path provided is null. This could be because this file is not a PDF, but has a highlight. Skipping for now.")
        return None
    offset = 0
    #some books will require an offset.
    if book_name in OFFSETS_BY_BOOK_NAME.keys():
        offset = OFFSETS_BY_BOOK_NAME[book_name]
    print("Offset, book > ", offset, book_name)

    with open(pdf_path, 'rb') as file:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(file)
        # Initialize an empty string to store text from specified pages
        text = "HIGHLIGHTED CONTENT: "+highlighted_content+'\n' if highlighted_content is not None else ''
        intified = int(page_numbers[0])
        # read pages +-1 above the target
        page_numbers = [intified-1, intified, intified+1]
        # Iterate over page numbers
        for page_number in page_numbers:
            page_number = page_number - 1 + offset # Page numbers are 0-based in PyPDF2
            # Check if the page number is valid
            if 0 <= page_number < len(pdf_reader.pages):
                # Extract text from the specified page
                page_text = pdf_reader.pages[page_number].extract_text()
                text += page_text
        return text

'''
Returns the path to the pdf of the book with book_nme
Assumed conventions: the target pdf is the ONLY file starting with book_name; though there can be directories 
starting with the same name

Returns: the path to the file starting with book_name
'''
def find_pdf_path(book_name, folder_path):
    # print(folder_path, " The path to the folder")
    book_name = book_name.strip()
    book_name = book_name.split(":")[0] # i believe that kindle stops the pdf aftre the colon
    # print(book_name+ "The book name")

    for file_name in os.listdir(folder_path):
        path = os.path.join(folder_path, file_name)

        # print(repr(book_name), repr(file_name.strip()[:len(book_name)-1]), file_name.startswith(book_name[1:]), file_name.startswith(book_name[:len(file_name)]))
        clean_file_name = file_name.split("-cdeKey")[0]
        # i put book[1:] because printing repr(book_name) has a BOM in front of it (byte order mark)
        if os.path.isfile(path) and (file_name.strip().startswith(book_name[1:]) or file_name.startswith(book_name[:len(file_name)])) and file_name[-4:] == ".pdf":
            return path
    return None

'''
params:
    data_folder: the output folder where data is uploaded
    highlights: the highlights list, from extract_highlights
'''
def make_pdf_from_highlight(data_folder: str, highlight: List[Union[Note, Highlight]], pdf_path: str, book_name=None):
    # for idx, highlight in enumerate(highlights):
        # Extract text from PDF based on page numbers
    highlighto = highlight.__dict__
    marked_content = None
    if type(highlight) == Highlight:
        marked_content = highlighto['content']
    text = extract_text_from_pdf(pdf_path, highlighto['page'].split('-'), book_name, marked_content)

    if text == None:
        print("Did not recieve any text ^^")
        print("Exiting this book")
        return None

    # Save extracted text to a file in the data folder
    output_file = os.path.join(os.getcwd(), data_folder, f"info_{highlighto['title']}_{highlighto['author']}_{highlighto['page']}.txt")
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(text)

    print(f"Highlight text saved to {output_file}")

# Main function
def main():
    # Path to the "My Clippings.txt" file on your Kindle
    clippings_file = os.path.join(PATH_TO_KINDLE, 'documents', 'My Clippings.txt')

    # Check if the file exists
    if os.path.exists(clippings_file):
        # Extract highlights and notes
        highlights = extract_highlights(clippings_file)

        # Create a data folder if it doesn't exist
        if not os.path.exists(OUTPUT_DATA_FOLDER):
            os.makedirs(OUTPUT_DATA_FOLDER)

        # Process each highlight
        for idx, highlight in enumerate(highlights):
            # Extract text from PDF based on page numbers
            partial_path = os.path.join(PATH_TO_KINDLE, 'documents', 'Downloads', 'Items01')
            pdf_path = find_pdf_path(highlight.title, partial_path) #gets the book pdf path

            # Save extracted text to a file in the data folder
            # output_file = os.path.join(OUTPUT_DATA_FOLDER, f"highlight_{idx + 1}.txt")
            make_pdf_from_highlight(OUTPUT_DATA_FOLDER, highlight, pdf_path, highlight.title)

            # print(f"Highlight {idx + 1} text saved to {output_file}")
    else:
        print("The 'My Clippings.txt' file was not found. Please provide the correct path.")

if __name__ == "__main__":
    main()
