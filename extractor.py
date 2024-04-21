import os
from config import PATH_TO_KINDLE
from typing import List, Union, Dict

from config import Note, Highlight

# Function to extract highlights and notes from "My Clippings.txt" file
def extract_highlights(filepath: str) -> Dict[str, List[Union[Note, Highlight]]]:
    highlights = {}
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        title = ''
        author = ''
        content = ''
        for line in lines:
            if line.strip() == '==========':
                # Append highlight to the list
                content_type = content[7:11] #note or highlight?
                my_obj = None
                if content_type == "Note":
                    my_obj = Note(title, author, content)
                else: #if highlight
                    my_obj = Highlight(title, author, content)

                #check if book is already in the highlight keys
                if my_obj.title not in highlights.keys():
                    highlights[my_obj.title] = []
                highlights[my_obj.title].append(my_obj)
                # Reset variables for the next highlight
                title = ''
                author = ''
                content = ''
            elif not title:
                # First line contains title and author
                title_author = line.split(' (')
                title = title_author[0].strip()
                if len(title_author) > 1:
                    author = title_author[1].replace(')\n', '').strip()
            else:
                # Subsequent lines contain highlight content
                content += line.strip() + '\n'
    return highlights

def print_highlights(highlights):
    # Print highlights
    for book in highlights.keys():
        print(f"-------------BOOK: {book}---------------")
        for content in highlights[book]:
            new_highligh = content.__dict__
            print(f"Title: {new_highligh['title']}")
            print(f"Author: {new_highligh['author']}")
            print(f"Pages: {new_highligh['page']}")
            print("Content:")
            print(new_highligh['content'])
            print("\n")

def main():
    # Path to the "My Clippings.txt" file on your Kindle
    clippings_file = os.path.join(PATH_TO_KINDLE, 'documents', 'My Clippings.txt')

    # Check if the file exists
    if os.path.exists(clippings_file):
        # Extract highlights and notes
        highlights = extract_highlights(clippings_file)
        print_highlights(highlights)
        return highlights

    else:
        raise Exception("The path to your kindle was not found. Are you sure the path is correct?")

if __name__ == "__main__":
    main()
