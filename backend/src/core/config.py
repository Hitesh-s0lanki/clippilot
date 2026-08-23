"""Application configuration, loaded from the environment."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# The model each provider uses when AGENT_MODEL is left blank.
DEFAULT_AGENT_MODELS: dict[str, str] = {
    "anthropic": "claude-opus-5",
    "openai": "gpt-5.1",
}


class Settings(BaseSettings):
    """Environment-backed settings.

    Values are read from the process environment, falling back to a local
    ``.env`` file during development. See ``.env.example`` for the full list.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = "ClipPilot API"
    version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False

    api_prefix: str = "/api/v1"

    # Comma-separated list of allowed browser origins for the frontend.
    cors_origins: str = "http://localhost:5173,http://localhost:3002"

    # PostgreSQL is the deployment target. The default points at a local
    # instance; set DATABASE_URL to override. SQLite remains supported for
    # quick local runs and is what the test suite uses by default, but the
    # suite also runs against Postgres via TEST_DATABASE_URL.
    database_url: str = "postgresql+asyncpg://trustvid:trustvid@localhost:5432/trustvid"
    database_echo: bool = False

    # --- Clerk -------------------------------------------------------------
    # Clerk owns sign-up, sign-in and session lifetime. This service never
    # issues or stores credentials; it only verifies the session JWT that the
    # frontend sends and reads the Clerk user id from it.
    clerk_jwks_url: str = ""
    clerk_issuer: str = ""
    clerk_audience: str = ""

    # Development escape hatch: accept X-Dev-User-Id instead of a real Clerk
    # token so the API is usable before Clerk keys exist. Refused in production
    # by Settings.validate_runtime().
    allow_dev_auth_header: bool = True

    # Give an account with no audiences the three sample lists on its first
    # visit, so a new sign-in lands on a populated segment breakdown rather
    # than an empty screen. Demo behaviour - turn it off for a real tenant that
    # should start clean.
    sample_audiences: bool = True

    # Salt for hashing event IP addresses. Raw IPs are never stored.
    ip_hash_salt: str = "dev-only-change-me"

    # --- Video storage (AWS S3) --------------------------------------------
    # An experience needs a publicly playable video URL. A pasted CDN link is
    # still accepted; these settings add the other half - uploading the file
    # itself. Leaving S3_BUCKET empty simply disables the upload endpoints,
    # so the API runs without any AWS account at all.
    s3_bucket: str = ""
    s3_region: str = "ap-south-1"

    # Credentials are optional on purpose. When they are blank boto3 falls
    # back to its own chain - shared config, EC2/ECS/EKS instance roles - which
    # is how this should be deployed. Field names match the standard AWS
    # variables, so AWS_ACCESS_KEY_ID and friends are picked up as they are.
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""

    # S3-compatible endpoint for local work (MinIO, LocalStack). Empty = AWS.
    s3_endpoint_url: str = ""

    # Key prefix every uploaded object lives under, inside the bucket.
    s3_key_prefix: str = "campaign-videos"

    # CloudFront (or any CDN) origin serving the bucket. Empty falls back to
    # the bucket's own virtual-hosted URL, which requires the bucket policy in
    # backend/README.md to allow public reads.
    s3_public_base_url: str = ""

    # ACL applied to uploaded objects. Empty is correct for buckets created
    # since April 2023: they have Object Ownership set to "bucket owner
    # enforced", where sending any ACL fails with AccessControlListNotSupported.
    # Set to "public-read" only for an older bucket that still has ACLs on.
    s3_object_acl: str = ""

    # How long a presigned upload ticket stays valid.
    s3_upload_expires_seconds: int = 900

    # Hard ceiling, enforced by S3 itself through the presigned policy - not
    # merely checked here, so a tampered client cannot exceed it.
    max_video_upload_bytes: int = 200 * 1024 * 1024

    # Content types the uploader accepts, aligned with ALLOWED_VIDEO_SUFFIXES.
    allowed_video_content_types: str = "video/mp4,video/webm,video/quicktime"

    # --- AI agents ----------------------------------------------------------
    # The campaign builder asks for a lot of fields. An agent drafts them from
    # a sentence of intent plus the business's own website, so the user edits a
    # filled form instead of facing an empty one. Leaving ANTHROPIC_API_KEY
    # blank disables every agent endpoint - the rest of the API is unaffected,
    # the same way a blank S3_BUCKET disables uploads.
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Which provider runs the agents. "auto" picks whichever key is present,
    # preferring Anthropic when both are - the prompts were written and tuned
    # against Claude. Naming one explicitly is how you override that.
    agent_provider: Literal["auto", "anthropic", "openai"] = "auto"

    # Blank means "the provider's default" - see DEFAULT_AGENT_MODELS. Set it
    # to pin a specific model, and remember it is provider-specific: a Claude
    # id with AGENT_PROVIDER=openai is a 404 from OpenAI, not a fallback.
    agent_model: str = ""

    # Depth of reasoning. Both providers take the same first three levels;
    # `xhigh` and `max` are Anthropic-only and are clamped for OpenAI rather
    # than sent and rejected.
    agent_effort: Literal["low", "medium", "high", "xhigh", "max"] = "high"

    # Thinking tokens are drawn from the same allowance as the answer, so this
    # ceiling covers both the reasoning and the structured result.
    agent_max_tokens: int = 16_000

    # How many model turns one run may take. Each turn is either a research
    # tool call or the final result, so this bounds cost and latency.
    agent_max_steps: int = 12

    # Wall-clock ceiling for a whole run, research included.
    agent_timeout_seconds: float = 240.0

    # Ceiling for a single tool call. One page that never responds must cost
    # this much and not the whole run - without it a slow site holds the loop
    # until the global timeout and every lookup already done is lost.
    agent_tool_timeout_seconds: float = 45.0

    # --- Firecrawl (MCP) ----------------------------------------------------
    # Firecrawl is reached over MCP rather than its REST SDK, so any other MCP
    # server can be added to AgentToolkit without touching an agent. A blank
    # key does not disable the agents: they fall back to reasoning from the
    # user's own brief and say so in the response.
    firecrawl_api_key: str = ""
    firecrawl_mcp_url: str = "https://mcp.firecrawl.dev/v2/mcp"
    firecrawl_mcp_timeout_seconds: float = 90.0

    @property
    def cors_origin_list(self) -> list[str]:
        """Split the configured origins into the list CORSMiddleware expects."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def clerk_configured(self) -> bool:
        return bool(self.clerk_jwks_url and self.clerk_issuer)

    @property
    def storage_configured(self) -> bool:
        """Uploads are enabled only once a bucket is named."""
        return bool(self.s3_bucket)

    @property
    def allowed_video_content_type_list(self) -> list[str]:
        return [
            item.strip().lower()
            for item in self.allowed_video_content_types.split(",")
            if item.strip()
        ]

    @property
    def agents_configured(self) -> bool:
        """Agent endpoints are live only once some model key is present."""
        return self.agent_provider_resolved is not None

    @property
    def agent_provider_resolved(self) -> str | None:
        """The provider that will actually run, or None if none can.

        An explicit choice is honoured only when its key exists; naming a
        provider you have no key for is a misconfiguration, not a request to
        silently use the other one and bill you somewhere you did not expect.
        """
        if self.agent_provider == "anthropic":
            return "anthropic" if self.anthropic_api_key else None
        if self.agent_provider == "openai":
            return "openai" if self.openai_api_key else None

        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        return None

    @property
    def agent_model_resolved(self) -> str:
        """The model id to use, falling back to the provider's default."""
        if self.agent_model:
            return self.agent_model
        provider = self.agent_provider_resolved
        return DEFAULT_AGENT_MODELS.get(provider or "", "")

    @property
    def firecrawl_configured(self) -> bool:
        """Web research is available only once Firecrawl can be reached."""
        return bool(self.firecrawl_api_key and self.firecrawl_mcp_url)

    @property
    def s3_prefix(self) -> str:
        """The key prefix, without leading or trailing slashes."""
        return self.s3_key_prefix.strip("/")

    @property
    def s3_public_origin(self) -> str:
        """Origin that serves uploaded objects to a browser, no trailing slash.

        A CDN in front of the bucket is the deployment shape this is written
        for; the virtual-hosted bucket URL is the fallback so a bucket with a
        public-read policy works with no extra configuration.
        """
        if self.s3_public_base_url:
            return self.s3_public_base_url.rstrip("/")
        return f"https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com"

    def validate_runtime(self) -> list[str]:
        """Return configuration problems that must not reach production.

        Called at startup. Returning a list rather than raising lets the caller
        decide between a hard failure and a logged warning.
        """
        problems: list[str] = []

        if not self.is_production:
            return problems

        if self.debug:
            problems.append(
                "DEBUG must be false in production: Starlette renders tracebacks "
                "to the client when it is on."
            )
        if self.allow_dev_auth_header:
            problems.append(
                "ALLOW_DEV_AUTH_HEADER must be false in production: it lets any "
                "caller assert an identity via X-Dev-User-Id."
            )
        if not self.clerk_configured:
            problems.append("CLERK_JWKS_URL and CLERK_ISSUER are required in production.")
        if self.ip_hash_salt == "dev-only-change-me":
            problems.append("IP_HASH_SALT must be set to a secret value in production.")
        if self.s3_public_base_url and not self.s3_public_base_url.startswith("https://"):
            problems.append(
                "S3_PUBLIC_BASE_URL must use https: the experience validator "
                "rejects any video URL that does not."
            )

        return problems


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so the environment is parsed once per process; tests can clear the
    cache via ``get_settings.cache_clear()``.
    """
    return Settings()
