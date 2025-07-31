from docx.api import Document;
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

document = Document("../tests/inputs/test1.docx");



document.save("../tests/outputs/test1.docx");