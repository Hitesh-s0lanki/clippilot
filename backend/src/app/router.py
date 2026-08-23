"""Central router registry.

Every controller router is mounted here, and ``src.main`` includes only this
module. Adding a resource means writing its controller and appending one
``include_router`` call.
"""

from fastapi import APIRouter

from src.controllers import (
    ad_controller,
    agent_controller,
    audience_controller,
    campaign_controller,
    health_controller,
    public_controller,
    upload_controller,
)

# Operational endpoints live at the root so platform probes can reach them
# without knowing the versioned API prefix.
root_router = APIRouter()
root_router.include_router(health_controller.router)

# Versioned endpoints, mounted under settings.api_prefix in src.main.
api_router = APIRouter()
api_router.include_router(campaign_controller.router)  # Clerk session required
api_router.include_router(ad_controller.router)  # Clerk session required
api_router.include_router(audience_controller.router)  # Clerk session required
api_router.include_router(upload_controller.router)  # Clerk session required
api_router.include_router(agent_controller.router)  # Clerk session required
api_router.include_router(public_controller.router)  # viewer-facing, no session
