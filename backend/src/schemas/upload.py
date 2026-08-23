"""Video upload schemas.

The wire shape of the two-step direct-to-S3 flow described in
``src.services.storage_service``.
"""

from pydantic import Field

from src.schemas.common import StrictModel


class UploadConfig(StrictModel):
    """What the builder needs to decide whether to show an uploader at all."""

    enabled: bool = Field(description="False when no S3 bucket is configured.")
    max_bytes: int
    accepted_content_types: list[str] = Field(default_factory=list)


class VideoUploadRequest(StrictModel):
    filename: str = Field(max_length=255, description="The browser's filename, for a readable key.")
    content_type: str = Field(max_length=100, description="Must be an accepted video type.")
    size_bytes: int = Field(gt=0, description="Declared size, checked against the limit.")


class VideoUploadTicket(StrictModel):
    """A presigned POST. ``fields`` go into the form body **before** the file."""

    key: str
    upload_url: str
    fields: dict[str, str] = Field(default_factory=dict)
    video_url: str = Field(description="Where the object will be readable once uploaded.")
    expires_in_seconds: int
    max_bytes: int


class VideoUploadComplete(StrictModel):
    key: str = Field(min_length=1, max_length=1024)


class VideoUploadResult(StrictModel):
    key: str
    video_url: str
    content_type: str | None = None
    size_bytes: int | None = None
