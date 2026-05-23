"""
GrokDent FL — Billing & Subscriptions Router
Stripe checkout sessions, webhooks, plan info, and cancellations.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import stripe

from backend.config import settings
from backend.database import get_db
from backend.models.clinic import Clinic
from backend.models.user import User
from backend.api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Billing"])

# Configure stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

# Pricing plans
PLANS = {
    "starter": {
        "name": "Starter Plan",
        "price_monthly": 299.00,
        "call_limit": 200,
        "stripe_price_id": "price_starter_mock_123"
    },
    "professional": {
        "name": "Professional Plan",
        "price_monthly": 599.00,
        "call_limit": 500,
        "stripe_price_id": "price_professional_mock_456"
    },
    "enterprise": {
        "name": "Enterprise Plan",
        "price_monthly": 999.00,
        "call_limit": 999999,  # Unlimited
        "stripe_price_id": "price_enterprise_mock_789"
    }
}

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CheckoutRequest(BaseModel):
    plan_name: str  # starter | professional | enterprise
    success_url: str
    cancel_url: str

class CheckoutResponse(BaseModel):
    checkout_url: str

class SubscriptionStatusResponse(BaseModel):
    subscription_plan: str
    subscription_status: str
    stripe_subscription_id: Optional[str] = None
    call_limit: int
    price_monthly: float
    is_active: bool

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.get("/subscription", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the clinic's current active plan and billing status."""
    clinic = db.query(Clinic).filter(Clinic.id == current_user.clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    plan_key = clinic.subscription_plan or "starter"
    plan_info = PLANS.get(plan_key, PLANS["starter"])

    return SubscriptionStatusResponse(
        subscription_plan=plan_key,
        subscription_status=clinic.subscription_status or "trial",
        stripe_subscription_id=clinic.stripe_subscription_id,
        call_limit=plan_info["call_limit"],
        price_monthly=plan_info["price_monthly"],
        is_active=clinic.subscription_status in ("active", "trial")
    )

@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a Stripe checkout URL for practice subscription onboarding."""
    clinic = db.query(Clinic).filter(Clinic.id == current_user.clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    plan_key = body.plan_name.lower()
    if plan_key not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan name selection")

    plan_info = PLANS[plan_key]

    # In development/test mode without keys, simulate successful checkout URL
    if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY == "sk_test_placeholder":
        logger.warning("STRIPE_SECRET_KEY is placeholder — simulating success redirect URL")
        # Direct them back with a simulated success
        simulated_url = f"{body.success_url}?session_id=mock_checkout_session_{clinic.id}_{plan_key}"
        return CheckoutResponse(checkout_url=simulated_url)

    try:
        # Create Stripe customer if they don't have one
        customer_id = clinic.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                name=clinic.name,
                email=clinic.email or current_user.email,
                metadata={"clinic_id": clinic.id}
            )
            customer_id = customer.id
            clinic.stripe_customer_id = customer_id
            db.commit()

        # Create Checkout Session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": plan_info["stripe_price_id"],
                "quantity": 1,
            }],
            mode="subscription",
            success_url=body.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=body.cancel_url,
            metadata={
                "clinic_id": clinic.id,
                "plan_name": plan_key
            }
        )
        return CheckoutResponse(checkout_url=session.url)
    except Exception as exc:
        logger.error("Failed to create Stripe checkout session: %s", exc)
        raise HTTPException(status_code=500, detail=f"Stripe initialization error: {str(exc)}")

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel subscription via Stripe or fall back to local deactivation."""
    clinic = db.query(Clinic).filter(Clinic.id == current_user.clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    sub_id = clinic.stripe_subscription_id
    if sub_id and settings.STRIPE_SECRET_KEY and settings.STRIPE_SECRET_KEY != "sk_test_placeholder":
        try:
            stripe.Subscription.delete(sub_id)
        except Exception as exc:
            logger.error("Failed to cancel Stripe subscription %s: %s", sub_id, exc)
            # Continue to cancel locally anyway

    clinic.subscription_status = "cancelled"
    clinic.stripe_subscription_id = None
    db.commit()

    logger.info("Cancelled subscription for clinic: %s", clinic.name)
    return {"message": "Subscription successfully cancelled"}

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Receives Stripe asynchronous events for invoice payments, modifications, and cancellations."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    if not sig_header or not webhook_secret or webhook_secret == "whsec_placeholder":
        # Simulating webhook parsing in dev mode
        logger.warning("STRIPE_WEBHOOK_SECRET is empty/placeholder. Webhook signature skipped.")
        return Response(status_code=200)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return Response(status_code=400, content="Invalid payload")
    except stripe.error.SignatureVerificationError:
        return Response(status_code=400, content="Invalid signature")

    event_type = event["type"]
    data_obj = event["data"]["object"]

    logger.info("Processing Stripe webhook: %s", event_type)

    if event_type == "checkout.session.completed":
        clinic_id = data_obj["metadata"].get("clinic_id")
        plan_name = data_obj["metadata"].get("plan_name", "starter")
        sub_id = data_obj.get("subscription")

        clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
        if clinic:
            clinic.subscription_plan = plan_name
            clinic.stripe_subscription_id = sub_id
            clinic.subscription_status = "active"
            db.commit()
            logger.info("Clinic %s subscription upgraded to %s", clinic.name, plan_name)

    elif event_type == "invoice.payment_succeeded":
        sub_id = data_obj.get("subscription")
        clinic = db.query(Clinic).filter(Clinic.stripe_subscription_id == sub_id).first()
        if clinic:
            clinic.subscription_status = "active"
            db.commit()

    elif event_type == "invoice.payment_failed":
        sub_id = data_obj.get("subscription")
        clinic = db.query(Clinic).filter(Clinic.stripe_subscription_id == sub_id).first()
        if clinic:
            clinic.subscription_status = "inactive"
            db.commit()
            logger.warning("Billing invoice payment failed for clinic %s", clinic.name)

    elif event_type == "customer.subscription.deleted":
        sub_id = data_obj.get("id")
        clinic = db.query(Clinic).filter(Clinic.stripe_subscription_id == sub_id).first()
        if clinic:
            clinic.subscription_status = "inactive"
            clinic.stripe_subscription_id = None
            db.commit()
            logger.info("Stripe subscription deleted/ended for clinic %s", clinic.name)

    return Response(status_code=200)
