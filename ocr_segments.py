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
    s = s.replace("“", "").replace("”", "").replace("’", "").replace("‘", "")
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r'https?://\S+', '', s)       # remove URLs
    s = re.sub(r'[^\w\s-]', '', s)           # remove special characters
    s = re.sub(r'\s+', '_', s.strip())       # replace spaces with underscores
    return s.lower()


def simplify_title(title, max_words=10):
    """Extract first N words of cleaned title."""
    title = re.sub(r'https?://\S+', '', title)
    title = re.sub(r'[^\w\s-]', '', title)
    title = title.replace("“", "").replace("”", "").replace("’", "").replace("‘", "")
    words = title.strip().split()
    return '_'.join(words[:max_words]).lower()


from rapidfuzz import process, fuzz
import unicodedata


def normalize_title(title, tab, max_words=12):
    # Remove non-ascii chars, normalize unicode
    title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")

    title = title.lower()
    title = re.sub(r'https?://\S+', '', title)
    title = re.sub(r'[^\w\s-]', '', title)        # remove punctuation
    title = re.sub(r'\s+', '_', title.strip())    # replace spaces with underscores

    # Keep just the first N words
    title_words = title.split('_')[:max_words]
    short_title = '_'.join(title_words)
    return f"{tab.lower()}_{short_title}"

    for entry in toc:
    tab = entry.get("tab", "").strip()
    title = entry.get("title", "").strip()

    if not tab or not title:
        continue

    normalized_key = normalize_title(title, tab)

    best_match, score = process.extractOne(normalized_key, cleaned_filenames, scorer=fuzz.partial_token_sort_ratio)

    if score >= 55:
        matched_index = cleaned_filenames.index(best_match)
        matched_filename = segment_filenames[matched_index]
        filepath = os.path.join(segments_dir, matched_filename)
    else:
        print(f"⚠️ No match found for {tab} - {title[:70]}... (score: {score})")
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
