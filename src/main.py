from docx.api import Document;

document = Document("../tests/inputs/test1.docx");



document.save("../tests/outputs/test1.docx");