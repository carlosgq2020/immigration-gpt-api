import re
import json
from pathlib import Path
from typing import List, Dict, Optional

import fitz  # PyMuPDF
import pytesseract
from PIL import Image


def extract_toc_blocks(pdf_path: str, page_index: int = 3) -> List[str]:
    """Return block-sorted text lines from the TOC page."""
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    blocks = page.get_text("blocks")
    sorted_blocks = sorted(blocks, key=lambda b: (round(b[1]), b[0]))
    return [b[4].strip() for b in sorted_blocks if b[4].strip()]


def extract_toc_lines(pdf_path: str, page_index: int = 3) -> List[str]:
    """Extract TOC lines using text or OCR if needed."""
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    text_lines = [line.strip() for line in page.get_text("text").splitlines() if line.strip()]
    if text_lines:
        return text_lines

    # Fallback to OCR when no text is extracted
    pix = page.get_pixmap(dpi=300)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    ocr_text = pytesseract.image_to_string(img)
    return [line.strip() for line in ocr_text.splitlines() if line.strip()]


def parse_toc(lines: List[str]) -> List[Dict[str, object]]:
    """Parse lines into a list of TOC entries."""
    toc_entries = []
    current: Dict[str, object] = {}
    i = 0

    tab_pattern = re.compile(r"^([A-Z]{1,3})\.?$")
    page_pattern = re.compile(r"^(\d+)\s*[–—-]?\s*(\d+)?$")

    while i < len(lines):
        line = lines[i]
        tab_match = tab_pattern.match(line)

        if tab_match:
            if current:
                toc_entries.append(current)
                current = {}

            current["tab"] = tab_match.group(1)
            i += 1

            title_parts = []
            while i < len(lines) and not page_pattern.match(lines[i]) and not tab_pattern.match(lines[i]):
                title_parts.append(lines[i])
                i += 1
            current["title"] = " ".join(title_parts).strip()

            if i < len(lines) and page_pattern.match(lines[i]):
                page_match = page_pattern.match(lines[i])
                current["startPage"] = int(page_match.group(1))
                current["endPage"] = int(page_match.group(2)) if page_match.group(2) else int(page_match.group(1))
                i += 1
        else:
            i += 1

    if current:
        toc_entries.append(current)

    return toc_entries


def parse_pdf(pdf_path: str, page_index: int = 3) -> List[Dict[str, object]]:
    """Convenience wrapper to parse a PDF's TOC."""
    lines = extract_toc_lines(pdf_path, page_index)
    return parse_toc(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse TOC from a PDF")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save JSON")
    parser.add_argument("--page_index", type=int, default=3, help="0-based page index of TOC")
    args = parser.parse_args()

    entries = parse_pdf(args.pdf_path, args.page_index)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
    print(f"\n✅ TOC parsed: {len(entries)} entries saved to {args.output}")

