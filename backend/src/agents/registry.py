"""The agent registry.

Agents self-register with the ``@register`` decorator, so adding one means
writing its module and importing it in ``src/agents/__init__.py``. Nothing in
the controller, the service or the router changes.
"""

from __future__ import annotations

from src.agents.base import BaseAgent
from src.app.errors import ApiError

_REGISTRY: dict[str, type[BaseAgent]] = {}


def register[AgentT: type[BaseAgent]](agent: AgentT) -> AgentT:
    """Class decorator that adds an agent to the registry."""
    name = getattr(agent, "name", "")
    if not name:
        raise ValueError(f"{agent.__name__} must declare a `name`.")
    if name in _REGISTRY and _REGISTRY[name] is not agent:
        raise ValueError(f"Two agents both claim the name '{name}'.")
    _REGISTRY[name] = agent
    return agent


def get(name: str) -> type[BaseAgent]:
    """Look up one agent, or 404 with the names that do exist."""
    agent = _REGISTRY.get(name)
    if agent is None:
        known = ", ".join(sorted(_REGISTRY)) or "none"
        raise ApiError(404, "AGENT_NOT_FOUND", f"No agent named '{name}'. Available: {known}.")
    return agent


def all_agents() -> list[type[BaseAgent]]:
    """Every registered agent, ordered by name."""
    return [_REGISTRY[name] for name in sorted(_REGISTRY)]
