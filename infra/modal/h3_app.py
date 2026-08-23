"""MiniMax H3 on Modal — self-hosted 768p video + audio generation.

Serves the open-weight ``H3-Base`` checkpoint behind SGLang's diffusion runtime.
Design notes and the cost model live in ``docs/ai-video-pipeline.md``; the model's
limits are in ``docs/minimax-h3-model.md``. Two facts from those docs drive
everything here:

* the open weights are **768p only** — ``H3-Regenerate-2K`` is not released, so
  ``target.short_edge`` is pinned to 768 and 2K requests belong to the hosted API;
* there is no ``H3-Context-IR``, so the ``prompt`` field must already carry the
  six-section structured format. This module does not write prompts; the backend's
  prompt builder does.

Usage::

    modal run   infra/modal/h3_app.py::download_weights     # once, ~144 GB
    modal run   infra/modal/h3_app.py::smoke                # measures T, writes an mp4
    modal deploy infra/modal/h3_app.py                      # expose H3Server.generate
"""

import json
import subprocess
import time

import modal

# --- Model -----------------------------------------------------------------

MODEL_REPO = "MiniMaxAI/MiniMax-H3"

# Pinned so a silent upstream re-upload cannot change what we serve. Refresh
# deliberately, then re-run download_weights.
MODEL_REVISION = "42ed227ee7df40d41602854ae760620d6eb651fe"

# SGLang consumes the *original checkpoint* bundles (FL2VA/, Ref2VA/), not the
# diffusers modular layout that also lives in this repo. Each bundle is
# self-contained and ~144 GB; only download the task families you serve.
VARIANT_PATTERNS = {
    "ref2va": ["model_index.json", "Ref2VA/*"],
    "fl2va": ["model_index.json", "FL2VA/*"],
}

# The vendor runs one server per variant on its own port. Keeping their numbering
# makes the official reproducible scripts work unmodified against this deployment.
VARIANT_PORTS = {"fl2va": 30010, "ref2va": 30011}

CACHE_PATH = "/cache"

# --- Image -----------------------------------------------------------------

# SGLang's diffusion server ships ONLY in the dev/nightly builds. The tagged
# release (v0.5.18) has no diffusion support at all: `sglang serve` rejects
# --model-variant / --num-gpus / --performance-mode, and sglang.srt exposes no
# diffusion modules. Installing the `sglang[diffusion]` extra on top of the
# release resolves cleanly and adds nothing, which makes the failure confusing.
#
# This stock nightly already carries the diffusion server and diffusers 0.37.0,
# so no source build is needed: the cookbook's
# `pip install -e /sgl-workspace/sglang/python[diffusion]` compiles for 15+
# minutes to no benefit here.
#
# Pinned by date+sha so builds are reproducible. Before bumping it, confirm the
# replacement still answers `sglang serve --help` with a
# "--- Help for Diffusion Model Server ---" section carrying --model-variant.
SGLANG_IMAGE = "lmsysorg/sglang:nightly-dev-cu12-20260823-eec794bc"

image = (
    modal.Image.from_registry(SGLANG_IMAGE)
    .apt_install("ffmpeg")
    .env(
        {
            "HF_HOME": CACHE_PATH,
            # hf_transfer is deprecated in this huggingface_hub build; Xet is
            # its replacement for high-throughput downloads.
            "HF_XET_HIGH_PERFORMANCE": "1",
            # Required near capacity. Without it you OOM at a footprint that
            # fits on paper — see docs/minimax-h3-model.md §6.2.
            "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
        }
    )
)

# Weights live in a Volume rather than the image: 144 GB makes image builds slow
# and pulls slower, while a Volume is read straight into every container.
hf_cache = modal.Volume.from_name("clippilot-h3-cache", create_if_missing=True)

app = modal.App("clippilot-h3")


# --- Weights ---------------------------------------------------------------


@app.function(
    image=image,
    volumes={CACHE_PATH: hf_cache},
    timeout=60 * 60 * 4,
    cpu=8.0,
    memory=16384,
)
def download_weights(variant: str = "ref2va") -> dict:
    """Populate the Volume with one task-family bundle. CPU only — no GPU billed."""
    from huggingface_hub import snapshot_download

    if variant not in VARIANT_PATTERNS:
        raise ValueError(f"unknown variant {variant!r}; expected one of {list(VARIANT_PATTERNS)}")

    started = time.monotonic()
    path = snapshot_download(
        MODEL_REPO,
        revision=MODEL_REVISION,
        allow_patterns=VARIANT_PATTERNS[variant],
        max_workers=16,
    )
    hf_cache.commit()

    total = sum(f.stat().st_size for f in __import__("pathlib").Path(path).rglob("*") if f.is_file())
    return {
        "variant": variant,
        "path": path,
        "gigabytes": round(total / 1e9, 2),
        "seconds": round(time.monotonic() - started, 1),
    }


