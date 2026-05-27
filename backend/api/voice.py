"""
Renia AI — Voice API Router
Exposes secure proxy endpoints for xAI Grok Realtime API session tokens and Text-to-Speech synthesis.
Ensures zero blocking I/O by utilizing httpx.AsyncClient.
"""

import json
import logging
import re
import time
import httpx
from collections import defaultdict, deque
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response
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


class LandingDemoTurn(BaseModel):
    role: str = Field(..., max_length=16)
    content: str = Field(..., max_length=700)


class LandingDemoRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=700)
    history: List[LandingDemoTurn] = Field(default_factory=list, max_length=10)


class LandingDemoResponse(BaseModel):
    reply: str
    patient_name: str = "Prospect"
    triage: str = "Consultation"
    insurance: str = "Demo Mode"
    portal_status: str = "Ready"
    pipeline_status: str = "Live Demo"
    log: str = "Conversation handled by Renia voice demo."


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


_landing_demo_hits: Dict[str, deque[float]] = defaultdict(deque)
_LANDING_DEMO_LIMIT = 24
_LANDING_DEMO_WINDOW_SECONDS = 60


LANDING_DEMO_SYSTEM_PROMPT = """
You are Renia, a live voice demo for a Florida dental AI receptionist product.

Your audience is usually a dentist, office manager, or patient role-playing a dental call.
Your job is to sell the product by demonstrating the receptionist experience, not by giving
a long sales pitch. Sound warm, human, confident, and fast.

Core capabilities to demonstrate naturally:
- Answer inbound dental calls 24/7 without voicemail.
- Triage emergencies such as tooth pain, swelling, trauma, or bleeding.
- Capture caller name, phone, reason for visit, preferred time, insurance, and language.
- Offer realistic same-day emergency openings and routine appointment times.
- Explain that production integrations can write appointments to Dentrix, Eaglesoft, or Open Dental.
- Explain that production integrations can verify eligibility for Delta Dental PPO, Humana, Guardian,
  MCNA Florida Medicaid, Florida Blue, and Cigna when the clinic connects its payer workflows.
- Handle English or Spanish in the caller's language.

Important guardrails:
- This is a landing-page demo. Do not claim you actually booked a real appointment, verified real
  insurance, or stored real patient data. Use phrases like "for this demo" or "in production I would".
- Do not ask for sensitive medical details beyond what is needed for a dental front-desk triage demo.
- Keep each spoken reply under 55 words.
- If the caller is evaluating as a dentist, invite them to test you with a hard front-desk scenario.
- If the caller role-plays as a patient, act like the receptionist and move them toward booking.

Return JSON only with these keys:
reply, patient_name, triage, insurance, portal_status, pipeline_status, log.
"""


def _enforce_landing_demo_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    hits = _landing_demo_hits[client_ip]

    while hits and now - hits[0] > _LANDING_DEMO_WINDOW_SECONDS:
        hits.popleft()

    if len(hits) >= _LANDING_DEMO_LIMIT:
        raise HTTPException(status_code=429, detail="Demo limit reached. Please wait a minute and try again.")

    hits.append(now)


def _extract_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _landing_demo_fallback(user_message: str) -> LandingDemoResponse:
    lower = user_message.lower()
    if any(term in lower for term in ("spanish", "español", "espanol", "dolor", "muela")):
        return LandingDemoResponse(
            reply=(
                "Claro. Para esta demo, puedo atender en español, clasificar el dolor como urgencia, "
                "ofrecer una cita hoy y preparar el registro para Dentrix o Eaglesoft."
            ),
            patient_name="Spanish Caller",
            triage="Emergency tooth pain",
            insurance="Pending capture",
            portal_status="Demo ready",
            pipeline_status="Bilingual flow",
            log="Spanish triage path selected. Ready to capture appointment and insurance fields.",
        )

    if any(term in lower for term in ("insurance", "delta", "humana", "ppo", "medicaid")):
        return LandingDemoResponse(
            reply=(
                "For this demo, I can capture payer details, explain eligibility steps, and show how "
                "production verification flows reduce front-desk hold time."
            ),
            patient_name="Insurance Lead",
            triage="Benefits question",
            insurance="PPO or Medicaid",
            portal_status="Eligibility demo",
            pipeline_status="Payer workflow",
            log="Insurance-focused demo path selected. Eligibility status is simulated on the landing page.",
        )

    return LandingDemoResponse(
        reply=(
            "Hi, this is Renia for the dental office. Try me with a real front-desk call: emergency pain, "
            "a Spanish caller, Delta Dental eligibility, or booking a new patient cleaning."
        ),
        patient_name="Dentist Prospect",
        triage="Demo evaluation",
        insurance="Demo Mode",
        portal_status="Ready",
        pipeline_status="Voice demo active",
        log="Fallback response served because live Grok generation was unavailable.",
    )


