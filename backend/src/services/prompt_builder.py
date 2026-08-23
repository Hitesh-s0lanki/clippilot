"""Compile a campaign brief into the structured prompt MiniMax H3 expects.

H3 is not prompted in prose. MiniMax ships a six-section format, and the hosted
API puts ``H3-Context-IR`` in front of the model to produce it from a casual
sentence. **That component is not open-weight**, so a self-hosted deployment
gets no such help and the structure has to be built here. Even against the
hosted API the compiled form is better: it states reference roles explicitly,
which is what stops a product drifting between shots.

The format, in order (docs/minimax-h3-model.md 9):

1. ``subject_definitions``  - declare each reference, its source and its role
2. ``summary``              - bracketed task types
3. ``retention_analysis``   - what must survive unchanged
4. ``detailed_description`` - shot by shot
5. ``overall_soundscape``   - diegetic sound
6. ``non_diegetic_music``   - score

This module is deliberately pure: campaign facts in, string out. No database,
no HTTP, no provider. That is what makes it testable without a GPU or an API
key, and it is why it is the first thing built.
"""

from dataclasses import dataclass, field

from src.schemas.enums import (
    CampaignObjective,
    GenerationAssetKind,
    GenerationAssetRole,
    SpecialCategory,
    VideoAspectRatio,
)

# How the campaign's objective changes the shot grammar. The objective already
# decides what "performing well" means for analytics; here it decides how the
# ad is shot, so the two stay consistent.
SHOT_GRAMMAR: dict[CampaignObjective, str] = {
    CampaignObjective.AWARENESS: (
        "Open wide and atmospheric, letting the setting establish mood before the subject "
        "is resolved. Favour slow, continuous camera movement."
    ),
    CampaignObjective.ENGAGEMENT: (
        "Keep the subject central and legible throughout. Favour a steady push-in that "
        "invites the viewer to look closer."
    ),
    CampaignObjective.LEAD_CAPTURE: (
        "Lead with the subject in close-up so it reads within the first second, then widen "
        "just enough to show context."
    ),
    CampaignObjective.CONVERSION: (
        "Product-forward throughout. Hold the subject centred and end on a clean, static "
        "composition with space in frame for an end card."
    ),
    CampaignObjective.RETENTION: (
        "Warm and familiar. Favour soft light and an unhurried, almost still camera."
    ),
}

# Ratios that imply a phone-first crop, where the subject must stay centred.
PORTRAIT_RATIOS = frozenset({VideoAspectRatio.NINE_SIXTEEN, VideoAspectRatio.THREE_FOUR})

# Below this, there is only room for one shot.
SINGLE_SHOT_MAX_SECONDS = 7
# Above this, a third shot is worth having.
THREE_SHOT_MIN_SECONDS = 12

LABEL_BY_KIND = {
    GenerationAssetKind.IMAGE: "Subject",
    GenerationAssetKind.VIDEO: "Video",
    GenerationAssetKind.AUDIO: "Audio",
}


@dataclass(slots=True)
class PromptReference:
    """One reference file as the builder sees it."""

    kind: GenerationAssetKind
    role: GenerationAssetRole = GenerationAssetRole.REFERENCE
    # The user's own words for what must not change. The highest-leverage
    # field on the form: it becomes retention_analysis.
    subject_note: str | None = None
    duration_seconds: int | None = None


@dataclass(slots=True)
class PromptBrief:
    """Everything the builder needs. Assembled from the campaign and the form."""

    user_prompt: str
    duration_seconds: int
    aspect_ratio: VideoAspectRatio = VideoAspectRatio.NINE_SIXTEEN
    objective: CampaignObjective = CampaignObjective.ENGAGEMENT
    special_category: SpecialCategory = SpecialCategory.NONE
    headline: str | None = None
    references: list[PromptReference] = field(default_factory=list)
    with_audio: bool = True


@dataclass(slots=True)
class CompiledPrompt:
    text: str
    labels: list[str]
    # Advisory notes for the UI: things the user could fix to get a better
    # result. Never blocking - a thin brief still generates.
    warnings: list[str] = field(default_factory=list)


