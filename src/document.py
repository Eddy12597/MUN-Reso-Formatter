from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt, RGBColor


file_path = "tests/inputs/"
file_name = "test1.docx"

doc = Document(file_path + file_name)
style = doc.styles['Normal']
font = style.font # type: ignore
font.name = "Times New Roman"
font.size = Pt(12)

class paragraph:
    def __init__(self, 
                 text: str = "",
                 bold: bool = False, 
                 italic: bool = False, 
                 underline: bool = False,
                 font_size: int = 12,
                 font_color: tuple[int, int, int] | None = None,  # RGB tuple
                 align: WD_PARAGRAPH_ALIGNMENT | None = None,
                 style: str | None = None) -> None:
        self.text = text
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.font_size = font_size
        self.font_color = font_color
        self.align = align
        self.style = style
        self._runs: list[dict[str, str | bool | int | None]] = []

    def add_run(self, text: str, bold: bool = False, italic: bool = False, 
                underline: bool = False, font_size: int | None = None) -> None:
        """Add a formatted text run to the paragraph"""
        self._runs.append({
            'text': text,
            'bold': bold,
            'italic': italic,
            'underline': underline,
            'font_size': font_size or self.font_size
        })
    
    def clear_runs(self) -> None:
        """Clear all text runs"""
        self._runs = []
    
    def render(self, document) -> None:
        """Add the paragraph to a docx Document"""
        p = document.add_paragraph(style=self.style)

        print(f"DEBUG: self.text = '{self.text}'")
        print(f"DEBUG: self._runs = {self._runs}")

        if self.text:
            run = p.add_run(self.text)
            run.bold = self.bold
            run.italic = self.italic
            run.underline = self.underline
            run.font.size = Pt(self.font_size)
            if self.font_color:
                run.font.color.rgb = RGBColor(*self.font_color)

        for run_spec in self._runs:
            run = p.add_run(run_spec['text'])
            run.bold = run_spec['bold']
            run.italic = run_spec['italic']
            run.underline = run_spec['underline']
            if run_spec['font_size']:
                try:
                    run.font.size = Pt(float(run_spec['font_size']))
                except Exception as e:
                    print(f"Error occurred in paragraph.render: {e}")
            if self.font_color:
                run.font.color.rgb = RGBColor(*self.font_color)

        if self.align:
            p.alignment = self.align

            """Add the paragraph to a docx Document"""
            p = document.add_paragraph(style=self.style)

            # Render the base text first if it exists
            if self.text:
                run = p.add_run(self.text)
                run.bold = self.bold
                run.italic = self.italic
                run.underline = self.underline
                run.font.size = Pt(self.font_size)
                if self.font_color:
                    run.font.color.rgb = RGBColor(*self.font_color)

            # Render additional runs
            for run_spec in self._runs:
                run = p.add_run(run_spec['text'])
                run.bold = run_spec['bold']
                run.italic = run_spec['italic']
                run.underline = run_spec['underline']
                if run_spec['font_size']:
                    try:
                        run.font.size = Pt(float(run_spec['font_size']))
                    except Exception as e:
                        print(f"Error occurred in paragraph.render: {e}")
                if self.font_color:
                    run.font.color.rgb = RGBColor(*self.font_color)

            # Set paragraph alignment
            if self.align:
                p.alignment = self.align

    
    def _apply_formatting(self, run) -> None:
        """Apply formatting to a run object"""
        run.bold = self.bold
        run.italic = self.italic
        run.underline = self.underline
        run.font.size = Pt(self.font_size)
        if self.font_color:
            run.font.color.rgb = RGBColor(*self.font_color)
    
    def set_alignment(self, align: WD_PARAGRAPH_ALIGNMENT) -> None:
        """Set paragraph alignment"""
        self.align = align
    
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