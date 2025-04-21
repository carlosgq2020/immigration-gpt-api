import io, pathlib, base64, json, httpx

API_KEY = "local-dev-key"  # overridden in CI

def tiny_pdf() -> bytes:
    """1‑page blank PDF created with PyMuPDF."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    buf = doc.tobytes()
    doc.close()
    return buf

def test_pdf_upload():
    pdf_bytes = tiny_pdf()
    files = {"file": ("blank.pdf", pdf_bytes, "application/pdf")}
    data  = {"jurisdiction": "EOIR", "context": "Asylum"}
    headers = {"x-api-key": API_KEY}

    resp = httpx.post("http://localhost:8000/uploadEvidence",
                      files=files, data=data, headers=headers, timeout=30.0)
    assert resp.status_code == 200
    js = resp.json()
    # blank PDF will yield empty summary but must not error
    assert js["fileType"] == "pdf"
    assert js["summary"] != "Could not process file."
