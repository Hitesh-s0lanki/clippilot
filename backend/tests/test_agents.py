"""Tests for the agent framework.

Nothing here touches the network. The loop is driven by a scripted stand-in for
the chat model, which is why ``BaseAgent`` takes ``chat_model`` as a
constructor argument: the tool-calling loop is the part worth testing, and it
is only testable if the model can be replaced.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from src.agents import registry
from src.agents.base import MAX_TOOL_RESULT_CHARS, BaseAgent
from src.agents.campaign_strategist import CampaignStrategistAgent
from src.agents.prompts import PromptLibrary, PromptNotFoundError
from src.agents.toolkits import FIRECRAWL, AgentToolkit, ToolsetResult
from src.app.dependencies import get_agent_service
from src.app.errors import ApiError
from src.core.config import Settings
from src.core.security import DEV_USER_HEADER
from src.schemas.enums import CallToAction, CampaignObjective
from src.schemas.strategy import CampaignBrief, CampaignDraft, CampaignStrategy
from src.services.agent_service import AgentService
from tests.conftest import OWNER

# --- doubles ---------------------------------------------------------------


class ScriptedModel:
    """Replays a fixed list of replies in place of ChatAnthropic."""

    model = "scripted-model"

    def __init__(self, *replies: AIMessage) -> None:
        self._replies = list(replies)
        self.turns: list[list[BaseMessage]] = []
        self.bound_tools: list[Any] = []

    def bind_tools(self, tools: list[Any]) -> ScriptedModel:
        self.bound_tools = tools
        return self

    async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
        self.turns.append(list(messages))
        if not self._replies:
            # Keep replying so step-limit tests terminate on the limit itself.
            return AIMessage(content="still thinking")
        return self._replies.pop(0)


class StubToolkit(AgentToolkit):
    """An AgentToolkit that yields fixed tools without an MCP handshake."""

    def __init__(self, tools: list[BaseTool] | None = None, notes: list[str] | None = None) -> None:
        self._tools = tools or []
        self._notes = notes or []
        self._toolsets = {}
        self._cache = {}

    @property
    def configured(self) -> frozenset[str]:
        return frozenset({FIRECRAWL}) if self._tools else frozenset()

    async def load(self, names) -> ToolsetResult:  # noqa: ANN001 - matches the base signature
        return ToolsetResult(tools=list(self._tools), notes=list(self._notes))


class ProbeInput(BaseModel):
    question: str


class ProbeResult(BaseModel):
    """Submit the answer."""

    answer: str = Field(..., min_length=1)


class ProbeAgent(BaseAgent[ProbeInput, ProbeResult]):
    """Minimal agent, used to exercise the loop in isolation."""

    name: ClassVar[str] = "probe"
    title: ClassVar[str] = "probe agent"
    description: ClassVar[str] = "Test double."
    prompt_file: ClassVar[str] = "probe"
    input_model: ClassVar[type[ProbeInput]] = ProbeInput
    output_model: ClassVar[type[ProbeResult]] = ProbeResult
    toolsets: ClassVar[tuple[str, ...]] = (FIRECRAWL,)

    def opening_message(self, payload: ProbeInput) -> str:
        return payload.question


def _call(name: str, args: dict[str, Any], call_id: str = "call-1") -> dict[str, Any]:
    return {"name": name, "args": args, "id": call_id, "type": "tool_call"}


def _reply(*calls: dict[str, Any], content: str = "") -> AIMessage:
    return AIMessage(
        content=content,
        tool_calls=list(calls),
        usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
    )


@pytest.fixture
def prompt_dir(tmp_path: Path) -> Path:
    (tmp_path / "probe.md").write_text(
        "Answer with {{output_tool}}. Tools: {{research_tools}}. Keep {{customer_name}}.",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def agent_settings() -> Settings:
    return Settings(environment="test", anthropic_api_key="sk-test-not-used")


def _probe(
    settings: Settings,
    prompt_dir: Path,
    model: ScriptedModel,
    toolkit: AgentToolkit | None = None,
) -> ProbeAgent:
    return ProbeAgent(
        settings,
        toolkit=toolkit or StubToolkit(),
        prompts=PromptLibrary(prompt_dir),
        chat_model=model,  # type: ignore[arg-type]
    )


# --- prompts ---------------------------------------------------------------


class TestPromptLibrary:
    def test_substitutes_supplied_variables(self, prompt_dir: Path) -> None:
        rendered = PromptLibrary(prompt_dir).render("probe", {"output_tool": "Result"})

        assert "Answer with Result." in rendered

    def test_leaves_unknown_placeholders_untouched(self, prompt_dir: Path) -> None:
        """{{customer_name}} is product syntax the model must be taught to emit."""
        rendered = PromptLibrary(prompt_dir).render("probe", {"output_tool": "Result"})

        assert "{{customer_name}}" in rendered

    def test_none_renders_as_empty_not_the_word_none(self, prompt_dir: Path) -> None:
        rendered = PromptLibrary(prompt_dir).render("probe", {"research_tools": None})

        assert "Tools: ." in rendered
        assert "None" not in rendered

    def test_missing_prompt_names_what_does_exist(self, prompt_dir: Path) -> None:
        with pytest.raises(PromptNotFoundError, match="probe"):
            PromptLibrary(prompt_dir).load("nope")

    def test_rejects_a_traversing_name(self, prompt_dir: Path) -> None:
        with pytest.raises(PromptNotFoundError):
            PromptLibrary(prompt_dir).load("../../etc/passwd")

    def test_every_registered_agent_has_its_prompt_file(self) -> None:
        available = set(PromptLibrary().available())

        for agent in registry.all_agents():
            assert agent.prompt_file in available


# --- registry --------------------------------------------------------------


class TestRegistry:
    def test_strategist_is_registered(self) -> None:
        assert registry.get("campaign-strategist") is CampaignStrategistAgent

    def test_unknown_agent_is_a_404_listing_the_known_ones(self) -> None:
        with pytest.raises(ApiError) as exc:
            registry.get("nope")

        assert exc.value.status_code == 404
        assert exc.value.code == "AGENT_NOT_FOUND"
        assert "campaign-strategist" in exc.value.message


# --- the loop --------------------------------------------------------------


class TestAgentLoop:
    async def test_finishes_when_the_model_calls_the_output_tool(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        model = ScriptedModel(_reply(_call("ProbeResult", {"answer": "42"})))

        run = await _probe(agent_settings, prompt_dir, model).run(ProbeInput(question="q"))

        assert run.output.answer == "42"
        assert run.steps == 1
        assert run.usage.total_tokens == 15
        assert run.degraded is False

    async def test_output_schema_is_bound_as_a_tool_beside_the_research_tools(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        @tool
        def lookup(query: str) -> str:
            """Look something up."""
            return "found"

        model = ScriptedModel(_reply(_call("ProbeResult", {"answer": "ok"})))
        agent = _probe(agent_settings, prompt_dir, model, StubToolkit([lookup]))

        await agent.run(ProbeInput(question="q"))

        assert model.bound_tools == [lookup, ProbeResult]

    async def test_runs_a_research_tool_and_records_it(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        @tool
        def lookup(query: str) -> str:
            """Look something up."""
            return f"result for {query}"

        model = ScriptedModel(
            _reply(_call("lookup", {"query": "acme"})),
            _reply(_call("ProbeResult", {"answer": "done"})),
        )
        agent = _probe(agent_settings, prompt_dir, model, StubToolkit([lookup]))

        run = await agent.run(ProbeInput(question="q"))

        assert run.steps == 2
        assert [(c.tool, c.ok) for c in run.tool_calls] == [("lookup", True)]
        # The result was fed back to the model on the following turn.
        assert "result for acme" in str(model.turns[1][-1].content)

    async def test_a_failing_tool_degrades_the_turn_not_the_run(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        @tool
        def flaky(query: str) -> str:
            """Always fails."""
            raise RuntimeError("upstream is down")

        model = ScriptedModel(
            _reply(_call("flaky", {"query": "x"})),
            _reply(_call("ProbeResult", {"answer": "answered anyway"})),
        )
        agent = _probe(agent_settings, prompt_dir, model, StubToolkit([flaky]))

        run = await agent.run(ProbeInput(question="q"))

        assert run.output.answer == "answered anyway"
        assert run.tool_calls[0].ok is False
        assert "upstream is down" in (run.tool_calls[0].error or "")

    async def test_an_invented_tool_name_is_reported_back_not_raised(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        model = ScriptedModel(
            _reply(_call("no_such_tool", {})),
            _reply(_call("ProbeResult", {"answer": "recovered"})),
        )

        run = await _probe(agent_settings, prompt_dir, model).run(ProbeInput(question="q"))

        assert run.output.answer == "recovered"
        assert run.tool_calls[0].error == "unknown tool"

    async def test_an_invalid_result_is_handed_back_for_repair(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        """A schema this wide fails on a detail far more often than on substance."""
        model = ScriptedModel(
            _reply(_call("ProbeResult", {"answer": ""})),  # fails min_length
            _reply(_call("ProbeResult", {"answer": "second time"})),
        )

        run = await _probe(agent_settings, prompt_dir, model).run(ProbeInput(question="q"))

        assert run.output.answer == "second time"
        assert "Rejected" in str(model.turns[1][-1].content)

    async def test_prose_is_nudged_then_gives_up(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        model = ScriptedModel(AIMessage(content="Here is my answer in prose."))

        with pytest.raises(ApiError) as exc:
            await _probe(agent_settings, prompt_dir, model).run(ProbeInput(question="q"))

        assert exc.value.status_code == 502
        assert exc.value.code == "AGENT_NO_RESULT"

    async def test_a_nudged_model_can_still_finish(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        model = ScriptedModel(
            AIMessage(content="Thinking out loud."),
            _reply(_call("ProbeResult", {"answer": "finally"})),
        )

        run = await _probe(agent_settings, prompt_dir, model).run(ProbeInput(question="q"))

        assert run.output.answer == "finally"

    async def test_the_step_limit_is_enforced(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        @tool
        def lookup(query: str) -> str:
            """Look something up."""
            return "again"

        # The model never submits; it just keeps calling the research tool.
        model = ScriptedModel(*[_reply(_call("lookup", {"query": "x"})) for _ in range(20)])
        agent = _probe(agent_settings, prompt_dir, model, StubToolkit([lookup]))
        agent.max_steps = 3  # type: ignore[misc]

        with pytest.raises(ApiError) as exc:
            await agent.run(ProbeInput(question="q"))

        assert exc.value.status_code == 504
        assert exc.value.code == "AGENT_STEP_LIMIT"

    async def test_an_oversized_tool_result_is_truncated(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        @tool
        def huge(query: str) -> str:
            """Returns far too much."""
            return "x" * (MAX_TOOL_RESULT_CHARS * 2)

        model = ScriptedModel(
            _reply(_call("huge", {"query": "x"})),
            _reply(_call("ProbeResult", {"answer": "ok"})),
        )
        agent = _probe(agent_settings, prompt_dir, model, StubToolkit([huge]))

        await agent.run(ProbeInput(question="q"))

        fed_back = str(model.turns[1][-1].content)
        assert "truncated" in fed_back
        assert len(fed_back) < MAX_TOOL_RESULT_CHARS * 1.1

    async def test_an_unreachable_toolset_degrades_the_run(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        model = ScriptedModel(_reply(_call("ProbeResult", {"answer": "from the brief alone"})))
        toolkit = StubToolkit(notes=["firecrawl could not be reached."])

        run = await _probe(agent_settings, prompt_dir, model, toolkit).run(ProbeInput(question="q"))

        assert run.degraded is True
        assert run.notes == ["firecrawl could not be reached."]

    async def test_an_upstream_failure_becomes_a_502(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        class BrokenModel(ScriptedModel):
            async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
                raise ConnectionError("no route to host")

        with pytest.raises(ApiError) as exc:
            await _probe(agent_settings, prompt_dir, BrokenModel()).run(ProbeInput(question="q"))

        assert exc.value.status_code == 502
        assert exc.value.code == "AGENT_UPSTREAM_ERROR"

    async def test_the_timeout_is_a_504(self, agent_settings: Settings, prompt_dir: Path) -> None:
        import asyncio

        class SlowModel(ScriptedModel):
            async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
                await asyncio.sleep(1)
                raise AssertionError("should have timed out")

        agent = _probe(agent_settings, prompt_dir, SlowModel())
        agent.timeout_seconds = 0.05  # type: ignore[misc]

        with pytest.raises(ApiError) as exc:
            await agent.run(ProbeInput(question="q"))

        assert exc.value.status_code == 504
        assert exc.value.code == "AGENT_TIMEOUT"

    def test_a_bad_payload_is_a_422_with_field_details(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        agent = _probe(agent_settings, prompt_dir, ScriptedModel())

        with pytest.raises(ApiError) as exc:
            agent.parse_payload({"wrong": "shape"})

        assert exc.value.status_code == 422
        assert exc.value.details == [
            {"field": "question", "code": "REQUIRED", "message": "Field required"}
        ]


# --- the strategist ---------------------------------------------------------


def _strategy_args(**overrides: Any) -> dict[str, Any]:
    """A complete, valid CampaignStrategy as the model would submit it."""
    args: dict[str, Any] = {
        "researched": True,
        "business": {
            "name": "Acme Capital",
            "summary": "A mutual fund distributor selling SIPs to salaried investors.",
            "industry": "Wealth management",
            "value_propositions": ["No commission", "Start from 500 a month"],
            "tone_of_voice": "Plain and reassuring",
        },
        "competitors": [
            {
                "name": "Rival Invest",
                "website_url": "https://rival.example.com",
                "positioning": "Highest returns",
                "ad_angles": ["Beat the index"],
                "hooks": ["Your money deserves better"],
                "gap": "Nobody addresses investors who already stopped.",
            }
        ],
        "creative": {
            "angle": "Speak to the investor who paused, not the one who never started.",
            "why_it_wins": "Every competitor markets acquisition; none market resumption.",
            "video_concept": "Open on a paused SIP statement, then the cost of the gap.",
            "opening_hook": "You stopped in March. Here is what that cost.",
            "proof_points": ["Zero commission"],
            "avoid": ["Guaranteed returns"],
        },
        "campaign": {
            "name": "SIP Resumption - Lapsed Investors",
            "objective": "LEAD_CAPTURE",
            "schedule": {"timezone": "Asia/Kolkata"},
            "budget": {
                "budget_type": "LIFETIME",
                "budget_amount_minor": 5000000,
                "currency": "INR",
            },
            "compliance": {
                "special_category": "FINANCIAL_PRODUCTS_SERVICES",
                "disclaimer_text": "Investments are subject to market risk.",
            },
            "tracking": {"utm_campaign": "sip-resumption"},
            "ads": [
                {
                    "name": "Paused-SIP cost of waiting",
                    "headline": "Your SIP is still paused",
                    "description": "Restarting takes one tap. No paperwork, no penalty.",
                    "cta": "GET_QUOTE",
                    "personalised_message": (
                        "Hi {{customer_name}}, your SIP has been paused since March."
                    ),
                    "options": [
                        {
                            "position": 2,
                            "label": "Not right now",
                            "intent": "NEGATIVE",
                            "follow_up_type": "MESSAGE",
                            "follow_up_message": "Understood - we will not follow up.",
                        },
                        {
                            "position": 1,
                            "label": "Restart my SIP",
                            "intent": "POSITIVE",
                            "follow_up_type": "MESSAGE",
                            "follow_up_message": "Great - an advisor will call you.",
                        },
                    ],
                }
            ],
        },
        "rationale": [
            {
                "field": "campaign.objective",
                "reason": "The goal is positive intent, not reach.",
                "confidence": "HIGH",
            }
        ],
        "open_questions": ["The video itself still needs recording."],
        "sources": [{"url": "https://acme.example.com", "title": "Home"}],
    }
    args.update(overrides)
    return args


def _strategist(settings: Settings, model: ScriptedModel) -> CampaignStrategistAgent:
    return CampaignStrategistAgent(settings, toolkit=StubToolkit(), chat_model=model)  # type: ignore[arg-type]


class TestCampaignStrategist:
    async def test_drafts_a_campaign_from_a_brief(self, agent_settings: Settings) -> None:
        model = ScriptedModel(_reply(_call("CampaignStrategy", _strategy_args())))

        run = await _strategist(agent_settings, model).run(
            CampaignBrief(requirements="Win back investors who paused their SIP.")
        )

        assert isinstance(run.output, CampaignStrategy)
        assert run.output.campaign.name == "SIP Resumption - Lapsed Investors"

    async def test_options_come_back_in_position_order(self, agent_settings: Settings) -> None:
        """The builder renders by position; a swapped pair reverses the buttons."""
        model = ScriptedModel(_reply(_call("CampaignStrategy", _strategy_args())))

        run = await _strategist(agent_settings, model).run(
            CampaignBrief(requirements="Win back investors who paused their SIP.")
        )

        options = run.output.campaign.ads[0].options
        assert [option.position for option in options] == [1, 2]
        assert options[0].label == "Restart my SIP"

    async def test_a_user_chosen_objective_survives_the_model(
        self, agent_settings: Settings
    ) -> None:
        """The objective is the user's decision, so it is enforced in code."""
        model = ScriptedModel(_reply(_call("CampaignStrategy", _strategy_args())))

        run = await _strategist(agent_settings, model).run(
            CampaignBrief(
                requirements="Win back investors who paused their SIP.",
                objective=CampaignObjective.RETENTION,
            )
        )

        assert run.output.campaign.objective is CampaignObjective.RETENTION

    async def test_already_filled_fields_are_put_to_the_model(
        self, agent_settings: Settings
    ) -> None:
        model = ScriptedModel(_reply(_call("CampaignStrategy", _strategy_args())))
        brief = CampaignBrief(
            requirements="Win back investors who paused their SIP.",
            existing=CampaignDraft(name="Q3 Winback"),
        )

        await _strategist(agent_settings, model).run(brief)

        opening = str(model.turns[0][-1].content)
        assert "Q3 Winback" in opening
        assert "Keep every one of these values" in opening

    async def test_the_draft_maps_onto_the_campaign_create_contract(
        self, agent_settings: Settings
    ) -> None:
        """A draft the builder cannot apply is not a draft."""
        from src.schemas.campaign import CampaignCreate

        model = ScriptedModel(_reply(_call("CampaignStrategy", _strategy_args())))
        run = await _strategist(agent_settings, model).run(
            CampaignBrief(requirements="Win back investors who paused their SIP.")
        )

        payload = run.output.campaign.model_dump(exclude_none=True, mode="json")
        campaign = CampaignCreate.model_validate(payload)

        assert campaign.name == "SIP Resumption - Lapsed Investors"
        ad = campaign.ads[0]
        assert ad.name == "Paused-SIP cost of waiting"
        assert ad.cta is CallToAction.GET_QUOTE
        assert ad.personalised_message.startswith("Hi {{customer_name}}")
        assert [o.label for o in ad.options] == ["Restart my SIP", "Not right now"]

    def test_the_prompt_names_the_tool_the_loop_actually_binds(
        self, agent_settings: Settings
    ) -> None:
        agent = _strategist(agent_settings, ScriptedModel())
        brief = CampaignBrief(requirements="Win back investors who paused their SIP.")

        prompt = agent._system_prompt(brief, ["firecrawl_search"])

        assert f"`{agent.output_tool}`" in prompt
        assert "{{customer_name}}" in prompt  # the product's own token, taught verbatim
        assert "{{output_tool}}" not in prompt  # ... but every real placeholder resolved


