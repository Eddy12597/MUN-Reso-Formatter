from docx.api import Document
import document as doc

class subsubclause:
    def __init__(self, index: int, 
                 text: str = "Sub sub clause text") -> None:
        self.index = index
        self.text = text


class subclause:
    def __init__(self, index: int,
                 text: str = "Sub clause text",
                 listsubsubclauses: list[subsubclause] | None = None) -> None:
        self.index = index
        self.text = text
        self.listsubsubclauses = listsubsubclauses if listsubsubclauses is not None else []

class clause:
    def __init__(self, index: int,
                 text: str = "Clause text",
                 listsubclauses: list[subclause] | None = None) -> None:
        self.index = index
        self.text = text
        self.listsubclauses = listsubclauses if listsubclauses is not None else []
