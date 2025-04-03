import fitz  # PyMuPDF

pdf_path = "/Users/carlosquintana/Desktop/IH TOC Asylum CQ JuanLealMtz.pdf"

doc = fitz.open(pdf_path)
page_num = 3  # Page 4 in PDF (0-indexed)

page = doc[page_num]
blocks = page.get_text("blocks")

print(f"🔍 Debugging Page {page_num + 1} - Block Lines\n")

for i, block in enumerate(blocks):
    print(f"[{i}] {block[4].strip()}")

import fitz  # PyMuPDF

doc = fitz.open("/Users/carlosquintana/Desktop/IH TOC Asylum CQ JuanLealMtz.pdf")

with open("toc_raw_lines.txt", "w") as f:
    page = doc[3]  # TOC is on page 4
    text = page.get_text("text")
    for i, line in enumerate(text.splitlines()):
        f.write(f"[{i}] {line.strip()}\n")

print("✅ Dumped TOC lines to toc_raw_lines.txt")
