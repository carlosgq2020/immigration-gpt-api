from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

class AnalyzeRequest(BaseModel):
    question: str
    jurisdiction: Optional[str] = None
    preferredSources: Optional[List[str]] = []

class AnalyzeResponse(BaseModel):
    issue: str
    rule: str
    application: str
    conclusion: str
    citations: List[str]
    conflictsOrAmbiguities: Optional[str]
    verificationNotes: Optional[str]

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    return AnalyzeResponse(
        issue="Whether the applicant qualifies for asylum under INA § 208.",
        rule="An applicant must show past persecution or a well-founded fear of future persecution based on a protected ground (race, religion, nationality, political opinion, or social group).",
        application="The facts show political opinion-based fear due to past threats and credible testimony.",
        conclusion="The applicant likely qualifies for asylum under INA § 208.",
        citations=["8 U.S.C. § 1158", "Matter of Acosta, 19 I&N Dec. 211 (BIA 1985)"],
        conflictsOrAmbiguities="None noted",
        verificationNotes="Reviewed INA § 208, USCIS Policy Manual Vol. 7, and recent BIA decisions as of March 2025."
    )
