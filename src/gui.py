import main as parser

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import document as doc
from docx.opc.exceptions import PackageNotFoundError


root = tk.Tk()
root.title("Resolution Formatter")
input_var = tk.StringVar()
output_var = tk.StringVar()

def run_formatter(input_path: str | Path, output_path: str | Path) -> None:
    try:
        resolutionRawDocument = doc.document(str(input_path), str(output_path))
        parsedResolution, components, errorList = parser.parseToResolution(resolutionRawDocument)
        parser.writeToFile(parsedResolution, output_path)
        
        if errorList:
            errors = "\n".join(str(e) for e in errorList)
            messagebox.showwarning("Formatting completed with errors", errors)
        else:
            messagebox.showinfo("Success", f"Formatted resolution saved at {output_path}")
    except PackageNotFoundError:
        messagebox.showerror("Error", "Invalid input or output file path")

def select_input():
    filename = filedialog.askopenfilename(filetypes=[("Word documents", "*.docx")])
    if filename:
        input_var.set(filename)

def select_output():
    filename = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word documents", "*.docx")])
    if filename:
        output_var.set(filename)

def run():
    if not input_var.get():
        messagebox.showerror("Error", "Please select an input file")
        return
    out = output_var.get() or input_var.get()
    run_formatter(Path(input_var.get()), Path(out))

tk.Label(root, text="Input file:").grid(row=0, column=0, sticky="w")
tk.Entry(root, textvariable=input_var, width=50).grid(row=0, column=1)
tk.Button(root, text="Browse", command=select_input).grid(row=0, column=2)

tk.Label(root, text="Output file:").grid(row=1, column=0, sticky="w")
tk.Entry(root, textvariable=output_var, width=50).grid(row=1, column=1)
tk.Button(root, text="Browse", command=select_output).grid(row=1, column=2)

tk.Button(root, text="Run Formatter", command=run).grid(row=2, column=1, pady=10)

root.mainloop()