from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
import json

app = FastAPI()

# Load your OpenAI key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# ----------------------------
# IRAC Analysis Endpoint
# ----------------------------

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
You are an expert U.S. immigration attorney. Analyze the following legal question using the IRAC format.

Question: {req.question}
Jurisdiction: {req.jurisdiction or "General U.S. immigration law"}

Return only raw JSON (no markdown), with the following fields:
- issue
- rule
- application
- conclusion
- citations (list of strings)
- conflictsOrAmbiguities
- verificationNotes
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a legal expert. Respond ONLY in JSON using IRAC format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        # Remove markdown formatting if present
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


# ----------------------------
# Draft Motion Endpoint
# ----------------------------

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
You are an expert immigration litigator. Draft a persuasive legal motion based on the following:

- Issue: {req.issue}
- Facts: {req.facts}
- Jurisdiction: {req.jurisdiction or "EOIR/BIA"}

Return only raw JSON (no markdown), with the following fields:
- heading
- introduction
- legalArgument
- conclusion
- citations (list of strings)
- verificationNotes
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a legal brief writer. Respond in strict JSON format."},
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