@app.function(image=image, volumes={CACHE_PATH: hf_cache}, timeout=60 * 10)
def verify_weights(variant: str = "ref2va") -> dict:
    """Pre-flight: confirm the bundle is on the Volume before booting any GPU.

    Cheap insurance — a missing shard surfaces here for fractions of a cent
    instead of 15 minutes into a 4-GPU cold start.
    """
    from pathlib import Path as _Path

    root = _Path(CACHE_PATH) / "hub" / f"models--{MODEL_REPO.replace('/', '--')}"
    snapshot = root / "snapshots" / MODEL_REVISION
    if not snapshot.exists():
        raise RuntimeError(f"no snapshot for revision {MODEL_REVISION} under {root}")

    bundle = snapshot / variant.upper().replace("REF2VA", "Ref2VA").replace("FL2VA", "FL2VA")
    files = [f for f in snapshot.rglob("*") if f.is_file() or f.is_symlink()]
    total = sum(f.stat().st_size for f in files)
    shards = sorted(f.name for f in bundle.rglob("*.safetensors")) if bundle.exists() else []

    report = {
        "snapshot": str(snapshot),
        "bundle_present": bundle.exists(),
        "files": len(files),
        "safetensors_shards": len(shards),
        "gigabytes": round(total / 1e9, 2),
    }
    print("weights:", json.dumps(report, indent=2), flush=True)
    return report


# --- Server ----------------------------------------------------------------


