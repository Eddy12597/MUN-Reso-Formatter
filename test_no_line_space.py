import src.document as doc

test = doc.document("tests/inputs/test_no_line_space.docx", "tests/outputs/test_no_line_sapce.docx")

test_paragraph = doc.paragraph("Test paragraph")
test_bold_paragraph = doc.paragraph("Test bold paragraph", bold=True)
test_bold_italic_underline_paragraph = doc.paragraph("Test bold, italic, underline paragraph", True, True, True)

test.append(test_paragraph).append(test_bold_paragraph).append(test_bold_italic_underline_paragraph)

test.save()