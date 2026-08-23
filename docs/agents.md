# Agents — Base Class, Prompts and the Campaign Strategist

[← Index](README.md) · Related: [Backend Architecture](backend-architecture.md) · [Campaign Data Model](campaign-data-model.md)

The campaign builder asks for a name, an objective, an audience, a budget, a
compliance category, tracking parameters, a headline, a personalised message and two
response options with their follow-ups. That is a lot of empty fields for someone who
knows what they want to say but not how this product wants it said.

The strategist agent turns a sentence of intent — plus, when there is one, the business's
own website — into a filled-in draft, with the competitor research that justifies it.

---

## 1. Layout

```
src/agents/
├── base.py                  BaseAgent - the loop every agent inherits
├── registry.py              name → class, populated by @register
├── models.py                the chat model factory
├── toolkits.py              MCP servers, and the allow-list per server
├── prompts.py               loads and renders the .md files
├── prompts/
│   ├── README.md            the prompt format, and what belongs in one
│   └── campaign-strategist.md
└── campaign_strategist.py   the first concrete agent
```

It sits beside `src/services/` rather than inside it: agents have their own vocabulary —
prompts, tools, steps, token budgets — and folding that into the service layer would blur
what `services/` means. `AgentService` is the seam, and it is deliberately thin.

```
controllers/agent_controller.py    HTTP in / HTTP out
   ↓
services/agent_service.py          enabled? which agent? validate the payload
   ↓
agents/                            prompt → tools → loop → validated result
```

---

## 2. `BaseAgent`

A subclass declares *what* it is and answers two hooks. The base class owns prompt
rendering, tool loading, the tool-calling loop, validation, timeouts, token accounting and
error mapping.

| Declaration | Meaning |
| --- | --- |
| `name` | URL-safe id, unique in the registry |
| `title`, `description` | Shown in the catalogue and in OpenAPI |
| `prompt_file` | The `.md` under `prompts/`, without the suffix |
| `input_model` | Schema an untrusted payload is validated against |
| `output_model` | Schema the agent must return |
| `toolsets` | Which MCP toolsets it asks for |
| `max_steps`, `max_tokens`, `effort`, `timeout_seconds` | Per-agent overrides; `None` defers to `Settings` |

| Hook | Default | Use it for |
| --- | --- | --- |
| `opening_message(payload)` | **abstract** | Writing the caller's request out as the first user turn |
| `prompt_variables(payload)` | `{}` | The `{{placeholders}}` in the prompt file |
| `finalise(output, payload)` | identity | Rules that must hold *every* time |

### 2.1 Structured output is a terminal tool

The obvious design is two phases: research with tools, then a second call constrained to
the schema with `with_structured_output`. It does not hold up here.

- A constrained call forces `tool_choice`, and a forced tool choice conflicts with the
  extended thinking Claude Opus 5 runs by default.
- It pays for the entire research transcript a second time.

So the output schema is bound as **one more tool** alongside the research tools, and the
run finishes when the model calls it. One loop, no forced choice, no second billing of the
context — and the model decides for itself when it has read enough.

```python
bound = model.bind_tools([*research_tools, self.output_model])
```

The tool's name is the schema's class name, and `{{output_tool}}` renders it into the
prompt — so a renamed schema can never leave the prompt naming a tool that no longer
exists.

### 2.2 A rejected result is repaired, not raised

`CampaignStrategy` is wide: a business profile, up to five competitors, a creative
direction, a full campaign draft, per-field rationale and sources. A schema that size fails
on a *detail* — a 42-character label against a 40-character limit — far more often than on
substance.

So a `ValidationError` is handed back as a tool result and the model gets another turn.
Re-prompting costs one turn; failing costs the user the whole run.

### 2.3 Failure modes

| Situation | Behaviour |
| --- | --- |
| Firecrawl unreachable | Run continues from the brief. `meta.degraded: true` plus a note |
| A tool call fails | Reported to the model as a tool error; it carries on |
| The model invents a tool | Told the tool does not exist, and what does |
| Result fails validation | Errors handed back for repair |
| Model replies in prose | Nudged twice, then `502 AGENT_NO_RESULT` |
| Step limit reached | `504 AGENT_STEP_LIMIT` |
| Whole run too slow | `504 AGENT_TIMEOUT` |
| Provider unreachable | `502 AGENT_UPSTREAM_ERROR` |
| No `ANTHROPIC_API_KEY` | `503 AGENTS_NOT_CONFIGURED`, before any work is done |

