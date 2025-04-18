from dotenv import load_dotenv
import os
import json
from tempfile import SpooledTemporaryFile
from typing import List, Optional

import openai
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import docx
import fitz  # PyMuPDF

# === Load environment and set API key ===
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
print("🔑 API KEY:", "FOUND" if openai_api_key else "NOT FOUND")
client = openai.OpenAI(api_key=openai_api_key)

# === FastAPI App ===
app = FastAPI(
    title="LawQB Immigration Legal AI API",
    description="Upload declarations and receive legal analysis and motion drafting assistance. Powered by GPT-4.",
    version="1.0.0",
)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


# === /analyze endpoint ===
class AnalyzeRequest(BaseModel):
    question: str
    jurisdiction: Optional[str] = None
    preferredSources: Optional[List[str]] = None


class AnalyzeResponse(BaseModel):
    issue: str
    rule: str
    application: str
    conclusion: str
    citations: List[str]
    conflictsOrAmbiguities: str
    verificationNotes: str


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    prompt = f"""
You are an expert U.S. immigration attorney. Use the IRAC format to answer this legal question.

Question: {req.question}
Jurisdiction: {req.jurisdiction or "General U.S. immigration law"}

Respond in raw JSON only (no markdown), with the following fields:
- issue
- rule
- application
- conclusion
- citations (list of strings)
- conflictsOrAmbiguities
- verificationNotes
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an immigration law expert. Reply using only IRAC format in JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").strip()
        if content.endswith("```"):
            content = content[:-3].strip()

        print("GPT IRAC Output:", content)
        parsed = json.loads(content)
        return AnalyzeResponse(**parsed)

    except Exception as e:
        print(f"❌ Analyze endpoint error: {e}")
        return AnalyzeResponse(
            issue="Error generating analysis",
            rule="",
            application="",
            conclusion="",
            citations=[],
            conflictsOrAmbiguities="",
            verificationNotes=f"Exception: {str(e)}",
        )


# === /uploadEvidence endpoint ===
class SummarizeEvidenceResponse(BaseModel):
    filename: str
    sizeInBytes: int
    readableSize: str
    fileType: str
    truncated: bool
    summary: str
    keyFacts: List[str]
    legalIssues: List[str]
    credibilityConcerns: str
    recommendation: str
    verificationNotes: str


@app.post("/uploadEvidence", response_model=SummarizeEvidenceResponse)
async def upload_evidence(
    file: UploadFile = File(...),
    jurisdiction: Optional[str] = Form(None),
    context: Optional[str] = Form("Asylum"),
):
    ext = file.filename.lower().split(".")[-1]
    content = ""
    truncated = False
    total_bytes = 0
    readable_size = "Unknown"

    try:
        temp_file = SpooledTemporaryFile(max_size=1024 * 1024 * 100)
        while chunk := await file.read(1024 * 1024):
            total_bytes += len(chunk)
            temp_file.write(chunk)
        temp_file.seek(0)
        readable_size = f"{round(total_bytes / 1024, 1)} KB"

        # ---------- DOCX ----------
        if ext == "docx":
            document = docx.Document(temp_file)
            content = "\n".join(
                [p.text for p in document.paragraphs if p.text.strip()]
            )

        # ---------- PDF (with OCR fallback) ----------
        elif ext == "pdf":
            pdf_bytes = temp_file.read()

            # 1) try embedded text
            pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
            content = "".join(page.get_text() or "" for page in pdf)
            pdf.close()

            # 2) OCR fallback if empty
            if not content.strip():
                from pdf2image import convert_from_bytes
                import pytesseract
                import io

                images = convert_from_bytes(pdf_bytes, fmt="png")
                ocr_parts = []
                for img in images:
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    ocr_parts.append(pytesseract.image_to_string(buf.getvalue()))
                content = "\n".join(ocr_parts)

        # ---------- TXT ----------
        elif ext == "txt":
            content = temp_file.read().decode("utf-8")

        else:
            raise ValueError("Unsupported file type")

    except Exception as e:
        return SummarizeEvidenceResponse(
            filename=file.filename,
            sizeInBytes=total_bytes,
            readableSize=readable_size,
            fileType=ext,
            truncated=False,
            summary="Could not process file.",
            keyFacts=[],
            legalIssues=[],
            credibilityConcerns="",
            recommendation="",
            verificationNotes=f"File processing error: {str(e)}",
        )

    # ---------- Chunking ----------
    MAX_CHARS = 11000
    chunks = [content[i : i + MAX_CHARS] for i in range(0, len(content), MAX_CHARS)]
    if len(chunks) > 1:
        truncated = True

    # ---------- GPT analysis helper ----------
    def gpt_analyze(text_chunk: str):
        prompt = f"""
You are an expert immigration attorney analyzing part of a legal evidence document.

Jurisdiction: {jurisdiction or "General U.S. immigration law"}
Context: {context or "Asylum"}

Summarize the text, extract key facts, identify legal issues, note credibility concerns, and give a legal recommendation.

Text:
{text_chunk}

Return JSON only:
- summary
- keyFacts (list of strings)
- legalIssues (list of strings)
- credibilityConcerns
- recommendation
- verificationNotes
"""
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior immigration attorney. Reply ONLY in flat JSON. No markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").strip()
            if result.endswith("```"):
                result = result[:-3].strip()

            # raw GPT output for debugging
            print("\n--- GPT RAW RESPONSE START ---")
            print(result)
            print("--- GPT RAW RESPONSE END ---\n")

            return json.loads(result)

        except Exception as e:
            print(f"❌ GPT error during evidence chunk analysis: {e}")
            return {
                "summary": "Error during GPT analysis.",
                "keyFacts": [],
                "legalIssues": [],
                "credibilityConcerns": "",
                "recommendation": "",
                "verificationNotes": f"GPT error: {e}",
            }

    # ---------- Aggregate GPT results ----------
    summaries: List[str] = []
    keyFacts: List[str] = []
    legalIssues: List[str] = []
    credibilityNotes: List[str] = []
    recommendations: List[str] = []
    verificationNotes: List[str] = []

    for chunk in chunks:
        parsed = gpt_analyze(chunk)
        summaries.append(parsed.get("summary", ""))
        keyFacts.extend(parsed.get("keyFacts", []))
        legalIssues.extend(parsed.get("legalIssues", []))
        credibilityNotes.append(parsed.get("credibilityConcerns") or "")
        recommendations.append(parsed.get("recommendation") or "")
        verificationNotes.append(parsed.get("verificationNotes") or "")

    return SummarizeEvidenceResponse(
        filename=file.filename,
        sizeInBytes=total_bytes,
        readableSize=readable_size,
        fileType=ext,
        truncated=truncated,
        summary=" ".join(summaries),
        keyFacts=list(set(keyFacts)),
        legalIssues=list(set(legalIssues)),
        credibilityConcerns=" ".join(c for c in credibilityNotes if c),
        recommendation=" ".join(r for r in recommendations if r),
        verificationNotes="\n".join(v for v in verificationNotes if v),
    )

