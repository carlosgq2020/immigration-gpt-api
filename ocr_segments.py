import os
import json
import re
from pathlib import Path
from difflib import get_close_matches
from rapidfuzz import fuzz

TOC_FILE = "toc.json"
SEGMENT_FOLDER = "output_segments"
OCR_OUTPUT_FILE = "segments_text.json"

def normalize_for_matching(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())

def load_toc():
    with open(TOC_FILE, "r") as f:
        return json.load(f)

def load_pdf_segments():
    return {
        f.name.replace(".pdf", ""): f
        for f in Path(SEGMENT_FOLDER).glob("*.pdf")
    }

def manual_matches = {
    "TAB": "TAB_Page_Identity_Documents",  # This must match the filename (minus .pdf)
    "C": "C_Definition_of_a_Refugee_INA_101a42",
    "H": "H_Affidavit_of_Jesniher_L",
    "M": "M_Gomez_Natalia_Persecution_of_Protest_Leaders",
    "N": "N_PBI_The_Peasant_Movement_in_Exile",
    "O": "O_UN_Annual_Report_on_Human_Rights_2022",
    "P": "P_IACHR_Six_Years_After_Social_Protests",
}

    match_title_to_segment(title, pdf_segments):
    normalized_title = normalize_for_matching(title)
    normalized_to_filename = {
        normalize_for_matching(name): name for name in pdf_segments.keys()
    }
if key in manual_matches:
    manual_file = manual_matches[key]
    if manual_file in pdf_segments:
        print(f"🧷 Manual match for {key}: {manual_file}")
        return manual_file

    # Try fuzzy matching with rapidfuzz
    best_match = None
    best_score = 0
    for norm_name, original_name in normalized_to_filename.items():
        score = fuzz.ratio(normalized_title, norm_name)
        if score > best_score:
            best_score = score
            best_match = original_name

    if best_score >= 85:
        return best_match

    # Fallback: match using just the TOC key like "H", "M"
    key = title.split(" ")[0].strip(" -")
    for seg_name in pdf_segments:
        if seg_name.startswith(f"{key}_"):
            print(f"🟡 Fallback match using key '{key}': {seg_name}")
            return seg_name

    # Manual override for known edge cases
   manual_matches = {
    "TAB": "TAB_Identity_Documents.pdf",
    "C": "C_Definition_of_a_Refugee_INA_101a42.pdf",
    "H": "H_Affidavit_of_Jesniher_L.pdf",
    "M": "M_Gomez_Natalia_Persecution_of_rural_protest_movement.pdf",
    "N": "N_PBI_The_Peasant_Movement_in_Exile.pdf",
    "O": "O_UN_Annual_Report_on_Human_Rights_Nicaragua_2022.pdf",
    "P": "P_IACHR_Six_Years_after_Social_Protests.pdf",
}

        if key in manual_matches:
        manual_file = manual_matches[key].replace(".pdf", "")
        if manual_file in pdf_segments:
            print(f"🧷 Manual match for {key}: {manual_file}")
            return manual_file

    return None

def run_ocr_on_pdf(pdf_path):
    # Placeholder for actual OCR logic
    return f"[OCR output for {pdf_path.name}]"

def main():
    toc_entries = load_toc()
    pdf_segments = load_pdf_segments()
    results = {}

    for entry in toc_entries:
        title = entry.get("title", "")
        print(f"\n🔍 Checking {title}...")

        match = match_title_to_segment(title, pdf_segments)

        if match:
            pdf_path = pdf_segments[match]
            ocr_result = run_ocr_on_pdf(pdf_path)
            results[match] = ocr_result
            print(f"✅ Finished: {match}")
        else:
            print(f"⚠️ No match found for {title}")

    with open(OCR_OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📝 Saved OCR results to: {OCR_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
