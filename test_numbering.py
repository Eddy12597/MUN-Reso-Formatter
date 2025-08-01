from src.document import *

doc = document()  # Your custom doc class

doc.append(paragraph("First item", list_level=1))     # Shows as "1. First item" 
doc.append(paragraph("Sub-item", list_level=2))      # Shows as "a. Sub-item"
doc.append(paragraph("Next top-level", list_level=1)) # Shows as "2. Next top-level"
doc.save("tests/outputs/auto_numbered.docx")