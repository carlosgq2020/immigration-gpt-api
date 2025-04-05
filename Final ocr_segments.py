import os
import re
import json
from pathlib import Path
from PyPDF2 import PdfReader
from tqdm import tqdm

# Paths
SEGMENTS_DIR = Path("output_segments")
LABELS_FILE = Path("labels.txt")
RESULTS_FILE = Path("segments_text.json")

def normalize(text):
    """Normalize text for comparison: lowercase and remove non-alphanumerics."""
    return re.sub(r'[^a-z0-9]', '', text.lower())

def extract_text_from_pdf(file_path):
    """Extract text from all pages of a PDF."""
    try:
        reader = PdfReader(file_path)
        return "".join([page.extract_text() or "" for page in reader.pages]).strip()
    except Exception as e:
        return f"⚠️ Error reading {file_path.name}: {e}"

def load_labels(label_path):
    """Load and return cleaned labels from labels.txt."""
    if not label_path.exists():
        print(f"⚠️ Label file not found: {label_path}")
        return []
    return [line.strip() for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()]

def main():
    segment_files = sorted(SEGMENTS_DIR.glob("*.pdf"))
    labels = load_labels(LABELS_FILE)
    normalized_labels = {normalize(label): label for label in labels}

    results = {}
    matched_labels = set()
    unmatched_labels = set(labels)

    for file_path in tqdm(segment_files, desc="Processing PDFs"):
        file_key = normalize(file_path.stem)
        file_text = extract_text_from_pdf(file_path)
        results[file_path.name] = file_text

        print(f"\n📄 Checking file: {file_path.name}")
        print(f"🔍 Normalized filename: {file_key}")

        match_found = False
        for norm_label, original_label in normalized_labels.items():
            if file_key.startswith(norm_label) or norm_label.startswith(file_key):
                print(f"✅ Matched with label: {original_label}")
                matched_labels.add(original_label)
                unmatched_labels.discard(original_label)

                # Rename file to match label (safe file name)
                safe_filename = original_label.replace(":", "").replace("?", "")
                safe_filename = safe_filename.replace("/", "-").replace("\\", "-")
                new_file_path = SEGMENTS_DIR / f"{safe_filename}.pdf"

                if new_file_path != file_path:
                    try:
                        file_path.rename(new_file_path)
                        print(f"📁 Renamed to: {new_file_path.name}")
                    except Exception as e:
                        print(f"⚠️ Could not rename file: {e}")
                match_found = True
                break

        if not match_found:
            print(f"⚠️ No match found for file: {file_path.name}")

    # Report any unmatched labels
    if unmatched_labels:
        print("\n❌ Unmatched Labels:")
        for label in unmatched_labels:
            print(f" - {label}")

    # Save OCR results to JSON
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n📝 OCR results saved to: {RESULTS_FILE}")

if __name__ == "__main__":
    main()
