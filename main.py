from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
import json

app = FastAPI()

# Initialize OpenAI with your API key
openai.api_key = os.getenv("OPENAI_API_KEY")

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
You are an expert U.S. immigration attorney. Please analyze the following legal question using the IRAC format.

Question: {req.question}
Jurisdiction: {req.jurisdiction or "General U.S. immigration law"}

Please respond as raw JSON (no markdown), with the following fields:
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
                {"role": "system", "content": "You are an immigration attorney. Reply in strict JSON using IRAC."},
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
        return AnalyzeResponse(
            issue="Unable to complete analysis",
            rule="",
            application="",
            conclusion="",
            citations=[],
            conflictsOrAmbiguities="",
            verificationNotes=f"Error: {str(e)}"
        )