Scraped pages are truncated at 24 000 characters, so one greedy fetch cannot crowd the
brief and the accumulated research out of the context window.

---

### 2.4 Two providers, one loop

`BaseAgent` only ever calls `bind_tools` and `ainvoke`, which every LangChain chat model
gives the same shape — so which provider runs is configuration, not code. `AGENT_PROVIDER`
is `auto` (whichever key is present, preferring Anthropic), `anthropic`, or `openai`.

Naming a provider you have no key for **disables** the agents rather than quietly falling
back to the other one and billing you somewhere you did not expect.

The per-provider quirks live in `models.py`, once:

| | Anthropic (Claude Opus 5) | OpenAI (GPT-5 family) |
| --- | --- | --- |
| Default model | `claude-opus-5` | `gpt-5.1` |
| `temperature` | rejected with a 400 | only the default; omitted |
| Thinking | adaptive; `budget_tokens` removed | reasoning models |
| Effort levels | `low`–`max` (five) | `low`/`medium`/`high` — `xhigh` and `max` are **clamped**, not sent and rejected |

### 2.5 One turn's lookups run at once

A model that asks for three lookups in one turn expects three lookups, not three round
trips. They are dispatched with `asyncio.gather` and re-ordered back into the order they
were asked for, so the transcript still reads as the model wrote it.

Each call is bounded by `AGENT_TOOL_TIMEOUT_SECONDS` (45s) **on top of** the run's own
ceiling. That second bound is not belt-and-braces: a single page that never responds used
to hold the loop until the global timeout and lose every lookup already done. It is now one
failed tool result the model is told to carry on without.

---

## 3. Prompts are Markdown files

One `.md` per agent, sent to the model verbatim. They live on disk rather than in Python
string literals so a change to behaviour shows up in a diff looking like one.

`{{name}}` is substituted when `name` is one of the supplied variables and **left exactly
as written** when it is not. That second half is load-bearing: the campaign prompt has to
teach the model to emit the product's own personalisation token, the literal
`{{customer_name}}`, and a templating engine that substituted or errored on every
placeholder would eat it.

| Goes in the prompt | Goes in the schema | Goes in code |
| --- | --- | --- |
| Method, priorities, standards of evidence, tone | Field names, types, lengths, enums, per-field instructions | Rules that must hold every time |

Field-level instruction belongs in the Pydantic `description=`, because the output schema
*is* handed to the model as a tool definition — every description is read as part of the
instructions. Restating the schema in prose just creates a second copy to keep in sync.

Full conventions: [`backend/src/agents/prompts/README.md`](../backend/src/agents/prompts/README.md).

---

## 4. Firecrawl over MCP

Firecrawl is reached over MCP rather than through its REST SDK. That costs one adapter
module and buys two things: adding another provider is a table entry rather than a client
wrapper, and the tools arrive already shaped as LangChain tools, so `BaseAgent` never
learns a vendor's request format.

**Not every tool a server offers should reach an agent.** Firecrawl exposes crawling and
monitoring alongside search and scrape. A campaign draft has no business starting a
site-wide crawl or registering a recurring monitor — both spend credits, and the monitor
outlives the request. Each toolset therefore declares what it exposes:

```python
FIRECRAWL_TOOLS = ("firecrawl_search", "firecrawl_scrape", "firecrawl_map", "firecrawl_extract")
```

Anything else the server advertises is dropped before an agent sees it. The API key travels
as a bearer token, which is what Firecrawl's own documentation requires — it is never
embedded in the URL.

---

## 5. The campaign strategist

`POST /api/v1/agents/campaign-strategist/draft`

**In** — `requirements` (the only mandatory field), and optionally `website_url`,
`competitor_urls`, `business_name`, `industry`, `market`, `audience_note`, `objective`, and
`existing`.

`existing` is the one that matters most in practice: it carries whatever the user has
already typed into the form, and those values come back untouched. The agent completes the
form, it does not rewrite it.

**Out** — `CampaignStrategy`:

