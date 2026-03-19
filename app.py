"""
Combined Microservice — AEM Algorithm
Includes both Card Generator (catbox.moe) and Twitter/X posting.

Deploy on Render.com free tier to save resources.
POST /generate  ->  {image_url}
POST /tweet     ->  {success, tweet_url}
GET  /health    ->  {status: ok}
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from requests_oauthlib import OAuth1

# ---------------------------------------------------------
# CARD GENERATOR MODULE SETUP
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# TWITTER OAUTH SETUP
# ---------------------------------------------------------
API_KEY = os.getenv("TWITTER_API_KEY", "")
API_SECRET = os.getenv("TWITTER_API_SECRET", "")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

TWEET_CREATE_URL = "https://api.twitter.com/2/tweets"
MEDIA_UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"

# ---------------------------------------------------------
# FASTAPI APP SETUP
# ---------------------------------------------------------
app = FastAPI(
    title="AEM Combined Cloud Service",
    description="Card Generator & Twitter Post service combined to save Render free tier.",
    version="1.1.0",
)

# --- Models ---
class CardRequest(BaseModel):
    term: str
    explanation: str
    day_num: int | None = None
    date: str | None = None      # e.g. "March 11, 2026"
    day_name: str | None = None  # e.g. "Wednesday"

class CardResponse(BaseModel):
    image_url: str
    term: str

class TweetRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=280)
    image_url: Optional[str] = None

class TweetResponse(BaseModel):
    success: bool
    tweet_id: str = ""
    tweet_url: str = ""
    error: str = ""

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "aem-combined-service"}


# --- 1) CARD GENERATION PIPELINE ---
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

@app.post("/generate", response_model=CardResponse)
async def generate(req: CardRequest):
    """
    Generate a branded card image and upload it to catbox.moe.
    Returns the public URL to use with Instagram Graph API / Telegram / Twitter.
    """
    if not req.term or not req.explanation:
        raise HTTPException(status_code=400, detail="term and explanation are required")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        output_path = tmp.name

    try:
        generate_card(
            term=req.term,
            explanation=req.explanation,
            output_path=output_path,
        )
        image_url = upload_to_catbox(output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.unlink(output_path)
        except OSError:
            pass

    return CardResponse(image_url=image_url, term=req.term)


# --- 2) TWITTER PIPELINE ---
def _oauth() -> OAuth1:
    if not (API_KEY and API_SECRET and ACCESS_TOKEN and ACCESS_TOKEN_SECRET):
        raise HTTPException(
            status_code=500,
            detail=(
                "Twitter credentials missing. Required env vars: "
                "TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, "
                "TWITTER_ACCESS_TOKEN_SECRET"
            ),
        )
    return OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

def _upload_media_from_url(image_url: str) -> str:
    import time
    headers = {"User-Agent": "AEM-Bot/1.0 (https://aem-algorithm.com)"}
    last_exc = None
    download_resp = None
    for attempt in range(3):
        try:
            download_resp = requests.get(image_url, timeout=30, headers=headers)
            download_resp.raise_for_status()
            break
        except Exception as exc:
            last_exc = exc
            time.sleep(2 * (attempt + 1))
    if download_resp is None or download_resp.status_code != 200:
        raise RuntimeError(f"Failed to download image_url after 3 retries: {last_exc}")

    try:
        upload_resp = requests.post(
            MEDIA_UPLOAD_URL,
            auth=_oauth(),
            files={"media": ("image.jpg", download_resp.content)},
            timeout=30,
        )
        upload_resp.raise_for_status()
        payload = upload_resp.json()
    except Exception as exc:
        raise RuntimeError(f"Failed to upload media to X: {exc}")

    media_id = payload.get("media_id_string")
    if not media_id:
        raise RuntimeError(f"media_id_string missing in upload response: {payload}")
    return media_id

def _create_tweet(text: str, media_id: Optional[str] = None) -> dict:
    body: dict[str, object] = {"text": text}
    if media_id:
        body["media"] = {"media_ids": [media_id]}

    try:
        resp = requests.post(
            TWEET_CREATE_URL,
            auth=_oauth(),
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        raise RuntimeError(f"Failed to create tweet: {exc}")

@app.post("/tweet", response_model=TweetResponse)
async def tweet(req: TweetRequest):
    text = req.text.strip()
    if len(text) > 280:
        return TweetResponse(success=False, error="text must be <= 280 characters")

    try:
        media_id = _upload_media_from_url(req.image_url) if req.image_url else None
        result = _create_tweet(text=text, media_id=media_id)

        tweet_id = (result.get("data") or {}).get("id", "")
        tweet_url = ""
        if tweet_id:
            tweet_url = f"https://x.com/i/web/status/{tweet_id}"

        return TweetResponse(success=True, tweet_id=tweet_id, tweet_url=tweet_url)
    except HTTPException:
        raise
    except Exception as exc:
        return TweetResponse(success=False, error=str(exc))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
