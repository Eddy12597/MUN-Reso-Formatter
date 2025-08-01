from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt, RGBColor, Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.oxml.numbering import CT_Numbering
from docx.opc.constants import CONTENT_TYPE as CT, RELATIONSHIP_TYPE as RT
from typing import Union


class ResoFormattingError(BaseException):
    def __init__(self, msg: str | None = None):
        super().__init__(msg)



class NumberingStyleManager:
    """
    A multilevel list implementation that:
     1. Builds a new <w:abstractNum> + <w:num> in numbering.xml
     2. Appends them directly to the CT_Numbering root
     3. Reuses that numId for all paragraphs
    """

    def __init__(self, doc):
        self.doc = doc
        self.num_id = None
        self._ensure_numbering()

    def _ensure_numbering(self):
        num_part = self.doc.part.numbering_part
        ct_num = num_part.element  # CT_Numbering element

        # 1) find all existing abstractNumId and numId values
        abs_ids = [int(el.get(qn('w:abstractNumId')))
                   for el in ct_num.findall(qn('w:abstractNum'))]
        num_ids = [int(el.get(qn('w:numId')))
                   for el in ct_num.findall(qn('w:num'))]

        new_abs_id = max(abs_ids + [0]) + 1
        new_num_id = max(num_ids + [0]) + 1
        self.num_id = str(new_num_id)

        # 2) build abstractNum
        abstractNum = OxmlElement('w:abstractNum')
        abstractNum.set(qn('w:abstractNumId'), str(new_abs_id))

        # define up to 4 levels (decimal, a, i, decimal)
        level_formats = {
            0: 'decimal',
            1: 'lowerLetter',
            2: 'lowerRoman',
            3: 'decimal',
        }
        for lvl, fmt in level_formats.items():
            lvl_elm = OxmlElement('w:lvl')
            lvl_elm.set(qn('w:ilvl'), str(lvl))

            start = OxmlElement('w:start')
            start.set(qn('w:val'), '1')
            numFmt = OxmlElement('w:numFmt')
            numFmt.set(qn('w:val'), fmt)
            lvlText = OxmlElement('w:lvlText')
            # %1., %2., etc.
            lvlText.set(qn('w:val'), f'%{lvl+1}.')
            suff = OxmlElement('w:suff')
            suff.set(qn('w:val'), 'space')

            for node in (start, numFmt, lvlText, suff):
                lvl_elm.append(node)
            abstractNum.append(lvl_elm)

        # 3) build concrete <w:num> that references our abstractNum
        num = OxmlElement('w:num')
        num.set(qn('w:numId'), self.num_id)
        abstrId = OxmlElement('w:abstractNumId')
        abstrId.set(qn('w:val'), str(new_abs_id))
        num.append(abstrId)

        # 4) append both to the CT_Numbering element
        ct_num.append(abstractNum)
        ct_num.append(num)

    def add_numbered_paragraph(self, text, level=1):
        # create a normal paragraph, then inject numbering XML
        p = self.doc.add_paragraph()
        p.add_run(text)

        numPr = p._p.get_or_add_pPr().get_or_add_numPr()

        ilvl = OxmlElement('w:ilvl')
        ilvl.set(qn('w:val'), str(level-1))
        numPr.append(ilvl)

        numId = OxmlElement('w:numId')
        numId.set(qn('w:val'), self.num_id)
        numPr.append(numId)

        # indent by 0.5" per level
        p.paragraph_format.left_indent = Inches(0.5 * level)
        p.paragraph_format.first_line_indent = Inches(-0.25)

        return p
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
        first_line_indent: Union[float | int, Pt] | None = None, # float | int -> Inches, Pt -> Pt
        left_indent: Union[float | int, Pt] | None = None,       # float | int -> Inches, Pt -> Pt
        right_indent: Union[float | int, Pt] | None = None,      # float | int -> Inches, Pt -> Pt
        list_level: int = 0, # 0: no list, 1: level 1, 2: level 2 (alpha), 3: level 3 (roman)
        list_format: str = 'decimal',
        list_indents: dict[int, float] | None = None
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
        self.first_line_indent = first_line_indent
        self.left_indent = left_indent
        self.right_indent = right_indent
        self.list_level = list_level
        self.list_format = list_format
        self.list_indents = list_indents or {}
        
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
        """Add a formatted text run.
        kwargs choices: bold, italic, underline, font_size
        """
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
        
        # Apply list formatting if needed
        if self.list_level > 0:
            # Use the proper numbering method
            p = NumberingStyleManager(doc).add_numbered_paragraph(self.text, self.list_level)
            
            # Apply additional formatting
            for run in p.runs:
                run.bold = self.bold
                run.italic = self.italic
                run.underline = self.underline
                run.font.size = Pt(self.font_size)
                if self.font_color:
                    run.font.color.rgb = RGBColor(*self.font_color)
        else:
            # Regular paragraph handling
            p = doc.add_paragraph(style=self.style)
            run = p.add_run(self.text)
            self._apply_formatting(run)
            
            
            # Apply indentation
            if self.first_line_indent is not None:
                if isinstance(self.first_line_indent, (int, float)):
                    p.paragraph_format.first_line_indent = Inches(self.first_line_indent)
                else:
                    p.paragraph_format.first_line_indent = (self.first_line_indent)
                    
            if self.left_indent is not None:
                if isinstance(self.left_indent, (int, float)):
                    p.paragraph_format.left_indent = Inches(self.left_indent)
                else:
                    p.paragraph_format.left_indent = (self.left_indent)
                    
            if self.right_indent is not None:
                if isinstance(self.right_indent, (int, float)):
                    p.paragraph_format.right_indent = Inches(self.right_indent)
                else:
                    p.paragraph_format.right_indent = (self.right_indent)

            # Add main text if it exists
            if not self._runs and self.text:
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
        
    # float | int -> Inches, Pt -> Pt
    def set_first_line_indent(self, value: Union[float | int, Pt]) -> None:
        """Set first line indent (in inches or Pt)"""
        self.first_line_indent = Inches(value) if isinstance(value, (int, float)) else (value)

    # float | int -> Inches, Pt -> Pt
    def set_left_indent(self, value: Union[float | int, Pt]) -> None:
        """Set left indent (in inches or Pt)"""
        self.left_indent = Inches(value) if isinstance(value, (int, float)) else (value)
    
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
    def getdocument(self) -> 'Document': # type: ignore
        return self._doc        