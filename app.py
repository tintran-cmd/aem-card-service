"""
Card Generator Microservice — AEM Algorithm
FastAPI wrapper around instagram_definition_card.py

Deploy on Render.com free tier.
POST /generate  ->  {image_url}
GET  /health    ->  {status: ok}
"""

import io
import os
import sys
import tempfile
from pathlib import Path

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Allow importing the card generator from the parent package
# When deployed on Render, copy instagram_definition_card.py alongside app.py
CARD_MODULE_PATH = Path(__file__).parent
sys.path.insert(0, str(CARD_MODULE_PATH))

try:
    from instagram_definition_card import generate_card
except ImportError:
    raise RuntimeError(
        "instagram_definition_card.py must be in the same directory as app.py"
    )

CATBOX_URL = "https://catbox.moe/user/api.php"
CATBOX_USERHASH = os.getenv("CATBOX_USERHASH", "")  # optional catbox account

app = FastAPI(
    title="AEM Card Generator",
    description="Generates branded 1080x1080 crypto education cards and returns a public image URL.",
    version="1.0.0",
)


class CardRequest(BaseModel):
    term: str
    explanation: str
    day_num: int | None = None
    day_name: str | None = None  # e.g. "mon", "tue" ... used in filename hint


class CardResponse(BaseModel):
    image_url: str
    term: str


def upload_to_catbox(file_path: str) -> str:
    """Upload a file to catbox.moe and return the public URL."""
    with open(file_path, "rb") as f:
        payload = {"reqtype": "fileupload"}
        if CATBOX_USERHASH:
            payload["userhash"] = CATBOX_USERHASH
        resp = requests.post(
            CATBOX_URL,
            files={"fileToUpload": f},
            data=payload,
            timeout=30,
        )
    resp.raise_for_status()
    url = resp.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"catbox.moe upload failed: {url}")
    return url


@app.get("/health")
async def health():
    return {"status": "ok", "service": "aem-card-generator"}


@app.post("/generate", response_model=CardResponse)
async def generate(req: CardRequest):
    """
    Generate a branded card image and upload it to catbox.moe.

    Returns the public URL to use with Instagram Graph API.
    """
    if not req.term or not req.explanation:
        raise HTTPException(status_code=400, detail="term and explanation are required")

    # Use a temp file so the service is stateless
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        output_path = tmp.name

    try:
        generate_card(
            term=req.term,
            explanation=req.explanation,
            output_path=output_path,
            day_num=req.day_num,
        )
        image_url = upload_to_catbox(output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Always clean up temp file
        try:
            os.unlink(output_path)
        except OSError:
            pass

    return CardResponse(image_url=image_url, term=req.term)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
