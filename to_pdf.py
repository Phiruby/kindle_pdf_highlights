import os
import re
import PyPDF2
from typing import List, Dict, Union
from config import Note, Highlight

from extractor import extract_highlights
from config import PATH_TO_KINDLE, OUTPUT_DATA_FOLDER, OFFSETS_BY_BOOK_NAME, CONTENT_SPLIT_KEY

# Function to extract text from specific page of PDF
'''
pdf_path: the path to the book pdf (inside kindle)
page_numbers: a list storing the page numbers we want to read. If it is not a list of int, converts it to an int
contents: a list of highlights / notes for a specific book
existing_highlights: returned from get_all_highlights()
'''
def extract_text_from_pdf(contents: List[Union[Highlight, Note]], book_name: None, existing_highlights: None):
    # Open the PDF file
    offset = 0
    #some books will require an offset.
    if book_name in OFFSETS_BY_BOOK_NAME.keys():
        offset = OFFSETS_BY_BOOK_NAME[book_name]
    print("Offset, book > ", offset, repr(book_name))

    
    partial_path = os.path.join(PATH_TO_KINDLE, 'documents', 'Downloads', 'Items01')
    pdf_path = find_pdf_path(book_name, partial_path) #gets the book pdf path

    if pdf_path is None:
        print("The following path provided is null. This could be because this file is not a PDF, but has a highlight. Skipping for now.")
        return None

    with open(pdf_path, 'rb') as file:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(file)
        # loop through each highlight / note in the book
        content_texts = []
        for index, content in enumerate(contents):
            #checks if this highlight already exists
            if check_if_highlight_exists(content.content, content.page, book_name, existing_highlights):
                # print(content.__dict__)
                content_texts.append(None)
                continue 
  
        # Initialize an empty string to store text from specified pages
            highlighted_content = content.content 
            page_numbers = content.page.split("-")

            text = "HIGHLIGHTED CONTENT: "+highlighted_content+f' {CONTENT_SPLIT_KEY}\n' if highlighted_content is not None else ''
            intified = int(page_numbers[0].strip())
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
            content_texts.append(text)
            # text = ''
        return content_texts

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
def make_pdf_from_highlight(data_folder: str, highlights: Dict[str, List[Union[Note, Highlight]]]):
    # for idx, highlight in enumerate(highlights):
        # Extract text from PDF based on page numbers

    book_contents_dict = {}
    existing_highlights = get_all_highlights()
    for book_name in highlights.keys():

        texts = extract_text_from_pdf(highlights[book_name], book_name, existing_highlights)
        book_contents_dict[book_name] = texts

    #iterate through each book
    index_sep = 0
    for book in book_contents_dict.keys():
        #some books may have no highlights OR they are not pdf (eg: Data Engineering Book of mine)
        # in the case that the file already exists
        if book_contents_dict[book] is None or len([x for x in book_contents_dict[book] if x is not None]) == 0: 
            continue 
        print(f"Proceeding to write to file: {book}")
        #iterate through each read item
        for index, text in enumerate(book_contents_dict[book]):
            if text is None: 
                continue #text already saved
            # Save extracted text to a file in the data folder
            author = highlights[book][index].author
            pages = highlights[book][index].page
            #in the case of multiple highlights on the same page
            if os.path.exists(os.path.join(os.getcwd(), data_folder, f"info_{book}__{pages}.txt")):
                output_file = os.path.join(os.getcwd(), data_folder, f"info_{book}__{pages}.txt"+str(index_sep))
                index_sep+=1
            else:
                output_file = os.path.join(os.getcwd(), data_folder, f"info_{book}__{pages}.txt")

            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(text)
    try:
        print(f"Highlight text saved to {output_file}")
    except Exception as e:
        print("Everything is already saved! Nothing changed.")

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
        # for idx, highlight in enumerate(highlights):
        #     # Extract text from PDF based on page numbers
        # partial_path = os.path.join(PATH_TO_KINDLE, 'documents', 'Downloads', 'Items01')
        # pdf_path = find_pdf_path(highlight.title, partial_path) #gets the book pdf path

        # Save extracted text to a file in the data folder
        # output_file = os.path.join(OUTPUT_DATA_FOLDER, f"highlight_{idx + 1}.txt")
        make_pdf_from_highlight(OUTPUT_DATA_FOLDER, highlights)

            # print(f"Highlight {idx + 1} text saved to {output_file}")
    else:
        print("The 'My Clippings.txt' file was not found. Please provide the correct path.")

'''
gets all highlights, stored in the following format:
{
    name: (name of the book)
    page: the first page number of the highlight
    content: the highlighted content
}
The above dictionary will be in a list
'''
def get_all_highlights():
    highlights_stored_path = os.path.join(os.getcwd(), OUTPUT_DATA_FOLDER)
    all_highlights_dict = []
    for highlight in os.listdir(highlights_stored_path):
        with open(os.path.join(highlights_stored_path, highlight), 'r', encoding='utf-8') as file:
            highlighted_cont, text = file.read().split(CONTENT_SPLIT_KEY)
            new_dict = {}
            new_dict['content'] = highlighted_cont[20:].strip() if highlighted_cont.startswith("HIGHLIGHTED CONTENT") else None 
            name_and_page = highlight[5:].split('.txt')[0] #removes info_ and .txt 
            name, pages = name_and_page.split('__')
            page = pages.split("-")[0]
            new_dict['page'] = int(page)
            new_dict['name'] = name.strip()
            all_highlights_dict.append(new_dict)
    
    return all_highlights_dict

'''
Returns a boolean if the highlight is already saved
Params
    content: the highlighted text / note
    page: the pages ofthe highlight, formated x-y
    book: the title of th book
'''
def check_if_highlight_exists(content: str, page: str, book: str, all_highlights: None):
    assert all_highlights is not None, "Make sure you passed in the right highlights by calling get_all_highlights()"

    new_dict = {
        'content': content.strip(),
        'page': int(page.split('-')[0]),
        'name': book.strip()
    }
    # print(new_dict)
    return (new_dict in all_highlights)



if __name__ == "__main__":
    main()
    # print(get_all_highlights())
    # # tester = {'content': ' then ', 'page': 67, 'name': '\ufeffmain_notes'}
    # # print(tester in get_all_highlights())
    # print(check_if_highlight_exists(' then ', page="67-67", book='\ufeffmain_notes', all_highlights=get_all_highlights()))
