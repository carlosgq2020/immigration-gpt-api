import io
from fastapi.testclient import TestClient
from main import app
from auth import LAWQB_API_KEY

client = TestClient(app)

def test_case_facts_txt():
    content = b"This affidavit describes events in detail."
    files = {"file": ("facts.txt", content, "text/plain")}
    data = {"jurisdiction": "EOIR"}
    headers = {"x-api-key": LAWQB_API_KEY}
    resp = client.post("/uploadEvidence", files=files, data=data, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "case facts"


def test_country_conditions_txt():
    content = b"According to the U.S. Department of State Country Report, conditions remain unstable."
    files = {"file": ("cc.txt", content, "text/plain")}
    data = {"jurisdiction": "EOIR"}
    headers = {"x-api-key": LAWQB_API_KEY}
    resp = client.post("/uploadEvidence", files=files, data=data, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "country conditions"

