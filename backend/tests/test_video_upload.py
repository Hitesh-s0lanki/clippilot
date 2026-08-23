"""Video upload: presigned tickets, ownership and confirmation.

boto3 is never reached. ``VideoStorage`` is exercised directly with a stubbed
S3 client, so the suite runs with no AWS account, no network and no
credentials - while still covering the parts that matter: what goes into the
signed policy, how keys are built, and who is allowed to confirm one.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.app.dependencies import get_video_storage
from src.app.errors import ApiError
from src.core.config import Settings
from src.core.security import DEV_USER_HEADER
from src.services.storage_service import VideoStorage

OWNER = "user_test_owner"
INTRUDER = "user_someone_else"


class StubS3Client:
    """The two boto3 calls VideoStorage makes, recorded rather than performed."""

    def __init__(self, *, head: dict[str, Any] | None = None, error: Exception | None = None):
        self._head = head if head is not None else {"ContentType": "video/mp4", "ContentLength": 42}
        self._error = error
        self.presigned_calls: list[dict[str, Any]] = []
        self.head_calls: list[dict[str, Any]] = []

    def generate_presigned_post(self, **kwargs: Any) -> dict[str, Any]:
        self.presigned_calls.append(kwargs)
        return {
            "url": f"https://{kwargs['Bucket']}.s3.ap-south-1.amazonaws.com",
            "fields": {"key": kwargs["Key"], "policy": "stub", **kwargs["Fields"]},
        }

    def head_object(self, **kwargs: Any) -> dict[str, Any]:
        self.head_calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return self._head


def s3_error(status: int) -> Exception:
    """A botocore-shaped failure, without importing botocore."""
    error = Exception("S3 said no")
    error.response = {"ResponseMetadata": {"HTTPStatusCode": status}}  # type: ignore[attr-defined]
    return error


def storage_settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "environment": "test",
        "s3_bucket": "clippilot-videos",
        "s3_region": "ap-south-1",
        "s3_key_prefix": "campaign-videos",
        "max_video_upload_bytes": 10 * 1024 * 1024,
    }
    return Settings(**{**base, **overrides})


@pytest.fixture
def storage() -> VideoStorage:
    instance = VideoStorage(storage_settings())
    instance._client = StubS3Client()
    return instance


@pytest.fixture
def upload_client(app: FastAPI, storage: VideoStorage) -> Iterator[TestClient]:
    """A client whose app has S3 configured, with the stub client behind it."""
    app.dependency_overrides[get_video_storage] = lambda: storage

    with TestClient(app) as client:
        client.headers[DEV_USER_HEADER] = OWNER
        yield client
    app.dependency_overrides.pop(get_video_storage, None)


class TestKeysAndUrls:
    def test_key_is_namespaced_and_unique(self, storage: VideoStorage) -> None:
        first = storage.build_key(owner_id=OWNER, filename="clip.mp4", content_type="video/mp4")
        second = storage.build_key(owner_id=OWNER, filename="clip.mp4", content_type="video/mp4")

        assert first != second, "two uploads of the same filename must not collide"
        assert first.startswith(f"campaign-videos/{storage.owner_segment(OWNER)}/")
        assert first.endswith(".mp4")

    def test_key_does_not_leak_the_user_id(self, storage: VideoStorage) -> None:
        key = storage.build_key(owner_id=OWNER, filename="clip.mp4", content_type="video/mp4")
        assert OWNER not in key

    def test_filename_cannot_escape_the_prefix(self, storage: VideoStorage) -> None:
        key = storage.build_key(
            owner_id=OWNER,
            filename="../../../etc/passwd.mp4",
            content_type="video/mp4",
        )
        assert ".." not in key
        assert key.startswith("campaign-videos/")
        assert key.count("/") == 2

    def test_extension_comes_from_the_content_type(self, storage: VideoStorage) -> None:
        """A .mp4 name on a WebM body would produce a key the validator lies about."""
        key = storage.build_key(owner_id=OWNER, filename="clip.mp4", content_type="video/webm")
        assert key.endswith(".webm")

    def test_public_url_prefers_the_cdn(self) -> None:
        cdn = VideoStorage(storage_settings(s3_public_base_url="https://cdn.example.com/"))
        assert cdn.public_url("a/b.mp4") == "https://cdn.example.com/a/b.mp4"

    def test_public_url_falls_back_to_the_bucket(self, storage: VideoStorage) -> None:
        url = storage.public_url("a/b.mp4")
        assert url == "https://clippilot-videos.s3.ap-south-1.amazonaws.com/a/b.mp4"

    def test_public_url_passes_the_experience_validator(self, storage: VideoStorage) -> None:
        """The URL this produces has to survive the field it is saved into."""
        from src.schemas.validators import validate_video_url

        key = storage.build_key(owner_id=OWNER, filename="clip.mov", content_type="video/quicktime")
        assert validate_video_url(storage.public_url(key))


class TestTicket:
    def test_policy_pins_key_type_and_size(self, storage: VideoStorage) -> None:
        ticket = storage.create_upload_ticket(
            owner_id=OWNER, filename="clip.mp4", content_type="video/mp4", size_bytes=1_000
        )
        call = storage.client.presigned_calls[0]

        assert call["Bucket"] == "clippilot-videos"
        assert call["Key"] == ticket.key
        assert {"Content-Type": "video/mp4"} in call["Conditions"]
        assert ["content-length-range", 1, 10 * 1024 * 1024] in call["Conditions"]
        assert call["ExpiresIn"] == 900
        assert ticket.video_url.endswith(ticket.key)

    def test_no_acl_is_sent_by_default(self, storage: VideoStorage) -> None:
        """Modern buckets have ACLs disabled; sending one fails the PutObject."""
        ticket = storage.create_upload_ticket(
            owner_id=OWNER, filename="clip.mp4", content_type="video/mp4", size_bytes=1_000
        )
        assert "acl" not in ticket.fields
        assert "acl" not in storage.client.presigned_calls[0]["Fields"]

    def test_acl_is_sent_when_configured(self) -> None:
        legacy = VideoStorage(storage_settings(s3_object_acl="public-read"))
        legacy._client = StubS3Client()

        ticket = legacy.create_upload_ticket(
            owner_id=OWNER, filename="clip.mp4", content_type="video/mp4", size_bytes=1_000
        )
        assert ticket.fields["acl"] == "public-read"
        assert {"acl": "public-read"} in legacy.client.presigned_calls[0]["Conditions"]

    def test_unsupported_type_is_refused(self, storage: VideoStorage) -> None:
        with pytest.raises(ApiError) as caught:
            storage.create_upload_ticket(
                owner_id=OWNER, filename="clip.avi", content_type="video/x-msvideo", size_bytes=10
            )
        assert caught.value.status_code == 415
        assert caught.value.code == "UNSUPPORTED_MEDIA_TYPE"

    def test_oversized_upload_is_refused(self, storage: VideoStorage) -> None:
        with pytest.raises(ApiError) as caught:
            storage.create_upload_ticket(
                owner_id=OWNER,
                filename="clip.mp4",
                content_type="video/mp4",
                size_bytes=20 * 1024 * 1024,
            )
        assert caught.value.status_code == 413
        assert caught.value.code == "UPLOAD_TOO_LARGE"

    def test_unconfigured_storage_reports_it(self) -> None:
        with pytest.raises(ApiError) as caught:
            VideoStorage(Settings(environment="test", s3_bucket="")).create_upload_ticket(
                owner_id=OWNER, filename="clip.mp4", content_type="video/mp4", size_bytes=10
            )
        assert caught.value.status_code == 503
        assert caught.value.code == "STORAGE_NOT_CONFIGURED"


class TestConfirm:
    async def test_confirmed_upload_returns_its_url(self, storage: VideoStorage) -> None:
        key = storage.build_key(owner_id=OWNER, filename="clip.mp4", content_type="video/mp4")
        stored = await storage.confirm_upload(owner_id=OWNER, key=key)

        assert stored.video_url == storage.public_url(key)
        assert stored.size_bytes == 42
        assert storage.client.head_calls == [{"Bucket": "clippilot-videos", "Key": key}]

    async def test_another_owners_key_is_not_found(self, storage: VideoStorage) -> None:
        """Ownership is checked before S3 is, so the object is never even probed."""
        key = storage.build_key(owner_id=INTRUDER, filename="clip.mp4", content_type="video/mp4")

        with pytest.raises(ApiError) as caught:
            await storage.confirm_upload(owner_id=OWNER, key=key)

        assert caught.value.status_code == 404
        assert storage.client.head_calls == []

    async def test_missing_object_is_not_found(self, storage: VideoStorage) -> None:
        storage._client = StubS3Client(error=s3_error(404))
        key = storage.build_key(owner_id=OWNER, filename="clip.mp4", content_type="video/mp4")

        with pytest.raises(ApiError) as caught:
            await storage.confirm_upload(owner_id=OWNER, key=key)

        assert caught.value.status_code == 404
        assert caught.value.code == "UPLOAD_NOT_FOUND"

    async def test_s3_outage_is_not_reported_as_missing(self, storage: VideoStorage) -> None:
        storage._client = StubS3Client(error=s3_error(500))
        key = storage.build_key(owner_id=OWNER, filename="clip.mp4", content_type="video/mp4")

        with pytest.raises(ApiError) as caught:
            await storage.confirm_upload(owner_id=OWNER, key=key)

        assert caught.value.status_code == 502
        assert caught.value.code == "STORAGE_UNAVAILABLE"


class TestEndpoints:
    def test_ticket_round_trip(self, upload_client: TestClient, api: str) -> None:
        response = upload_client.post(
            f"{api}/uploads/video",
            json={"filename": "clip.mp4", "content_type": "video/mp4", "size_bytes": 2_048},
        )
        assert response.status_code == 201

        ticket = response.json()
        assert ticket["fields"]["Content-Type"] == "video/mp4"
        assert ticket["video_url"].endswith(ticket["key"])

        confirmed = upload_client.post(f"{api}/uploads/video/complete", json={"key": ticket["key"]})
        assert confirmed.status_code == 200
        assert confirmed.json()["video_url"] == ticket["video_url"]

    def test_config_reports_the_limits(self, upload_client: TestClient, api: str) -> None:
        body = upload_client.get(f"{api}/uploads/config").json()

        assert body["enabled"] is True
        assert body["max_bytes"] == 10 * 1024 * 1024
        assert "video/mp4" in body["accepted_content_types"]

    def test_uploads_require_a_session(self, client: TestClient, api: str) -> None:
        response = client.post(
            f"{api}/uploads/video",
            json={"filename": "clip.mp4", "content_type": "video/mp4", "size_bytes": 10},
        )
        assert response.status_code == 401

    def test_config_is_disabled_without_a_bucket(self, owner_client: TestClient, api: str) -> None:
        """The default app has no bucket, so the builder is told not to offer one."""
        body = owner_client.get(f"{api}/uploads/config").json()
        assert body["enabled"] is False

    def test_oversized_upload_reports_413(self, upload_client: TestClient, api: str) -> None:
        response = upload_client.post(
            f"{api}/uploads/video",
            json={
                "filename": "clip.mp4",
                "content_type": "video/mp4",
                "size_bytes": 999 * 1024 * 1024,
            },
        )
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "UPLOAD_TOO_LARGE"
