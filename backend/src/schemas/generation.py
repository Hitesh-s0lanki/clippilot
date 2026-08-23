"""AI video generation wire schemas.

The validation here is not ceremony. Each rule below prevents either a silently
wrong result or a charge for a video nobody wanted - see
docs/minimax-h3-model.md 4.2 for where each one comes from:

* a reference the model cannot fetch **still bills in full** if the request
  otherwise succeeds, so references are checked before submitting;
* reference roles and keyframe roles are mutually exclusive, and the vendor API
  **accepts both and silently drops one**;
* ``duration`` is always sent explicitly, because the playground defaults to 8
  seconds and the API to 5 - a 60% swing in the bill for a parameter left alone.
"""

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from src.schemas.common import StrictModel
from src.schemas.enums import (
    DEFAULT_CLIP_SECONDS,
    MAX_CLIP_SECONDS,
    MAX_REFERENCE_AUDIO,
    MAX_REFERENCE_BYTES,
    MAX_REFERENCE_CLIP_SECONDS,
    MAX_REFERENCE_FILES,
    MAX_REFERENCE_IMAGES,
    MAX_REFERENCE_TOTAL_SECONDS,
    MAX_REFERENCE_VIDEOS,
    MIN_CLIP_SECONDS,
    MIN_REFERENCE_CLIP_SECONDS,
    GenerationAssetKind,
    GenerationAssetRole,
    GenerationMode,
    GenerationProvider,
    GenerationStatus,
    VideoAspectRatio,
    VideoResolution,
)
from src.schemas.validators import clean_text

KEYFRAME_ROLES = frozenset({GenerationAssetRole.FIRST_FRAME, GenerationAssetRole.LAST_FRAME})

MAX_PER_KIND = {
    GenerationAssetKind.IMAGE: MAX_REFERENCE_IMAGES,
    GenerationAssetKind.VIDEO: MAX_REFERENCE_VIDEOS,
    GenerationAssetKind.AUDIO: MAX_REFERENCE_AUDIO,
}


class GenerationAssetInput(StrictModel):
    """One reference file, already uploaded to object storage."""

    kind: GenerationAssetKind
    role: GenerationAssetRole = GenerationAssetRole.REFERENCE
    storage_key: str = Field(..., min_length=1, max_length=1024)
    content_type: str = Field(..., max_length=100)
    size_bytes: int = Field(..., ge=1)
    duration_seconds: int | None = Field(
        None,
        ge=MIN_REFERENCE_CLIP_SECONDS,
        le=MAX_REFERENCE_CLIP_SECONDS,
        description="Required for video and audio; the model bounds clips to 2-15s.",
    )
    subject_note: str | None = Field(
        None,
        max_length=200,
        description=(
            "What must not change about this reference, in the user's own words. "
            "Becomes the prompt's retention_analysis."
        ),
    )

    @field_validator("subject_note")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)

    @model_validator(mode="after")
    def _check_kind_rules(self) -> "GenerationAssetInput":
        ceiling = MAX_REFERENCE_BYTES[self.kind]
        if self.size_bytes > ceiling:
            noun = self.kind.value.lower()
            article = "An" if noun[0] in "aeiou" else "A"
            raise ValueError(
                f"{article} {noun} reference may be at most {ceiling // (1024 * 1024)} MB."
            )

        timed = self.kind in {GenerationAssetKind.VIDEO, GenerationAssetKind.AUDIO}
        if timed and self.duration_seconds is None:
            raise ValueError(f"duration_seconds is required for a {self.kind.value} reference.")

        # Only an image can be a literal frame.
        if self.role in KEYFRAME_ROLES and self.kind is not GenerationAssetKind.IMAGE:
            raise ValueError("Only an image reference can be a first or last frame.")

        return self


