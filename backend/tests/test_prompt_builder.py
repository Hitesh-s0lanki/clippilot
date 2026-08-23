"""The prompt builder compiles a brief into MiniMax H3's six-section format.

Pure-function tests: no database, no GPU, no API key. That is the point of
building this piece first - the whole compilation path is verifiable before a
single provider exists.

The rules under test come from MiniMax's published format
(docs/minimax-h3-model.md 9). Getting them wrong does not raise; it silently
produces a video in which the product drifts between shots.
"""

import pytest

from src.schemas.enums import (
    CampaignObjective,
    GenerationAssetKind,
    GenerationAssetRole,
    SpecialCategory,
    VideoAspectRatio,
)
from src.services.prompt_builder import (
    PromptBrief,
    PromptReference,
    assign_labels,
    compile_prompt,
)

SECTIONS = (
    "subject_definitions:",
    "summary:",
    "retention_analysis:",
    "detailed_description:",
    "overall_soundscape:",
    "non_diegetic_music:",
)


def image(note: str | None = "a matte black perfume bottle") -> PromptReference:
    return PromptReference(kind=GenerationAssetKind.IMAGE, subject_note=note)


def brief(**overrides) -> PromptBrief:
    defaults = dict(
        user_prompt="A cinematic luxury advertisement lit by warm golden light on black marble.",
        duration_seconds=10,
        references=[image()],
    )
    return PromptBrief(**{**defaults, **overrides})


class TestStructure:
    def test_all_six_sections_present_in_order(self) -> None:
        text = compile_prompt(brief()).text
        positions = [text.index(section) for section in SECTIONS]
        assert positions == sorted(positions), "sections must appear in the published order"

    def test_text_only_omits_the_reference_sections(self) -> None:
        """With no references there is nothing to define or retain.

        Emitting empty headings would be noise; MiniMax documents a separate
        base-mode guide for text-only generation.
        """
        text = compile_prompt(brief(references=[])).text
        assert "subject_definitions:" not in text
        assert "retention_analysis:" not in text
        for section in ("summary:", "detailed_description:", "overall_soundscape:"):
            assert section in text

    def test_user_prompt_is_carried_verbatim(self) -> None:
        sentence = "A slow dolly-in across wet obsidian under a single warm key light."
        assert sentence in compile_prompt(brief(user_prompt=sentence)).text


class TestLabels:
    def test_numbered_within_each_kind(self) -> None:
        refs = [
            image(),
            PromptReference(kind=GenerationAssetKind.VIDEO, duration_seconds=5),
            image(),
            PromptReference(kind=GenerationAssetKind.AUDIO, duration_seconds=5),
        ]
        assert assign_labels(refs) == ["Subject 1", "Video 1", "Subject 2", "Audio 1"]

    def test_every_visual_label_is_cited_in_the_description(self) -> None:
        """An uncited reference is one the model has no instruction to place."""
        compiled = compile_prompt(brief(references=[image("the bottle"), image("the wordmark")]))
        description = compiled.text.split("detailed_description:")[1].split("overall_soundscape:")[
            0
        ]
        for label in compiled.labels:
            assert f"<{label}>" in description, f"<{label}> declared but never cited"

    def test_every_label_is_defined_and_retained(self) -> None:
        compiled = compile_prompt(brief(references=[image("the bottle"), image("the wordmark")]))
        definitions = compiled.text.split("subject_definitions:")[1].split("summary:")[0]
        retention = compiled.text.split("retention_analysis:")[1].split("detailed_description:")[0]
        for label in compiled.labels:
            assert f"<{label}>" in definitions
            assert f"<{label}>" in retention


class TestTaskTypes:
    def test_reference_generation_for_image_references(self) -> None:
        assert "[reference generation]" in compile_prompt(brief()).text

    def test_keyframe_completion_for_first_frame(self) -> None:
        ref = PromptReference(kind=GenerationAssetKind.IMAGE, role=GenerationAssetRole.FIRST_FRAME)
        assert "[keyframe completion]" in compile_prompt(brief(references=[ref])).text

    def test_audio_reference_is_declared_alongside(self) -> None:
        refs = [image(), PromptReference(kind=GenerationAssetKind.AUDIO, duration_seconds=4)]
        text = compile_prompt(brief(references=refs)).text
        assert "[reference generation + audio reference]" in text


