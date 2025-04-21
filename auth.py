# auth.py
"""
Very small helper for local tests and simple header‑based auth.

Anything that calls the API must supply header:

    x-api-key: <whatever_key_you_choose>

For Render (production) you already store the real key as a secret.
For local tests we default to a dummy value so pytest can import it.
"""

import os
from fastapi import Header, HTTPException, status

# ---------- constant the tests need ----------
LAWQB_API_KEY: str = os.getenv("LAWQB_API_KEY", "dummy-local-key")
# ---------------------------------------------

def require_api_key(x_api_key: str = Header(..., alias="x-api-key")) -> None:
    """Raise 401 if header key doesn’t match."""
    if x_api_key != LAWQB_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

