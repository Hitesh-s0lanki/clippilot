"""Video upload endpoints.

Three routes, all requiring a Clerk session. The bytes go from the browser to
S3 directly; these only mint the ticket and confirm the result - see
``src.services.storage_service`` for why.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from src.app.dependencies import CurrentUserDep, VideoStorageDep
from src.schemas.upload import (
    UploadConfig,
    VideoUploadComplete,
    VideoUploadRequest,
    VideoUploadResult,
    VideoUploadTicket,
)

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.get(
    "/config",
    response_model=UploadConfig,
    summary="Whether uploads are available, and their limits",
)
async def read_upload_config(storage: VideoStorageDep, user: CurrentUserDep) -> UploadConfig:
    """Lets the builder hide the uploader instead of failing on click."""
    return UploadConfig(
        enabled=storage.is_configured,
        max_bytes=storage.max_bytes,
        accepted_content_types=storage.allowed_content_types,
    )


@router.post(
    "/video",
    response_model=VideoUploadTicket,
    status_code=status.HTTP_201_CREATED,
    summary="Start a video upload",
)
async def create_video_upload(
    payload: VideoUploadRequest,
    storage: VideoStorageDep,
    user: CurrentUserDep,
) -> VideoUploadTicket:
    ticket = storage.create_upload_ticket(
        owner_id=user.id,
        filename=payload.filename,
        content_type=payload.content_type,
        size_bytes=payload.size_bytes,
    )
    return VideoUploadTicket(**vars(ticket))


@router.post(
    "/video/complete",
    response_model=VideoUploadResult,
    summary="Confirm a video upload landed in the bucket",
)
async def complete_video_upload(
    payload: VideoUploadComplete,
    storage: VideoStorageDep,
    user: CurrentUserDep,
) -> VideoUploadResult:
    stored = await storage.confirm_upload(owner_id=user.id, key=payload.key)
    return VideoUploadResult(**vars(stored))
