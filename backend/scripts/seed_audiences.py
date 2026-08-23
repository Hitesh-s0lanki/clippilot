"""Seed the sample audiences - 100 people in three lists - for one account.

Rarely needed by hand: an account with no audiences is given these lists
automatically on its first visit, which is what makes them show up for whoever
signs in. This script exists for the cases that bypasses - preparing a demo
database ahead of time, or topping an account back up after it deleted them.

    uv run python -m scripts.seed_audiences --owner user_2abc...

Idempotent: a list whose name the account already has is left exactly as it is,
so running this twice does not double anybody.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from src.core.config import get_settings
from src.core.database import build_engine, build_session_factory
from src.repositories.audience_repository import AudienceRepository
from src.services.audience_service import AudienceService
from src.services.sample_audience import SAMPLE_SEGMENTS, SAMPLE_TOTAL


async def seed(owner_user_id: str) -> int:
    """Run the same provisioner the API runs, against a one-off session."""
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)

    try:
        async with session_factory() as session:
            service = AudienceService(AudienceRepository(session))
            return await service.provision_samples(owner_user_id)
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--owner",
        default="user_dev",
        help="Clerk user id to own the audiences. Match the X-Dev-User-Id you "
        "develop with, or the real Clerk id from a signed-in session.",
    )
    args = parser.parse_args()

    for segment in SAMPLE_SEGMENTS:
        print(f"  {segment.name} ({segment.size} people)")

    added = asyncio.run(seed(args.owner))

    if added == 0:
        print(f"{args.owner} already has these lists. Nothing to do.")
    else:
        print(f"Added {added} of {SAMPLE_TOTAL} people for {args.owner}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
