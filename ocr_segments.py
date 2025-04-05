import os
import json
import re
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

def sanitize_filename(title: str, max_length=150) -> str:
    # Remove unsafe characters
    title = re.sub(r'https?://\S+', '', title)  # Remove URLs
    title = re.sub(r'[^\w\s-]', '', title)  # Remove special characters
    title = re.sub(r'[\s]+', '_', title)  # Replace spaces with underscores
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
    segment_filenames = set(os.listdir(segments_dir))

    for entry in toc:
        tab = entry.get("tab")
        title = entry.get("title")

        if not tab or not title:
            print(f"⚠️ No match found for {tab} - {title}")
            continue

        sanitized_title = sanitize_filename(title)
        expected_filename = f"{tab}_{sanitized_title}.pdf"
        expected_filename_lower = expected_filename.lower()
        segment_path = os.path.join(segments_dir, expected_filename)

        # Match exactly first
        if os.path.exists(segment_path):
            pass
        else:
            # Try partial and case-insensitive match
            matches = [
                fname for fname in segment_filenames
                if fname.lower().startswith(f"{tab.lower()}_{sanitized_title[:80].lower()}")
            ]
            if matches:
                segment_path = os.path.join(segments_dir, matches[0])
                expected_filename = matches[0]
            else:
                print(f"⚠️ No match found for {tab} - {title}")
                continue

        print(f"🔍 Checking {segment_path}...")
        try:
            text = ocr_pdf(segment_path)
            results[expected_filename] = text
            print(f"✅ Finished: {expected_filename[:-4]}")
        except Exception as e:
            print(f"❌ Error processing {expected_filename}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📝 Saved OCR results to: {output_path}")


if __name__ == "__main__":
    process_segments("toc_output.json", "output_segments")
