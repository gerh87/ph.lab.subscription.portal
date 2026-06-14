from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, courses, subscribers, enrollments, payments
from app.api.v1 import users


def create_app() -> FastAPI:
    app = FastAPI(title="ph.lab.subscriptionportal API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(courses.router, prefix="/api/v1/courses", tags=["courses"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(subscribers.router, prefix="/api/v1/subscribers", tags=["subscribers"])
    app.include_router(enrollments.router, prefix="/api/v1/enrollments", tags=["enrollments"])
    app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])

    return app


app = create_app()
