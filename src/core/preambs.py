from docx.api import Document
import document as doc

class preamb:
    def __init__(self, adverb: str = "Adverb",
                    content: str = "content") -> None:
        self.adverb = adverb
        self.content = content
    def toDocParagraph(self) -> doc.paragraph:
        _p = doc.paragraph(self.adverb, italic=True)
        _p.add_run(" " + self.content + ",")
        return _p
        