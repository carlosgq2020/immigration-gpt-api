#!/usr/bin/env python3
"""Buckets single-page PDFs into folders using QR divider pages."""
import shutil, cv2
from pathlib import Path
from pdf2image import convert_from_path
from utils.divider_detect import detect_divider

SRC = Path("parts")              # input single-page PDFs
DST = Path("out")                # output buckets
DST.mkdir(exist_ok=True)

current = DST / "UNCLASSIFIED"
current.mkdir(exist_ok=True)

for pdf in sorted(SRC.glob("*.pdf")):
    img = convert_from_path(str(pdf), dpi=300, first_page=1, last_page=1)[0]
    bgr = cv2.cvtColor(cv2.imread(img.filename), cv2.COLOR_RGB2BGR)
    if sec := detect_divider(bgr):
        current = DST / sec.upper().replace(" ", "_")
        current.mkdir(exist_ok=True)
        continue                      # skip copying the divider page itself
    shutil.copy2(pdf, current / pdf.name)

print("✅  Bucketing complete →", DST)
