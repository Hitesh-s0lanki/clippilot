"""Video object storage on AWS S3.

The browser uploads **straight to S3** using a presigned POST that this
service mints; the video bytes never pass through the API. That is the part
worth being deliberate about:

* a FastAPI worker streaming a 200 MB file would hold a connection (and, with
  ``UploadFile``, a spooled temp file) for the whole upload, so a handful of
  concurrent uploads is enough to stall the API;
* the size limit lives in the signed policy, which means **S3** rejects an
  oversized body. A client-side check is a courtesy; this is the enforcement.

Presigned POST is used rather than presigned PUT precisely because only POST
carries a ``content-length-range`` condition. PUT can be signed for a fixed
content type but not for a maximum size.

Two calls make up the flow:

    POST /uploads/video           -> ticket (url + form fields + final URL)
    (browser POSTs the file to S3 directly)
    POST /uploads/video/complete  -> HEAD confirms the object really landed
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from anyio import to_thread

from src.app.errors import ApiError
from src.core.config import Settings
from src.schemas.validators import ALLOWED_VIDEO_SUFFIXES

logger = logging.getLogger("clippilot.storage")

# Content type -> the extension the stored key gets. The key's suffix is what
# `validate_video_url` checks, so it is derived from the declared type rather
# than trusted from the filename the browser sent.
SUFFIX_BY_CONTENT_TYPE: dict[str, str] = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "video/x-quicktime": ".mov",
}

_UNSAFE_KEY_CHARS = re.compile(r"[^a-zA-Z0-9._-]+")


@dataclass(frozen=True)
class UploadTicket:
    """Everything the browser needs to send one file to S3."""

    key: str
    upload_url: str
    fields: dict[str, str] = field(default_factory=dict)
    video_url: str = ""
    expires_in_seconds: int = 0
    max_bytes: int = 0


@dataclass(frozen=True)
class StoredVideo:
    key: str
    video_url: str
    content_type: str | None = None
    size_bytes: int | None = None


class VideoStorage:
    """Presigned S3 uploads, scoped to the owner who asked for them."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Any | None = None

    # --- configuration -----------------------------------------------------

    @property
    def is_configured(self) -> bool:
        return self._settings.storage_configured

    @property
    def max_bytes(self) -> int:
        return self._settings.max_video_upload_bytes

    @property
    def allowed_content_types(self) -> list[str]:
        return self._settings.allowed_video_content_type_list

    def _require_configured(self) -> None:
        if not self.is_configured:
            raise ApiError(
                503,
                "STORAGE_NOT_CONFIGURED",
                "Video uploads are not available: no S3 bucket is configured. "
                "Paste a public video URL instead.",
            )

    def _build_client(self) -> Any:
        """Build the boto3 client on first use.

        Imported lazily so an API with no bucket configured never pays for
        botocore's import, and so the dependency stays optional in practice.
        """
        import boto3
        from botocore.config import Config

        settings = self._settings
        credentials: dict[str, str] = {}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            credentials = {
                "aws_access_key_id": settings.aws_access_key_id,
                "aws_secret_access_key": settings.aws_secret_access_key,
            }
            if settings.aws_session_token:
                credentials["aws_session_token"] = settings.aws_session_token

        return boto3.client(
            "s3",
            region_name=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url or None,
            config=Config(
                # SigV4 is required for presigned POST and for regions opened
                # after 2014; the default would break in ap-south-1.
                signature_version="s3v4",
                s3={"addressing_style": "virtual"},
                retries={"max_attempts": 3, "mode": "standard"},
            ),
            **credentials,
        )

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    # --- keys and URLs -----------------------------------------------------

    @staticmethod
    def owner_segment(owner_id: str) -> str:
        """A stable, non-reversible folder per owner.

        The Clerk user id is hashed rather than used directly: object keys end
        up in a public URL, and that URL should not carry an account id.
        """
        return hashlib.sha256(owner_id.encode("utf-8")).hexdigest()[:16]

    def build_key(self, *, owner_id: str, filename: str, content_type: str) -> str:
        """A collision-free key: ``prefix/owner-hash/uuid-slug.ext``.

        The uploader's filename is kept only as a readable tail, sanitised and
        truncated. Never used as the key on its own - two people uploading
        ``video.mp4`` must not overwrite one another, and a filename is
        attacker-controlled input to a path.
        """
        suffix = SUFFIX_BY_CONTENT_TYPE[content_type]

        stem = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        for allowed in ALLOWED_VIDEO_SUFFIXES:
            if stem.lower().endswith(allowed):
                stem = stem[: -len(allowed)]
                break
        slug = _UNSAFE_KEY_CHARS.sub("-", stem).strip("-.")[:48].strip("-.")

        name = f"{uuid4().hex}-{slug}{suffix}" if slug else f"{uuid4().hex}{suffix}"
        parts = [p for p in (self._settings.s3_prefix, self.owner_segment(owner_id), name) if p]
        return "/".join(parts)

    def public_url(self, key: str) -> str:
        """The URL saved on the experience and played by the recipient."""
        return f"{self._settings.s3_public_origin}/{key}"

    def owns_key(self, *, owner_id: str, key: str) -> bool:
        """Whether ``key`` sits in this owner's folder.

        Checked before confirming an upload: the key comes back from the
        client, so without this one signed-in user could point their campaign
        at another user's object.
        """
        prefix = "/".join(p for p in (self._settings.s3_prefix, self.owner_segment(owner_id)) if p)
        return key.startswith(f"{prefix}/") and ".." not in key

    # --- the flow ----------------------------------------------------------

    def create_upload_ticket(
        self, *, owner_id: str, filename: str, content_type: str, size_bytes: int
    ) -> UploadTicket:
        """Mint a short-lived, single-object presigned POST.

        The returned policy pins the exact key, the exact content type and a
        maximum body size, so the ticket cannot be replayed to write anything
        else into the bucket.
        """
        self._require_configured()

        declared = content_type.strip().lower()
        if declared not in self.allowed_content_types or declared not in SUFFIX_BY_CONTENT_TYPE:
            accepted = ", ".join(self.allowed_content_types)
            raise ApiError(
                415,
                "UNSUPPORTED_MEDIA_TYPE",
                f"{content_type or 'That file type'} cannot be uploaded. Accepted: {accepted}.",
            )

        if size_bytes > self.max_bytes:
            raise ApiError(
                413,
                "UPLOAD_TOO_LARGE",
                f"That video is larger than the {self.max_bytes // (1024 * 1024)} MB limit.",
            )

        settings = self._settings
        key = self.build_key(owner_id=owner_id, filename=filename, content_type=declared)

        fields: dict[str, str] = {"Content-Type": declared}
        conditions: list[Any] = [
            {"Content-Type": declared},
            ["content-length-range", 1, self.max_bytes],
        ]
        if settings.s3_object_acl:
            fields["acl"] = settings.s3_object_acl
            conditions.append({"acl": settings.s3_object_acl})

        try:
            presigned = self.client.generate_presigned_post(
                Bucket=settings.s3_bucket,
                Key=key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=settings.s3_upload_expires_seconds,
            )
        except Exception as exc:  # pragma: no cover - credential/config failure
            logger.exception("presigning the upload failed")
            raise ApiError(
                502,
                "STORAGE_UNAVAILABLE",
                "The upload could not be prepared. Try again in a moment.",
            ) from exc

        return UploadTicket(
            key=key,
            upload_url=presigned["url"],
            fields=presigned["fields"],
            video_url=self.public_url(key),
            expires_in_seconds=settings.s3_upload_expires_seconds,
            max_bytes=self.max_bytes,
        )

    async def confirm_upload(self, *, owner_id: str, key: str) -> StoredVideo:
        """Verify the object exists before its URL is saved on a campaign.

        S3 answers the browser directly, so without this step the API would be
        taking the client's word that the upload happened and would happily
        store a URL that 404s on the recipient's preview page.
        """
        self._require_configured()

        if not self.owns_key(owner_id=owner_id, key=key):
            # Reported as "not found" rather than "forbidden": a caller must
            # not be able to probe which keys exist in someone else's folder.
            raise ApiError(404, "UPLOAD_NOT_FOUND", "That upload could not be found.")

        try:
            head = await to_thread.run_sync(
                lambda: self.client.head_object(Bucket=self._settings.s3_bucket, Key=key)
            )
        except Exception as exc:
            status = getattr(exc, "response", {}).get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status in {403, 404}:
                raise ApiError(
                    404,
                    "UPLOAD_NOT_FOUND",
                    "That upload could not be found. It may have expired before it finished.",
                ) from exc
            logger.exception("HEAD on the uploaded object failed")
            raise ApiError(
                502,
                "STORAGE_UNAVAILABLE",
                "The upload could not be confirmed. Try again in a moment.",
            ) from exc

        return StoredVideo(
            key=key,
            video_url=self.public_url(key),
            content_type=head.get("ContentType"),
            size_bytes=head.get("ContentLength"),
        )