# --- Routes ---

@router.post("/session-token")
async def get_session_token(current_user: User = Depends(get_current_user)):
    """
    Mints a secure, temporary 5-minute xAI Realtime API session token.
    Enables frontend browser voice clients to establish secure WebSocket streams directly to xAI.
    """
    # Use clinic-level key first, then fall back to server env
    xai_key = getattr(current_user.clinic, 'xai_key', None) if current_user.clinic else None
    if not xai_key:
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
    # Use clinic-level key first, then fall back to server env
    xai_key = getattr(current_user.clinic, 'xai_key', None) if current_user.clinic else None
    if not xai_key:
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


@router.get("/xai-key")
async def get_default_xai_key(current_user: User = Depends(get_current_user)):
    """
    Returns the default xAI API key for the frontend to use.
    Checks clinic-level key first, then falls back to server environment.
    """
    xai_key = getattr(current_user.clinic, 'xai_key', None) if current_user.clinic else None
    if not xai_key:
        xai_key = settings.XAI_API_KEY
    return {"xai_key": xai_key or ""}


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


@router.post("/landing-demo", response_model=LandingDemoResponse)
async def landing_voice_demo(body: LandingDemoRequest, request: Request):
    """
    Public landing-page voice demo.

    The browser supplies speech-to-text text. The backend calls Grok with the
    server-side XAI_API_KEY and returns a compact JSON payload the page can speak
    with browser speech synthesis. No API key is exposed to visitors.
    """
    _enforce_landing_demo_rate_limit(request)

    xai_key = settings.XAI_API_KEY
    if not xai_key or xai_key == "placeholder":
        logger.warning("XAI_API_KEY not configured; serving landing demo fallback.")
        return _landing_demo_fallback(body.message)

    messages = [{"role": "system", "content": LANDING_DEMO_SYSTEM_PROMPT}]

    for turn in body.history[-8:]:
        role = "assistant" if turn.role == "assistant" else "user"
        messages.append({"role": role, "content": turn.content})

    messages.append({"role": "user", "content": body.message})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {xai_key}",
    }
    payload = {
        "model": "grok-4.20-reasoning",
        "messages": messages,
        "temperature": 0.45,
        "max_tokens": 360,
    }

    try:
        async with httpx.AsyncClient(base_url=settings.XAI_BASE_URL.rstrip("/")) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload, timeout=20.0)

        if not response.is_success:
            logger.error("Landing demo Grok call failed: status=%s body=%s", response.status_code, response.text[:300])
            return _landing_demo_fallback(body.message)

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = _extract_json_object(content)

        return LandingDemoResponse(
            reply=str(parsed.get("reply") or _landing_demo_fallback(body.message).reply)[:700],
            patient_name=str(parsed.get("patient_name") or "Prospect")[:80],
            triage=str(parsed.get("triage") or "Consultation")[:80],
            insurance=str(parsed.get("insurance") or "Demo Mode")[:80],
            portal_status=str(parsed.get("portal_status") or "Ready")[:80],
            pipeline_status=str(parsed.get("pipeline_status") or "Live Demo")[:80],
            log=str(parsed.get("log") or "Renia handled the landing-page demo turn.")[:180],
        )

    except Exception as exc:
        logger.error("Landing demo generation failed: %s", exc)
        return _landing_demo_fallback(body.message)
