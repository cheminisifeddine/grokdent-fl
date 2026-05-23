"""
GrokDent FL — Analytics Router
Provides dashboard statistics, KPIs, language breakdowns, and charts over time.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.api.auth import get_current_user
from backend.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analytics"])

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.get("/dashboard")
async def get_dashboard_kpis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve headline KPIs for the dashboard main view."""
    try:
        metrics = AnalyticsService.get_dashboard_metrics(current_user.clinic_id, db)
        return metrics
    except Exception as exc:
        logger.error("Failed to retrieve dashboard metrics: %s", exc)
        raise HTTPException(status_code=500, detail="Internal analytics computation error")

@router.get("/calls-over-time")
async def get_calls_trend(
    days: int = Query(7, description="Number of historical days, e.g. 7, 30, 90"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve daily call counts for the past X days."""
    try:
        data = AnalyticsService.get_calls_over_time(current_user.clinic_id, days, db)
        return data
    except Exception as exc:
        logger.error("Failed to retrieve calls over time: %s", exc)
        raise HTTPException(status_code=500, detail="Internal analytics error")

@router.get("/bookings-over-time")
async def get_bookings_trend(
    days: int = Query(7, description="Number of historical days, e.g. 7, 30, 90"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve daily appointment booking counts for the past X days."""
    try:
        data = AnalyticsService.get_bookings_over_time(current_user.clinic_id, days, db)
        return data
    except Exception as exc:
        logger.error("Failed to retrieve bookings over time: %s", exc)
        raise HTTPException(status_code=500, detail="Internal analytics error")

@router.get("/top-services")
async def get_top_services_ranked(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the most popular/requested dental service types."""
    try:
        data = AnalyticsService.get_top_services(current_user.clinic_id, db)
        return data
    except Exception as exc:
        logger.error("Failed to retrieve top services: %s", exc)
        raise HTTPException(status_code=500, detail="Internal analytics error")

@router.get("/language-breakdown")
async def get_language_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve call volume comparison between English and Spanish speakers."""
    try:
        data = AnalyticsService.get_language_stats(current_user.clinic_id, db)
        return data
    except Exception as exc:
        logger.error("Failed to retrieve language stats: %s", exc)
        raise HTTPException(status_code=500, detail="Internal analytics error")
