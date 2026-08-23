# ClipPilot — Documentation

Design and architecture notes for the ClipPilot **Mini Interactive Video Campaign
Builder**: a full-stack product demonstrating frontend craft, backend fundamentals,
data handling and product judgment.

> **On the source brief.** This project was built against a written assignment brief
> that is marked *CONFIDENTIAL — CANDIDATE EVALUATION*. That document, and the
> transcription of its sections (`01`–`10`), are deliberately **not published** in this
> repository. The documents below are original design work and are published in full.
> Some of them cite the brief's numbered sections by name; those files live only in the
> private working copy.

## At a glance

| | |
| --- | --- |
| **Time limit** | Maximum 8 hours / one working day |
| **Core scope** | Frontend, backend, database and basic analytics |
| **Expected result** | A working end-to-end campaign creation and preview flow |
| **Out of scope** | Actual AI generation, video rendering and production infrastructure |

## Documents

| Document | Covers |
| --- | --- |
| [Backend Architecture](backend-architecture.md) | Implemented schemas, services and routing |
| [Campaign Data Model](campaign-data-model.md) | The campaign as a proper top-level entity |
| [Agents](agents.md) | The LangChain base agent, the Markdown prompts, and the campaign strategist |
| [Delivery Checklist](delivery-checklist.md) | The requirements flattened into a tickable list |
| [AI Video Generation Pipeline](ai-video-pipeline.md) | `EXT` — uploading references and generating the campaign video |
| [MiniMax H3 Model Reference](minimax-h3-model.md) | `EXT` — what the model can do, and what it costs to run |

> The last two are **beyond the brief**, which puts AI generation out of scope. They design
> the subsystem that would fill `campaign_ads.video_url` with a generated file rather than an
> uploaded one, and they are written so the core flow keeps working with the whole thing
> switched off. Read them as a pair — the model's constraints are what shape the pipeline.

## Campaign structure

The brief describes a campaign as a video URL, one message and two buttons. That is a
*creative*. [**Campaign Data Model**](campaign-data-model.md) promotes **Campaign** to a
proper top-level entity — objective, lifecycle, schedule, budget, audience, compliance and
tracking — modelled on the Meta Ads campaign object, with one or more **ads** nested
beneath it.

Everything the brief mandates is preserved and marked `BRIEF`; everything added is marked
`EXT` and tiered by build priority, so the core flow still ships first.

## The one thing that matters most

> **PRIORITY** — The complete end-to-end flow is more important than adding many
> partially working screens. Optional features will not compensate for an incomplete
> or unreliable core flow.
