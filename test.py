from src.document import *
doc = document()

# centering doesn't work
pc = paragraph("Bold, Large, Centered text", bold=True, align="center", font_size=16)
pu = paragraph("Underlined text", underline=True)
pb = paragraph("Bold text ", bold=True)
pb.add_run(" followed by normal text")
doc.append(pc).append(pu).append(pb)
doc.save()