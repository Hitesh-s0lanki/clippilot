# MiniMax H3 — Model Reference

[← Index](README.md) · Related: [AI Video Generation Pipeline](ai-video-pipeline.md) · [Campaign Data Model](campaign-data-model.md)

> **Note:** This file is *derived* — it is **not** part of the source assignment document,
> and the brief puts [actual AI generation explicitly out of scope](README.md#at-a-glance).
> It is marked **`EXT`** throughout: a design study for the generation feature that sits
> behind ClipPilot's `campaign_ads.video_url`, not work the core flow depends on.
>
> Everything below is sourced from the model card, the vendor's own docs and measured
> third-party runs, current as of **August 2026**. Where a number is *not* published, this
> document says so rather than guessing. See [§10](#10-what-this-document-does-not-know).

---

## 1. What H3 actually is

MiniMax H3 (product name *Hailuo 3.0*) is an **omni-modal generative model**: it reads
text, images, video and audio as **one unified context** and returns video with a natively
generated stereo soundtrack. It is not a video model with a TTS pass bolted on — voice,
sound effects and music are jointly modelled with the pixels.

It is built from three components, and **only the middle one is open-weight**:

| Component | What it does | Open? |
| --- | --- | :---: |
| **H3-Context-IR** | Hosted preprocessing. Interprets the relationships between your inputs, enhances the prompt and emits a structured intermediate representation. ~100K tokens of inference distilled to ~4K. | ❌ |
| **H3-Base** | 33B dense Omni-Transformer. Generates 768p video + 32 kHz stereo audio. | ✅ |
| **H3-Regenerate-2K** | In-context regeneration to 2K — a full regeneration pass, not upscaling. | ❌ |

**This split is the single most important fact in this document.** See
[§5](#5-what-is-open-and-what-is-not) for what it costs you.

Internals worth knowing, because they explain the hardware profile in [§6](#6-hardware-requirements):

- **H3-Encoder** — full Qwen3-VL-32B weights, hidden states taken from layer 50. This is
  a second 32B model in memory alongside the 33B transformer.
- **H3-VisualVAE** — temporal causal video autoencoder, 16× spatial / 4× temporal
  compression (`f16t4d24`). The high compression ratio is what makes 2K tractable at all.
- **H3-AudioVAE** — independent stereo-channel processing at 40 Hz temporal rate.
- **MM-RoPE** — 3-dimensional multimodal rotary position embeddings across time and both
  spatial axes.

Of the 33B parameters, roughly **13B live in AdaLN branches** and are precomputable at
inference — which is exactly what the "pruned INT8" checkpoints exploit.

---

## 2. Generation modes

The open release ships **two task-specific checkpoints**. There is no separate
text-only checkpoint: pure text-to-video runs through FL2VA with zero conditioning images.

| Checkpoint | Task codes | Inputs | Use in ClipPilot |
| --- | --- | --- | --- |
| **FL2VA** | `t2va`, `i2va`, `l2va`, `fl2va` | Text + 0–2 images (first frame, last frame, or both) | Storyboarded ads where the brand controls the opening and closing frame |
| **Ref2VA** | `ref2va`, `v2v`, `audio_only`, `mixed_ref` | Text + up to 12 mixed image/video/audio references | **The one this product needs** — hold a product or a presenter identical across the clip |

### 2.1 The distinction that matters

A reference image is **not** the first frame. In `ref2va` the model extracts *identity* —
face, clothing, product geometry, environment, composition cues — and re-renders it into
whatever the prompt describes. In `fl2va` the image **is** a literal frame the video must
pass through.

For a product ad, `ref2va` is almost always right: the user uploads a perfume bottle on a
white studio background, and the prompt puts it on black marble under golden light. `fl2va`
would keep the white background.

### 2.2 Full capability list

Beyond video, the same model performs:

- **Video** — text-to-video · image-to-video with reference and editing · video-to-video
  motion transfer · multi-shot native modelling (cuts inside a single generation) ·
  video continuation from an existing clip
- **Audio** — text-to-audio · audio-to-audio reference and editing · voice transfer and
  cloning from a reference clip · native stereo on every video output
- **Image** — text-to-image · image-to-image reference and editing
- **Editing** — precise localised editing, and text/brand rendering, which the vendor
  calls out as a specific strength (relevant when a logo has to stay legible)

**Languages:** stable support for 11 — Arabic, Chinese, English, French, German, Italian,
Japanese, Korean, Portuguese, Russian, Spanish.

---

## 3. Output envelope

| Property | Value |
| --- | --- |
| **Duration** | **4–15 seconds**, integer seconds only. The hosted API is documented as 5–15s. |
| **Resolution** | **768p** from open weights. **2K** (1440px short edge) only via hosted `H3-Regenerate-2K`. |
| **Frame rate** | 24 fps, fixed |
| **Audio** | 32 kHz stereo, always generated |
| **Aspect ratios** | `21:9` · `16:9` · `4:3` · `1:1` · `3:4` · `9:16` · adaptive |
| **Outputs per request** | 1–10 (`num_outputs_per_prompt`) |

> **15 seconds is a hard ceiling.** There is no long-form mode. A 30-second ad is a
> stitching problem — generate 2–3 clips and join them, accepting a cut. The model's
> multi-shot support means one 15s generation can *contain* cuts, which is usually a better
> answer than concatenating two generations that will not match.

`9:16` at 15 seconds is the natural fit for the Instagram Reels / TikTok ad case, and
`16:9` for an embedded campaign player. ClipPilot's preview surface is portrait-first, so
`9:16` should be the default the builder offers.

---

## 4. Input envelope

### 4.1 Reference limits

| Input | Limit | Per-item constraint |
| --- | :---: | --- |
| Reference images | **9** | ≤ 30 MB each |
| Reference video clips | **3** | 2–15 s each, **15 s total across all clips**, ≤ 50 MB each |
| Reference audio clips | **3** | 2–15 s each, **15 s total**, ≤ 15 MB each |
| **Mixed total** | **12 files** | Whole request body ≤ 64 MB |
| Prompt | ~7,000 characters | Structured detail beats length — see [§9](#9-the-prompt-contract) |

### 4.2 Three constraints that will bite

1. **Audio cannot travel alone.** A reference audio clip must accompany at least one image
   or video file. An audio-only request is rejected.
2. **Reference mode and keyframe mode are mutually exclusive.** If any
   `reference_image` / `reference_video` / `reference_audio` is present, `first_frame` and
   `last_frame` must not be — and vice versa. The hosted API **accepts both and silently
   drops one**, so validate this yourself before submitting. This is the most likely
   source of a "why did it ignore my image" bug.
3. **The duration default differs by surface.** The web playground defaults to 8 seconds;
   omitting `duration` on the API defaults to 5. That is a 60% swing in the bill for a
   parameter you thought you had left alone. **Always send `duration` explicitly.**

---

## 5. What is open, and what is not

This is where the widely-repeated "H3 is open-weight, so deploy it on Modal and get 2K
video cheaply" summary goes wrong. Two of the three components are withheld:

| If you self-host | You get | You lose |
| --- | --- | --- |
| H3-Base FL2VA / Ref2VA | 768p @ 24fps, 4–15s, stereo audio, all reference modes | **2K output** (`H3-Regenerate-2K` is not released) |
| | Full control, no per-second vendor bill | **Prompt enhancement and multimodal context organisation** (`H3-Context-IR` is not released) |

The second loss is subtler than the first and matters more day to day. `H3-Context-IR` is
what turns a user's casual sentence into the structured, role-labelled representation the
base model was trained to consume. Self-hosted, **you have to write that structure
yourself** — which is why [§9](#9-the-prompt-contract) exists, and why the pipeline design
puts a prompt-builder service on the critical path.

### 5.1 Published checkpoints

Each checkpoint is a diffusers-style repository:

```
<TASK>/                 # FL2VA or Ref2VA
├── model_index.json
├── processor/
├── tokenizer/
├── text_encoder/       # Qwen3-VL-32B
├── transformer/        # H3-Base, 33B
├── visual_vae/
└── audio_vae/
```

| Artefact | Precision | Size |
| --- | --- | ---: |
| Diffusion transformer (FL2VA or Ref2VA) | BF16 | **61.7 GB** |
| | INT8 | 31.7 GB |
| | pruned INT8 *(precomputed AdaLN tables)* | **19.5 GB** |
| Text encoder (Qwen3-VL-32B) | BF16 | **48.0 GB** |
| | INT8 | 25.3 GB |
| | NVFP4 AWQ | **14.6 GB** |
| Video VAE | FP16 | 4.9 GB |
| Audio VAE | FP32 | 0.6 GB |

**Practical totals per variant:** ~**144 GB** at BF16 (measured, see below), or ~**42.5 GB**
for the community pruned INT8 + NVFP4 repacks. Plan **≥ 180 GiB** of fast NVMe before
containers and outputs if you intend to hold both FL2VA and Ref2VA.

### 5.2 Measured — what the repository actually contains

The quantised sizes in the table above come from community repacks. The **official
repository is BF16 throughout** and ships *two parallel layouts of the same weights*, which
is why a naive full clone pulls **498 GB**:

| Layout | Contents | Size | Consumed by |
| --- | --- | ---: | --- |
| **Original checkpoint bundles** | `FL2VA/` · `Ref2VA/` — each self-contained (transformer + text encoder + both VAEs) | **144.05 GB each** | **SGLang**, vLLM |
| **Diffusers modular** | `transformer/` (FL2VA) 66.28 · `transformer_ref/` (Ref2VA) 66.28 · shared `text_encoder/` 66.73 · `vae/` 10.42 · `audio_vae/` 0.61 | ~210 GB for **both** variants | `diffusers` |

Scope the download to the framework you actually serve with. For SGLang and a single task
family that is `--include "model_index.json" "Ref2VA/*"` — **144 GB, not 498**. The modular
layout is more efficient only if you need *both* variants, since it shares one text encoder.

The text encoder measures 66.73 GB, consistent with Qwen3-VL-32B at BF16 (32B × 2 bytes);
the 48.0 GB figure quoted for it elsewhere is a repack, not this repo.

**The repository is public and ungated** — no Hugging Face token and no access request is
needed to download it, notwithstanding the licence terms in [§7](#7-licensing--read-before-choosing-self-hosting),
which govern *use*, not download.

---

## 6. Hardware requirements

Measured configurations, all at 1344×768 / 5s unless noted:

| Configuration | Precision | Peak VRAM per GPU | Verdict |
| --- | --- | ---: | --- |
| **4× H100 80GB**, TP4 | BF16 | **49.80 GB** | ✅ Cheapest lossless datacenter config |
| 4× H100 80GB, FSDP | BF16 | 57.01 GB | ✅ |
| 4× H100 80GB, TP2 + Ulysses2 | BF16 | 66.04 GB | ✅ Lower latency, higher memory |
| 4× H200 141GB, Ulysses4 | BF16 | 94.3 GB | ✅ Vendor-verified single node |
| 8× B300, FP8 | FP8 | ~51.9 GB | ✅ Fastest published |
| 2× RTX 5090, layerwise offload | BF16 | 26.3 GiB | ✅ Proves offload works |
| 1× 80GB-class + layerwise offload | pruned INT8 + NVFP4 | fits | ⚠️ Works, slow |
| 1× RTX 4090 24GB | INT8 pruned | dynamic | ⚠️ ~230 s per 5s clip |
| 1× RTX 3060 12GB | INT8 pruned | dynamic | ⚠️ ~235 s, bit-identical output |
| **T4 / L4 / A10** | any | — | ❌ Not viable |

### 6.1 Correcting a common claim

The widely-circulated table listing **"L40S 48GB ✅ Good"** is wrong for any straightforward
deployment. No published configuration runs H3 on a single L40S. The 48 GB card sits below
every measured single-GPU resident footprint, so it needs the same layerwise-offload path
as the RTX cards — which is bounded by host RAM and PCIe bandwidth, not by the GPU. Treat
`L40S:2` with `--layerwise-offload-components` as **unverified**, not as a recommendation.

Equally, **"A100 80GB ✅ Excellent"** is only true in a multi-GPU arrangement. One A100
cannot hold BF16 weights; four can, at TP4's 49.80 GB/GPU.

### 6.2 Host-side requirements

- **System RAM** — 64 GB is the reported comfortable floor; layerwise offload pins DiT
  weights to host memory, so under-provisioning RAM silently degrades to checkpoint
  mapping and roughly doubles step time. The startup log reports which weights stayed on
  checkpoint mapping; check it.
- **`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`** — required near capacity, or you
  will see OOM at a footprint that fits on paper.
- **Disk** — ≥ 180 GiB free.

### 6.3 Serving runtimes

`H3-Base` runs under **SGLang**, **vLLM**, **diffusers** and **ComfyUI**. SGLang is the
documented path and the one [the pipeline doc](ai-video-pipeline.md#8-the-modal-deployment)
builds on:

```bash
sglang serve \
  --model-path MiniMaxAI/MiniMax-H3 \
  --model-variant ref2va \
  --num-gpus 4 --tp-size 4 \
  --attention-backend fa \
  --performance-mode speed \
  --host 0.0.0.0 --port 30010
```

Flags worth knowing:

| Flag | Why |
| --- | --- |
| `--model-variant fl2va\|ref2va` | Selects the checkpoint. Default `fl2va`. |
| `--tp-size` / `--ulysses-degree` / `--ring-degree` | Tensor / sequence / cross-node parallelism |
| `--performance-mode memory\|speed` | The memory/latency trade |
| `--layerwise-offload-components dit,text_encoder,vae` | The under-80GB escape hatch |
| `--quantization fp8` | Online FP8, verified on B200/B300 |
| `--attention-backend fa\|sage_attn\|aiter` | FlashAttention · approximate · AMD |
| `--enable-breakable-cuda-graph true` | Verified on B200/H200 Ref2VA |
| `--warmup-resolutions 1344x768` | Pre-compiles the shape you actually serve |

### 6.4 The parallelism flag is not one-size-fits-all

The vendor's published command uses `--ulysses-degree 4`. Cross-referencing it against the
measured table above matters, because **that recipe does not fit an H100**:

| Recipe | Peak VRAM/GPU | Fits 80 GB? | Fits 141 GB? |
| --- | ---: | :---: | :---: |
| `--ulysses-degree 4` *(vendor default)* | 94.3 GB | ❌ | ✅ H200 |
| `--tp-size 4` | 49.80 GB | ✅ H100 | ✅ |
| FSDP | 57.01 GB | ✅ | ✅ |

Copying the README command onto 4× H100 will OOM. Use `--tp-size 4` there.

### 6.5 The serving API is asynchronous

The server exposes `POST /v1/videos`, but it **returns immediately with an id** rather than
the video — generation is polled, then the content is fetched separately. Three calls:

```
POST /v1/videos              -> {"id": "..."}
GET  /v1/videos/{id}         -> {"status": "completed" | "failed" | ...}
GET  /v1/videos/{id}/content -> the MP4 bytes
```

A client written against a synchronous `POST` that returns a video will not work. Request
shape:

The vendor's own reproducible scripts send only `task`, `prompt`, `conditions`, `target`
and `seed`; everything else below is optional tuning.

```jsonc
{
  "task": "ref2va",
  "prompt": "...",
  "target": { "short_edge": 768, "aspect_ratio": "9:16", "duration_seconds": 10 },
  "quality": "lossless",
  "num_inference_steps": 50,
  "flow_shift": 12.0,
  "audio_flow_shift": 3.0,
  "seed": 42,
  "conditions": [
    { "type": "image", "uri": "file:///refs/bottle.png", "role": "reference" },
    { "type": "audio", "uri": "file:///refs/vo.wav",     "role": "reference" },
    { "type": "video", "uri": "file:///refs/dolly.mp4",  "role": "reference",
      "start_time_seconds": 0 }
  ]
}
```

`uri` accepts **`https://` as well as `file://`** — the server fetches remote references
itself, so a deployment can pass public or presigned object-storage URLs straight through
instead of staging files into the container first.

---

## 7. Licensing — read before choosing self-hosting

H3 is released under the **MiniMax H3 Community License Agreement**, not an OSI licence.

| Term | Effect |
| --- | --- |
| **Territory** | Local deployment of the weights is **excluded in the EU, UK, Republic of Korea and USA**. Those territories must apply for separate written authorisation. |
| **Revenue ceiling** | Organisations above **$20M annual revenue** need separate written authorisation. |
| **Attribution** | Products built on H3 must display **"MiniMax H3"** prominently in the user-facing interface. |
| **Distillation** | Training other models on H3 outputs is **prohibited**. |
| **Hosted API** | Operates under separate commercial terms and is **available globally**, with no territorial restriction. |

**Consequences for this product.** ClipPilot is developed in India, which is outside the
excluded set, so self-hosting is permitted today. But the licence makes self-hosting a
**business-geography decision, not an infrastructure one**: a US or EU entity, an
acquisition, a US-incorporated subsidiary, or crossing $20M revenue each invalidate the
deployment. The hosted API carries none of these conditions.

That asymmetry is the strongest argument for the provider abstraction in
[the pipeline doc §7](ai-video-pipeline.md#7-the-provider-abstraction) — the licence can
change the correct backend without changing the product.

---

## 8. Access routes compared

| | **Hosted API** | **fal.ai** | **Self-host on Modal** |
| --- | --- | --- | --- |
| 2K output | ✅ | ✅ | ❌ 768p only |
| Prompt enhancement (Context-IR) | ✅ | ✅ | ❌ you write the structure |
| Territorial restriction | none | none | ⚠️ EU/UK/KR/US excluded |
| Attribution required | per terms | per terms | ✅ required |
| Cost at low volume | ✅ best | ✅ | ❌ idle GPU dominates |
| Cost at high sustained volume | ❌ | ❌ | ✅ best |
| Cold start | none | none | ~1–2 min weight load |
| Control (seed, steps, flow_shift) | limited | limited | ✅ full |
| Ops burden | none | none | high |

### 8.1 Published pricing

**Official API, per second of finished video:**

| Tier | Price |
| --- | ---: |
| 2K | **$0.13 /s** |
| 768p | **$0.08 /s** |
| 768p → 2K regeneration | $0.05 /s |
| Reference images | first 5 free, then **$0.04** each (**$0.025** on regeneration) |

A 10-second 9:16 product ad therefore costs **$0.80 at 768p** or **$1.30 at 2K**, plus
$0.04 for each reference image past the fifth. Resellers quote higher — around $0.1625/s
at 2K — so buy direct.

**Rate limits:** concurrency is **2 on free, 15 on paid**, counted in concurrent *tasks*.
That is the real throughput ceiling for a campaign that generates in bulk, and the number
to design the queue around.

**Billing on failure:** a request rejected at submission (HTTP 400) costs nothing. A
request that *succeeds* on bad input — a broken reference URL that the model simply
ignores — **bills in full**. Validate references before submitting, not after.

**Callbacks:** the webhook challenge value must be echoed unchanged within **3 seconds**.

Modal's side of the comparison is worked out in
[the pipeline doc §12](ai-video-pipeline.md#12-cost-model-and-break-even).

---

## 9. The prompt contract

Self-hosted, `H3-Context-IR` is not there to structure the prompt for you, so the base
model expects the structure directly. MiniMax publishes the format; it is not free prose.

### 9.1 Reference labels

Every reference gets an explicit label and an explicit role. **Do not leave roles implicit.**

| Label | Meaning |
| --- | --- |
| `<Subject N>` | Content abstracted from a reference that is reused or modified in the target video |
| `<Picture N>` | A reference image acting as a concrete frame anchor or shot-planning guide |
| `<Video N>` | Editing source, continuation point, or temporal structure |
| `<Audio N>` | Audio copied or referenced for voice, music or sound texture |

If an image exists only to define a character or a product, nest it inside `<Subject N>` —
do **not** also declare a standalone `<Picture N>` for it.

### 9.2 Mandatory section order

1. `subject_definitions` — define each label, its source and its role
2. `summary` — declare task types in brackets, combined with `+`:
   `[reference generation]`, `[keyframe completion]`, `[video editing]`,
   `[video continuation]`, `[audio reuse]`, `[audio reference]`
3. `retention_analysis` — mark each reference `fully_preserved`, `partially_preserved` or
   `reference`
4. `detailed_description` — shot by shot: composition, subject appearance and position,
   environment and lighting, actions and state changes, camera movement, sound, and the
   points where each referenced label takes effect. Dialogue goes in `<d>` tags in its
   original language, with speaker IDs `(Sx)` assigned in order of actual vocal events.
5. `overall_soundscape` — ambient and physical sound
6. `non_diegetic_music` — score the audience hears but the characters do not

### 9.3 Rules

**Do** — name the identity, clothing, product geometry, colours and spatial relationships
that must not change. State which label locks identity, which controls motion, which
controls pacing. On a cut, state the new shot size *and* which established subject it
holds; that is what keeps a face consistent across shots.

**Don't** — repeat dialogue in the audio sections (it belongs only in
`detailed_description`); treat newly added plot elements as reference losses; pad with
repeated adjectives. **Structured detail beats length.**

> The mapping from ClipPilot's campaign fields into this format is
> [pipeline doc §6](ai-video-pipeline.md#6-the-prompt-builder).

---

## 10. What this document does not know

Stated plainly, because these gaps change the build order:

- ~~**Wall-clock latency on datacenter GPUs is not published.**~~ **Now measured.** On
  `4× H100 / --tp-size 4`, a 5-second clip takes **140.2 s warm** on the image-reference path
  and **276.5 s** on the video-editing path, after a ~350 s cold start. Both are barely faster
  than consumer cards (~230–250 s on a 4090/4080/3060), which says multi-GPU scaling for a
  *single* request is poor. Economics in
  [pipeline doc §12.4](ai-video-pipeline.md#124-measured): the hosted API is cheaper on both
  paths today, by 1.8× and 3.6× respectively. Optimisations that were off during the run
  (torch.compile, breakable CUDA graph, AdaLN cache, quantisation) are the remaining upside.
- **Per-GPU-hour throughput at concurrency** is unknown; `@modal.concurrent(max_inputs=…)`
  should start at 1 and be raised only against measurements.
- **Quality delta between hosted 2K and self-hosted 768p** is not quantified anywhere. For
  a 9:16 phone-delivered ad, 768p may be sufficient; that is a product call to make with
  real samples, not from a spec sheet.
- **Content-safety filtering** on the open weights is undocumented. The hosted API's
  moderation behaviour does not transfer to a self-hosted deployment — you own that.

---

## 11. Sources

- [MiniMaxAI/MiniMax-H3 model card](https://huggingface.co/MiniMaxAI/MiniMax-H3) · [prompt guide (ref mode)](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)
- [MiniMax — MiniMax H3 announcement](https://www.minimax.io/blog/minimax-h3)
- [SGLang cookbook — MiniMax-H3](https://docs.sglang.io/cookbook/diffusion/MiniMax/MiniMax-H3)
- [ComfyUI Wiki — open weights release](https://comfyui-wiki.com/en/news/2026-08-03-minimax-h3-open-weights-comfyui)
- [MiniMax H3 Wiki — hardware requirements](https://www.minimax-h3.wiki/local/minimax-h3-hardware-requirements/)
- [Morphic — full specs and input limits](https://morphic.com/resources/models/minimax-h3)
- [Atlas Cloud — API pricing and undocumented limits](https://www.atlascloud.ai/blog/tips/minimax-h3-api-pricing)
- [explainX — Community Licence territorial exclusions](https://explainx.ai/blog/minimax-h3-open-video-model-hailuo-july-2026)
- [fal.ai — hosted H3 endpoints](https://fal.ai/minimax-h3)
- [MarkTechPost — release coverage](https://www.marktechpost.com/2026/08/01/minimax-releases-minimax-h3-an-omni-modal-video-model-that-generates-15-second-2k-clips-with-native-stereo-audio/)
