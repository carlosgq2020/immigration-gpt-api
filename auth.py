<<<<<<< HEAD
# auth.py
"""
Tiny helper for header‑based API‑key auth and for the test‑suite.

Usage
=====

Every request must include a header:

    x-api-key: <your-secret>

For production Render you already inject the secret via “Environment → OPENAI_API_KEY”.
For local tests we default to 'dummy-local-key'.

The test file `tests/test_upload_pdf.py` imports `LAWQB_API_KEY`,
so we expose it as a module‑level constant.
"""

import os
from fastapi import Header, HTTPException, status

# ------------------------------------------------------------------
# This constant is what the test imports.  Keep the name *exactly*.
# ------------------------------------------------------------------
LAWQB_API_KEY: str = os.getenv("LAWQB_API_KEY", "dummy-local-key")
# ------------------------------------------------------------------


def require_api_key(x_api_key: str = Header(..., alias="x-api-key")) -> None:
    """
    Dependency for FastAPI routes.
    Raises 401 if the supplied header doesn’t match LAWQB_API_KEY.
    """
    if x_api_key != LAWQB_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
=======
import os
LAWQB_API_KEY = os.getenv("LAWQB_API_KEY", "dummy-local-key")
def verify_key(key: str) -> bool:
    return key == LAWQB_API_KEY

>>>>>>> a4e3613 (Add LAWQB_API_KEY constant)
