# Immigration GPT API

This project exposes a small FastAPI service for analyzing immigration case files using OpenAI models. The API allows you to submit legal questions and upload evidence documents for summarization and legal analysis.

## Setup

1. **Python 3.11** is recommended.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file (not committed to git) and define the following variables:

```
OPENAI_API_KEY=your-openai-key
LAWQB_API_KEY=your-api-key
```

## Running the Server

Start the API locally with Uvicorn:

```bash
uvicorn main:app --reload
```

## API Endpoints

- `POST /analyze` – Submit a legal question and receive an IRAC analysis.
- `POST /uploadEvidence` – Upload a PDF, DOCX, or TXT file. The file is read (with OCR fallback for PDFs) and summarized in chunks using GPT-4.

The OpenAPI specification can be found in `openapi.yaml`.

## Tests

Run the unit tests with:

```bash
pytest
```

## Utility Scripts

- `toc_parser_final.py` – Extracts a table of contents from a PDF.
- `segment_by_toc.py` – Splits a PDF into segments based on a TOC JSON file.

These scripts are optional helpers and are not required for running the API.
