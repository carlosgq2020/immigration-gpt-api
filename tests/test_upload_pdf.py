import io, os, pytest
from fastapi.testclient import TestClient
from main import app
from auth import LAWQB_API_KEY

client = TestClient(app)

def tiny_pdf():
    # 1‑page blank PDF bytes
    return (b'%PDF-1.4\n1 0 obj<<>>endobj\n'
            b'2 0 obj<<>>endobj\n'
            b'3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 100 100]>>endobj\n'
            b'4 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n'
            b'5 0 obj<</Type/Catalog/Pages 4 0 R>>endobj\n'
            b'xref\n0 6\n0000000000 65535 f \n'
            b'trailer<</Root 5 0 R/Size 6>>\nstartxref\n123\n%%EOF')

def test_pdf_upload():
    files = {"file": ("blank.pdf", tiny_pdf(), "application/pdf")}
    data  = {"jurisdiction": "EOIR", "context": "Asylum"}
    headers = {"x-api-key": LAWQB_API_KEY}

    resp = client.post("/uploadEvidence", files=files, data=data, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["fileType"] == "pdf"