# --- endpoints --------------------------------------------------------------


class ScriptedAgentService(AgentService):
    """AgentService whose agents run on a scripted model instead of Claude."""

    def __init__(self, settings: Settings, model: ScriptedModel) -> None:
        super().__init__(settings, toolkit=StubToolkit())
        self._model = model

    def _build(self, name: str) -> BaseAgent:
        return registry.get(name)(
            self._settings,
            toolkit=self._toolkit,
            prompts=self._prompts,
            chat_model=self._model,  # type: ignore[arg-type]
        )


@pytest.fixture
def agent_client(app: FastAPI, settings: Settings) -> TestClient:
    """A client whose agents answer from a script."""
    model = ScriptedModel(_reply(_call("CampaignStrategy", _strategy_args())))
    app.dependency_overrides[get_agent_service] = lambda: ScriptedAgentService(settings, model)
    with TestClient(app) as client:
        client.headers[DEV_USER_HEADER] = OWNER
        yield client
    app.dependency_overrides.clear()


class TestAgentEndpoints:
    def test_catalogue_requires_a_session(self, client: TestClient, api: str) -> None:
        assert client.get(f"{api}/agents").status_code == 401

    def test_catalogue_reports_the_feature_as_off_when_unconfigured(
        self, owner_client: TestClient, api: str
    ) -> None:
        """A client can hide the feature instead of discovering it by failing."""
        body = owner_client.get(f"{api}/agents").json()

        assert body["enabled"] is False
        assert [a["name"] for a in body["agents"]] == ["campaign-strategist"]

    def test_catalogue_publishes_the_input_schema(self, owner_client: TestClient, api: str) -> None:
        agent = owner_client.get(f"{api}/agents").json()["agents"][0]

        assert "requirements" in agent["input_schema"]["properties"]
        assert agent["toolsets"] == ["firecrawl"]
        assert agent["available_toolsets"] == []

    def test_running_an_agent_without_a_key_is_a_503(
        self, owner_client: TestClient, api: str
    ) -> None:
        response = owner_client.post(
            f"{api}/agents/campaign-strategist/draft",
            json={"requirements": "Win back investors who paused their SIP."},
        )

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "AGENTS_NOT_CONFIGURED"

    def test_draft_returns_the_strategy_and_how_it_was_produced(
        self, agent_client: TestClient, api: str
    ) -> None:
        response = agent_client.post(
            f"{api}/agents/campaign-strategist/draft",
            json={
                "requirements": "Win back investors who paused their SIP.",
                "market": "India",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["strategy"]["campaign"]["objective"] == "LEAD_CAPTURE"
        assert body["strategy"]["campaign"]["compliance"]["special_category"] == (
            "FINANCIAL_PRODUCTS_SERVICES"
        )
        assert body["strategy"]["campaign"]["ads"][0]["cta"] == "GET_QUOTE"
        assert body["meta"]["agent"] == "campaign-strategist"
        assert body["meta"]["steps"] == 1

    def test_a_short_brief_is_rejected_before_any_model_call(
        self, agent_client: TestClient, api: str
    ) -> None:
        response = agent_client.post(
            f"{api}/agents/campaign-strategist/draft", json={"requirements": "hi"}
        )

        assert response.status_code == 422
        assert response.json()["error"]["details"][0]["field"] == "requirements"

    def test_the_generic_route_runs_the_same_agent(
        self, agent_client: TestClient, api: str
    ) -> None:
        response = agent_client.post(
            f"{api}/agents/campaign-strategist/runs",
            json={"requirements": "Win back investors who paused their SIP."},
        )

        assert response.status_code == 200
        assert response.json()["output"]["campaign"]["name"]

    def test_the_generic_route_404s_on_an_unknown_agent(
        self, agent_client: TestClient, api: str
    ) -> None:
        response = agent_client.post(f"{api}/agents/nope/runs", json={})

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "AGENT_NOT_FOUND"


class TestToolConcurrency:
    """One turn's lookups run at once, and none of them can hang the run."""

    async def test_calls_in_one_turn_run_concurrently(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        """Three 100ms lookups should cost ~100ms, not 300ms."""
        import asyncio

        @tool
        async def slow(query: str) -> str:
            """Takes a moment."""
            await asyncio.sleep(0.1)
            return f"result for {query}"

        model = ScriptedModel(
            _reply(
                _call("slow", {"query": "a"}, "c1"),
                _call("slow", {"query": "b"}, "c2"),
                _call("slow", {"query": "c"}, "c3"),
            ),
            _reply(_call("ProbeResult", {"answer": "done"})),
        )
        agent = _probe(agent_settings, prompt_dir, model, StubToolkit([slow]))

        started = asyncio.get_running_loop().time()
        run = await agent.run(ProbeInput(question="q"))
        elapsed = asyncio.get_running_loop().time() - started

        assert len(run.tool_calls) == 3
        assert elapsed < 0.25, f"ran in {elapsed:.2f}s - looks sequential"

    async def test_results_keep_the_order_they_were_asked_for(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        """Concurrency must not reorder the transcript."""
        import asyncio

        @tool
        async def echo(query: str) -> str:
            """Slower for the first argument, so completion order differs."""
            await asyncio.sleep(0.15 if query == "first" else 0.01)
            return f"result for {query}"

        model = ScriptedModel(
            _reply(
                _call("echo", {"query": "first"}, "c1"),
                _call("echo", {"query": "second"}, "c2"),
            ),
            _reply(_call("ProbeResult", {"answer": "done"})),
        )
        agent = _probe(agent_settings, prompt_dir, model, StubToolkit([echo]))

        await agent.run(ProbeInput(question="q"))

        # The two tool results the model saw, in the order they were appended.
        fed_back = [str(message.content) for message in model.turns[1][-2:]]
        assert "first" in fed_back[0]
        assert "second" in fed_back[1]

    async def test_a_hanging_tool_costs_its_own_timeout_not_the_run(
        self, agent_settings: Settings, prompt_dir: Path
    ) -> None:
        """A page that never responds must not take the whole draft with it."""
        import asyncio

        @tool
        async def hangs(query: str) -> str:
            """Never returns."""
            await asyncio.sleep(60)
            return "unreachable"

        model = ScriptedModel(
            _reply(_call("hangs", {"query": "x"})),
            _reply(_call("ProbeResult", {"answer": "answered anyway"})),
        )
        agent = _probe(agent_settings, prompt_dir, model, StubToolkit([hangs]))
        agent._settings = agent_settings.model_copy(update={"agent_tool_timeout_seconds": 0.05})

        run = await agent.run(ProbeInput(question="q"))

        assert run.output.answer == "answered anyway"
        assert run.tool_calls[0].ok is False
        assert "timed out" in (run.tool_calls[0].error or "")
