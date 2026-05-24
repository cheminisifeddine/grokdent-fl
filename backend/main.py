"""
GrokDent FL — Main FastAPI Application
Asynchronous backend API server, routes registration, WebSocket bridge for real-time dashboard updates,
HIPAA audit middleware injection, CORS configs, and dental practice database startup seeding.
"""

import os
import json
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import engine, Base, SessionLocal
from backend.middleware.hipaa_audit import HIPAAAuditMiddleware

_thread_pool = ThreadPoolExecutor(max_workers=2)

# Import routers
from backend.api.auth import router as auth_router
from backend.api.clinics import router as clinics_router
from backend.api.appointments import router as appointments_router
from backend.api.patients import router as patients_router
from backend.api.calls import router as calls_router
from backend.api.knowledge import router as knowledge_router
from backend.api.billing import router as billing_router
from backend.api.webhooks import router as webhooks_router
from backend.api.analytics import router as analytics_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Florida Dental Clinic AI Voice Receptionist & Analytics SaaS",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/v1/openapi.json"
)

# 1. CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend domain e.g., ["https://grokdent.fl"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. HIPAA Compliance Audit Log Middleware
app.add_middleware(HIPAAAuditMiddleware)

# 3. Startup Events: Create DB tables and seed insurance reference data
@app.on_event("startup")
async def on_startup():
    logger.info("Initializing GrokDent FL database tables...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_thread_pool, lambda: Base.metadata.create_all(bind=engine))
    
    # Seed initial insurance providers if none exist
    db = SessionLocal()
    try:
        from backend.models.insurance import Insurance
        from backend.utils.florida_data import FL_INSURANCE_PROVIDERS
        
        count = db.query(Insurance).count()
        if count == 0:
            logger.info("Seeding Florida dental insurance providers...")
            for name, details in FL_INSURANCE_PROVIDERS.items():
                ins = Insurance(
                    name=name,
                    type=details.get("type", "PPO"),
                    florida_specific=details.get("florida_specific", False),
                    phone=details.get("phone", "800-555-0199"),
                    website=details.get("website", "https://insurance.com"),
                    is_active=True
                )
                db.add(ins)
            db.commit()
            logger.info("Successfully seeded %d insurance providers.", len(FL_INSURANCE_PROVIDERS))
    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed initial insurance providers: %s", exc)
    finally:
        db.close()
    
    logger.info("GrokDent FL backend API startup complete.")

# 4. API Routes Registration (v1)
api_prefix = "/api/v1"
app.include_router(auth_router, prefix=f"{api_prefix}/auth")
app.include_router(clinics_router, prefix=f"{api_prefix}/clinics")
app.include_router(appointments_router, prefix=f"{api_prefix}/appointments")
app.include_router(patients_router, prefix=f"{api_prefix}/patients")
app.include_router(calls_router, prefix=f"{api_prefix}/calls")
app.include_router(knowledge_router, prefix=f"{api_prefix}/knowledge")
app.include_router(billing_router, prefix=f"{api_prefix}/billing")
app.include_router(webhooks_router, prefix=f"{api_prefix}/webhooks")
app.include_router(analytics_router, prefix=f"{api_prefix}/analytics")

# 5. Live Feed Real-time Dashboard WebSockets Connection Manager
class DashboardConnectionManager:
    """Manages active WebSocket dashboard connections to push live calls, metrics, and appointment bookings."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, clinic_id: str, websocket: WebSocket):
        await websocket.accept()
        if clinic_id not in self.active_connections:
            self.active_connections[clinic_id] = set()
        self.active_connections[clinic_id].add(websocket)
        logger.info("WebSocket connected for clinic: %s", clinic_id)
        
    def disconnect(self, clinic_id: str, websocket: WebSocket):
        if clinic_id in self.active_connections:
            self.active_connections[clinic_id].discard(websocket)
            if not self.active_connections[clinic_id]:
                del self.active_connections[clinic_id]
        logger.info("WebSocket disconnected for clinic: %s", clinic_id)
        
    async def broadcast_to_clinic(self, clinic_id: str, message: dict):
        """Pushes events directly to active browser tabs for that clinic."""
        if clinic_id in self.active_connections:
            websockets = list(self.active_connections[clinic_id])
            logger.info("Broadcasting WebSocket event to %d clients at clinic %s", len(websockets), clinic_id)
            await asyncio.gather(
                *[ws.send_json(message) for ws in websockets],
                return_exceptions=True
            )

ws_manager = DashboardConnectionManager()

@app.websocket("/ws/{clinic_id}")
async def websocket_endpoint(websocket: WebSocket, clinic_id: str):
    """Real-time updates websocket endpoint."""
    await ws_manager.connect(clinic_id, websocket)
    try:
        while True:
            # Keep connection open, listen for incoming heartbeats if any
            data = await websocket.receive_text()
            # Simple heartbeat ping-pong response
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(clinic_id, websocket)
    except Exception as exc:
        logger.error("WebSocket endpoint error: %s", exc)
        ws_manager.disconnect(clinic_id, websocket)

# Global helper to broadcast dashboard changes externally
async def broadcast_dashboard_event(clinic_id: str, event_type: str, data: dict):
    """Helper method to publish real-time events to active clinic sessions."""
    event = {
        "event": event_type,  # call_started | call_ended | appointment_booked | metric_updated
        "timestamp": asyncio.get_event_loop().time(),
        "data": data
    }
    await ws_manager.broadcast_to_clinic(clinic_id, event)

# 6. Basic Health check API
@app.get("/health", tags=["Utilities"])
async def health_check():
    """Service health state checks."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": "development" if settings.DEBUG else "production",
        "timestamp": asyncio.get_event_loop().time()
    }

# 7. Static Files & Frontend SPA routing
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.exists(frontend_dir):
    logger.info("Frontend directory found at: %s. Mounting static file server.", frontend_dir)
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def get_index():
        """Serve login page at root URL."""
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/{page_name}.html")
    async def serve_page(page_name: str):
        """Serve individual pages (signup, dashboard, calls, settings, etc.)."""
        page_path = os.path.join(frontend_dir, f"{page_name}.html")
        if os.path.exists(page_path):
            return FileResponse(page_path)
        return RedirectResponse(url="/")
else:
    logger.warning("Frontend static directory NOT found at %s. Root redirects disabled.", frontend_dir)
