from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from urllib.parse import urlparse
from app.services.enrollment_service import EnrollmentService
from app.core.config import settings
from app.core.admin_auth import require_user
from app.core.database import SessionLocal
from app.models.enrollment import Enrollment
from app.repositories.subscriber_repository import SubscriberRepository

try:
    import mercadopago
except Exception:
    mercadopago = None

router = APIRouter()


def _mercadopago_error_message(response: dict) -> str:
    message = response.get("message") or response.get("error") or "Could not create Mercado Pago preference"
    cause = response.get("cause")
    if isinstance(cause, list) and cause:
        first_cause = cause[0]
        if isinstance(first_cause, dict):
            cause_message = first_cause.get("description") or first_cause.get("message") or first_cause.get("code")
            if cause_message:
                return f"{message}: {cause_message}"
    if isinstance(cause, dict):
        cause_message = cause.get("description") or cause.get("message") or cause.get("code")
        if cause_message:
            return f"{message}: {cause_message}"
    return str(message)


def _can_auto_return(app_url: str) -> bool:
    parsed = urlparse(app_url)
    return parsed.scheme == "https" and parsed.hostname not in {"localhost", "127.0.0.1", "0.0.0.0"}


class WebhookPayload(BaseModel):
    enrollment_id: int
    status: str


@router.post('/webhook')
async def payment_webhook(payload: WebhookPayload):
    """Simple payment webhook stub.

    Expected JSON: { "enrollment_id": 123, "status": "paid" }
    If status == 'paid' the enrollment will be marked paid via EnrollmentService.mark_paid.
    """
    # Simple stub: if status says paid, mark paid
    if payload.status == 'paid':
        e = await EnrollmentService.mark_paid(payload.enrollment_id)
        if not e:
            raise HTTPException(status_code=404, detail='Enrollment not found')
        return { 'ok': True, 'enrollment_id': e.id, 'payment_status': e.payment_status }
    return { 'ok': True, 'received': payload.status }


class PreferenceRequest(BaseModel):
    enrollment_id: int
    title: str | None = None
    price: float | None = None
    quantity: int = 1


@router.post('/create_preference')
async def create_preference(req: PreferenceRequest, user=Depends(require_user)):
    db = SessionLocal()
    try:
        enrollment = db.query(Enrollment).filter(Enrollment.id == req.enrollment_id).first()
        if not enrollment:
            raise HTTPException(status_code=404, detail='Enrollment not found')
        if not user.is_admin:
            subscriber = SubscriberRepository.get_by_id(db, enrollment.subscriber_id)
            if not subscriber or subscriber.user_id != user.id:
                raise HTTPException(status_code=403, detail='Enrollment access denied')
        if not enrollment.course:
            raise HTTPException(status_code=404, detail='Course not found')

        title = enrollment.course.title
        price = float(enrollment.course.price or 0)
    finally:
        db.close()

    if price <= 0:
        paid = await EnrollmentService.mark_paid(req.enrollment_id)
        if not paid:
            raise HTTPException(status_code=404, detail='Enrollment not found')
        return {"free": True, "enrollment_id": paid.id, "payment_status": paid.payment_status}

    if mercadopago is None:
        raise HTTPException(status_code=500, detail='mercadopago SDK not installed')
    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail='Mercado Pago access token is not configured')

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN or '')

    preference = {
        "items": [
            {"title": title, "quantity": req.quantity, "unit_price": price}
        ],
        "metadata": {"enrollment_id": req.enrollment_id},
        "external_reference": str(req.enrollment_id),
        "back_urls": {
            "success": f"{settings.APP_URL}/payments/success?enrollment_id={req.enrollment_id}",
            "failure": f"{settings.APP_URL}/payments/failure?enrollment_id={req.enrollment_id}",
            "pending": f"{settings.APP_URL}/payments/pending?enrollment_id={req.enrollment_id}",
        },
    }
    if _can_auto_return(settings.APP_URL):
        preference["auto_return"] = "approved"
    if settings.MERCADOPAGO_NOTIFICATION_URL:
        preference["notification_url"] = settings.MERCADOPAGO_NOTIFICATION_URL

    res = sdk.preference().create(preference)
    response = res.get("response") or {}
    status = res.get("status")
    if status and int(status) >= 400:
        detail = _mercadopago_error_message(response)
        raise HTTPException(status_code=502, detail=f"Mercado Pago preference error: {detail}")

    init_point = response.get("init_point") or response.get("sandbox_init_point")
    if not init_point:
        raise HTTPException(
            status_code=502,
            detail=f"Mercado Pago preference missing checkout URL (status {status or 'unknown'})",
        )
    return {
        "init_point": init_point,
        "sandbox_init_point": response.get("sandbox_init_point"),
        "id": response.get("id"),
    }


@router.post('/webhook/mp')
async def mercadopago_webhook(request: Request):
    """Handle Mercado Pago notifications: verify payment via SDK and mark enrollment paid.

    Expects Mercado Pago notification body (with `type` and `data.id` or `id`).
    """
    if mercadopago is None:
        raise HTTPException(status_code=500, detail='mercadopago SDK not installed')

    body = await request.json()
    # Extract possible payment id from notification
    payment_id = None
    if isinstance(body, dict):
        # usual MP notification: {"type":"payment","data":{"id":<id>}}
        payment_id = body.get('data', {}).get('id') or body.get('id')

    if not payment_id:
        return {'ok': False, 'reason': 'no id found'}

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN or '')
    # Get payment details
    pay = sdk.payment().get(payment_id)
    pay_resp = pay.get('response') or {}

    # merchant_order id may be present in payment.response.order.id
    merchant_order_id = None
    order = pay_resp.get('order') or {}
    merchant_order_id = order.get('id') or pay_resp.get('order_id')

    if not merchant_order_id:
        return {'ok': False, 'reason': 'no merchant_order id'}

    mo = sdk.merchant_order().get(merchant_order_id)
    mo_resp = mo.get('response') or {}

    # Try to read external_reference which we set to enrollment_id when creating preference
    ext = mo_resp.get('external_reference')

    # Check payments inside merchant_order
    payments = mo_resp.get('payments') or []
    approved = any(p.get('status') == 'approved' for p in payments)

    if approved and ext:
        try:
            enrollment_id = int(ext)
            e = await EnrollmentService.mark_paid(enrollment_id)
            if not e:
                raise HTTPException(status_code=404, detail='Enrollment not found')
            return {'ok': True, 'enrollment_id': e.id}
        except ValueError:
            return {'ok': False, 'reason': 'invalid external reference'}

    return {'ok': True, 'approved': approved}
