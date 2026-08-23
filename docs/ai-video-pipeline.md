# AI Video Generation Pipeline

[← Index](README.md) · Related: [MiniMax H3 Model Reference](minimax-h3-model.md) · [Campaign Data Model](campaign-data-model.md) · [Backend Architecture](backend-architecture.md)

> **Note:** This file is *derived* — it is **not** part of the source assignment document.
> The brief lists [actual AI generation, video rendering and production infrastructure as
> out of scope](README.md#at-a-glance). Everything here is marked **`EXT`**: it describes
> the feature that would fill `campaign_ads.video_url` with a generated file instead of an
> uploaded one, and it is deliberately designed so that **the core flow never depends on
> it**. A campaign with a pasted CDN URL must keep working with this whole subsystem
> switched off.
>
> The model constraints this design is built around are established in
> [MiniMax H3 — Model Reference](minimax-h3-model.md). Read that first; the two documents
> are meant as a pair.

---

## 1. What is being built

A campaign owner uploads **images of their product, brand or presenter**, writes **what the
ad should do**, and gets back a **4–15 second video with sound** that becomes the campaign's
experience video.

Concretely, this adds one screen, two tables, five endpoints and one Modal app to a
codebase that already has S3 upload, campaign persistence and a preview player.

### 1.1 The three constraints that shaped the design

Each of these comes from [the model reference](minimax-h3-model.md) and each one changes
the architecture, so they are restated here:

1. **Self-hosted H3 cannot produce 2K.** `H3-Regenerate-2K` is not open-weight. Modal gets
   you 768p. If the product promises 2K, part of the traffic must go to the hosted API —
   so the backend needs **two interchangeable providers**, not one.
2. **The licence excludes the EU, UK, South Korea and the USA** from local deployment, and
   caps at $20M revenue. That makes the choice of backend a **business fact that can change
   without warning**, which is the second reason for the abstraction in [§7](#7-the-provider-abstraction).
3. **Self-hosted has no prompt enhancer.** `H3-Context-IR` is not released, so the
   structured prompt the model expects has to be built server-side. That makes the
   [prompt builder](#6-the-prompt-builder) a first-class service, not a string template.

### 1.2 The recommendation

**Ship the hosted MiniMax API first; keep Modal as the scale path.** The abstraction goes
in on day one, `MiniMaxApiProvider` is the only implementation that ships, and
`ModalH3Provider` lands when sustained volume justifies it — which
[§12](#12-cost-model-and-break-even) shows is *not* at low volume.

This is the same conclusion the informal analysis reached, but for different reasons: not
"GPU management is hard", but "you lose 2K, you lose the prompt enhancer, you inherit a
territorial licence, and the idle GPU costs more than the API until you are generating
in bulk."

---

## 2. The user flow

```
Campaign builder
      │
      ▼
1. Upload references      up to 9 images, ≤30 MB each, straight to S3
      │                   (presigned POST — bytes never touch FastAPI)
      ▼
2. Describe the ad        objective · what must not change · mood · camera · duration
      │                   aspect ratio (9:16 default) · voiceover on/off
      ▼
3. Submit                 POST /generations → 202 + job id
      │
      ▼
4. Poll / stream          GET /generations/{id} → QUEUED → RUNNING → SUCCEEDED
      │                   45 s – 4 min depending on provider and cold start
      ▼
5. Review                 inline player · regenerate with a new seed · try a variant
      │
      ▼
6. Attach                 POST /generations/{id}/attach → sets campaign_ads.video_url
                          the campaign preview now plays the generated ad
```

Steps 1–2 are one screen. Step 5 is the one that decides whether the feature is usable:
**generation is non-deterministic, so the product must make a second attempt cheap.**
Re-running with a new seed and the same references is one click and one row.

---

## 3. Architecture

```
┌────────────────┐        ┌─────────────────────────────┐
│  Next.js       │        │  FastAPI  (src/)            │
│  (protected)   │        │                             │
│  /campaigns/   │ POST   │  generation_controller      │
│   [id]/generate├───────►│  generation_service         │
│                │        │  prompt_builder             │
│  poll GET      │◄───────┤  generation_repository      │
└───────┬────────┘        └──────┬──────────────┬───────┘
        │ presigned POST         │ spawn        │ HTTP
        ▼                        ▼              ▼
┌────────────────┐   ┌──────────────────┐  ┌─────────────────┐
│  S3 / R2       │   │  Modal           │  │  MiniMax hosted │
│  references/   │◄──┤  clippilot-h3    │  │  API            │
│  generated/    │   │  4×H100 · SGLang │  │  2K · global    │
└───────┬────────┘   └────────┬─────────┘  └────────┬────────┘
        │                     │ callback (HMAC)     │ callback
        │                     ▼                     ▼
        │            ┌─────────────────────────────────┐
        └───────────►│  POST /internal/generations/    │
          public URL │       callback                  │
                     └─────────────────────────────────┘
```

**Why the video bytes never pass through FastAPI.** The same reasoning that
[`storage_service`](../backend/src/services/storage_service.py) already applies to uploads
applies in reverse: a worker streaming a 40 MB MP4 through the API holds a connection for
the duration. The Modal worker writes to the **same S3 bucket** the uploader uses, under a
`generated/` prefix, and the callback carries only the resulting URL.

---

## 4. Data model

Two new tables. Both follow the conventions already in
[`campaign-data-model.md`](campaign-data-model.md): UUID primary keys, timestamps from
`TimestampMixin`, enums persisted as constrained TEXT rather than native database enums,
and **references stored as rows, not as `image_1_url … image_9_url` columns** — the same
decision that made `campaign_options` a table.

### 4.1 `generation_jobs`

| Field | Type | Req. | Notes |
| --- | --- | :---: | --- |
| `id` | UUID | auto | |
| `owner_user_id` | string(120) | ✅ | Clerk subject. Indexed. |
| `campaign_id` | UUID FK → `campaigns` | — | Nullable: a user may generate before choosing a campaign. `ON DELETE SET NULL`. |
| `ad_id` | UUID FK → `campaign_ads` | — | Set on attach, not on submit. |
| `status` | enum | ✅ | See [§4.3](#43-enums). |
| `mode` | enum | ✅ | `REF2VA` · `FL2VA` · `T2VA` |
| `provider` | enum | ✅ | `MINIMAX_API` · `MODAL_H3` · `FAL` |
| `provider_job_ref` | string(200) | — | Modal `call_id`, or the vendor task id. Indexed. |
| `user_prompt` | Text | ✅ | Exactly what the user typed. Never overwritten. |
| `compiled_prompt` | Text | — | What [§6](#6-the-prompt-builder) produced. Kept for debugging and for re-running a good result. |
| `duration_seconds` | int | ✅ | 4–15. `CHECK (BETWEEN 4 AND 15)`. |
| `aspect_ratio` | enum | ✅ | Default `NINE_SIXTEEN`. |
| `resolution` | enum | ✅ | `P768` · `K2`. `K2` is rejected when `provider = MODAL_H3`. |
| `seed` | bigint | — | Null = random. Persisted from the response so a result is reproducible. |
| `with_audio` | bool | ✅ | Default `true`. H3 always generates audio; this records whether the product keeps it. |
| `output_video_url` | string(2048) | — | |
| `output_poster_url` | string(2048) | — | Frame extracted by the worker. Feeds `campaign_ads.poster_url`. |
| `output_duration_seconds` | int | — | Measured, not requested. |
| `cost_minor` | bigint | — | Minor units, matching `campaigns.budget_amount_minor`. |
| `currency` | string(3) | — | |
| `error_code` | string(60) | — | Stable machine code — see [§13](#13-failure-modes). |
| `error_message` | string(500) | — | Safe to show the user. |
| `queued_at` / `started_at` / `finished_at` | timestamptz | — | Latency is a product metric here, so measure all three. |

Indexes: `(owner_user_id, status, created_at)` for the list screen, and
`(status, queued_at)` for the reconciliation sweep in [§9.3](#93-reconciliation).

### 4.2 `generation_assets`

One row per reference file, which is what makes the 9-image limit a `CHECK` and not a
migration.

| Field | Type | Req. | Notes |
| --- | --- | :---: | --- |
| `id` | UUID | auto | |
| `job_id` | UUID FK → `generation_jobs` | ✅ | `ON DELETE CASCADE` |
| `position` | int | ✅ | Ordering is meaningful — it is what `<Subject 1>` refers to. |
| `kind` | enum | ✅ | `IMAGE` · `VIDEO` · `AUDIO` |
| `role` | enum | ✅ | `REFERENCE` · `FIRST_FRAME` · `LAST_FRAME` |
| `label` | string(40) | ✅ | `SUBJECT_1`, `PICTURE_2`, … The prompt cites this. |
| `subject_note` | string(200) | — | The user's own words: *"the bottle — shape and label must not change"*. Feeds `subject_definitions`. |
| `storage_key` | string(1024) | ✅ | S3 key under `campaign-references/`. |
| `content_type` | string(100) | ✅ | |
| `size_bytes` | bigint | ✅ | Enforced by the presigned policy, recorded here. |

### 4.3 Enums

Added to [`src/schemas/enums.py`](../backend/src/schemas/enums.py), matching the existing
SCREAMING_SNAKE_CASE-on-the-wire convention:

```python
class GenerationStatus(StrEnum):
    QUEUED = "QUEUED"          # row written, provider not yet called
    SUBMITTED = "SUBMITTED"    # provider accepted, has a job ref
    RUNNING = "RUNNING"        # provider reports work in progress
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"        # no terminal signal inside the SLA window


class GenerationMode(StrEnum):
    T2VA = "T2VA"      # text only
    FL2VA = "FL2VA"    # first and/or last frame
    REF2VA = "REF2VA"  # reference-driven — the default for product ads


class GenerationProvider(StrEnum):
    MINIMAX_API = "MINIMAX_API"
    MODAL_H3 = "MODAL_H3"
    FAL = "FAL"


class VideoAspectRatio(StrEnum):
    TWENTYONE_NINE = "21:9"
    SIXTEEN_NINE = "16:9"
    FOUR_THREE = "4:3"
    ONE_ONE = "1:1"
    THREE_FOUR = "3:4"
    NINE_SIXTEEN = "9:16"


class VideoResolution(StrEnum):
    P768 = "P768"
    K2 = "K2"


class GenerationAssetKind(StrEnum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"


class GenerationAssetRole(StrEnum):
    REFERENCE = "REFERENCE"
    FIRST_FRAME = "FIRST_FRAME"
    LAST_FRAME = "LAST_FRAME"
```

### 4.4 Validation rules that belong in the schema layer

These come straight from [the model's input envelope](minimax-h3-model.md#4-input-envelope)
and every one of them prevents either a silent wrong result or a wasted charge:

| Rule | Why |
| --- | --- |
| ≤ 9 `IMAGE`, ≤ 3 `VIDEO`, ≤ 3 `AUDIO`, ≤ 12 total | Model limits |
| Video and audio references: 2–15 s each, **15 s total per kind** | Model limits |
| An `AUDIO` asset requires ≥ 1 `IMAGE` or `VIDEO` | Audio cannot travel alone |
| `REFERENCE` roles and `FIRST_FRAME`/`LAST_FRAME` roles are **mutually exclusive** | The API accepts both and **silently drops one** |
| `duration_seconds` always sent explicitly | Playground defaults to 8, API to 5 — a 60% billing swing |
| `resolution = K2` ⟹ `provider ≠ MODAL_H3` | Open weights cannot do 2K |
| Reference URLs `HEAD`-checked before submit | A broken URL that the model ignores **still bills in full** |

---

## 5. Reference upload

The existing [`storage_service`](../backend/src/services/storage_service.py) already does
the hard part — presigned POST with a `content-length-range` condition, so **S3** enforces
the size limit rather than a client-side courtesy check. The generation feature reuses it
verbatim and adds an image path.

**Changes:**

- `ALLOWED_IMAGE_SUFFIXES` and an image content-type map (`image/png` → `.png`,
  `image/jpeg` → `.jpg`, `image/webp` → `.webp`) alongside the existing video map.
- A second key prefix, `S3_REFERENCE_KEY_PREFIX = "campaign-references"`, so generated
  outputs, uploaded campaign videos and user references are separable by prefix in
  lifecycle rules and in the bill.
- Per-kind size ceilings in the signed policy: **30 MB** image, **50 MB** video, **15 MB**
  audio — matching the model's own per-file caps, so a file that S3 accepts is a file H3
  will accept.
- New routes on the existing `/uploads` router: `POST /uploads/image` and
  `POST /uploads/image/complete`, mirroring the video pair exactly.

Generated outputs are written by the worker to `generated/{job_id}/video.mp4` and
`generated/{job_id}/poster.jpg` in the same bucket, served through the same
`S3_PUBLIC_BASE_URL` CDN origin the campaign player already uses.

---

## 6. The prompt builder

`src/services/prompt_builder.py`. This is the piece that carries the most product value and
the one that is easiest to underestimate, because self-hosted H3 has **no
`H3-Context-IR`** to structure the input for you — see
[model reference §9](minimax-h3-model.md#9-the-prompt-contract) for the full contract.

The builder takes the user's sentence plus the campaign's own fields and emits the six
mandatory sections in order.

### 6.1 Inputs it has for free

ClipPilot already stores everything a good ad prompt needs:

| Source | Field | Use in the prompt |
| --- | --- | --- |
| `campaigns.objective` | `AWARENESS` … `CONVERSION` | Picks the shot grammar: awareness → wide, atmospheric; conversion → product-forward with a clear end card |
| `campaigns.special_category` | e.g. `FINANCIAL_PRODUCTS_SERVICES` | Suppresses claims language; the disclaimer stays a DOM overlay, never burnt into pixels |
| `campaign_ads.headline` | 80 chars | Candidate on-screen text — H3 renders text and brand marks well |
| `campaign_ads.personalised_message` | Text | Tone and voiceover source |
| `generation_assets.subject_note` | User's own words | `subject_definitions` and `retention_analysis` |
| Requested `aspect_ratio`, `duration` | | `detailed_description` shot count — a 6s clip is one or two shots, 15s supports three |

### 6.2 Shape of the output

```
subject_definitions:
  <Subject 1>  Source: reference image 1. A matte-black rectangular glass perfume
               bottle with an embossed logo and a stone-inlaid cap.
               Identity lock: silhouette, cap geometry, logo placement, matte finish.
  <Subject 2>  Source: reference image 2. The brand wordmark.
               Identity lock: letterforms and spacing.

summary:
  [reference generation]

retention_analysis:
  <Subject 1>  fully_preserved      — geometry, finish and logo must not change
  <Subject 2>  fully_preserved      — wordmark must remain legible
  environment  reference            — newly generated, not taken from any reference

detailed_description:
  Shot 1 (0.0–4.5s) — Macro three-quarter view of <Subject 1> standing on wet black
  marble. Warm golden key light rakes from camera left through the glass, throwing an
  amber caustic across the stone. Slow dolly-in, 35mm, shallow depth of field. Fine
  water droplets bead and slide down the bottle's left face.
  Shot 2 (4.5–10.0s) — Cut to a centred medium-wide holding <Subject 1>. Camera
  settles. <Subject 2> fades up in the lower third. Light steadies to a soft key.

overall_soundscape:
  Close, dry room tone. A single low water droplet impact at 5.2s. No footsteps,
  no voices.

non_diegetic_music:
  Sparse, slow cello with a low synth pad. Enters at 1.0s, resolves at 9.0s.
```

### 6.3 Rules the builder enforces

- Every reference gets an explicit label **and** an explicit role. Implicit roles are the
  documented cause of identity drift.
- An image that exists only to define a product is nested inside `<Subject N>` — it does
  **not** also get a standalone `<Picture N>`.
- On every cut, state the new shot size *and* which established subject it holds. This is
  what preserves a face or a product silhouette across shots.
- Dialogue appears **only** in `detailed_description`, inside `<d>` tags, in its original
  language, with speaker ids `(Sx)` in order of first vocal event — never repeated in the
  soundscape sections.
- Adjective padding is stripped. Structured detail beats length.

### 6.4 Personalisation — the token, not the render

`{{customer_name}}` **must not** reach the prompt.

[`personalisation.py`](../backend/src/services/personalisation.py) already resolves
variables at render time, into the DOM, per recipient. That stays true here: **one video
per campaign, personalised text over the top.** The alternative — one generation per
recipient — multiplies cost by the size of the audience:

| Recipients | Per-recipient generation @ 10 s, 768p | One master video |
| ---: | ---: | ---: |
| 1 | $0.80 | $0.80 |
| 100 | $80 | $0.80 |
| 5,000 | $4,000 | $0.80 |

Per-recipient generation is a real feature, but it is a **paid, explicitly-gated,
budget-checked** feature that must reconcile against `campaigns.spend_cap_minor` before it
starts — not a default. The default is a master video plus a personalised overlay, which
is what the brief's flow already does.

---

## 7. The provider abstraction

`src/services/generation/` — a `Protocol` and, initially, one implementation.

```python
from typing import Protocol
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GenerationRequest:
    job_id: str
    mode: GenerationMode
    compiled_prompt: str
    duration_seconds: int
    aspect_ratio: VideoAspectRatio
    resolution: VideoResolution
    seed: int | None
    references: tuple[ReferenceRef, ...]   # public URL + kind + role + label
    callback_url: str
    callback_token: str


@dataclass(slots=True, frozen=True)
class GenerationAccepted:
    provider_job_ref: str
    estimated_seconds: int | None


class VideoGenerationProvider(Protocol):
    name: GenerationProvider

    @property
    def is_configured(self) -> bool:
        """False disables the feature cleanly, exactly like storage.is_configured."""

    def supports(self, resolution: VideoResolution) -> bool: ...

    async def submit(self, request: GenerationRequest) -> GenerationAccepted: ...

    async def poll(self, provider_job_ref: str) -> GenerationOutcome: ...

    async def cancel(self, provider_job_ref: str) -> None: ...
```

`is_configured` mirrors the pattern
[`storage_service`](../backend/src/services/storage_service.py) already uses: with no
provider credentials the endpoints report the feature as unavailable and the builder hides
the button, rather than the API failing on click. **The app must run with no GPU and no
vendor account at all.**

Selection is a settings value, with a guard:

```python
generation_provider: Literal["none", "minimax_api", "modal_h3", "fal"] = "none"
```

`GenerationService` refuses `resolution=K2` against `MODAL_H3` at validation time rather
than discovering it at the worker — an error the user can act on, delivered before the
GPU spins up.

---

## 8. The Modal deployment

**Implemented in [`infra/modal/h3_app.py`](../infra/modal/h3_app.py)**, with operating
instructions in [`infra/modal/README.md`](../infra/modal/README.md). This section records the
decisions and the things that only surfaced once it was built; the file itself is the source
of truth for the code.

### 8.1 Image

Not `debian_slim` plus `pip install sglang`. SGLang's diffusion runtime needs `sgl-kernel`
and FlashInfer, which are painful to assemble by hand, so the build starts from the vendor
container and layers the diffusion extra on at the same pinned version:

```python
modal.Image.from_registry("lmsysorg/sglang:v0.5.18-cu129")
    .apt_install("ffmpeg")
    .run_commands("pip install --no-cache-dir 'sglang[diffusion]==0.5.18'", ...)
```

`ffmpeg` is not decoration — it extracts the poster frame and probes the true output
duration, both persisted on the job.

`MODEL_REVISION` is pinned to a commit sha so a silent upstream re-upload cannot change what
is served.

### 8.2 Weights: 144 GB, and which 144 GB

Weights live in a **Volume**, not the image: a 144 GB image builds slowly and pulls slower,
while a Volume is read straight into every container. Storage is the one charge that
persists when nothing is running — roughly **$13/month** for this footprint.

The repository ships the same weights in two layouts, so a naive clone pulls **498 GB**. See
[model reference §5.2](minimax-h3-model.md#52-measured--what-the-repository-actually-contains).
SGLang consumes the self-contained bundles, so the download is scoped:

```python
allow_patterns = ["model_index.json", "Ref2VA/*"]   # 144 GB, not 498
```

`Ref2VA` is the variant this product needs. `FL2VA` is another 144 GB and only earns its
place once first/last-frame storyboarding is a real feature.

The download runs **CPU-only** — no GPU is billed for it — and takes about half an hour.
No Hugging Face token is required: the repository is public and ungated.

### 8.3 The worker

An `@app.cls` parametrized by `variant` and `tensor_parallel`, starting `sglang serve` as a
subprocess in `@modal.enter()` and health-polling until it answers. Blocking there is
correct: Modal routes no inputs to a container until every `enter` hook returns, so the
container is not considered warm until the model is actually loaded.

**Concurrency stays at 1 until measured.** There is no published figure for H3 throughput at
concurrency on datacenter GPUs, and a second concurrent request on memory-saturated GPUs is
as likely to OOM as to help.

### 8.4 GPU selection — and the flag that OOMs

Modal's syntax is `gpu="H100:4"`, up to 8 GPUs per machine. Mapping
[the measured configurations](minimax-h3-model.md#6-hardware-requirements) onto Modal's
catalogue and per-second pricing:

| Modal `gpu=` | Recipe | Peak VRAM/GPU | GPU $/s | GPU $/hr | Verdict |
| --- | --- | ---: | ---: | ---: | --- |
| `"A100-80GB:4"` | `--tp-size 4` | 49.80 GB | $0.002776 | $9.99 | Cheapest. No FP8, lower bandwidth — slower per clip. |
| **`"H100:4"`** | **`--tp-size 4`** | **49.80 GB** | **$0.004388** | **$15.80** | **Deployed.** Best cost/latency balance. |
| `"H200:4"` | `--ulysses-degree 4` | 94.3 GB | $0.005044 | $18.16 | The vendor's published recipe |
| `"B200:8"` | `--quantization fp8` | ~51.9 GB | $0.013888 | $50.00 | Fastest; only under sustained load |
| `"T4"` / `"L4"` / `"A10"` / `"L40S"` | — | — | — | — | ❌ Not viable — see model doc §6.1 |

> **The vendor's own command OOMs on an H100.** The README publishes
> `--ulysses-degree 4`, which measures **94.3 GB/GPU** and needs H200's 141 GB. Copying it
> onto 4× H100 fails. `--tp-size 4` is the documented 80 GB recipe at 49.80 GB/GPU, and is
> what the `tensor_parallel` parameter selects.

Add ~18% to every GPU figure for the CPU and memory Modal bills alongside it
($0.0000131 per core-second, $0.00000222 per GiB-second). `"H100:4"` therefore costs roughly
**$0.00517/s**, and that is the number [§12](#12-cost-model-and-break-even) uses.

**Modal bills per second of container runtime**, not per hour; with `min_containers=0`
nothing is billed while idle.

### 8.5 Cold start

Two costs, one fixable:

- **Weight load** — 144 GB from Volume across 4 GPUs, plus SGLang init and CUDA-graph
  warmup. Budget several minutes; `@modal.enter` allows 15.
- **Idle scaledown** — every burst leaves `scaledown_window` seconds of paid idle behind it.
  Set to **60 s** while benchmarking so idle does not swamp the measurement; raise toward
  300 s in production, where holding a container warm across a burst is precisely what makes
  self-hosting cheaper than the API.

**Memory snapshots do not rescue this.** GPU memory snapshots are alpha, documented as
"generally incompatible with multi-GPU", and explicitly *cannot accelerate model loading from
storage* — the actual bottleneck. Worth revisiting only for a single-GPU INT8 configuration.

The real lever is **batching**: [§12](#12-cost-model-and-break-even) shows self-hosting only
pays when several clips share a warm container, so the queue should deliberately hold and
release work in groups rather than spawning per request.

### 8.6 The serving protocol is asynchronous

This is the detail most likely to be got wrong from memory. `POST /v1/videos` returns an
**id, not a video**:

```
POST /v1/videos              -> {"id": "..."}
GET  /v1/videos/{id}         -> {"status": "completed" | "failed" | ...}
GET  /v1/videos/{id}/content -> the MP4 bytes
```

`generate()` implements exactly that loop. Two consequences worth designing around:

- `conditions[].uri` accepts **`https://`**, and the server fetches references itself — so
  S3 public or presigned URLs pass straight through and no file staging into the container
  is needed.
- `target.short_edge` is pinned to **768**. The open weights cannot do 2K
  ([model doc §5](minimax-h3-model.md#5-what-is-open-and-what-is-not)), so a `K2` request is
  rejected at validation rather than discovered here.

Once a clip exists the worker extracts a poster frame with `ffmpeg`, probes the true
duration, writes both objects to S3 under `generated/{job_id}/`, and posts the signed
callback in [§9.2](#92-callback).

### 8.7 A trap in the Modal API

`from __future__ import annotations` **breaks `modal.parameter`**. It stringifies the
annotations, and Modal's parameter type validation then fails with a misleading
`AttributeError: 'str' object has no attribute '__name__'`. Do not add it to this module.

## 9. Job lifecycle

### 9.1 Submission

```
POST /api/v1/generations
  → validate (§4.4) — reject before spending anything
  → compile prompt (§6)
  → INSERT generation_jobs (QUEUED) + generation_assets
  → provider.submit(...)
  → UPDATE status = SUBMITTED, provider_job_ref = call_id
  → 202 Accepted { id, status, poll_after_seconds }
```

The row is written **before** the provider is called. A crash between the two leaves a
`QUEUED` row the reconciler can retry; the reverse order leaves an untracked GPU job that
nothing will ever collect.

### 9.2 Callback

`POST /api/v1/internal/generations/callback`, outside the Clerk-authenticated router.

- **Signature** — `X-ClipPilot-Signature: sha256=<hmac>` over the raw body, compared with
  `hmac.compare_digest`. Never a bearer token in a query string.
- **Timestamp** — `X-ClipPilot-Timestamp`, rejected outside a 5-minute window, so a
  captured callback cannot be replayed.
- **Idempotent** — keyed on `job_id`. A terminal job ignores further callbacks and still
  returns 200; retrying providers must not see a 4xx.
- **Fast** — the hosted API's webhook challenge must be echoed **unchanged within 3
  seconds**, so the handler writes the row and returns. No transcoding, no thumbnailing,
  no S3 round-trip on the request path.

### 9.3 Reconciliation

Callbacks get lost. A periodic sweep — a Modal cron, or the existing scheduler — picks up
`SUBMITTED`/`RUNNING` jobs older than their expected duration and calls `provider.poll()`.

For `MODAL_H3` that is `modal.FunctionCall.from_id(call_id).get(timeout=0)`, handling
`TimeoutError` as still-running and `modal.exception.OutputExpiredError` as gone. Jobs past
**30 minutes** with no terminal signal move to `EXPIRED` — a distinct status from `FAILED`,
because it means *"we do not know"*, and the two need different retry and refund handling.

---

## 10. API contract

All under `/api/v1`, all Clerk-authenticated except the callback.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/generations/config` | `{ enabled, providers, max_images, max_duration_seconds, resolutions }` — lets the builder hide the feature instead of failing on click, exactly like `/uploads/config` |
| `POST` | `/uploads/image` | Presigned POST for a reference image |
| `POST` | `/uploads/image/complete` | `HEAD`-confirms the object landed |
| `POST` | `/generations` | Submit. `202` + job |
| `GET` | `/generations/{id}` | Poll. Includes `status`, `error_code`, and outputs when done |
| `GET` | `/generations?campaign_id=&status=&limit=&cursor=` | History, for the regenerate-and-compare screen |
| `POST` | `/generations/{id}/cancel` | Best-effort. `CANCELLED` is only set once the provider confirms |
| `POST` | `/generations/{id}/attach` | Writes `video_url`, `poster_url` and `video_duration_seconds` onto the ad |
| `POST` | `/internal/generations/callback` | Signed provider callback |

`attach` is a separate call on purpose. Generation is non-deterministic, so **the user
chooses which result becomes the campaign video** — auto-attaching the first success would
overwrite a good video with a worse one on every retry.

---

## 11. Frontend surface

Per [`frontend-structure`](../frontend/src/app), the feature is one route inside the
protected group, owning its own `_components/`:

```
app/(protected)/campaigns/[id]/generate/
├── page.tsx                        # composes only
└── _components/
    ├── generation-form.tsx         # client — orchestrates the three steps
    ├── reference-uploader.tsx      # client — dropzone, 9-image cap, per-file progress
    ├── reference-tile.tsx          # one thumbnail + its subject_note field
    ├── generation-brief-fields.tsx # prompt, duration, aspect ratio, resolution
    ├── generation-progress.tsx     # client — polls, shows elapsed vs expected
    ├── generation-result.tsx       # player, seed, cost, attach / regenerate
    └── generation-history.tsx      # prior jobs for this campaign
```

`src/lib/api/generations.ts` joins the existing `client.ts` / `uploads.ts` /
`storage-upload.ts` trio — components never call `fetch` directly.

**The three states that decide whether this feels finished:**

- **Waiting** — 45 s to 4 minutes is long enough that a spinner is not enough. Show elapsed
  time against the provider's expected duration, and say what is happening
  ("starting a GPU" reads very differently from a stalled spinner during a 2-minute cold
  start).
- **Partial** — references uploaded but generation not yet submitted is a resumable state,
  not a lost one. It is a `QUEUED` row.
- **Failed** — `error_code` maps to specific copy and a specific next action. "Generation
  failed" is not an error message.

The `subject_note` field on each thumbnail is the highest-leverage control on the screen:
it is what becomes `retention_analysis`, and it is the difference between the product
staying recognisable and drifting.

---

## 12. Cost model and break-even

### 12.1 The two prices

| | Hosted API | Modal `H100:4` |
| --- | ---: | ---: |
| Unit | per second of **finished video** | per second of **wall-clock GPU time** |
| Price | **$0.08/s** at 768p · **$0.13/s** at 2K | **$0.00517/s** all-in |
| 10s 768p clip | **$0.80** | $0.00517 × *T* |

where *T* is warm wall-clock seconds per clip. Reference images past the fifth add $0.04
each on the hosted API and nothing on Modal.

### 12.2 Break-even

Ignoring overhead, Modal is cheaper per clip whenever

```
T < $0.80 / $0.00517 ≈ 155 seconds
```

But overhead is the whole story. Each *warm window* carries:

- cold start ≈ 120 s × $0.00517 ≈ **$0.62**
- idle scaledown 300 s × $0.00517 ≈ **$1.55**
- **≈ $2.17 before generating anything**

So the clips-per-warm-window needed to break even is `2.17 / (0.80 − 0.00517·T)`:

| Warm seconds per clip (*T*) | Marginal cost | Saving vs $0.80 | **Clips per window to break even** |
| ---: | ---: | ---: | ---: |
| 45 s | $0.23 | $0.57 | **~4** |
| 60 s | $0.31 | $0.49 | **~5** |
| 90 s | $0.47 | $0.33 | **~7** |
| 120 s | $0.62 | $0.18 | **~12** |
| 155 s | $0.80 | $0.00 | **never** |

**Read this as the deployment rule.** One-off generations from a campaign builder — a user
clicking generate, thinking, clicking again — are the worst possible shape for a
self-hosted GPU. Bulk generation of a campaign's variants in one burst is the best.

*T* is the input nobody has published for datacenter GPUs
([model reference §10](minimax-h3-model.md#10-what-this-document-does-not-know)); consumer
cards land at 230–250 s for a 5s clip. **Measure it on `H100:4` before committing.** If
*T* lands above ~155 s, self-hosting never pays at any volume.

### 12.3 Two traps

- **`min_containers=1` on `H100:4` costs about $447/day**, whether or not anyone generates
  anything. Leave it at 0 and accept the cold start.
- **The hosted API caps concurrency at 15 tasks** (2 on free). That is a throughput
  ceiling, not a cost one — and it is the argument for Modal that has nothing to do with
  price: a campaign generating 200 variants queues for a long time behind 15 slots.

---

### 12.4 Measured

**Run on 2026-08-23** on `H100:4` / `--tp-size 4`, via `infra/modal/h3_app.py`. Both outputs
verified: 24 fps, AAC stereo 32 kHz, and the vendor reproduction within 0.1% of MiniMax's own
published `assets/ref2va.mp4`.

Two workloads were measured, and **they differ by 2×** — which is why the first number alone
would have been the wrong basis for a decision:

| Workload | Command | T (warm, 5s clip) |
| --- | --- | ---: |
| Video-editing — video + audio references | `::reproduce` | 276.5 s |
| **Image-reference — one product image + text** *(the product path)* | `::product` | **140.2 s** |

Cold start is ~350 s either way (144 GB across 4 GPUs, including warmup).

Costing at `H100:4`'s $0.00517/s against the hosted API's $0.08/s of finished video:

| | Self-hosted, warm | Hosted API | Ratio |
| --- | ---: | ---: | ---: |
| Video-editing, 5s | $1.43 | $0.40 | **3.6×** |
| **Image-reference, 5s** | **$0.72** | **$0.40** | **1.8×** |

Break-even for a 5s clip is **T under 77 s**.

**The API is cheaper today, on both paths.** Marginal cost exceeds the API price, so
amortising cold start across a warm burst does not rescue it — [§12.2](#122-break-even)'s
clips-per-window table never comes into play, and there is no volume at which the current
configuration wins on price.

**But the product path is one optimisation pass from parity, not three.** Closing 1.8× is a
different proposition from closing 3.6×, and the run had every lever switched off:
`enable_torch_compile: false`, `enable_breakable_cuda_graph: false`, no AdaLN cache
(`minimax_h3_adaln_cache_path: null`), no quantisation. Those plausibly return 1.5–2×
together. Self-hosting is **not** categorically dead here — it is unproven, and the
experiment that would settle it is a day's work, not a rebuild.

One measured surprise worth carrying forward: 4× H100 at 140–276 s is **barely faster than a
single RTX 4090** (~230–250 s per 5s clip). Multi-GPU scaling for a *single* request is poor,
so the promising direction is more concurrent requests per container, not more GPUs per
request.

> **Decision, unchanged but for better reasons.** Ship `MiniMaxApiProvider`: cheaper today on
> both paths, plus 2K, plus the prompt enhancer, plus no territorial licence.
> `ModalH3Provider` stays behind the interface as a **working, measured** fallback — earning
> its place against the hosted API's **15-task concurrency ceiling**, which price cannot fix.
> Revisit self-hosting when either sustained volume hits that ceiling, or an optimisation pass
> brings T under 77 s.

## 13. Failure modes

Every code is stable, machine-readable, and maps to specific copy plus a specific action.

| `error_code` | Cause | Response |
| --- | --- | --- |
| `REFERENCE_UNREACHABLE` | `HEAD` failed before submit | Reject at validation. **Costs nothing** — and prevents a full-price charge for a result that ignored the image |
| `REFERENCE_LIMIT` | >9 images / >3 video / >12 total / >15 s | Reject with the offending asset ids |
| `MODE_CONFLICT` | Reference and keyframe roles mixed | Reject. The API would silently drop one |
| `RESOLUTION_UNSUPPORTED` | `K2` on `MODAL_H3` | Reject at validation, offer 768p or the hosted provider |
| `PROVIDER_RATE_LIMITED` | 15-task ceiling hit | Keep `QUEUED`, retry with backoff, tell the user their position |
| `PROVIDER_REJECTED` | Vendor 400 | Surface the vendor message. **No charge** |
| `CONTENT_BLOCKED` | Moderation | Distinct code — never merge with generic failure |
| `GPU_UNAVAILABLE` | No Modal capacity | Retry; fall back to the hosted provider if configured |
| `WORKER_TIMEOUT` | 30 min elapsed | `EXPIRED`, not `FAILED` |
| `OUTPUT_INVALID` | Zero-length or unprobeable MP4 | Fail loudly. Never attach an unplayable file to a campaign |

**Safety belongs to whoever runs the model.** The hosted API's moderation does not transfer
to a self-hosted deployment, and this is an ad product where users upload photographs of
people. Before `ModalH3Provider` ships: a pre-submission check on uploaded references, a
post-generation check on outputs, and — because
`campaigns.special_category` already exists — a hard block on generating for
`FINANCIAL_PRODUCTS_SERVICES` and `CREDIT` campaigns until someone has decided what a
synthetic financial-services ad is allowed to depict.

**Attribution is a licence obligation, not a nicety.** The Community Licence requires
"MiniMax H3" displayed prominently in the user-facing interface. It goes in the generation
screen and in the generated-video metadata, and it is part of the definition of done for
`ModalH3Provider`.

---

## 14. Build order

Sized against the way the rest of this repo is tiered in
[Campaign Data Model §8](campaign-data-model.md#8-scope-guidance).

**Tier A — the feature works, no GPU involved**

1. Enums, both tables, migration, repository
2. `POST /uploads/image` on the existing storage service
3. `prompt_builder` + its unit tests — testable with no provider at all
4. Provider `Protocol`, `is_configured`, and a `FakeProvider` that returns a fixture MP4
   after a delay
5. The route, the form, the three states, `attach`
6. Callback endpoint with HMAC verification

At the end of Tier A the whole flow is exercisable end to end, in CI, for free. That
sequencing is deliberate: everything expensive and everything jurisdiction-dependent is
still behind an interface.

**Tier B — real generation**

7. `MiniMaxApiProvider` — 2K, global, no licence conditions, no ops
8. Reconciliation sweep and `EXPIRED` handling
9. Cost recording against `campaigns.spend_cap_minor`

**Tier C — self-hosted, only if [§12](#12-cost-model-and-break-even) says so**

10. `download_weights`, deploy `h3_app.py`, **benchmark *T* on `H100:4`**
11. `ModalH3Provider` behind a settings flag, 768p only
12. Moderation on both sides, attribution in the UI, licence-territory check

> **The order is the point.** Steps 1–6 cost nothing and are reversible. Step 10 is where
> the money and the licence exposure start, and it should not begin until the measured
> value of *T* proves the GPU is cheaper than the API for this product's actual traffic
> shape.

---

## 15. Sources

Model capabilities, limits, hardware and licensing are sourced in
[MiniMax H3 — Model Reference §11](minimax-h3-model.md#11-sources). Modal platform
specifics used above:

- [Modal — GPU types and multi-GPU syntax](https://modal.com/docs/guide/gpu) · [pricing](https://modal.com/pricing)
- [Modal — Volumes](https://modal.com/docs/guide/volumes) · [Images](https://modal.com/docs/guide/images) · [Secrets](https://modal.com/docs/guide/secrets)
- [Modal — parametrized classes](https://modal.com/docs/guide/parametrized-functions) · [lifecycle functions](https://modal.com/docs/guide/lifecycle-functions)
- [Modal — cold start guide](https://modal.com/docs/guide/cold-start) · [memory snapshots](https://modal.com/docs/guide/memory-snapshot)
- [Modal — job queue and polling](https://modal.com/docs/guide/job-queue) · [web endpoints](https://modal.com/docs/guide/webhooks)
