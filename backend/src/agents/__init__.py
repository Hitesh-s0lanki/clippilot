"""LangChain agents.

``BaseAgent`` owns the loop; a concrete agent is a name, a Markdown prompt, an
input schema, an output schema and two small hooks. Importing the concrete
modules here is what puts them in the registry, so a new agent needs one line
added below and nothing else touched outside its own files.
"""

from src.agents.base import AgentContext, AgentRun, AgentUsage, BaseAgent, ToolCallRecord
from src.agents.campaign_strategist import CampaignStrategistAgent
from src.agents.prompts import PromptLibrary
from src.agents.registry import all_agents, get, register
from src.agents.toolkits import FIRECRAWL, AgentToolkit

__all__ = [
    "FIRECRAWL",
    "AgentContext",
    "AgentRun",
    "AgentToolkit",
    "AgentUsage",
    "BaseAgent",
    "CampaignStrategistAgent",
    "PromptLibrary",
    "ToolCallRecord",
    "all_agents",
    "get",
    "register",
]
