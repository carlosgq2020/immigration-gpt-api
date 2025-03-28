from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
import json
from tempfile import SpooledTemporaryFile
import docx
import fitz  # PyMuPDF

app = FastAPI()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------
# /analyze Endpoint (IRAC Format)
# -------------------------------

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
                {"role": "system", "content": "You are an immigration law expert. Reply using only IRAC format in JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").strip()
        if content.endswith("```"):
            content = content[:-3].strip()

        parsed = json.loads(content)

        return AnalyzeResponse(
            issue=parsed.get("issue", ""),
            rule=parsed.get("rule", ""),
            application=parsed.get("application", ""),
            conclusion=parsed.get("conclusion", ""),
            citations=parsed.get("citations", []),
            conflictsOrAmbiguities=parsed.get("conflictsOrAmbiguities", ""),
            verificationNotes=parsed.get("verificationNotes", "")
        )

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

# -------------------------------
# /draftMotion Endpoint
# -------------------------------

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

@app.post("/draftMotion", response_model=DraftMotionResponse)
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

Your response must be valid JSON — no markdown, no extra formatting.
Return the following fields:

- heading
- introduction
- legalArgument
- conclusion
- citations (list of strings)
- verificationNotes
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior U.S. immigration litigator. Respond ONLY in flat JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").strip()
        if content.endswith("```"):
            content = content[:-3].strip()

        parsed = json.loads(content)

        return DraftMotionResponse(
            heading=parsed.get("heading", ""),
            introduction=parsed.get("introduction", ""),
            legalArgument=parsed.get("legalArgument", ""),
            conclusion=parsed.get("conclusion", ""),
            citations=parsed.get("citations", []),
            verificationNotes=parsed.get("verificationNotes", "")
        )

    except Exception as e:
        return DraftMotionResponse(
            heading="Error generating motion",
            introduction="",
            legalArgument="",
            conclusion="",
            citations=[],
            verificationNotes=f"Exception: {str(e)}"
        )

# -------------------------------
# /uploadEvidence Endpoint
# -------------------------------

class SummarizeEvidenceResponse(BaseModel):
    filename: str
    sizeInBytes: int
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
    content = ""
    truncated = False

    try:
        temp_file = SpooledTemporaryFile(max_size=1024 * 1024 * 50)  # 50MB
        while chunk := await file.read(1024 * 1024):
            temp_file.write(chunk)

        temp_file.seek(0)

        if ext == "docx":
            doc = docx.Document(temp_file)
            content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

        elif ext == "pdf":
            pdf = fitz.open(stream=temp_file.read(), filetype="pdf")
            content = "\n".join(page.get_text() for page in pdf)
            pdf.close()

        elif ext == "txt":
            content = temp_file.read().decode("utf-8")

        else:
            return SummarizeEvidenceResponse(
                filename=file.filename,
                sizeInBytes=0,
                fileType=ext,
                truncated=False,
                summary="Unsupported file type.",
                keyFacts=[],
                legalIssues=[],
                credibilityConcerns="",
                recommendation="",
                verificationNotes="Only PDF, DOCX, and TXT are supported."
            )

    except Exception as e:
        return SummarizeEvidenceResponse(
            filename=file.filename,
            sizeInBytes=0,
            fileType=ext,
            truncated=False,
            summary="Could not read file.",
            keyFacts=[],
            legalIssues=[],
            credibilityConcerns="",
            recommendation="",
            verificationNotes=f"Read error: {str(e)}"
        )

    MAX_CHARS = 12000
    if len(content) > MAX_CHARS:
        content = content[:MAX_CHARS]
        truncated = True

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

        notes = parsed.get("verificationNotes", "")
        if truncated:
            notes += "\nNote: Input file was truncated to ~12,000 characters."

        return SummarizeEvidenceResponse(
            filename=file.filename,
            sizeInBytes=len(content.encode("utf-8")),
            fileType=ext,
            truncated=truncated,
            summary=parsed.get("summary", ""),
            keyFacts=parsed.get("keyFacts", []),
            legalIssues=parsed.get("legalIssues", []),
            credibilityConcerns=parsed.get("credibilityConcerns", ""),
            recommendation=parsed.get("recommendation", ""),
            verificationNotes=notes
        )

    except Exception as e:
        return SummarizeEvidenceResponse(
            filename=file.filename,
            sizeInBytes=0,
            fileType=ext,
            truncated=truncated,
            summary="GPT analysis failed.",
            keyFacts=[],
            legalIssues=[],
            credibilityConcerns="",
            recommendation="",
            verificationNotes=f"GPT error: {str(e)}"
        )
