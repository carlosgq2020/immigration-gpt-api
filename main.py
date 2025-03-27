from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
import json

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")

# -----------------------------
# IRAC Analyzer Schema & Route
# -----------------------------

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
You are a highly experienced U.S. immigration attorney. Analyze the following legal issue using the IRAC method.

Question: {req.question}
Jurisdiction: {req.jurisdiction or "General U.S. immigration law"}

Return your answer as raw JSON, with no markdown formatting or code block.

JSON fields:
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
                {"role": "system", "content": "You are an expert immigration lawyer. Answer using IRAC format in JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").strip()
        if content.endswith("```"):
            content = content[:-3].strip()

        parsed = json.loads(content)
        return parsed

    except Exception as e:
        return AnalyzeResponse(
            issue="Unable to complete analysis",
            rule="",
            application="",
            conclusion="",
            citations=[],
            conflictsOrAmbiguities="",
            verificationNotes=f"Error during GPT processing: {str(e)}"
        )

# -----------------------------
# Draft Motion Schema & Route
# -----------------------------

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
You are an expert immigration litigator. Draft a persuasive legal motion using the following:

- Legal Issue: {req.issue}
- Facts: {req.facts}
- Jurisdiction: {req.jurisdiction or "Federal immigration law (BIA, EOIR)"}

Return only raw JSON (no markdown) with these fields:
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
                {"role": "system", "content": "You are an expert litigator. Respond only in structured JSON legal format."},
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
        return parsed

    except Exception as e:
        return DraftMotionResponse(
            heading="Error",
            introduction="",
            legalArgument="",
            conclusion="",
            citations=[],
            verificationNotes=f"Error generating motion: {str(e)}"
        )
