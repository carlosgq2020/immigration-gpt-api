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

class SummarizeEvidenceResponse(BaseModel):
    filename: str
    fileType: str
    sizeInBytes: int
    truncated: bool
    summary: str
    keyFacts: List[str]
    legalIssues: List[str]
    credibilityConcerns: str
    recommendation: str
    verificationNotes: str

@app.post("/uploadEvidence", response_model=SummarizeEvidenceResponse, summary="Upload evidence (PDF, DOCX, TXT)", description="Parses declaration and returns asylum-focused summary + legal analysis.")
async def upload_evidence(
    file: UploadFile = File(...),
    jurisdiction: Optional[str] = Form(None),
    context: Optional[str] = Form("Asylum")
):
    ext = file.filename.lower().split(".")[-1]
    temp_file = SpooledTemporaryFile(max_size=1024 * 1024 * MAX_UPLOAD_SIZE_MB)
    content = ""
    truncated = False

    await file.seek(0, 2)
    size = await file.tell()
    await file.seek(0)

    if size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        return SummarizeEvidenceResponse(
            filename=file.filename,
            fileType=ext,
            sizeInBytes=size,
            truncated=False,
            summary="File is too large to process.",
            keyFacts=[], legalIssues=[], credibilityConcerns="",
            recommendation="", verificationNotes="File exceeded max upload size of 50MB"
        )

    # Read content into temp_file
    while chunk := await file.read(1024 * 1024):
        temp_file.write(chunk)
    temp_file.seek(0)

    try:
        if ext == "docx":
            document = docx.Document(temp_file)
            paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
            content = "\n".join(paragraphs)
        elif ext == "pdf":
            pdf = fitz.open(stream=temp_file.read(), filetype="pdf")
            content = "\n".join([page.get_text() for page in pdf])
            pdf.close()
        elif ext == "txt":
            content = temp_file.read().decode("utf-8")
        else:
            return SummarizeEvidenceResponse(
                filename=file.filename,
                fileType=ext,
                sizeInBytes=size,
                truncated=False,
                summary="Unsupported file type.",
                keyFacts=[], legalIssues=[], credibilityConcerns="",
                recommendation="", verificationNotes="Only PDF, DOCX, and TXT files are supported."
            )
    except Exception as e:
        return SummarizeEvidenceResponse(
            filename=file.filename,
            fileType=ext,
            sizeInBytes=size,
            truncated=False,
            summary="Error processing file.",
            keyFacts=[], legalIssues=[], credibilityConcerns="",
            recommendation="", verificationNotes=f"Error reading content: {str(e)}"
        )

    if len(content) > MAX_CHARS_FOR_GPT:
        content = content[:MAX_CHARS_FOR_GPT]
        truncated = True

    prompt = f"""
You are an expert immigration litigator. Analyze the following text as evidence in an asylum or immigration case.

Jurisdiction: {jurisdiction or "General"}
Context: {context}

Provide:
- summary
- keyFacts (list of strings)
- legalIssues (list of strings)
- credibilityConcerns
- recommendation
- verificationNotes

Text:
{content}

Reply ONLY in valid flat JSON.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior immigration litigator. Reply ONLY in raw flat JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        output = response.choices[0].message.content.strip()
        if output.startswith("```json"): output = output.replace("```json", "").strip()
        if output.endswith("```"): output = output[:-3].strip()
        parsed = json.loads(output)
        if truncated:
            parsed["verificationNotes"] += "\nNote: File was truncated to ~12,000 characters for GPT processing."

        return SummarizeEvidenceResponse(
            filename=file.filename,
            fileType=ext,
            sizeInBytes=size,
            truncated=truncated,
            **parsed
        )
    except Exception as e:
        return SummarizeEvidenceResponse(
            filename=file.filename,
            fileType=ext,
            sizeInBytes=size,
            truncated=truncated,
            summary="GPT analysis failed.",
            keyFacts=[], legalIssues=[], credibilityConcerns="",
            recommendation="", verificationNotes=f"GPT error: {str(e)}"
        )

# ===========================
# Test Upload (Dev Tool)
# ===========================
@app.post("/testUpload", summary="Echo file for testing")
async def test_upload(file: UploadFile = File(...)):
    content = await file.read()
    return {
        "filename": file.filename,
        "size": len(content),
        "preview": content.decode("utf-8")[:500]
    }
