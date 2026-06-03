from fastapi import APIRouter, Depends
from typing import List
from app.schemas.subscriber import SubscriberCreate, SubscriberRead
from app.services.subscriber_service import SubscriberService
from app.core.admin_auth import require_admin, require_user

router = APIRouter()


@router.post("/", response_model=SubscriberRead)
async def create_subscriber(sub: SubscriberCreate, user=Depends(require_user)):
    return await SubscriberService.create(sub, user)


@router.get("/", response_model=List[SubscriberRead])
async def list_subscribers(_admin=Depends(require_admin)):
    return await SubscriberService.list_all()
