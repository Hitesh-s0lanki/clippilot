"""MCP toolsets, and the allow-list that decides what an agent may call.

Firecrawl is reached over **MCP** rather than through its REST SDK. That costs
one adapter module and buys two things: adding another provider is a table
entry rather than a client wrapper, and the tools arrive already shaped as
LangChain tools, so ``BaseAgent`` never learns a vendor's request format.

**Not every tool a server offers should be handed to an agent.** Firecrawl
exposes crawling and monitoring alongside search and scrape; a campaign draft
has no business starting a site-wide crawl or registering a recurring monitor,
both of which spend credits and outlive the request. Each toolset therefore
declares the tools it exposes, and anything else the server advertises is
dropped before an agent ever sees it.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.core.config import Settings

if TYPE_CHECKING:  # pragma: no cover - import cost is paid only when tools run
    from langchain_core.tools import BaseTool

logger = logging.getLogger("clippilot.agents.toolkits")

FIRECRAWL = "firecrawl"

# Read-only research tools. `firecrawl_crawl`, `firecrawl_monitor` and friends
# are deliberately absent: see the module docstring.
FIRECRAWL_TOOLS = (
    "firecrawl_search",
    "firecrawl_scrape",
    "firecrawl_map",
    "firecrawl_extract",
)


@dataclass(frozen=True)
class Toolset:
    """One MCP server, and the subset of its tools agents may use."""

    name: str
    connection: dict[str, Any]
    allowed_tools: tuple[str, ...] = ()

    def permits(self, tool_name: str) -> bool:
        """An empty allow-list means "everything this server offers"."""
        return not self.allowed_tools or tool_name in self.allowed_tools


@dataclass
class ToolsetResult:
    """Tools that loaded, plus a note for each toolset that did not.

    A failed toolset is not an error. Research makes an agent's answer better,
    it does not make it possible - so a Firecrawl outage degrades the run and
    is reported in the response, rather than failing the request.
    """

    tools: list[BaseTool] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def degraded(self) -> bool:
        return bool(self.notes)


class AgentToolkit:
    """Builds LangChain tools from the MCP servers this deployment configures.

    One instance is shared per application. Tool objects are cached because
    discovering them costs an MCP handshake, and the adapter opens a fresh
    session per invocation anyway - so a cached tool is not a held connection.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._toolsets = self._build_toolsets(settings)
        self._cache: dict[str, list[BaseTool]] = {}

    @staticmethod
    def _build_toolsets(settings: Settings) -> dict[str, Toolset]:
        toolsets: dict[str, Toolset] = {}

        if settings.firecrawl_configured:
            toolsets[FIRECRAWL] = Toolset(
                name=FIRECRAWL,
                connection={
                    "transport": "streamable_http",
                    "url": settings.firecrawl_mcp_url,
                    # Firecrawl's own documentation is explicit that the key
                    # goes in the Authorization header and never in the URL.
                    "headers": {"Authorization": f"Bearer {settings.firecrawl_api_key}"},
                    "timeout": settings.firecrawl_mcp_timeout_seconds,
                    "sse_read_timeout": settings.firecrawl_mcp_timeout_seconds,
                },
                allowed_tools=FIRECRAWL_TOOLS,
            )

        return toolsets

    @property
    def configured(self) -> frozenset[str]:
        """Names of the toolsets this deployment can actually reach."""
        return frozenset(self._toolsets)

    def describes(self, names: Iterable[str]) -> list[str]:
        """The requested toolsets that are configured, in request order."""
        return [name for name in names if name in self._toolsets]

    async def load(self, names: Sequence[str]) -> ToolsetResult:
        """Load the tools for ``names``, skipping whatever cannot be reached."""
        result = ToolsetResult()

        for name in names:
            toolset = self._toolsets.get(name)
            if toolset is None:
                result.notes.append(
                    f"{name} is not configured on this server, so the agent worked "
                    f"from the brief alone."
                )
                continue

            try:
                result.tools.extend(await self._load_one(toolset))
            except Exception as exc:  # noqa: BLE001 - degrade, never fail the run
                logger.warning("toolset %s unavailable: %s", name, exc)
                result.notes.append(
                    f"{name} could not be reached ({type(exc).__name__}), so the agent "
                    f"worked from the brief alone."
                )

        return result

    async def _load_one(self, toolset: Toolset) -> list[BaseTool]:
        if toolset.name in self._cache:
            return self._cache[toolset.name]

        # Imported here so the module graph - and `src.main` - stays importable
        # in an environment that never runs an agent.
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient({toolset.name: toolset.connection})  # type: ignore[arg-type]
        discovered = await client.get_tools(server_name=toolset.name)

        tools = [tool for tool in discovered if toolset.permits(tool.name)]
        dropped = [tool.name for tool in discovered if not toolset.permits(tool.name)]
        if dropped:
            logger.debug("toolset %s: withheld %s", toolset.name, ", ".join(sorted(dropped)))

        self._cache[toolset.name] = tools
        return tools
