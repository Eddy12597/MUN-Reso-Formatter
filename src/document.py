from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt, RGBColor
from typing import Union

class paragraph:
    def __init__(
        self,
        text: str = "",
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        font_size: int = 12,
        font_color: tuple[int, int, int] | None = None,
        align: Union[WD_PARAGRAPH_ALIGNMENT, str, None] = None,
        style: str | None = None,
    ) -> None:
        self.text = text
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.font_size = font_size
        self.font_color = font_color
        self.style = style
        self._runs: list[dict] = []
        self.align = None
        if align is not None:
            self.set_alignment(align) # type: ignore

    def set_alignment(self, align: Union[WD_PARAGRAPH_ALIGNMENT, str]) -> None: # type: ignore
        """Set paragraph alignment using either enum or string."""
        if isinstance(align, WD_PARAGRAPH_ALIGNMENT):
            self.align = align
        elif isinstance(align, str):
            align_lower = align.lower()
            alignment_map = {
                "left": WD_PARAGRAPH_ALIGNMENT.LEFT,
                "center": WD_PARAGRAPH_ALIGNMENT.CENTER,
                "right": WD_PARAGRAPH_ALIGNMENT.RIGHT,
                "justify": WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
                "distribute": WD_PARAGRAPH_ALIGNMENT.DISTRIBUTE,
            }
            if align_lower in alignment_map:
                self.align = alignment_map[align_lower]
            else:
                raise ValueError(f"Invalid alignment string: {align}")
        else:
            raise TypeError("Alignment must be WD_PARAGRAPH_ALIGNMENT or str")

    def add_run(self, text: str, **kwargs) -> None:
        """Add a formatted text run."""
        self._runs.append({
            "text": text,
            "bold": kwargs.get("bold", False),
            "italic": kwargs.get("italic", False),
            "underline": kwargs.get("underline", False),
            "font_size": kwargs.get("font_size", self.font_size),
        })

    def render(self, doc: Document) -> None: # type: ignore
        """Render the paragraph to a docx Document."""
        p = doc.add_paragraph(style=self.style)

        

        # Add main text if it exists
        if self.text:
            run = p.add_run(self.text)
            self._apply_formatting(run)

        # Add additional runs
        for run_spec in self._runs:
            run = p.add_run(run_spec["text"])
            run.bold = run_spec["bold"]
            run.italic = run_spec["italic"]
            run.underline = run_spec["underline"]
            if run_spec["font_size"]:
                run.font.size = Pt(run_spec["font_size"])
            if self.font_color:
                run.font.color.rgb = RGBColor(*self.font_color)
                
        # Apply alignment AFTER adding runs
        if self.align is not None:
            p.alignment = self.align


    def _apply_formatting(self, run) -> None:
        """Helper to apply formatting to a run."""
        run.bold = self.bold
        run.italic = self.italic
        run.underline = self.underline
        run.font.size = Pt(self.font_size)
        if self.font_color:
            run.font.color.rgb = RGBColor(*self.font_color)
    
    
    def set_style(self, style: str) -> None:
        """Set paragraph style (e.g., 'Heading 1')"""
        self.style = style
    
    def set_font_color(self, r: int, g: int, b: int) -> None:
        """Set font color using RGB values (0-255)"""
        self.font_color = (r, g, b)
    
    def __str__(self) -> str:
        """Return plain text content"""
        if self._runs:
            return ''.join(str(r['text']) for r in self._runs)  # Explicitly convert to str
        return self.text
    
    

class document:
    def __init__(self, 
                 inputfile: str ="tests/inputs/test1.docx",
                 outputfile : str ="tests/outputs/test1.docx",
                 paragraphs: list[paragraph] | None = None,
                 overallstyle : str = "Normal",
                 font: str = "Times New Roman",
                 fontsize : int | float = 12):
        self.paragraphs = paragraphs if paragraphs is not None else []
        self.inputfile = inputfile
        self.outputfile = outputfile
        self._doc = Document(inputfile)
        self._doc.styles[overallstyle].font.name = font # type: ignore
        self._doc.styles[overallstyle].font.size = Pt(fontsize) # type: ignore
        
    def append(self, paragraph : paragraph) -> 'document': # makes chaining easier
        self.paragraphs.append(paragraph)
        paragraph.render(self._doc)
        return self
    
    def remove(self, paragraph: paragraph) -> None:
        self.paragraphs.remove(paragraph)
    def save(self, outputfile : str | None = None) -> None:
        if outputfile is None:
            outputfile = self.outputfile
        self._doc.save(outputfile)
        print(f"File saved to {outputfile}")
    def getdocument(self): # -> Document (Pylance couldn't resolve 'Document')
        return self._doc