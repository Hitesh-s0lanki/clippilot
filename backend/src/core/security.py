"""Clerk-backed request identity.

Clerk owns sign-up, sign-in, sessions and the user record. This service never
issues, stores or validates credentials: it receives the session JWT that Clerk
minted for the frontend, verifies the signature against Clerk's published JWKS,
and reads the Clerk user id from the ``sub`` claim.

That id is the only thing persisted (``campaigns.owner_user_id``), so there is
no local user table to keep in sync.
"""

from dataclasses import dataclass

import jwt
from jwt import PyJWKClient
from starlette.concurrency import run_in_threadpool

from src.app.errors import ApiError
from src.core.config import Settings

DEV_USER_HEADER = "X-Dev-User-Id"


@dataclass(frozen=True, slots=True)
class CurrentUser:
    """The authenticated caller, as asserted by Clerk."""

    id: str
    email: str | None = None
    session_id: str | None = None


class ClerkVerifier:
    """Verifies Clerk session JWTs against the JWKS endpoint.

    The JWKS client caches signing keys in memory, so only the first request
    after a key rotation performs network I/O. That fetch is synchronous, so it
    is pushed to a worker thread rather than blocking the event loop.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._jwks_client: PyJWKClient | None = None

    def _client(self) -> PyJWKClient:
        if self._jwks_client is None:
            self._jwks_client = PyJWKClient(
                self._settings.clerk_jwks_url,
                cache_keys=True,
                lifespan=3600,
            )
        return self._jwks_client

    async def verify(self, token: str) -> CurrentUser:
        """Return the caller described by a valid Clerk session token."""
        try:
            signing_key = await run_in_threadpool(self._client().get_signing_key_from_jwt, token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self._settings.clerk_issuer or None,
                audience=self._settings.clerk_audience or None,
                options={
                    "verify_aud": bool(self._settings.clerk_audience),
                    "require": ["sub", "exp"],
                },
            )
        except jwt.ExpiredSignatureError as exc:
            raise ApiError(401, "SESSION_EXPIRED", "Your session has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise ApiError(401, "INVALID_TOKEN", "The session token is not valid.") from exc
        except Exception as exc:  # JWKS fetch failure, malformed key set, ...
            raise ApiError(
                503, "AUTH_UNAVAILABLE", "Could not verify the session right now."
            ) from exc

        subject = claims.get("sub")
        if not subject:
            raise ApiError(401, "INVALID_TOKEN", "The session token has no subject.")

        return CurrentUser(
            id=str(subject),
            email=claims.get("email"),
            session_id=claims.get("sid"),
        )


def extract_bearer_token(authorization: str | None) -> str | None:
    """Pull the token out of an ``Authorization: Bearer <token>`` header."""
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None

    return token.strip()
