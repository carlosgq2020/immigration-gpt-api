from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
import os
import json

app = FastAPI()

# Initialize OpenAI client with your API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
- citations (as a list of strings)
- conflictsOrAmbiguities
- verificationNotes
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert immigration lawyer. Answer using structured JSON with full citations and legal references using IRAC."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()

        # Clean up formatting just in case GPT includes code block marks
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