| Block | Holds |
| --- | --- |
| `researched` | Whether any page was actually read |
| `business` | What they sell, to whom, how they write |
| `competitors[]` | Positioning, ad angles, **quoted** hooks, and the gap in the set |
| `creative` | The recommended angle, why it wins, the video concept |
| `campaign` | The draft, including its `ads[]` — maps field-for-field onto `CampaignCreate` |
| `rationale[]` | Per field: why, and a confidence of `HIGH`/`MEDIUM`/`LOW` |
| `open_questions[]` | What the user still has to decide |
| `sources[]` | Only pages actually read |

One ad is the normal answer; the agent drafts a second only when the research supports a
genuinely different angle worth testing.

Confidence is about **evidence, not conviction**: `HIGH` means it was read on a page,
`MEDIUM` inferred from something read, `LOW` a reasonable guess. A draft that is honestly
mostly `LOW` is more useful than one uniformly and falsely `HIGH`.

### 5.1 The draft adds nothing to the data model

`CampaignDraft` mirrors `CampaignCreate` field for field, so applying it to the builder is
assignment and not translation — and a test asserts exactly that by feeding a draft
straight into `CampaignCreate`. Three blocks are deliberately absent:

| Absent | Why |
| --- | --- |
| `delivery` | Pacing and send caps are operational settings whose defaults are already right. Research tells you nothing about them |
| `schedule.start_at` / `end_at` | When a campaign runs is the user's call, and the model has no clock. Only `timezone` is inferable, so only `timezone` is offered |
| `ads[].status` | A drafted ad is a draft. Switching it on is the user's decision, taken after they have watched the video they still have to record |

The video is not drafted either. `creative.video_concept` describes what to shoot; the file
is still the user's to upload, and the agent says so in `open_questions`.

### 5.2 Two rules are enforced in code, not prompted

`finalise()` exists for rules that must hold every time. A prompt makes something likely;
only code makes it certain.

- **A user-chosen objective survives the model.** If the caller set `objective`, that is
  the objective, whatever the model returned.
- **Every ad's options come back in position order.** The builder renders by position, so a
  swapped pair would silently reverse the two buttons.

---

## 6. The generate flow

`/campaigns/generate` is where the strategist is used. Three states, and one rule:
**nothing is written until the draft is accepted.**

```
brief  ──▶  agent runs  ──▶  review  ──▶  create
(free)      (slow, costs)    (free)       (instant, irreversible)
```

Generating and creating are two decisions rather than one button, because they have
opposite costs: a run is slow and spends money upstream, a create is instant and cannot be
undone. A draft the user does not like costs them the run and nothing else.

**What the agent cannot supply, the screen asks for.** The draft carries no `audience_id` —
it has no idea which list this is for — so an audience is picked at the accept step.

**Generated ads arrive unfinished, on purpose.** `DraftAd` has no `video_url`: the agent
writes the concept, the user records the film. So the accepted campaign lands `INCOMPLETE`
with each ad blocked on exactly one field, and the user is taken straight to the ads screen:

```
POST /campaigns  ->  201, campaign INCOMPLETE
                     ad DRAFT/INCOMPLETE, blockers ['video_url']
                     campaign publish_blockers ['ads', 'ads.0.video_url']
```

Those campaign-level blockers are not fields on the campaign form, so the publish checklist
links them to the Ads tab rather than to an anchor that does not exist.

The screen is hidden when `GET /agents` reports `enabled: false` — a deployment with no
model key says so rather than offering a button that can only fail.

---

## 7. Adding the next agent

1. Two schemas — the input, and the output that doubles as the terminal tool. Write the
   `description=` on every field; the model reads them.
2. `src/agents/prompts/<name>.md`.
3. A subclass: the declarations, `opening_message()`, and `prompt_variables()` if the
   prompt needs any.
4. One import line in `src/agents/__init__.py`.

Nothing else. `GET /agents` publishes it, `POST /agents/<name>/runs` calls it, and the
catalogue carries its JSON Schemas.

---

## 8. Testing

Nothing in `tests/test_agents.py` touches the network. `BaseAgent` takes `chat_model` as a
constructor argument precisely so the loop — the part actually worth testing — can be
driven by a scripted stand-in: tool calls, a failing tool, an invented tool name, an
invalid result being repaired, the nudge, the step limit, the timeout, truncation, and
degraded research all have tests.