def label_for(kind: GenerationAssetKind, ordinal: int) -> str:
    """``<Subject 1>``, ``<Video 2>``, ``<Audio 1>`` - the citation form."""
    return f"{LABEL_BY_KIND[kind]} {ordinal}"


def assign_labels(references: list[PromptReference]) -> list[str]:
    """Number each reference within its own kind, in submission order."""
    counters: dict[GenerationAssetKind, int] = {}
    labels: list[str] = []
    for reference in references:
        counters[reference.kind] = counters.get(reference.kind, 0) + 1
        labels.append(label_for(reference.kind, counters[reference.kind]))
    return labels


def _shot_count(duration_seconds: int) -> int:
    if duration_seconds <= SINGLE_SHOT_MAX_SECONDS:
        return 1
    if duration_seconds < THREE_SHOT_MIN_SECONDS:
        return 2
    return 3


def _task_types(references: list[PromptReference]) -> list[str]:
    """The bracketed declarations that open the summary section."""
    kinds = {r.kind for r in references}
    roles = {r.role for r in references}

    types: list[str] = []
    if roles & {GenerationAssetRole.FIRST_FRAME, GenerationAssetRole.LAST_FRAME}:
        types.append("keyframe completion")
    elif kinds & {GenerationAssetKind.IMAGE, GenerationAssetKind.VIDEO}:
        types.append("reference generation")
    if GenerationAssetKind.AUDIO in kinds:
        types.append("audio reference")
    return types or ["reference generation"]


def _subject_definitions(references: list[PromptReference], labels: list[str]) -> str:
    lines = []
    for reference, label in zip(references, labels, strict=True):
        note = reference.subject_note or "the subject shown in this reference"
        if reference.role is GenerationAssetRole.FIRST_FRAME:
            source = "the opening frame of the target video"
        elif reference.role is GenerationAssetRole.LAST_FRAME:
            source = "the closing frame of the target video"
        elif reference.kind is GenerationAssetKind.AUDIO:
            source = "the audio timbre reference"
        elif reference.kind is GenerationAssetKind.VIDEO:
            source = "the motion and camera reference"
        else:
            source = "the identity reference"
        lines.append(f"<{label}> is {source}: {note}.")
    return "\n".join(lines)


def _retention_analysis(references: list[PromptReference], labels: list[str], shots: int) -> str:
    # Cite the shots the subject is actually in. Claiming [Shot 1] for a
    # subject that carries all three tells the model the wrong thing about
    # where identity has to hold.
    appears_in = ", ".join(f"[Shot {n}]" for n in range(1, shots + 1))
    lines = []
    for reference, label in zip(references, labels, strict=True):
        if reference.kind is GenerationAssetKind.AUDIO:
            lines.append(f"<{label}>: reference - the target audio references this timbre.")
            continue
        note = reference.subject_note or "its appearance, proportions and colour"
        lines.append(
            f"<{label}> (appears in {appears_in}): fully_preserved - {note} must remain unchanged."
        )
    lines.append("environment: reference - newly generated, not taken from any reference.")
    return "\n".join(lines)


