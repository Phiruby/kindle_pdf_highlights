PATH_TO_KINDLE = "D:\\" #your path to your kindle (connected via usb)
OUTPUT_DATA_FOLDER = 'data_stored'

OFFSETS_BY_BOOK_NAME = {
    '[1library': 28
}
from typing import Dict
#Some classes
class InformationStored:
    '''
    content_with_annot: is a string. This string first has the default "Your note on page 15-x | Added on ..." followed 
    by the actual highlight / note
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