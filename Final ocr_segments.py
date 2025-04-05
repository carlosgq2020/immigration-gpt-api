import os
import re
import json
from pathlib import Path
from PyPDF2 import PdfReader
from tqdm import tqdm

SEGMENTS_DIR = Path("output_segments")
LABELS_FILE = Path("segmenter/labels.json")
RESULTS_FILE = Path("segments_text.json")


def normalize(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        return f"⚠️ Error reading {file_path.name}: {e}"


def main():
    if not LABELS_FILE.exists():
        print(f"❌ No label file found at {LABELS_FILE}. Please create it (as JSON list).")
        return

    with open(LABELS_FILE, "r") as f:
        expected_labels = json.load(f)

    print("🔍 Matching PDF filenames to labels...\n")
    unmatched_labels = set(expected_labels)
    results = {}

    segment_files = sorted(SEGMENTS_DIR.glob("*.pdf"))
    for file_path in tqdm(segment_files, desc="Processing PDFs"):
        filename_norm = normalize(file_path.stem)
        matched = False

        for label in expected_labels:
            label_norm = normalize(label)
            if filename_norm.startswith(label_norm[:20]):  # Flexible prefix match
                print(f"✅ Matched: {file_path.name} ⇨ {label}")
                unmatched_labels.discard(label)
                matched = True
                break

        if not matched:
            print(f"⚠️ No match found for {file_path.name}")

        results[file_path.name] = extract_text_from_pdf(file_path)

    if unmatched_labels:
        print("\n❌ Unmatched Labels:")
        for label in unmatched_labels:
            print(f" - {label}")

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📝 Saved OCR results to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
