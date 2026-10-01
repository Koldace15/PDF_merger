# PDF Merger

A simple GUI tool to merge PDF files in a folder, sorted naturally by filename,
with an automatic **Table of Contents** (bookmarks) using each file's name.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python pdf_merger.py
```

1. Click **Browse…** to pick a folder with PDFs
2. Review the sorted list
3. Click **Merge into PDF…** and choose where to save and the saved file's name
4. Open the merged PDF — the bookmarks panel shows each lecture

## Requirements

- Python 3.8+
- `pypdf`
- Tkinter (bundled with Python)

## License

MIT
