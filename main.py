from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
import json
from tempfile import SpooledTemporaryFile
import docx
import fitz  # PyMuPDF
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="LawQB Immigration Legal AI API",
    description="Upload declarations and receive legal analysis and motion drafting assistance. Powered by GPT-4.",
    version="1.0.0"
)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_UPLOAD_SIZE_MB = 50
MAX_CHARS_FOR_GPT = 12000

# ===========================
# Health Check
# ===========================
@app.get("/health", summary="Health check", description="Returns status ok.")
def healthcheck():
    return {"status": "ok"}

# ===========================
# Analyze (IRAC Format)
# ===========================

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

@app.post("/analyze", response_model=AnalyzeResponse, summary="Analyze legal question in IRAC format")
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
                {"role": "system", "content": "You are an immigration law expert. Reply using only IRAC format in JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"): content = content.replace("```json", "").strip()
        if content.endswith("```"): content = content[:-3].strip()
        parsed = json.loads(content)
        return AnalyzeResponse(**parsed)
    except Exception as e:
        return AnalyzeResponse(
            issue="Error generating analysis",
            rule="",
            application="",
            conclusion="",
            citations=[],
            conflictsOrAmbiguities="",
            verificationNotes=f"Exception: {str(e)}"
        )

# ===========================
# Draft Motion
# ===========================

class DraftMotionRequest(BaseModel):
    issue: str
    facts: str
    jurisdiction: Optional[str] = None

class DraftMotionResponse(BaseModel):
    heading: str
    introduction: str
    legalArgument: str
    conclusion: str
    citations: List[str]
    verificationNotes: str

@app.post("/draftMotion", response_model=DraftMotionResponse, summary="Generate immigration motion")
def draft_motion(req: DraftMotionRequest):
    prompt = f"""
You are a senior U.S. immigration litigator preparing a persuasive legal motion for EOIR or a federal court.

Issue: {req.issue}
Facts: {req.facts}
Jurisdiction: {req.jurisdiction or "EOIR / BIA or federal immigration courts"}

Your task:
- Draft a formal motion, citing relevant law, tailored to the facts and jurisdiction.
- Cite at least one post-2018 BIA or Circuit Court decision, and explain how it applies.
- Include statutory or regulatory citations (INA, 8 CFR, USCIS Policy Manual).
- Avoid generic examples like Matter of Acosta unless contextually required.
- Use precise legal language and structure.

Return ONLY raw flat JSON — no markdown.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior U.S. immigration litigator. "
                        "Respond ONLY in raw, flat JSON with persuasive legal language and strong citations."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"): content = content.replace("```json", "").strip()
        if content.endswith("```"): content = content[:-3].strip()
        parsed = json.loads(content)
        return DraftMotionResponse(**parsed)
    except Exception as e:
        return DraftMotionResponse(
            heading="Error generating motion",
            introduction="",
            legalArgument="",
            conclusion="",
            citations=[],
            verificationNotes=f"Exception: {str(e)}"
        )

# ===========================
# Upload Evidence & Summarize
# ===========================

from fastapi import UploadFile, File, Form
from typing import Optional, List
from pydantic import BaseModel
from io import BytesIO
from tempfile import SpooledTemporaryFile
import fitz  # PyMuPDF
import docx
import json
import openai
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    context: Optional[str] = Form("Asylum")
):
    ext = file.filename.lower().split(".")[-1]
    file_size = 0
    content = ""
    truncated = False

    try:
        temp_file = SpooledTemporaryFile(max_size=1024 * 1024 * 50)  # 50MB
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            temp_file.write(chunk)
            file_size += len(chunk)
        temp_file.seek(0)

        if ext == "docx":
            try:
                document = docx.Document(temp_file)
                paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
                content = "\n".join(paragraphs)
            except Exception as e:
                return _error_response("Could not process DOCX file", file, file_size, ext, truncated, str(e))

        elif ext == "pdf":
            try:
                content = ""
                pdf = fitz.open(stream=temp_file.read(), filetype="pdf")
                for page in pdf:
                    content += page.get_text()
                pdf.close()
            except Exception as e:
                return _error_response("Could not extract text from PDF", file, file_size, ext, truncated, str(e))

        elif ext == "txt":
            try:
                content = temp_file.read().decode("utf-8")
            except Exception as e:
                return _error_response("Could not decode text file", file, file_size, ext, truncated, str(e))

        else:
            return _error_response("Unsupported file type", file, file_size, ext, truncated, "Only PDF, DOCX, and TXT are supported.")

    except Exception as e:
        return _error_response("Error reading uploaded file", file, file_size, ext, truncated, str(e))

    # Truncate content if too long
    MAX_CHARS_FOR_GPT = 12000
    if len(content) > MAX_CHARS_FOR_GPT:
        content = content[:MAX_CHARS_FOR_GPT]
        truncated = True

    # Send to GPT
    prompt = f"""
You are an expert immigration attorney analyzing a piece of evidence (e.g., affidavit or declaration).

Jurisdiction: {jurisdiction or "General U.S. immigration law"}
Context: {context or "Asylum"}

Please summarize the text, extract key facts, identify legal issues, flag any credibility concerns, and give a recommendation on how this could support or weaken the case.

Text:
{content}

Respond ONLY in raw JSON with these fields:
- summary
- keyFacts (list of bullet point strings)
- legalIssues (list of bullet point strings)
- credibilityConcerns
- recommendation
- verificationNotes
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior immigration litigator. Respond ONLY in flat JSON. No markdown, no nested objects."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        output = response.choices[0].message.content.strip()
        if output.startswith("```json"):
            output = output.replace("```json", "").strip()
        if output.endswith("```"):
            output = output[:-3].strip()

        parsed = json.loads(output)
        if truncated:
            parsed["verificationNotes"] += "\nNote: Input file was truncated to ~12,000 characters to fit GPT model limits."

        return SummarizeEvidenceResponse(
            filename=file.filename,
            sizeInBytes=file_size,
            readableSize=_human_readable_size(file_size),
            fileType=ext,
            truncated=truncated,
            summary=parsed.get("summary", ""),
            keyFacts=parsed.get("keyFacts", []),
            legalIssues=parsed.get("legalIssues", []),
            credibilityConcerns=parsed.get("credibilityConcerns", ""),
            recommendation=parsed.get("recommendation", ""),
            verificationNotes=parsed.get("verificationNotes", "")
        )

    except Exception as e:
        return _error_response("GPT analysis failed", file, file_size, ext, truncated, str(e))


# --- Utility functions

def _error_response(summary, file, size, ext, truncated, detail=""):
    return SummarizeEvidenceResponse(
        filename=file.filename,
        sizeInBytes=size,
        readableSize=_human_readable_size(size),
        fileType=ext,
        truncated=truncated,
        summary=summary,
        keyFacts=[],
        legalIssues=[],
        credibilityConcerns="",
        recommendation="",
        verificationNotes=detail
    )

def _human_readable_size(size):
    for unit in ['bytes', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
