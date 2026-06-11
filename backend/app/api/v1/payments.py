import hashlib
import hmac
import json
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


def _parse_mp_signature(signature: str | None) -> dict[str, str]:
    if not signature:
        return {}
    parts = {}
    for item in signature.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parts[key.strip()] = value.strip()
    return parts


def _verify_mp_signature(request: Request, payment_id: str | None) -> None:
    if not settings.MERCADOPAGO_WEBHOOK_SECRET:
        return
    signature = _parse_mp_signature(request.headers.get("x-signature"))
    request_id = request.headers.get("x-request-id")
    ts = signature.get("ts")
    v1 = signature.get("v1")
    if not payment_id or not request_id or not ts or not v1:
        raise HTTPException(status_code=401, detail="Invalid Mercado Pago webhook signature")

    signed_payload = f"id:{payment_id};request-id:{request_id};ts:{ts};"
    expected = hmac.new(
        settings.MERCADOPAGO_WEBHOOK_SECRET.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, v1):
        raise HTTPException(status_code=401, detail="Invalid Mercado Pago webhook signature")


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
        paid = await EnrollmentService.mark_paid(req.enrollment_id, payment_method="free")
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
    await EnrollmentService.update_payment_attempt(
        req.enrollment_id,
        payment_method="mercadopago",
        payment_provider_id=response.get("id"),
        payment_provider_status="preference_created",
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

    raw_body = await request.body()
    try:
        body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except json.JSONDecodeError:
        body = {}
    # Extract possible payment id from notification
    payment_id = None
    if isinstance(body, dict):
        # usual MP notification: {"type":"payment","data":{"id":<id>}}
        payment_id = body.get('data', {}).get('id') or body.get('id')
    payment_id = payment_id or request.query_params.get("data.id") or request.query_params.get("id")

    if not payment_id:
        return {'ok': False, 'reason': 'no id found'}
    payment_id = str(payment_id)
    _verify_mp_signature(request, payment_id)

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
            provider_payment = next((p for p in payments if p.get('status') == 'approved'), None) or {}
            provider_payment_id = provider_payment.get('id') or payment_id
            e = await EnrollmentService.mark_paid(
                enrollment_id,
                payment_method="mercadopago",
                payment_reference=str(provider_payment_id),
                payment_provider_id=str(provider_payment_id),
                payment_provider_status="approved",
            )
            if not e:
                raise HTTPException(status_code=404, detail='Enrollment not found')
            return {'ok': True, 'enrollment_id': e.id}
        except ValueError:
            return {'ok': False, 'reason': 'invalid external reference'}

    if ext:
        try:
            enrollment_id = int(ext)
            status = pay_resp.get('status') or mo_resp.get('status') or 'pending'
            await EnrollmentService.update_payment_attempt(
                enrollment_id,
                payment_method="mercadopago",
                payment_provider_id=str(payment_id),
                payment_provider_status=str(status),
                payment_reference=str(payment_id),
            )
        except ValueError:
            return {'ok': False, 'reason': 'invalid external reference'}

    return {'ok': True, 'approved': approved}
