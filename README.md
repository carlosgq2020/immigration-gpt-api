# Immigration GPT API

This repository provides a simple set of scripts to parse a PDF's table of contents (TOC) and segment the PDF into smaller documents.

## TOC Based Segmentation

1. **Parse the TOC**
   ```bash
   python toc_parser.py path/to/document.pdf --output toc.json
   ```
   This extracts lines from the TOC page using PyMuPDF and falls back to OCR if necessary. The resulting `toc.json` contains entries like:
   ```json
   [
     {"tab": "A", "title": "First Document", "startPage": 1, "endPage": 3},
     {"tab": "B", "title": "Second Document", "startPage": 4, "endPage": 7}
   ]
   ```

2. **Segment the PDF**
   ```bash
   python segment_by_toc.py path/to/document.pdf --toc_path toc.json --output_dir output_segments
   ```
   If `toc.json` does not exist, the script automatically parses the TOC before segmenting. Each entry is saved as a separate PDF in `output_segments/`.

The TOC parser looks at page index `3` (page 4 of the PDF) by default. Use `--page_index` to override.

