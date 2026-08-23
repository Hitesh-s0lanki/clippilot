# MiniMax H3 on Modal

Self-hosted 768p video + audio generation for ClipPilot, behind SGLang's diffusion runtime.

- **What the model can do, and its limits** → [`docs/minimax-h3-model.md`](../../docs/minimax-h3-model.md)
- **How this fits the product, and the cost model** → [`docs/ai-video-pipeline.md`](../../docs/ai-video-pipeline.md)

> **768p only.** `H3-Regenerate-2K` is not open-weight, so this deployment cannot produce
> 2K. 2K requests belong to the hosted MiniMax API. `target.short_edge` is pinned to 768.

> **No prompt enhancer.** `H3-Context-IR` is not open-weight either. The `prompt` field must
> already carry the six-section structured format — see the model doc §9. This app does not
> write prompts; the backend's prompt builder does.

## Prerequisites

```bash
uv tool install modal          # CLI, kept out of the backend dependency tree
modal token new                # only if ~/.modal.toml has no active profile
```

No Hugging Face token is needed — `MiniMaxAI/MiniMax-H3` is public and ungated. The licence
governs *use*, not download; read §7 of the model doc before serving this commercially.

## One-time: fetch the weights

```bash
modal run infra/modal/h3_app.py::download_weights --variant ref2va
```

CPU-only, so no GPU is billed. Pulls **144 GB** into the `clippilot-h3-cache` Volume and
takes roughly half an hour.

`ref2va` is the variant this product needs — it is the mode that holds a product or
presenter identical across the clip. Add `--variant fl2va` later for first/last-frame
storyboarding; it is another 144 GB.

## Measure the generation time

```bash
modal run infra/modal/h3_app.py::smoke                 # 5s clip, ref2va, tp-size 4
modal run infra/modal/h3_app.py::smoke --duration 10
```

Writes `h3-ref2va-5s.mp4` locally and prints `wall_seconds` — that is **T** in the
break-even table in the pipeline doc §12.

```bash
modal run infra/modal/h3_app.py::reproduce    # replay MiniMax's published Ref2VA case
```

`reproduce` fetches the vendor's own reproducible script from the model repo and replays its
exact payload, so a correct deployment produces their published result. Use it as the
stack-correctness check after any image, flag or revision change.

### Measured, 2026-08-23

Verified working on `H100:4` / `--tp-size 4`. Outputs are 24 fps, AAC stereo 32 kHz; the
vendor reproduction lands within 0.1% of MiniMax's published `assets/ref2va.mp4`.

| Workload | T (warm, 5s clip) | Cost/clip | Hosted API |
| --- | ---: | ---: | ---: |
| Video-editing (`::reproduce`) | 276.5 s | $1.43 | $0.40 |
| **Image-reference (`::product`)** | **140.2 s** | **$0.72** | **$0.40** |

Cold start is ~350 s either way. Break-even needs T under **77 s**.

The hosted API is cheaper on both paths today, so this deployment is a fallback rather than
the default — its value is the hosted API's 15-task concurrency ceiling, not price. The
product path is 1.8× off parity with every optimisation switched off, so that gap is
plausibly closable; see
[pipeline doc §12.4](../../docs/ai-video-pipeline.md#124-measured).

## Deploy

```bash
modal deploy infra/modal/h3_app.py
```

## Configuration

| Setting | Value | Why |
| --- | --- | --- |
| `gpu` | `H100:4` | 49.80 GB/GPU measured with TP4 |
| `tensor_parallel` | `4` → `--tp-size 4` | See the OOM note below |
| `scaledown_window` | `60` | Short while benchmarking. Raise toward 300 in production. |
| `min_containers` | `0` | 4 warm datacenter GPUs cost ~$450/day doing nothing |
| `MODEL_REVISION` | pinned sha | A silent upstream re-upload cannot change what we serve |

Modal bills **per second of container runtime**, not per hour, and nothing runs while idle.
The recurring cost is the Volume: 144 GB is roughly **$13/month** whether or not you
generate anything.

## Things that cost time to discover

**The vendor's own serve flags OOM on an H100.** The published command uses
`--ulysses-degree 4`, measured at 94.3 GB/GPU — that needs H200's 141 GB. On 80 GB cards use
`--tp-size 4` (49.80 GB/GPU). The `tensor_parallel` parameter switches between them.

**The serving API is asynchronous.** `POST /v1/videos` returns an id, not a video. You then
poll `GET /v1/videos/{id}` and finally fetch `GET /v1/videos/{id}/content`. Code written
against a synchronous POST silently hangs.

**Download the right layout.** The repo ships the same weights twice — self-contained
bundles (`Ref2VA/`, for SGLang) *and* a diffusers modular tree. A full clone is 498 GB;
scoping to `model_index.json` + `Ref2VA/*` is 144 GB.

**`from __future__ import annotations` breaks `modal.parameter`.** It stringifies the
annotations, and Modal's parameter type validation then fails with a confusing
`'str' object has no attribute '__name__'`. Do not add it to this file.

**References can be remote URLs.** `conditions[].uri` accepts `https://`, and the server
fetches them itself — so S3 public or presigned URLs pass straight through without staging
files into the container.

## Licence obligations

Self-hosting these weights carries conditions that the hosted API does not — territorial
exclusions (EU, UK, South Korea, USA), a $20M revenue ceiling, and **mandatory "MiniMax H3"
attribution in the user-facing interface**. Model doc §7 has the detail. Attribution is part
of the definition of done for shipping this to users, not a nicety.
