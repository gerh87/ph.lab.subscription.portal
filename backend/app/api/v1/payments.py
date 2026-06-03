from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.enrollment_service import EnrollmentService
from app.core.config import settings

try:
    import mercadopago
except Exception:
    mercadopago = None

router = APIRouter()


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
    title: str
    price: float
    quantity: int = 1


@router.post('/create_preference')
async def create_preference(req: PreferenceRequest):
    if mercadopago is None:
        raise HTTPException(status_code=500, detail='mercadopago SDK not installed')

    # ensure enrollment exists
    e = await EnrollmentService.get(req.enrollment_id)
    if not e:
        raise HTTPException(status_code=404, detail='Enrollment not found')

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN or '')

    notification_url = settings.MERCADOPAGO_NOTIFICATION_URL or f"{settings.APP_URL}/api/v1/payments/webhook"

    preference = {
        "items": [
            {"title": req.title, "quantity": req.quantity, "unit_price": req.price}
        ],
        "metadata": {"enrollment_id": req.enrollment_id},
        "external_reference": str(req.enrollment_id),
        "notification_url": notification_url,
        "back_urls": {"success": f"{settings.APP_URL}/payments/success", "failure": f"{settings.APP_URL}/payments/fail"},
        "auto_return": "approved",
    }

    res = sdk.preference().create(preference)
    return {"init_point": res["response"].get("init_point"), "id": res["response"].get("id")}


@router.post('/webhook/mp')
async def mercadopago_webhook(request):
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
