from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from app.schemas.enrollment import EnrollmentCreate, EnrollmentRead
from app.services.enrollment_service import EnrollmentService
from app.core.database import SessionLocal
from app.core.admin_auth import require_admin, require_user
from app.models.enrollment import Enrollment
from app.repositories.subscriber_repository import SubscriberRepository

router = APIRouter()


class VirtualAccessRead(BaseModel):
    zoom_url: str


@router.post("/", response_model=EnrollmentRead)
async def enroll(enrollment: EnrollmentCreate, user=Depends(require_user)):
    created = await EnrollmentService.create(enrollment, user)
    if created == "full":
        raise HTTPException(status_code=400, detail="Course is full")
    if not created:
        raise HTTPException(status_code=400, detail="Subscriber profile is required")
    return created


@router.get("/", response_model=List[EnrollmentRead])
async def list_enrollments(_admin=Depends(require_admin)):
    return await EnrollmentService.list_all()


@router.get("/subscriber/{subscriber_id}", response_model=List[EnrollmentRead])
async def enrollments_by_subscriber(subscriber_id: int, user=Depends(require_user)):
    if not user.is_admin:
        db = SessionLocal()
        try:
            subscriber = SubscriberRepository.get_by_id(db, subscriber_id)
            if not subscriber or subscriber.user_id != user.id:
                raise HTTPException(status_code=403, detail="Subscriber access denied")
        finally:
            db.close()
    return await EnrollmentService.list_by_subscriber(subscriber_id)


@router.get("/course/{course_id}", response_model=List[EnrollmentRead])
async def enrollments_by_course(course_id: int, _admin=Depends(require_admin)):
    return await EnrollmentService.list_by_course(course_id)


@router.get("/{id}", response_model=EnrollmentRead)
async def get_enrollment(id: int, _admin=Depends(require_admin)):
    e = await EnrollmentService.get(id)
    if not e:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return e


@router.get("/{id}/virtual-access", response_model=VirtualAccessRead)
async def get_virtual_access(id: int, user=Depends(require_user)):
    db = SessionLocal()
    try:
        enrollment = db.query(Enrollment).filter(Enrollment.id == id).first()
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        subscriber = SubscriberRepository.get_by_id(db, enrollment.subscriber_id)
        if not user.is_admin and (not subscriber or subscriber.user_id != user.id):
            raise HTTPException(status_code=403, detail="Enrollment access denied")
        if enrollment.status != "active":
            raise HTTPException(status_code=403, detail="Subscription is not active")
        if not enrollment.course or enrollment.course.scheduled_date != date.today():
            raise HTTPException(status_code=403, detail="Virtual access is available only on the course date")
        if not enrollment.course.zoom_url:
            raise HTTPException(status_code=404, detail="Zoom link is not configured yet")
        return {"zoom_url": enrollment.course.zoom_url}
    finally:
        db.close()


@router.post("/{id}/cancel", response_model=EnrollmentRead)
async def cancel_enrollment(id: int, user=Depends(require_user)):
    e = await EnrollmentService.cancel_for_user(id, user)
    if e == "forbidden":
        raise HTTPException(status_code=403, detail="Enrollment access denied")
    if not e:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return e


@router.post("/{id}/pay", response_model=EnrollmentRead)
async def mark_enrollment_paid(id: int, _admin=Depends(require_admin)):
    e = await EnrollmentService.mark_paid(id)
    if not e:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return e
