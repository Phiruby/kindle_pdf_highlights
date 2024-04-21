PATH_TO_KINDLE = "D:\\" #your path to your kindle (connected via usb)
OUTPUT_DATA_FOLDER = 'data_stored'
QUESTION_OUTPUT_FOLDER = 'question_answers'
CONTENT_SPLIT_KEY = 'seceihraidufaiusdfhaisdfhaisdufh'

#some books start their pdf indexing after X pages. Insert X with their book names here
OFFSETS_BY_BOOK_NAME = {
    '[1library': 27,
    '\ufeffalgebraic-number-theory': 12,
    'main_notes': 1,
    'modern-ml-algo': 41,
    '\ufeffreal analysis': 12
}
print(OFFSETS_BY_BOOK_NAME.keys())

'''
Params
    highlighted_content: the string of highlighted text
    pdf_text: the text (1-2 pages worth) surrounding the highlighted text
'''
def get_prompt(highlighted_content: str, pdf_text: str, num_questions: int):
    prompt = f'''While reading a book, I highlighted the following delimited text:
    """{highlighted_content}"""

    The delimited text I will provide below are 2-3 pages centered around the above delimited text. Using this, provide a question-answer pair testing the reader on the knowledge they learnt, specifically revolving around the first delimited text. Provide your response in the following template:
    "Question: ...
    Answer: ..."
    In addition, when creating the question, make sure you do not include phrases such as "in the above text" or "in the delimited text", or anything along those lines. Include {num_questions} question-answer pairs.
    """ 
    {pdf_text}
    """
    '''
    return prompt

from typing import Dict

#Some classes
class InformationStored:
    '''
    content_with_annot: is a string. This string first has the default "Your note on page 15-x | Added on ..." followed 
    by the actual highlight / note

    Model Params
        page: a string with the page numbers, separated by '-'
        content: a string of the highlighted content, if any
        saved_time: a timestamp string indicating the time it was saved
    '''
    def __init__(self, book_title, author, content_with_annot):
        self.title = book_title
        self.author = author
        useful_dict = self.get_content_condensed(content_with_annot)
        self.page = useful_dict["page"]
        self.content = useful_dict["saved_information"]
        self.saved_time = useful_dict["date"]
    
    def get_content_condensed(self, content_with_annot: str) -> Dict[str, str]:
        new_dict = {}
        broken = content_with_annot.split("\n") #split by line breaks

        broken = [strong for strong in broken if strong != ''] #filter

        default_info = broken[0].split("|")

        new_dict["date"] = default_info[1] #extracts the date
        page_num = default_info[0].split(" page ")[1]
        new_dict["page"] = page_num 
        new_dict["saved_information"] = broken[-1]
        return new_dict
    
    '''
    Either "Highlight" or "Note"
    '''
    @property
    def information_kind(self):
        raise NotImplementedError()

class Note(InformationStored):
    def information_kind(self):
        return "Note"
class Highlight(InformationStored):
    def information_kind(self):
        return "Highlight"