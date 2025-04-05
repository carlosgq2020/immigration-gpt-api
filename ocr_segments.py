import os
import json
import re
import unicodedata
from pathlib import Path
from tqdm import tqdm
from PyPDF2 import PdfReader
from thefuzz import process, fuzz
import pytesseract
from pdf2image import convert_from_path

# Normalize the TOC entry into a comparable format
def normalize_title(title, tab, max_words=25):
    combined = f"{tab} {title}".lower()
    combined = unicodedata.normalize("NFKD", combined).encode("ascii", "ignore").decode("ascii")
    combined = re.sub(r'https?://\S+', '', combined)  # strip URLs
    combined = re.sub(r'["“”‘’\'()]', '', combined)  # strip quotes/parentheses
    combined = re.sub(r'available at|last accessed', '', combined)  # clean phrases
    combined = re.sub(r'[^\w\s]', '', combined)  # remove punctuation
    combined = re.sub(r'\s+', ' ', combined.strip())  # collapse spaces
    return "_".join(combined.split()[:max_words])  # limit length

# Run OCR and return text
def ocr_pdf(path):
    images = convert_from_path(path)
    text = ''
    for img in images:
        text += pytesseract.image_to_string(img)
    return text

# Main OCR matching routine
def main():
    segments_dir = Path("output_segments")
    toc_path = Path("toc_output.json")
    output_path = Path("segments_text.json")

    with toc_path.open() as f:
        toc = json.load(f)

    filenames = [p.stem for p in segments_dir.glob("*.pdf")]
    cleaned_filenames = [re.sub(r'[^\w\s]', '', f).lower() for f in filenames]

    results = {}
    for entry in toc:
        tab = entry.get("tab", "").strip()
        title = entry.get("title", "").strip()
        normalized_key = normalize_title(title, tab)

        # Try to match with filename
        matches = process.extract(normalized_key, cleaned_filenames, scorer=fuzz.partial_ratio, limit=5)
        best_match, score = matches[0][0], matches[0][1] if matches else ("", 0)

# inside your loop, after generating `normalized_key` and `matches`
best_match, score, _ = matches[0]

if score >= 85:
    # High-confidence match
    print(f"\n✅ Match found for {tab} - {title}")
    matched_filename = best_match

elif score >= 70:
    # Low-confidence match, but accept
    print(f"\n⚠️ Low-confidence match for {tab} - {title}")
    print(f"   🔗 Using: {best_match} (score: {score})")
    matched_filename = best_match

else:
    # No acceptable match
    print(f"\n❌ No match found for {tab} - {title}")
    print(f"   🔍 Normalized: {normalized_key}")
    print(f"   🔍 Top 3 guesses:")
    for name, s, _ in matches[:3]:
        print(f"     → {name} (score: {s})")
    continue  # skip this item
        try:
            text = ocr_pdf(pdf_path)
            results[matched_file] = {
                "tab": tab,
                "title": title,
                "text": text
            }
            print(f"✅ Finished: {matched_file}")
        except Exception as e:
            print(f"❌ Error processing {pdf_path}: {e}")

    with output_path.open("w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📝 Saved OCR results to: {output_path}")

if __name__ == "__main__":
    main()

    if not tab or not title:
        continue

    normalized_key = normalize_title(title, tab)

    # Prepare filenames for comparison (without .pdf)
    cleaned_filenames = [os.path.splitext(f)[0].lower() for f in segment_filenames]

    matches = process.extract(normalized_key, cleaned_filenames, scorer=fuzz.partial_ratio, limit=5)
print(f"\n🔎 No match for TOC entry: {tab} - {title}")
print(f"   Normalized key: {normalized_key}")
print("   Top guesses:")
for name, score, _ in matches:
    print(f"     → {name} (score: {score})")
    
    if score >= 55:
        matched_index = cleaned_filenames.index(best_match)
        matched_filename = segment_filenames[matched_index]
        filepath = os.path.join(segments_dir, matched_filename)
    else:
        print(f"⚠️ No match found for {tab} - {title[:70]}... (score: {score})")
        continue
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📝 Saved OCR results to: {output_path}")


if __name__ == "__main__":
    process_segments("toc_output.json", "output_segments")
