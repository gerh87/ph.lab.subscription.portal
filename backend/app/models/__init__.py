from sqlalchemy.orm import declarative_base

Base = declarative_base()

# import models to ensure they are visible to Alembic autogenerate
from app.models import user, course, subscriber, enrollment, course_file  # noqa: F401
