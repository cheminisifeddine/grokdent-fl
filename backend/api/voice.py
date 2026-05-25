"""
Renia AI — Voice API Router
Exposes secure proxy endpoints for xAI Grok Realtime API session tokens and Text-to-Speech synthesis.
Ensures zero blocking I/O by utilizing httpx.AsyncClient.
"""

import logging
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.config import settings
from backend.models.user import User
from backend.api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Voice Receptionist"])


# --- Schemas ---

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text content to synthesize into voice speech")
    voice_id: Optional[str] = Field("eve", description="Voice selection ID (Ash, Coral, Sage, etc.)")
    speed: Optional[float] = Field(1.0, description="Speed of speech")
    language: Optional[str] = Field("en", description="Language code")


class SimulateRequest(BaseModel):
    scenario: Optional[str] = Field("general", description="Scenario type for simulation")
    voice: Optional[str] = Field("Ash", description="Selected voice persona")


# --- xAI Voice Map ---

XAI_VOICE_MAP = {
    "ash": "rex",
    "ballad": "ara",
    "coral": "eve",
    "sage": "eve",
    "verse": "sal",
    "ani": "ara",
    "eve": "eve",
    "leo": "leo"
}


# --- Routes ---

@router.post("/session-token")
async def get_session_token(current_user: User = Depends(get_current_user)):
    """
    Mints a secure, temporary 5-minute xAI Realtime API session token.
    Enables frontend browser voice clients to establish secure WebSocket streams directly to xAI.
    """
    xai_key = settings.XAI_API_KEY
    if not xai_key or xai_key == "placeholder":
        logger.error("XAI_API_KEY not configured on backend server")
        raise HTTPException(
            status_code=500,
            detail="xAI API key not configured on backend. Please add XAI_API_KEY to your .env file."
        )

    url = "https://api.x.ai/v1/realtime/client_secrets"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {xai_key}"
    }
    payload = {
        "expires_after": {"seconds": 300}
    }

    try:
        logger.info("Requesting client secret realtime session token from xAI...")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=15.0)

        if not response.is_success:
            err_text = response.text
            logger.error("xAI session token minting failed: %s (status %d)", err_text, response.status_code)
            raise HTTPException(
                status_code=502,
                detail=f"Failed to mint session token from xAI: {err_text[:200]}"
            )

        data = response.json()
        logger.info("Successfully minted xAI Realtime token. Expires at: %s", data.get("expires_at"))
        
        return {
            "token": data.get("value"),
            "expires_at": data.get("expires_at")
        }

    except httpx.HTTPError as http_err:
        logger.error("HTTP error calling xAI Realtime API: %s", http_err)
        raise HTTPException(status_code=502, detail="Network error contacting xAI Realtime API.")
    except Exception as exc:
        logger.error("Unexpected error in session token generation: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error generating session token.")


@router.post("/tts")
async def text_to_speech(body: TTSRequest, current_user: User = Depends(get_current_user)):
    """
    Secure Text-to-Speech proxy. Calls the xAI TTS API to synthesize text and streams
    the resulting audio/mpeg (MP3) back to the client, avoiding CORS issues and leaking API keys.
    """
    xai_key = settings.XAI_API_KEY
    if not xai_key or xai_key == "placeholder":
        logger.error("XAI_API_KEY not configured on backend server")
        raise HTTPException(
            status_code=500,
            detail="xAI API key not configured on backend. Please add XAI_API_KEY to your .env file."
        )

    # Resolve UI selection to official xAI voice code
    selected_voice = (body.voice_id or "eve").lower()
    matched_voice = XAI_VOICE_MAP.get(selected_voice, "eve")

    # Target xAI's OpenAI-compatible speech synthesis endpoint
    url = "https://api.x.ai/v1/audio/speech"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {xai_key}"
    }
    payload = {
        "model": "tts-1",
        "input": body.text,
        "voice": matched_voice,
        "speed": body.speed or 1.0
    }

    try:
        logger.info("Proxying Text-to-Speech request to xAI. Input text length: %d", len(body.text))
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=20.0)

        if not response.is_success:
            err_text = response.text
            logger.error("xAI TTS request failed: %s (status %d)", err_text, response.status_code)
            
            # Fallback to alternate TTS path `/v1/tts` if standard audio/speech is not supported
            logger.info("Attempting alternate xAI /tts endpoint fallback...")
            alt_url = "https://api.x.ai/v1/tts"
            alt_payload = {
                "text": body.text,
                "voice_id": matched_voice,
                "speed": body.speed or 1.0,
                "language": body.language or "en"
            }
            response = await client.post(alt_url, headers=headers, json=alt_payload, timeout=20.0)
            
            if not response.is_success:
                raise HTTPException(
                    status_code=502,
                    detail=f"xAI TTS services failed: {response.text[:200]}"
                )

        # Return streaming audio response
        return Response(content=response.content, media_type="audio/mpeg")

    except httpx.HTTPError as http_err:
        logger.error("HTTP error proxying to xAI TTS: %s", http_err)
        raise HTTPException(status_code=502, detail="Network error contacting xAI voice synthesis systems.")
    except Exception as exc:
        logger.error("Unexpected error in TTS synthesis proxy: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error during speech synthesis.")


@router.post("/simulate")
async def simulate_voice_agent(body: SimulateRequest, current_user: User = Depends(get_current_user)):
    """
    Simulation proxy route to test conversation prompts and system rules.
    """
    return {
        "status": "success",
        "message": f"Simulation initialized for voice {body.voice} in scenario {body.scenario}",
        "reply": f"Hello! This is {body.voice} AI Receptionist. I am fully provisioned and ready to simulate your dental clinic front desk."
    }
