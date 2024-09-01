import aspose.pdf as ap
import os 
import fitz

input_pdf = "D:\\documents\\Downloads\\Items01\\main_notes.pdf-cdeKey_D6QW3LT3KRRN2CTRIUAYB5VOFXC2T62O.pdf"
output_tex = os.path.join(os.getcwd(), "output.tex")

doc = fitz.open(input_pdf)

page_number = 11
page_index = page_number - 1

page = doc.load_page(page_index)  # Load the specific page
print(page.get_text("latex"))
# page_text = page.get_text("text")

# # Open PDF file
# document = ap.Document(input_pdf)

# # Create an object of LaTeXSaveOptions class
# saveOptions = ap.LaTeXSaveOptions()
# # saveOptions.pages_count = 10
# print(saveOptions.pages_count)

# # Save PDF as TEX
# document.save(output_tex, saveOptions)