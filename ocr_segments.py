import os
import json
import re
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from rapidfuzz import process, fuzz


def ocr_pdf(pdf_path):
    text = ''
    images = convert_from_path(pdf_path, dpi=300)
    for image in images:
        text += pytesseract.image_to_string(image)
    return text


def clean_string(s):
    # Lowercase, remove special characters
    return re.sub(r'[^\w\s]', '', s).lower()


def process_segments(toc_path, segments_dir, output_path="segments_text.json"):
    with open(toc_path, "r", encoding="utf-8") as f:
        toc = json.load(f)

    results = {}
    segment_filenames = os.listdir(segments_dir)

    for entry in toc:
        tab = entry.get("tab", "")
        title = entry.get("title", "")

        if not tab or not title:
            print(f"⚠️ No match found for {tab} - {title}")
            continue

        # Build a search string using just tab + cleaned keywords
        search_string = f"{tab}_{clean_string(title)}"

        # Prepare a list of cleaned filenames for matching
        filename_scores = {}
        for f in segment_filenames:
            f_clean = clean_string(f)
            score = fuzz.partial_ratio(search_string, f_clean)
            filename_scores[f] = score

        # Pick the best match above a threshold
        best_match = max(filename_scores.items(), key=lambda x: x[1])
        if best_match[1] >= 70:
            filename = best_match[0]
            segment_path = os.path.join(segments_dir, filename)
        else:
            print(f"⚠️ No match found for {tab} - {title}")
            continue

        print(f"🔍 Checking {segment_path}...")
        try:
            text = ocr_pdf(segment_path)
            results[filename] = text
            print(f"✅ Finished: {filename[:-4]}")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📝 Saved OCR results to: {output_path}")


if __name__ == "__main__":
    process_segments("toc_output.json", "output_segments")