def _detailed_description(brief: PromptBrief, labels: list[str]) -> str:
    visual = [
        label
        for label, reference in zip(labels, brief.references, strict=True)
        if reference.kind is not GenerationAssetKind.AUDIO
    ]
    # What the shots are *about*. With no visual reference the user's own words
    # carry the subject.
    subject = f"<{visual[0]}>" if visual else "the subject"

    shots = _shot_count(brief.duration_seconds)
    grammar = SHOT_GRAMMAR[brief.objective]
    framing = (
        "Keep the subject centred and clear of the top and bottom edges, since the frame is "
        "vertical."
        if brief.aspect_ratio in PORTRAIT_RATIOS
        else "Compose for a horizontal frame."
    )

    lines = [
        "The target video is in realistic photographic style with a shallow depth of field.",
        f"[Shot 1] {brief.user_prompt} {subject} is the subject of this shot. {grammar} {framing}",
    ]
    if shots >= 2:
        lines.append(
            f"[Shot 2] Cut to a closer view still holding {subject}, matching the lighting and "
            f"styling of [Shot 1] so the subject reads as the same object."
        )
    if shots >= 3:
        lines.append(
            f"[Shot 3] Cut to a centred medium composition holding {subject}. The camera settles "
            f"and holds steady through the end of the video."
        )

    # Every declared label must be cited where its role applies - an
    # uncited reference is one the model has no instruction to place.
    for extra in visual[1:]:
        lines.append(
            f"<{extra}> appears in the final third, composed clearly within the frame and "
            f"holding its exact appearance from the reference."
        )

    if brief.headline:
        lines.append(
            f'Near the end, the text "{brief.headline}" appears cleanly in frame, correctly '
            f"spelled and fully legible."
        )
    return "\n".join(lines)


def _soundscape(brief: PromptBrief, labels: list[str]) -> tuple[str, str]:
    audio = [
        label
        for label, reference in zip(labels, brief.references, strict=True)
        if reference.kind is GenerationAssetKind.AUDIO
    ]
    if not brief.with_audio:
        # H3 always generates audio; a silent ad is a product decision applied
        # downstream. Asking for a quiet bed beats asking for silence, which
        # the model has no clean way to represent.
        return ("Quiet, neutral room tone. No voices and no music.", "None.")

    diegetic = "Close, dry room tone with subtle material detail matching the subject."
    if audio:
        diegetic += f" The target references the timbre of <{audio[0]}>."
    music = "A sparse, slow instrumental bed that enters early and resolves at the end, mixed low."
    return diegetic, music


def compile_prompt(brief: PromptBrief) -> CompiledPrompt:
    """Build the six-section prompt. Pure: brief in, text out."""
    labels = assign_labels(brief.references)
    warnings: list[str] = []

    unnamed = sum(
        1
        for r in brief.references
        if r.kind is not GenerationAssetKind.AUDIO and not r.subject_note
    )
    if unnamed:
        warnings.append(
            f"{unnamed} reference(s) have no note describing what must not change. "
            "Naming the product, its shape and its markings measurably improves consistency."
        )
    if len(brief.user_prompt.split()) < 8:
        warnings.append(
            "The brief is very short. Describing the setting, lighting and camera movement "
            "gives the model more to work with than adjectives do."
        )
    if brief.special_category is not SpecialCategory.NONE:
        # The disclaimer stays a DOM overlay: text burnt into pixels cannot be
        # corrected without regenerating, and compliance copy changes.
        warnings.append(
            "This campaign is in a special category. The required disclaimer is rendered over "
            "the player and is deliberately not generated into the video."
        )

    audio_only = brief.references and all(
        r.kind is GenerationAssetKind.AUDIO for r in brief.references
    )
    if audio_only:
        raise ValueError("An audio reference must accompany at least one image or video reference.")

    diegetic, music = _soundscape(brief, labels)
    shots = _shot_count(brief.duration_seconds)

    sections: list[tuple[str, str]] = []
    if brief.references:
        # Reference mode. With no references there is nothing to define or
        # retain, and MiniMax documents a separate base-mode guide for that -
        # emitting empty headings would be noise the model has to ignore.
        sections.append(("subject_definitions", _subject_definitions(brief.references, labels)))
    summary_types = (
        " + ".join(_task_types(brief.references)) if brief.references else "text to video"
    )
    sections.append(("summary", f"[{summary_types}] {brief.user_prompt}"))
    if brief.references:
        sections.append(
            ("retention_analysis", _retention_analysis(brief.references, labels, shots))
        )
    sections.extend(
        [
            ("detailed_description", _detailed_description(brief, labels)),
            ("overall_soundscape", diegetic),
            ("non_diegetic_music", music),
        ]
    )
    text = "\n\n".join(f"{name}:\n{body}" for name, body in sections if body)

    return CompiledPrompt(text=text, labels=labels, warnings=warnings)
