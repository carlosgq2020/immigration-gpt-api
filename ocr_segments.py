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
    s = re.sub(r'https?://\S+', '', s)  # remove URLs
    s = re.sub(r'[^\w\s-]', '', s)      # remove special characters
    s = re.sub(r'\s+', '_', s.strip())  # normalize spacing
    return s.lower()


def simplify_title(title, max_words=12):
    """Returns a simplified string of the first few words of the title."""
    title = re.sub(r'["“”]', '', title)
    title = re.sub(r'https?://\S+', '', title)
    words = title.strip().split()
    return ' '.join(words[:max_words])


def process_segments(toc_path, segments_dir, output_path="segments_text.json"):
    with open(toc_path, "r", encoding="utf-8") as f:
        toc = json.load(f)

    results = {}
    segment_filenames = os.listdir(segments_dir)
    cleaned_filenames = [clean_string(f) for f in segment_filenames]

    for entry in toc:
        tab = entry.get("tab", "").strip()
        title = entry.get("title", "").strip()

        if not tab or not title:
            print(f"⚠️ Skipping entry with missing tab or title: {entry}")
            continue

        # Clean and shorten TOC title
        simplified_title = simplify_title(title)
        match_string = clean_string(f"{tab}_{simplified_title}")

        # Fuzzy match against available segment filenames
        best_match, score = process.extractOne(
            match_string, cleaned_filenames, scorer=fuzz.partial_ratio
        )

        if score >= 65:
            index = cleaned_filenames.index(best_match)
            matched_filename = segment_filenames[index]
            filepath = os.path.join(segments_dir, matched_filename)
        else:
            print(f"⚠️ No match found for {tab} - {simplified_title} (score: {score})")
            continue

        print(f"🔍 Checking {filepath}...")
        try:
            text = ocr_pdf(filepath)
            results[matched_filename] = text
            print(f"✅ Finished: {matched_filename[:-4]}")
        except Exception as e:
            print(f"❌ Error processing {matched_filename}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📝 Saved OCR results to: {output_path}")


if __name__ == "__main__":
    process_segments("toc_output.json", "output_segments")
