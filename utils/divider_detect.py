import json, zlib, base45
from typing import Optional
from pyzbar.pyzbar import decode
import cv2

def _unpack(data: bytes) -> Optional[dict]:
    try:
        raw = zlib.decompress(base45.b45decode(data.decode()))
        return json.loads(raw)
    except Exception:
        return None

def detect_divider(page_bgr) -> Optional[str]:
    for rot in [0, 1, 2, 3]:           # 0°, 90°, 180°, 270°
        img = cv2.rotate(page_bgr, rot) if rot else page_bgr
        for sym in decode(img):
            if sym.type == "QRCODE" and (p := _unpack(sym.data)):
                if p.get("marker") == "DIV":
                    return p["section"]
    return None
