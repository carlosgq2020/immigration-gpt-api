import fitz  # PyMuPDF

# Path to the TOC PDF file
input_path = "/Users/carlosquintana/Desktop/IH TOC Asylum CQ JuanLealMtz.pdf"

# Open the PDF and load page 4 (index 3)
doc = fitz.open(input_path)
page = doc[3]

# Extract lines of text from page 4
lines = page.get_text("text").splitlines()

print("🔍 Debugging Page 4 - Block Lines\n")
for i, line in enumerate(lines):
    print(f"[{i}] {line}")
