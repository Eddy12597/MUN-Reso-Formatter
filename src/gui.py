from sys import exit

import main as parser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import document as doc
from docx.opc.exceptions import PackageNotFoundError

class ResolutionFormatterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Resolution Formatter")
        self.root.geometry("600x250")
        self.root.resizable(True, True)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('TButton', padding=5)
        self.style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        
        # Variables
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for responsiveness
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Resolution Document Formatter", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input file section
        ttk.Label(main_frame, text="Input File:").grid(row=1, column=0, sticky="w", pady=5)
        input_entry = ttk.Entry(main_frame, textvariable=self.input_var, width=60)
        input_entry.grid(row=1, column=1, sticky="ew", padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.select_input, 
                  width=10).grid(row=1, column=2, padx=(0, 0), pady=5)
        
        # Output file section
        ttk.Label(main_frame, text="Output File:").grid(row=2, column=0, sticky="w", pady=5)
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=60)
        output_entry.grid(row=2, column=1, sticky="ew", padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.select_output, 
                  width=10).grid(row=2, column=2, padx=(0, 0), pady=5)
        
        # Auto-fill output when input changes
        self.input_var.trace_add('write', self.auto_fill_output)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        # Action buttons
        ttk.Button(button_frame, text="Format Document", 
                  command=self.run, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", 
                  command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", 
                  command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
    def auto_fill_output(self, *args):
        """Auto-generate output path when input path is provided"""
        if self.input_var.get() and not self.output_var.get():
            input_path = Path(self.input_var.get())
            if input_path.suffix.lower() == '.docx':
                # Create output path with ' - formatted' appended before .docx
                output_path = input_path.parent / f"{input_path.stem} - formatted{input_path.suffix}"
                self.output_var.set(str(output_path))
    
    def select_input(self):
        filename = filedialog.askopenfilename(
            title="Select Input Document",
            filetypes=[("Word documents", "*.docx"), ("All files", "*.*")]
        )
        if filename:
            self.input_var.set(filename)
            self.status_var.set(f"Input file selected: {Path(filename).name}")
    
    def select_output(self):
        default_name = ""
        if self.input_var.get():
            input_path = Path(self.input_var.get())
            # Use the same naming convention for the save dialog
            default_name = f"{input_path.stem} - formatted.docx"
        
        filename = filedialog.asksaveasfilename(
            title="Save Output As",
            defaultextension=".docx",
            initialfile=default_name,
            filetypes=[("Word documents", "*.docx"), ("All files", "*.*")]
        )
        if filename:
            self.output_var.set(filename)
            self.status_var.set(f"Output file set: {Path(filename).name}")
    
    def validate_inputs(self):
        """Validate input and output paths"""
        if not self.input_var.get():
            messagebox.showerror("Error", "Please select an input file")
            return False
        
        input_path = Path(self.input_var.get())
        if not input_path.exists():
            messagebox.showerror("Error", f"Input file does not exist:\n{input_path}")
            return False
        
        if input_path.suffix.lower() != '.docx':
            messagebox.showerror("Error", "Input file must be a .docx file")
            return False
        
        # Set default output if not provided
        if not self.output_var.get():
            self.auto_fill_output()
        
        output_path = Path(self.output_var.get())
        if output_path.exists():
            result = messagebox.askyesno(
                "Overwrite File", 
                f"Output file already exists:\n{output_path}\n\nDo you want to overwrite it?"
            )
            if not result:
                return False
        
        return True
    
    def clear_all(self):
        """Clear all input fields"""
        self.input_var.set("")
        self.output_var.set("")
        self.status_var.set("Ready")
    
    def run(self):
        if not self.validate_inputs():
            return
        
        input_path = Path(self.input_var.get())
        output_path = Path(self.output_var.get())
        
        # Update status and disable UI during processing
        self.status_var.set("Formatting document...")
        self.root.config(cursor="watch")
        self.root.update()
        
        try:
            # Run the formatter
            self.run_formatter(input_path, output_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")
            self.status_var.set("Error occurred")
        finally:
            # Restore UI state
            self.root.config(cursor="")
            self.root.update()
    
    def run_formatter(self, input_path: str | Path, output_path: str | Path) -> None:
        try:
            resolutionRawDocument = doc.document(str(input_path), str(output_path))
            parsedResolution, components, errorList = parser.parseToResolution(resolutionRawDocument)
            parser.writeToFile(parsedResolution, output_path)
            
            if errorList:
                errors = "\n".join(str(e) for e in errorList)
                messagebox.showwarning("Formatting Completed with Warnings", 
                                     f"The document was formatted successfully but with some warnings:\n\n{errors}")
                self.status_var.set("Completed with warnings")
            else:
                messagebox.showinfo("Success", 
                                  f"Resolution formatted successfully!\n\nSaved to: {output_path}")
                self.status_var.set("Formatting completed successfully")
                
        except PackageNotFoundError:
            messagebox.showerror("Error", "Invalid Word document file path or corrupted document")
            self.status_var.set("Error: Invalid document")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process document:\n{str(e)}")
            self.status_var.set("Error: Processing failed")

def main() -> int:
    root = tk.Tk()
    app = ResolutionFormatterGUI(root)
    root.mainloop()
    return 0

if __name__ == "__main__":
    exit(main()) # sys.exit