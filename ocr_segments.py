import os
import json
import re
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from rapidfuzz import process, fuzz


def sanitize_filename(title: str, max_length=150) -> str:
    # Remove URLs and special characters
    title = re.sub(r'https?://\S+', '', title)
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[\s]+', '_', title)
    return title.strip()[:max_length]


def ocr_pdf(pdf_path):
    text = ''
    images = convert_from_path(pdf_path, dpi=300)
    for image in images:
        text += pytesseract.image_to_string(image)
    return text


def process_segments(toc_path, segments_dir, output_path="segments_text.json"):
    with open(toc_path, "r", encoding="utf-8") as f:
        toc = json.load(f)

    results = {}
    segment_filenames = os.listdir(segments_dir)

    for entry in toc:
        tab = entry.get("tab")
        title = entry.get("title")

        if not tab or not title:
            print(f"⚠️ No match found for {tab} - {title}")
            continue

        sanitized_title = sanitize_filename(title)
        expected_filename = f"{tab}_{sanitized_title}.pdf"

        # Fuzzy match if not exact
        match, score, _ = process.extractOne(
            expected_filename,
            segment_filenames,
            scorer=fuzz.partial_ratio
        )

        if score >= 85:
            segment_path = os.path.join(segments_dir, match)
        else:
            print(f"⚠️ No match found for {tab} - {title}")
            continue

        print(f"🔍 Checking {segment_path}...")
        try:
            text = ocr_pdf(segment_path)
            results[match] = text
            print(f"✅ Finished: {match[:-4]}")
        except Exception as e:
            print(f"❌ Error processing {match}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📝 Saved OCR results to: {output_path}")


if __name__ == "__main__":
    process_segments("toc_output.json", "output_segments")
