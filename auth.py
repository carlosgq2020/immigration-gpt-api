# auth.py
from fastapi import Header, HTTPException, status, Depends
import os

_API_KEY = os.getenv("LAWQB_API_KEY")  # set in Render secrets

def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
