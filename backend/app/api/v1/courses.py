from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from typing import List
from urllib.parse import quote
from botocore.exceptions import ClientError

from app.schemas.course import CourseAdminRead, CourseCreate, CourseRead, CourseUpdate
from app.schemas.course_file import CourseFileRead
from app.services.course_file_service import CourseFileService
from app.services.course_service import CourseService
from app.core.admin_auth import require_admin, require_user

router = APIRouter()


@router.post("/", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(course: CourseCreate, _admin=Depends(require_admin)):
    return await CourseService.create(course)


@router.get("/", response_model=List[CourseRead])
async def list_courses():
    return await CourseService.list_all()


@router.get("/admin", response_model=List[CourseAdminRead])
async def list_admin_courses(_admin=Depends(require_admin)):
    return await CourseService.list_all_admin()


@router.post("/{course_id}/files", response_model=CourseFileRead, status_code=status.HTTP_201_CREATED)
async def upload_course_file(
    course_id: int,
    file: UploadFile = File(...),
    resource_type: str = Form("public_resource"),
    admin=Depends(require_admin),
):
    created = await CourseFileService.upload(course_id, file, admin, resource_type)
    if not created:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if created == "invalid_resource_type":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course file type")
    return created


@router.get("/{course_id}/resources", response_model=List[CourseFileRead])
async def list_course_public_resources(course_id: int):
    files = await CourseFileService.list_public_resources(course_id)
    if files is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return files


@router.get("/{course_id}/resources/{file_id}/download")
async def download_course_public_resource(course_id: int, file_id: int):
    try:
        result = await CourseFileService.get_public_resource_download(course_id, file_id)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in {"NoSuchKey", "404"}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found")
        raise

    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course resource not found")

    course_file = result["file"]
    s3_object = result["object"]
    filename = quote(course_file.original_filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
    }
    if course_file.size_bytes is not None:
        headers["Content-Length"] = str(course_file.size_bytes)

    return StreamingResponse(
        s3_object["Body"].iter_chunks(),
        media_type=course_file.content_type or "application/octet-stream",
        headers=headers,
    )


@router.get("/{course_id}/files", response_model=List[CourseFileRead])
async def list_course_files(course_id: int, user=Depends(require_user)):
    files = await CourseFileService.list_for_course(course_id, user)
    if files == "forbidden":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Course file access denied")
    if files is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return files


@router.get("/{course_id}/files/{file_id}/download")
async def download_course_file(course_id: int, file_id: int, user=Depends(require_user)):
    try:
        result = await CourseFileService.get_download(course_id, file_id, user)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in {"NoSuchKey", "404"}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found")
        raise

    if result == "forbidden":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Course file access denied")
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course file not found")

    course_file = result["file"]
    s3_object = result["object"]
    filename = quote(course_file.original_filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
    }
    if course_file.size_bytes is not None:
        headers["Content-Length"] = str(course_file.size_bytes)

    return StreamingResponse(
        s3_object["Body"].iter_chunks(),
        media_type=course_file.content_type or "application/octet-stream",
        headers=headers,
    )


@router.delete("/{course_id}/files/{file_id}")
async def delete_course_file(course_id: int, file_id: int, _admin=Depends(require_admin)):
    ok = await CourseFileService.delete(course_id, file_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course file not found")
    return {"deleted": True}


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(course_id: int):
    course = await CourseService.get(course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.put("/{course_id}", response_model=CourseRead)
async def update_course(course_id: int, changes: CourseUpdate, _admin=Depends(require_admin)):
    updated = await CourseService.update(course_id, {k: v for k, v in changes.model_dump().items() if v is not None})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return updated


@router.delete("/{course_id}")
async def delete_course(course_id: int, _admin=Depends(require_admin)):
    ok = await CourseService.delete(course_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return {"deleted": True}