class GenerationCreate(StrictModel):
    """Submit one generation."""

    campaign_id: str | None = Field(None, max_length=36)
    ad_id: str | None = Field(None, max_length=36, description="Optional at submit; set on attach.")

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=7000,
        description="What the ad should do, in the user's own words.",
    )
    duration_seconds: int = Field(
        DEFAULT_CLIP_SECONDS,
        ge=MIN_CLIP_SECONDS,
        le=MAX_CLIP_SECONDS,
        description="Always sent explicitly - provider defaults differ by surface.",
    )
    aspect_ratio: VideoAspectRatio = VideoAspectRatio.NINE_SIXTEEN
    resolution: VideoResolution = VideoResolution.P768
    seed: int | None = Field(None, ge=0, description="Null means random.")
    with_audio: bool = True

    assets: list[GenerationAssetInput] = Field(default_factory=list, max_length=MAX_REFERENCE_FILES)

    @field_validator("prompt")
    @classmethod
    def _clean_prompt(cls, value: str) -> str:
        cleaned = clean_text(value)
        if not cleaned:
            raise ValueError("A prompt is required.")
        return cleaned

    @model_validator(mode="after")
    def _check_reference_envelope(self) -> "GenerationCreate":
        by_kind: dict[GenerationAssetKind, list[GenerationAssetInput]] = {}
        for asset in self.assets:
            by_kind.setdefault(asset.kind, []).append(asset)

        for kind, assets in by_kind.items():
            if len(assets) > MAX_PER_KIND[kind]:
                raise ValueError(
                    f"At most {MAX_PER_KIND[kind]} {kind.value.lower()} references are allowed."
                )
            # 15 seconds total per kind, not just per clip.
            total = sum(a.duration_seconds or 0 for a in assets)
            if total > MAX_REFERENCE_TOTAL_SECONDS:
                raise ValueError(
                    f"{kind.value.title()} references total {total}s; the limit is "
                    f"{MAX_REFERENCE_TOTAL_SECONDS}s."
                )

        # Audio cannot travel alone: it must accompany an image or a video.
        if by_kind.get(GenerationAssetKind.AUDIO) and not (
            by_kind.get(GenerationAssetKind.IMAGE) or by_kind.get(GenerationAssetKind.VIDEO)
        ):
            raise ValueError(
                "An audio reference must accompany at least one image or video reference."
            )

        # Reference mode and keyframe mode are mutually exclusive. The vendor
        # API accepts both and silently drops one, so it is rejected here.
        roles = {a.role for a in self.assets}
        if roles & KEYFRAME_ROLES and GenerationAssetRole.REFERENCE in roles:
            raise ValueError(
                "First/last-frame and reference inputs cannot be combined in one generation."
            )
        if sum(1 for a in self.assets if a.role is GenerationAssetRole.FIRST_FRAME) > 1:
            raise ValueError("Only one first frame is allowed.")
        if sum(1 for a in self.assets if a.role is GenerationAssetRole.LAST_FRAME) > 1:
            raise ValueError("Only one last frame is allowed.")

        return self

    @property
    def mode(self) -> GenerationMode:
        """Derived, never user-supplied: the references decide the mode."""
        if not self.assets:
            return GenerationMode.T2VA
        if {a.role for a in self.assets} & KEYFRAME_ROLES:
            return GenerationMode.FL2VA
        return GenerationMode.REF2VA


class GenerationAssetRead(StrictModel):
    id: str
    position: int
    kind: GenerationAssetKind
    role: GenerationAssetRole
    label: str
    subject_note: str | None = None
    url: str | None = Field(None, description="Public or signed URL for the thumbnail.")
    content_type: str
    size_bytes: int
    duration_seconds: int | None = None


class GenerationRead(StrictModel):
    id: str
    campaign_id: str | None = None
    ad_id: str | None = None

    status: GenerationStatus
    mode: GenerationMode
    provider: GenerationProvider

    user_prompt: str
    duration_seconds: int
    aspect_ratio: VideoAspectRatio
    resolution: VideoResolution
    seed: int | None = None
    with_audio: bool

    output_video_url: str | None = None
    output_poster_url: str | None = None
    output_duration_seconds: int | None = None

    cost_minor: int | None = None
    currency: str | None = None

    error_code: str | None = None
    error_message: str | None = None

    assets: list[GenerationAssetRead] = Field(default_factory=list)

    created_at: datetime
    queued_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @property
    def is_terminal(self) -> bool:
        from src.schemas.enums import TERMINAL_GENERATION_STATUSES

        return self.status in TERMINAL_GENERATION_STATUSES


class GenerationConfig(StrictModel):
    """What the builder needs to render the form without hardcoding limits.

    Mirrors ``/uploads/config``: when generation is unavailable the builder
    hides the feature rather than failing on click.
    """

    enabled: bool
    provider: GenerationProvider | None = None
    resolutions: list[VideoResolution] = Field(default_factory=list)
    aspect_ratios: list[VideoAspectRatio] = Field(default_factory=list)
    min_duration_seconds: int = MIN_CLIP_SECONDS
    max_duration_seconds: int = MAX_CLIP_SECONDS
    default_duration_seconds: int = DEFAULT_CLIP_SECONDS
    max_images: int = MAX_REFERENCE_IMAGES
    max_videos: int = MAX_REFERENCE_VIDEOS
    max_audio: int = MAX_REFERENCE_AUDIO
    max_files: int = MAX_REFERENCE_FILES
    max_bytes_by_kind: dict[GenerationAssetKind, int] = Field(
        default_factory=lambda: dict(MAX_REFERENCE_BYTES)
    )


class GenerationAttach(StrictModel):
    """Attach a finished generation to an ad.

    Separate from submission on purpose: generation is non-deterministic, so
    the user chooses which attempt becomes the campaign video. Auto-attaching
    every success would overwrite a good video with a worse one on each retry.
    """

    ad_id: str = Field(..., max_length=36)