class TestShotCount:
    @pytest.mark.parametrize(
        ("duration", "expected"),
        [(4, 1), (6, 1), (7, 1), (8, 2), (11, 2), (12, 3), (15, 3)],
    )
    def test_shots_scale_with_duration(self, duration: int, expected: int) -> None:
        """A 5s clip cut three ways is unwatchable; 15s supports three shots."""
        text = compile_prompt(brief(duration_seconds=duration)).text
        headers = [ln for ln in text.splitlines() if ln.startswith("[Shot ")]
        assert len(headers) == expected


class TestCampaignContext:
    def test_objective_changes_the_shot_grammar(self) -> None:
        conversion = compile_prompt(brief(objective=CampaignObjective.CONVERSION)).text
        awareness = compile_prompt(brief(objective=CampaignObjective.AWARENESS)).text
        assert "end card" in conversion
        assert "end card" not in awareness
        assert conversion != awareness

    def test_portrait_ratio_adds_a_framing_instruction(self) -> None:
        portrait = compile_prompt(brief(aspect_ratio=VideoAspectRatio.NINE_SIXTEEN)).text
        landscape = compile_prompt(brief(aspect_ratio=VideoAspectRatio.SIXTEEN_NINE)).text
        assert "vertical" in portrait
        assert "horizontal" in landscape

    def test_headline_becomes_an_on_screen_text_instruction(self) -> None:
        text = compile_prompt(brief(headline="Discover the new scent")).text
        assert '"Discover the new scent"' in text
        assert "legible" in text

    def test_subject_note_drives_retention(self) -> None:
        note = "the embossed logo and stone-inlaid cap"
        retention = compile_prompt(brief(references=[image(note)])).text.split(
            "retention_analysis:"
        )[1]
        assert note in retention
        assert "fully_preserved" in retention


class TestAudio:
    def test_audio_reference_timbre_is_cited(self) -> None:
        refs = [image(), PromptReference(kind=GenerationAssetKind.AUDIO, duration_seconds=4)]
        text = compile_prompt(brief(references=refs)).text
        assert "<Audio 1>" in text.split("overall_soundscape:")[1]

    def test_audio_only_references_are_rejected(self) -> None:
        """H3 refuses audio that does not accompany an image or video."""
        refs = [PromptReference(kind=GenerationAssetKind.AUDIO, duration_seconds=4)]
        with pytest.raises(ValueError, match="must accompany"):
            compile_prompt(brief(references=refs))

    def test_with_audio_false_asks_for_a_quiet_bed(self) -> None:
        """H3 always generates audio, so silence is requested, not omitted."""
        text = compile_prompt(brief(with_audio=False)).text
        assert "No voices and no music." in text


class TestWarnings:
    def test_missing_subject_note_warns(self) -> None:
        warnings = compile_prompt(brief(references=[image(None)])).warnings
        assert any("no note" in w for w in warnings)

    def test_thin_brief_warns(self) -> None:
        warnings = compile_prompt(brief(user_prompt="make it nice")).warnings
        assert any("very short" in w for w in warnings)

    def test_special_category_warns_disclaimer_is_not_generated(self) -> None:
        """Compliance copy changes; text burnt into pixels cannot be corrected."""
        warnings = compile_prompt(
            brief(special_category=SpecialCategory.FINANCIAL_PRODUCTS_SERVICES)
        ).warnings
        assert any("disclaimer" in w for w in warnings)

    def test_a_good_brief_produces_no_warnings(self) -> None:
        assert compile_prompt(brief()).warnings == []


class TestPersonalisation:
    def test_merge_tags_are_not_the_builders_job(self) -> None:
        """One video per campaign; {{customer_name}} is resolved into the DOM.

        Per-recipient generation multiplies cost by the audience size, so the
        merge tag must never reach the model - it stays literal here and is
        substituted at render time.
        """
        text = compile_prompt(brief(headline="Hi {{customer_name}}")).text
        assert "{{customer_name}}" in text
