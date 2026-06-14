import asyncio

from app.services import enrollment_service
from app.services.enrollment_service import EnrollmentService


class FakeQuery:
    def __init__(self, first_value=None, count_value=0):
        self.first_value = first_value
        self.count_value = count_value

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.first_value

    def count(self):
        return self.count_value


class FakeDb:
    def __init__(self, course, active_count):
        self.course = course
        self.active_count = active_count

    def query(self, model):
        if model.__name__ == "Course":
            return FakeQuery(first_value=self.course)
        return FakeQuery(count_value=self.active_count)

    def close(self):
        pass


class FakeCourse:
    max_students = 1


class FakeEnrollment:
    id = 10
    course_id = 100
    status = "pending_payment"
    payment_method = "manual"
    payment_status = "pending"
    paid_at = None
    payment_reference = None
    manual_payment_notes = None
    payment_provider_id = None
    payment_provider_status = None


def test_mark_paid_refuses_to_activate_when_course_is_full(monkeypatch):
    enrollment = FakeEnrollment()
    updated = []

    monkeypatch.setattr(enrollment_service, "SessionLocal", lambda: FakeDb(FakeCourse(), active_count=1))
    monkeypatch.setattr(enrollment_service.EnrollmentRepository, "get_by_id", lambda db, id: enrollment)
    monkeypatch.setattr(enrollment_service.EnrollmentRepository, "update", lambda db, item: updated.append(item) or item)

    result = asyncio.run(EnrollmentService.mark_paid(enrollment.id))

    assert result == "full"
    assert enrollment.status == "pending_payment"
    assert updated == []


def test_mark_paid_activates_when_capacity_is_available(monkeypatch):
    enrollment = FakeEnrollment()

    monkeypatch.setattr(enrollment_service, "SessionLocal", lambda: FakeDb(FakeCourse(), active_count=0))
    monkeypatch.setattr(enrollment_service.EnrollmentRepository, "get_by_id", lambda db, id: enrollment)
    monkeypatch.setattr(enrollment_service.EnrollmentRepository, "update", lambda db, item: item)

    result = asyncio.run(EnrollmentService.mark_paid(enrollment.id, payment_reference="manual-1"))

    assert result is enrollment
    assert enrollment.status == "active"
    assert enrollment.payment_status == "paid"
    assert enrollment.payment_reference == "manual-1"
