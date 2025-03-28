from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
import json

app = FastAPI()

# ✅ Initialize OpenAI client using v1.0+ style
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

        # 🧹 Clean markdown formatting if GPT includes ```json
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
- Be specific. Write like you are trying to persuade an immigration judge or BIA panel.
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
                {
                    "role": "system",
                    "content": (
                        "You are a senior U.S. immigration litigator. "
                        "Respond ONLY in raw, flat JSON with persuasive legal language, strong citations, and jurisdiction-specific reasoning. "
                        "Avoid markdown and avoid nested objects."
                    )
                },
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

        # Flatten any fields just in case
        def flatten(value):
            return json.dumps(value) if isinstance(value, dict) else value

        return DraftMotionResponse(
            heading=flatten(parsed.get("heading", "")),
            introduction=flatten(parsed.get("introduction", "")),
            legalArgument=flatten(parsed.get("legalArgument", "")),
            conclusion=flatten(parsed.get("conclusion", "")),
            citations=[
                json.dumps(c) if isinstance(c, dict) else c
                for c in parsed.get("citations", [])
            ],
            verificationNotes=flatten(parsed.get("verificationNotes", ""))
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

class SummarizeEvidenceRequest(BaseModel):
    text: str
    jurisdiction: Optional[str] = None
    context: Optional[str] = None  # e.g., "Asylum", "CAT", "Motion to Reopen"

class SummarizeEvidenceResponse(BaseModel):
    summary: str
    keyFacts: List[str]
    legalIssues: List[str]
    credibilityConcerns: str
    recommendation: str
    verificationNotes: str

@app.post("/uploadEvidence", response_model=SummarizeEvidenceResponse)
async def upload_evidence(file: UploadFile = File(...), jurisdiction: Optional[str] = None, context: Optional[str] = "Asylum"):

    ext = file.filename.lower().split(".")[-1]
    content = ""

    try:
        file_bytes = await file.read()

        if ext == "pdf":
            pdf = fitz.open(stream=file_bytes, filetype="pdf")
            for page in pdf:
                content += page.get_text()
            pdf.close()

        elif ext == "docx":
            from io import BytesIO
            doc = docx.Document(BytesIO(file_bytes))
            content = "\n".join([p.text for p in doc.paragraphs])

        elif ext == "txt":
            content = file_bytes.decode("utf-8")

        else:
            return SummarizeEvidenceResponse(
                summary="Unsupported file type",
                keyFacts=[],
                legalIssues=[],
                credibilityConcerns="",
                recommendation="",
                verificationNotes="Only PDF, DOCX, and TXT files are supported."
            )

    except Exception as e:
        return SummarizeEvidenceResponse(
            summary="Could not extract text from file.",
            keyFacts=[],
            legalIssues=[],
            credibilityConcerns="",
            recommendation="",
            verificationNotes=f"File read error: {str(e)}"
        )

    # Call GPT with content
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
                {"role": "system", "content": "You are a senior immigration litigator. Respond ONLY in strict, flat JSON. No markdown or nesting."},
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

        return SummarizeEvidenceResponse(
            summary=parsed.get("summary", ""),
            keyFacts=parsed.get("keyFacts", []),
            legalIssues=parsed.get("legalIssues", []),
            credibilityConcerns=parsed.get("credibilityConcerns", ""),
            recommendation=parsed.get("recommendation", ""),
            verificationNotes=parsed.get("verificationNotes", "")
        )

    except Exception as e:
        return SummarizeEvidenceResponse(
            summary="Error analyzing evidence",
            keyFacts=[],
            legalIssues=[],
            credibilityConcerns="",
            recommendation="",
            verificationNotes=f"GPT exception: {str(e)}"
        )