@app.cls(
    image=image,
    # H100 80 GB with --tp-size 4, measured at 49.80 GB/GPU. Note the vendor's
    # published recipe (--ulysses-degree 4) measures 94.3 GB/GPU and would OOM
    # here; it needs H200's 141 GB. TP4 is the documented low-VRAM alternative.
    gpu="H100:4",
    volumes={CACHE_PATH: hf_cache},
    timeout=60 * 60,
    # 60s while benchmarking so idle does not dominate the bill. Raise toward
    # 300s in production, where keeping a container warm across a burst of
    # generations is what makes self-hosting cheaper than the API at all.
    scaledown_window=60,
    # Never keep 4 datacenter GPUs warm — that is ~$450/day doing nothing.
    min_containers=0,
)
class H3Server:
    variant: str = modal.parameter(default="ref2va")
    # >0 selects --tp-size (needed to fit 80 GB cards). 0 falls back to the
    # vendor's --ulysses-degree 4, which only fits H200-class memory.
    tensor_parallel: int = modal.parameter(default=4)

    @modal.enter()
    def start_server(self) -> None:
        import httpx

        port = VARIANT_PORTS[self.variant]
        parallel = (
            ["--tp-size", str(self.tensor_parallel)]
            if self.tensor_parallel
            else ["--ulysses-degree", "4"]
        )
        cmd = [
            "sglang", "serve",
            "--model-path", MODEL_REPO,
            "--num-gpus", "4",
            *parallel,
            "--performance-mode", "speed",
            "--warmup-resolutions", "1344x768",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--model-variant", self.variant,
        ]
        print("launching:", " ".join(cmd), flush=True)
        self.proc = subprocess.Popen(cmd)
        self.base_url = f"http://127.0.0.1:{port}"

        # Modal routes no inputs until every @modal.enter returns, so blocking
        # here is correct: the container is not "warm" until the model is loaded.
        deadline = time.monotonic() + 15 * 60
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"sglang exited early with code {self.proc.returncode}")
            try:
                if httpx.get(f"{self.base_url}/health", timeout=5).status_code == 200:
                    print(f"sglang healthy on :{port}", flush=True)
                    return
            except httpx.HTTPError:
                pass
            time.sleep(5)
        raise RuntimeError("sglang did not become healthy within 15 minutes")

    def _stage_references(self, conditions: list[dict]) -> list[dict]:
        """Fetch every http(s) reference to a local file and rewrite its uri.

        Validates before spending: a reference that cannot be fetched, or that
        arrives empty, raises here rather than at the server.
        """
        import mimetypes
        import pathlib

        import httpx

        SUFFIX_BY_KIND = {"image": ".jpg", "video": ".mp4", "audio": ".mp3"}
        staged: list[dict] = []
        stage_dir = pathlib.Path("/tmp/references")
        stage_dir.mkdir(parents=True, exist_ok=True)

        # A descriptive User-Agent is not politeness: Wikimedia and others
        # return 403 to anonymous library defaults.
        headers = {"User-Agent": "ClipPilot/0.1 (+https://github.com/clippilot) httpx"}

        for index, condition in enumerate(conditions):
            uri = condition.get("uri", "")
            if not uri.startswith(("http://", "https://")):
                staged.append(condition)
                continue

            try:
                response = httpx.get(
                    uri, timeout=60, follow_redirects=True, headers=headers
                )
            except httpx.HTTPError as exc:
                raise RuntimeError(f"reference {index} unreachable: {uri} ({exc})") from None
            if response.status_code >= 400:
                raise RuntimeError(
                    f"reference {index} unreachable: {uri} -> HTTP {response.status_code}"
                )
            if not response.content:
                raise RuntimeError(f"reference {index} is empty: {uri}")

            kind = condition.get("type", "image")
            suffix = (
                mimetypes.guess_extension(response.headers.get("content-type", "").split(";")[0])
                or SUFFIX_BY_KIND.get(kind, "")
            )
            path = stage_dir / f"ref-{index}{suffix}"
            path.write_bytes(response.content)
            print(
                f"staged reference {index} ({kind}): {len(response.content) / 1e6:.2f} MB "
                f"-> {path}",
                flush=True,
            )
            staged.append({**condition, "uri": f"file://{path}"})

        return staged

    @modal.method()
    def generate(
        self,
        prompt: str,
        conditions: list[dict] | None = None,
        duration_seconds: int = 5,
        aspect_ratio: str = "auto",
        seed: int = 0,
        poll_seconds: float = 5.0,
        timeout_seconds: float = 45 * 60,
        stage_references: bool = True,
    ) -> dict:
        """Run one generation and return the MP4 bytes plus timings.

        Mirrors the vendor's own three-call protocol: submit, poll, fetch content.
        ``conditions`` entries are ``{"type": "image"|"video"|"audio", "uri": ...,
        "role": "reference"|"keyframe"}``.

        With ``stage_references`` (the default) every http(s) reference is fetched
        here first and handed to the server as a ``file://`` path. SGLang can
        fetch remote URIs itself, but doing it here buys two things:

        * **a cheap, specific failure.** An unreachable reference fails in
          milliseconds with the URL and status, instead of a 500 from the
          server's fetcher - or worse, a full-price generation that silently
          ignored the reference. This is REFERENCE_UNREACHABLE in
          docs/ai-video-pipeline.md 13.
        * **control of the request.** Some hosts reject anonymous fetchers
          (Wikimedia requires a descriptive User-Agent), and private buckets
          need headers the server will not send.
        """
        import httpx

        if not 4 <= duration_seconds <= 15:
            raise ValueError("duration_seconds must be between 4 and 15")

        conditions = list(conditions or [])
        if stage_references:
            conditions = self._stage_references(conditions)

        body = {
            "task": self.variant,
            "prompt": prompt,
            "conditions": conditions,
            # 768 is the ceiling for the open weights. 2K needs H3-Regenerate-2K,
            # which is not released — see docs/minimax-h3-model.md §5.
            "target": {
                "short_edge": 768,
                "aspect_ratio": aspect_ratio,
                "duration_seconds": duration_seconds,
            },
            "seed": seed,
        }

        started = time.monotonic()
        with httpx.Client(base_url=self.base_url, timeout=120) as client:
            created = client.post("/v1/videos", json=body)
            if created.status_code >= 400:
                # Re-raise as a plain builtin. An httpx.HTTPStatusError cannot be
                # deserialized by a caller that lacks httpx, which turns a clear
                # 400 into "Could not deserialize remote exception".
                raise RuntimeError(
                    f"POST /v1/videos -> {created.status_code}: {created.text[:1000]}"
                )
            video_id = created.json()["id"]
            print(f"submitted {video_id}", flush=True)

            status = "unknown"
            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                time.sleep(poll_seconds)
                poll = client.get(f"/v1/videos/{video_id}")
                if poll.status_code >= 400:
                    raise RuntimeError(
                        f"GET /v1/videos/{video_id} -> {poll.status_code}: {poll.text[:500]}"
                    )
                payload = poll.json()
                status = payload.get("status", "unknown")
                if status in {"completed", "succeeded"}:
                    break
                if status in {"failed", "cancelled", "error"}:
                    raise RuntimeError(f"generation {status}: {json.dumps(payload)[:500]}")
            else:
                raise TimeoutError(f"generation {video_id} still {status} after {timeout_seconds}s")

            content = client.get(f"/v1/videos/{video_id}/content")
            if content.status_code >= 400:
                raise RuntimeError(
                    f"GET /v1/videos/{video_id}/content -> {content.status_code}: "
                    f"{content.text[:500]}"
                )
            mp4 = content.content

        elapsed = round(time.monotonic() - started, 1)
        print(f"{video_id} {status} in {elapsed}s, {len(mp4) / 1e6:.2f} MB", flush=True)
        return {
            "video_id": video_id,
            "status": status,
            "mp4": mp4,
            "bytes": len(mp4),
            "wall_seconds": elapsed,
            "duration_seconds": duration_seconds,
        }

    @modal.method()
    def reproduce(self, poll_seconds: float = 5.0, timeout_seconds: float = 45 * 60) -> dict:
        """Run MiniMax's own published Ref2VA case against this deployment.

        Fetches the vendor's reproducible script from the model repo and replays
        its exact payload, rather than embedding a copy that can drift. If this
        produces a video, the whole stack - weights, parallelism, serving
        protocol - is correct, and any difference is ours rather than theirs.
        """
        import re

        import httpx

        script_url = (
            "https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/"
            "scripts/readme/reproducible-768p-ref2va-request.sh"
        )
        script = httpx.get(script_url, timeout=60, follow_redirects=True).text
        match = re.search(r"<<'JSON'\n(.*?)\nJSON", script, re.S)
        if not match:
            raise RuntimeError("could not extract the JSON payload from the vendor script")
        body = json.loads(match.group(1))
        print(f"replaying vendor payload: task={body.get('task')} "
              f"conditions={len(body.get('conditions', []))} "
              f"target={body.get('target')}", flush=True)

        started = time.monotonic()
        with httpx.Client(base_url=self.base_url, timeout=120) as client:
            created = client.post("/v1/videos", json=body)
            if created.status_code >= 400:
                raise RuntimeError(
                    f"POST /v1/videos -> {created.status_code}: {created.text[:1000]}"
                )
            video_id = created.json()["id"]
            print(f"submitted {video_id}", flush=True)

            status = "unknown"
            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                time.sleep(poll_seconds)
                poll = client.get(f"/v1/videos/{video_id}")
                payload = poll.json() if poll.status_code < 400 else {}
                status = payload.get("status", "unknown")
                if status in {"completed", "succeeded"}:
                    break
                if status in {"failed", "cancelled", "error"}:
                    raise RuntimeError(f"generation {status}: {json.dumps(payload)[:800]}")
            else:
                raise TimeoutError(f"still {status} after {timeout_seconds}s")

            mp4 = client.get(f"/v1/videos/{video_id}/content").content

        elapsed = round(time.monotonic() - started, 1)
        print(f"{video_id} {status} in {elapsed}s, {len(mp4) / 1e6:.2f} MB", flush=True)
        return {"video_id": video_id, "status": status, "mp4": mp4,
                "bytes": len(mp4), "wall_seconds": elapsed}

    @modal.exit()
    def stop_server(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()


# --- Smoke test ------------------------------------------------------------

# Minimal but correctly shaped: the six-section structure H3-Base expects when
# there is no H3-Context-IR in front of it.
SMOKE_PROMPT = """subject_definitions:
<Subject 1> is a matte black glass perfume bottle with a squared silhouette and a stone-inlaid cap, standing upright.

summary:
[reference generation] A short luxury product advertisement for <Subject 1>.

retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - the bottle's silhouette, matte finish and cap geometry are unchanged.
environment: reference - newly generated, not taken from any reference.

detailed_description:
The target video is in realistic photographic style.
[Shot 1] A macro three-quarter view of <Subject 1> standing on wet black marble. Warm golden key light rakes in from camera left, throwing an amber caustic across the stone. The camera performs a slow dolly-in on a 35mm lens with shallow depth of field. Fine water droplets bead and slide down the bottle's left face. The light steadies as the camera settles and holds through the end of the video.

overall_soundscape:
Close, dry room tone with a single low water droplet impact partway through. No voices, no footsteps.

non_diegetic_music:
A sparse, slow cello line beneath a low synth pad, entering early and resolving at the end."""


@app.local_entrypoint()
def smoke(variant: str = "ref2va", tensor_parallel: int = 4, duration: int = 5) -> None:
    """Cold-start one server, generate one clip, and report the numbers that matter.

    ``wall_seconds`` here is *T* in the break-even table in
    docs/ai-video-pipeline.md §12. Everything downstream depends on it.
    """
    server = H3Server(variant=variant, tensor_parallel=tensor_parallel)

    started = time.monotonic()
    result = server.generate.remote(prompt=SMOKE_PROMPT, duration_seconds=duration, seed=42)
    total = time.monotonic() - started

    out = f"h3-{variant}-{duration}s.mp4"
    with open(out, "wb") as fh:
        fh.write(result["mp4"])

    print("\n--- smoke result ---")
    print(f"  variant           {variant}")
    print(f"  parallelism       {'tp-size ' + str(tensor_parallel) if tensor_parallel else 'ulysses-degree 4'}")
    print(f"  clip length       {duration}s")
    print(f"  generate (warm)   {result['wall_seconds']}s   <- T")
    print(f"  total incl. cold  {total:.1f}s")
    print(f"  output            {out}  ({result['bytes'] / 1e6:.2f} MB)")


@app.local_entrypoint()
def reproduce(tensor_parallel: int = 4) -> None:
    """Replay MiniMax's published Ref2VA case. The stack-correctness check."""
    server = H3Server(variant="ref2va", tensor_parallel=tensor_parallel)
    started = time.monotonic()
    result = server.reproduce.remote()
    total = time.monotonic() - started

    out = "h3-vendor-ref2va.mp4"
    with open(out, "wb") as fh:
        fh.write(result["mp4"])
    print("\n--- vendor reproduction ---")
    print(f"  generate (warm)   {result['wall_seconds']}s   <- T")
    print(f"  total incl. cold  {total:.1f}s")
    print(f"  output            {out}  ({result['bytes'] / 1e6:.2f} MB)")


# --- Product-reference smoke test ------------------------------------------

# The real product path: one uploaded product image + text, which is what a
# campaign owner actually does. Kept separate from the vendor reproduction
# because it measures a different (and lighter) conditioning workload.
PRODUCT_REFERENCE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/"
    "Perfume_Bottle_%2848708706252%29.jpg/1280px-Perfume_Bottle_%2848708706252%29.jpg"
)

