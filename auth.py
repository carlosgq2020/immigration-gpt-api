# auth.py
"""
Tiny helper for header‑based API‑key auth and for the test‑suite.

Every request must include the header:

    x-api-key: <your‑secret>

In Render you set the secret in “Environment → LAWQB_API_KEY”.
For local tests we default to 'dummy-local-key'.
"""

import os
from fastapi import Header, HTTPException, status

# ------------------------------------------------------------------
# Constant the test‑suite imports
# ------------------------------------------------------------------
LAWQB_API_KEY: str = os.getenv("LAWQB_API_KEY", "dummy-local-key")
# ------------------------------------------------------------------


def require_api_key(x_api_key: str = Header(..., alias="x-api-key")) -> None:
    """
    FastAPI dependency.  Raises 401 if the supplied header
    doesn’t match LAWQB_API_KEY.
    """
    if x_api_key != LAWQB_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
