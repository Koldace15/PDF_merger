import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import re
from pypdf import PdfWriter, PdfReader
from datetime import datetime as dt


def natural_key(path: Path):
    """Sort so 'Lecture 2' comes before 'Lecture 10'."""
    return [int(c) if c.isdigit() else c.lower()
            for c in re.split(r'(\d+)', path.stem)]


def clean_title(filename: str) -> str:
    
    #Turn 'lecture_10_intro.pdf' → 'Lecture 10: Intro'
    #Turn 'lecture_2.pdf'         → 'Lecture 2'
    #Falls back to a prettified filename otherwise.


    stem = Path(filename).stem

    # Match patterns 
    m = re.match(r'(lecture|lec|chapter|ch|week|session|part)[\s_\-]*(\d+)[\s_\-]*(.*)',
                 stem, re.IGNORECASE)
    if m:
        prefix, num, rest = m.groups()
        prefix = prefix.capitalize()
        rest = re.sub(r'[_-]+', ' ', rest).strip().title()
        return f"{prefix} {num}: {rest}" if rest else f"{prefix} {num}"

    # Fallback: prettify the filename
    pretty = re.sub(r'[_-]+', ' ', stem)
    pretty = re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', pretty)
    return re.sub(r'\s+', ' ', pretty).strip().title()


def list_pdfs(folder: str):
    """Return PDFs in folder sorted naturally by filename."""
    return sorted(Path(folder).glob("*.pdf"), key=natural_key)


#GUI

class PDFMergerApp:
    def __init__(self, root):
        self.root = root
        root.title("PDF Merger")
        root.geometry("520x560")
        root.minsize(480, 480)

        self.folder = None
        self.pdfs = []

        self._build_ui()

    # ----- UI construction -----
    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # Top: folder selection
        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)

        self.folder_var = tk.StringVar(value="No folder selected")
        ttk.Label(top, text="Folder:", font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Label(top, textvariable=self.folder_var, foreground="#555").pack(
            side="left", padx=(6, 0), fill="x", expand=True
        )
        ttk.Button(top, text="Browse…", command=self.pick_folder).pack(side="right")

        # File list label + count
        self.count_var = tk.StringVar(value="Files to merge (sorted):")
        ttk.Label(self.root, textvariable=self.count_var,
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10)

        # Scrollable listbox
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                  activestyle="none", height=10)
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)

        # Options
        opts = ttk.LabelFrame(self.root, text="Options")
        opts.pack(fill="x", padx=10, pady=6)

        self.add_toc_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Add Table of Contents (bookmarks per file)",
                        variable=self.add_toc_var).pack(anchor="w", padx=8, pady=2)

        self.toc_parent_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text='Wrap entries under a "Table of Contents" node',
                        variable=self.toc_parent_var).pack(anchor="w", padx=8, pady=2)

        # Buttons
        btns = ttk.Frame(self.root)
        btns.pack(fill="x", padx=10, pady=6)

        self.merge_btn = ttk.Button(btns, text="Merge into PDF…",
                                    command=self.merge, state="disabled")
        self.merge_btn.pack(side="right")

        ttk.Button(btns, text="Refresh",
                   command=self.refresh).pack(side="right", padx=6)

        # Status bar
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self.root, textvariable=self.status_var,
                  relief="sunken", anchor="w").pack(fill="x", side="bottom")

    # ----- Actions -----
    def pick_folder(self):
        folder = filedialog.askdirectory(title="Select folder with PDFs")
        if not folder:
            return
        self.folder = folder
        self.folder_var.set(folder)
        self.refresh()

    def refresh(self):
        if not self.folder:
            return
        self.pdfs = list_pdfs(self.folder)
        self.listbox.delete(0, tk.END)

        if not self.pdfs:
            self.count_var.set("Files to merge (0):")
            self.merge_btn.config(state="disabled")
            self.status_var.set("No PDF files found in that folder.")
            return

        for i, p in enumerate(self.pdfs, 1):
            title = clean_title(p.name)
            self.listbox.insert(tk.END, f"{i:>3}.  {title}    —  ({p.name})")

        self.count_var.set(f"Files to merge ({len(self.pdfs)}), in order:")
        self.merge_btn.config(state="normal")
        self.status_var.set(f"Found {len(self.pdfs)} PDF file(s).")

    def merge(self):
        if not self.pdfs:
            return

        out = filedialog.asksaveasfilename(
            title="Save merged PDF as…",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="merged.pdf"
        )
        if not out:
            return

        writer = PdfWriter()
        try:
            parent = None
            if self.add_toc_var.get() and self.toc_parent_var.get():
                parent = writer.add_outline_item("Table of Contents", 0)

            added = 0
            for pdf_path in self.pdfs:
                try:
                    reader = PdfReader(str(pdf_path))
                    start_index = len(writer.pages)
                    for page in reader.pages:
                        writer.add_page(page)
                    added += 1

                    if self.add_toc_var.get():
                        title = clean_title(pdf_path.name)
                        writer.add_outline_item(title, start_index, parent=parent)

                    self.status_var.set(f"Added: {pdf_path.name}")
                    self.root.update_idletasks()
                except Exception as e:
                    print(f"Skipping {pdf_path.name}: {e}")

            with open(out, "wb") as f:
                writer.write(f)
        finally:
            writer.close()

        self.status_var.set(f"Merged {added} file(s) → {out}")
        messagebox.showinfo("Done", f"Merged {added} file(s) into:\n{out}")
        now = dt.now()
        horas = now.hour
        if (horas>7 and horas <12 ):
            messagebox.showinfo("Greetings! ","Good morning")
        elif(horas == 12):
            messagebox.showinfo("Greetings! ","Good noon")
        elif(horas >12 and horas<18):
            messagebox.showinfo("Greetings! ","Good ebening")
        else:
            messagebox.showinfo("Greetings !","Good night")


    def merge_to_writer(self, writer, pdf_path):
        """Add all pages from pdf_path; return (start_index, page_count)."""
        reader = PdfReader(str(pdf_path))
        start_index = len(writer.pages)
        for page in reader.pages:
            writer.add_page(page)
        return start_index, len(reader.pages)


if __name__ == "__main__":
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    PDFMergerApp(root)
    root.mainloop()