import os
import re
import json
from pathlib import Path
from PyPDF2 import PdfReader
from tqdm import tqdm

# Load labels to match against filenames
LABELS = [
    "TAB - PAGE IDENTITY DOCUMENTS",
    "A - Copy of Respondent's birth certificate with certified translation",
    "B - Copy of Respondent's Republic of Nicaragua Identification Card with certified translation",
    "C - Definition of a Refugee INA § 101 (a)(42)",
    "D - Respondent's Declaration in both English and Spanish",
    "E - Affidavit of Juan De Dios Leal Reynosa in support of Respondent with certified English translations",
    "F - Affidavit of Fatima Del Carmen Oporta Solorzano in support of Respondent with certified English translations",
    "G - Affidavit of Denis Bismark Lopez Oporta in support of Respondent with certified English translations",
    "H - Affidavit of Jesniher L. in support of Respondent with certified English translation",
    "I - Nicaragua 2023 Human Rights Report",
    "J - Nicaragua Travel Advisory",
    "K - Nicaragua Amnesty International Annual Report",
    "L - Nicaragua Human Rights Watch",
    "M - Gomez, Natalia “Persecution of rural protest movement leaders continue as crisis deepens in Nicaragua” Sept. 06, 2018",
    "N - PBI “The Peasant Movement in Exile” Jan. 01, 2021",
    "O - UN “Annual report of the United Nations High Commissioner for Human Rights on the situation of human rights in Nicaragua” Mar. 07, 2022",
    "P - IACHR ”Nicaragua: Six Years after Social Protests, IACHR Urges Reestablishment of",
]

SEGMENTS_DIR = Path("output_segments")
RESULTS_FILE = Path("segments_text.json")


def normalize(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


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
    results = {}
    segment_files = sorted(SEGMENTS_DIR.glob("*.pdf"))
    unmatched_labels = set(LABELS)

    for file_path in tqdm(segment_files, desc="Processing PDFs"):
        print(f"🔍 Checking {file_path.name}...")

        file_text = extract_text_from_pdf(file_path)
        results[file_path.name] = file_text

        print(f"\n📄 Checking file: {file_path.name}")
        print(f"🔍 Normalized filename: {normalize(file_path.stem)}")
    for label in LABELS:
        print(f"🆚 Comparing with: {normalize(label)} | Original: {label}")
        
        # Try to match a label using normalized comparison
        matched = False
        for label in LABELS:
            if normalize(label).startswith(normalize(file_path.stem)):
                print(f"✅ Matched: {label}")
                unmatched_labels.discard(label)
                matched = True
                break

        if not matched:
            print(f"⚠️ No match found for {file_path.stem}")

    # Report unmatched labels
    if unmatched_labels:
        print("\n❌ Unmatched Labels:")
        for label in unmatched_labels:
            print(f" - {label}")

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📝 Saved OCR results to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
