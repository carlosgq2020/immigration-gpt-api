from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import openai
import os

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
You are an expert U.S. immigration attorney. Use IRAC legal analysis to answer the following question.

Question: {req.question}
Jurisdiction: {req.jurisdiction or "General U.S. immigration law"}

Return your answer in JSON with the following fields:
- issue
- rule
- application
- conclusion
- citations (as a list)
- conflictsOrAmbiguities
- verificationNotes

Respond only in raw JSON.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert immigration attorney that replies only in structured JSON using IRAC legal analysis. Include real citations."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    try:
        content = response["choices"][0]["message"]["content"]
        return eval(content)  # Assumes OpenAI returns properly formatted JSON
    except Exception as e:
        return {"error": str(e)}
