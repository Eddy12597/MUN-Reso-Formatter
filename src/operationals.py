from icecream import ic
from docx.api import Document
import src.document as doc

class subsubclause:
    def __init__(self,
                 index: int, 
                 text: str = "Sub sub clause text") -> None:
        self.index = index
        self.text = text


class subclause:
    def __init__(self,
                 index: int,
                 text: str = "Sub clause text",
                 listsubsubclauses: list[subsubclause] | None = None) -> None:
        self.index = index
        self.text = text
        if (not self.text.endswith(',')) or (not self.text.endswith(', ')):
            self.text += ","
        self.listsubsubclauses = listsubsubclauses if listsubsubclauses is not None else []

class clause:
    def __init__(self,
                 index: int,
                 verb: str = "clause verb",
                 text: str = "Clause text",
                 listsubclauses: list[subclause] | None = None) -> None:
        self.index = index
        self.verb = verb
        self.text = text
        if (not self.text.endswith(',')) or (not self.text.endswith(', ')):
            self.text += ','
        self.listsubclauses = listsubclauses if listsubclauses is not None else []
        
    def toDocParagraphs(self) -> list[doc.paragraph]:
        paragraphs = []

        # Clause (level 1, 1., 2., 3., ...)
        clause_content = doc.paragraph(list_level=1)  # don't set text
        clause_content.add_run(f"{self.verb} ", underline=True)
        clause_content.add_run(self.text)
        paragraphs.append(clause_content)

        print(f"clause_cotent: {clause_content}")
        print(f"paragraphs: {[str(p) for p in paragraphs]}")

        # Subclauses (level 2, a), b), c), ...)
        for subcl in self.listsubclauses:
            subclause_text = subcl.text
            subclause_paragraph = doc.paragraph(subclause_text, list_level=2)
            paragraphs.append(subclause_paragraph)
            print(f"subclause_paragraph: {subclause_paragraph}")
            print(f"paragraphs: {[str(p) for p in paragraphs]}")

            # Sub-subclauses (level 3, i., ii., iii., ...)
            for subsubcl in subcl.listsubsubclauses:
                subsubclause_text = subsubcl.text
                subsubclause_paragraph = doc.paragraph(subsubclause_text, list_level=3)
                paragraphs.append(subsubclause_paragraph)
                print(f"subsubclause_paragraph: {subsubclause_paragraph}")
                print(f"paragraphs: {[str(p) for p in paragraphs]}")
        return paragraphs

            