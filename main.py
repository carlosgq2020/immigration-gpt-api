from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
import json

app = FastAPI()

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
You are an expert U.S. immigration attorney. Use the IRAC format to answer the following legal question.
Include real U.S. immigration law citations (INA, 8 CFR, BIA, etc).
Return the answer as **pure JSON**, with no markdown formatting or code blocks.

Question: {req.question}
Jurisdiction: {req.jurisdiction or "General U.S. immigration law"}

Your JSON output should have these fields:
- issue
- rule
- application
- conclusion
- citations (as a list of strings)
- conflictsOrAmbiguities
- verificationNotes
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert immigration attorney who answers in clean JSON using IRAC."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()

        # Clean up GPT response (remove ```json if it appears)
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