PRODUCT_PROMPT = """subject_definitions:
<Subject 1> is the spherical art-glass perfume bottle in reference image 1: a dark, rounded body with an iridescent metallic surface shifting between deep blue, violet and gold, scattered orange-red speckles, and fine black crackle lines running across the glass. It is topped by a clear, colourless glass stopper shaped like curved leaves or petals.

summary:
[reference generation] A short luxury product advertisement featuring <Subject 1>.

retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - the spherical silhouette, iridescent blue-violet-gold surface, orange-red speckling, black crackle lines and the clear leaf-shaped glass stopper all remain unchanged.
environment: reference - newly generated, not taken from any reference.

detailed_description:
The target video is in realistic photographic style with a shallow depth of field.
[Shot 1] A macro three-quarter view of <Subject 1> resting on polished black stone. A warm golden key light rakes in from camera left, igniting the iridescent surface so the blue, violet and gold shift as the light moves, and throwing a soft amber reflection across the stone beneath. The clear glass stopper catches a bright specular highlight along its upper edge. The camera performs a slow dolly-in on a 35mm lens.
[Shot 2] Cut to a centred medium close-up still holding <Subject 1>, now lit more evenly so the orange-red speckles and black crackle lines read clearly across the sphere. The camera settles and holds steady through the end of the video as the light softens.

overall_soundscape:
Close, dry room tone. A single soft glass chime as the light shifts between shots. No voices, no footsteps.

non_diegetic_music:
A sparse, slow cello line beneath a low synth pad, entering early and resolving at the end."""


@app.local_entrypoint()
def product(duration: int = 5, tensor_parallel: int = 4, seed: int = 42) -> None:
    """Measure the image-reference path - the workload this product actually runs."""
    server = H3Server(variant="ref2va", tensor_parallel=tensor_parallel)
    conditions = [{"type": "image", "uri": PRODUCT_REFERENCE_URL, "role": "reference"}]

    started = time.monotonic()
    result = server.generate.remote(
        prompt=PRODUCT_PROMPT,
        conditions=conditions,
        duration_seconds=duration,
        aspect_ratio="9:16",
        seed=seed,
    )
    total = time.monotonic() - started

    out = f"h3-product-{duration}s.mp4"
    with open(out, "wb") as fh:
        fh.write(result["mp4"])

    print("\n--- product reference smoke ---")
    print(f"  references        1 image")
    print(f"  aspect ratio      9:16")
    print(f"  clip length       {duration}s")
    print(f"  generate (warm)   {result['wall_seconds']}s   <- T (image-reference path)")
    print(f"  total incl. cold  {total:.1f}s")
    print(f"  output            {out}  ({result['bytes'] / 1e6:.2f} MB)")
