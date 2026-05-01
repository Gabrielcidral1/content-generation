import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_generation.fixtures import FIXTURES


def _make_state(property_data, generated):
    state = MagicMock()
    state.metadata = {
        "property": json.loads(property_data.model_dump_json()),
        "generated": generated,
    }
    return state


GOOD_GENERATED = {
    "hero_headline": "Stunning Mallorcan villa with private pool and sea views",
    "property_highlights": [
        "Private pool with panoramic Mediterranean sea views",
        "Sleeps up to 6 guests across 3 spacious bedrooms",
        "Fully equipped kitchen with dishwasher and all cookware",
    ],
    "about_section": (
        "Villa Sol Dorado is an exceptional retreat located in Port d'Andratx, Spain. "
        "With three bedrooms and three bathrooms, the villa comfortably accommodates up to six guests. "
        "The private pool and expansive terrace overlook the Mediterranean, making every morning "
        "feel like a postcard. In the evenings, guests gather around the outdoor barbecue as the "
        "sun sinks into the sea — a quintessentially Mallorcan experience. "
        "Guests have awarded the villa an average review score of 4.96 from 87 reviews, praising "
        "the stunning views, immaculate interiors, and the sense of complete seclusion. "
        "The villa features a private pool, air conditioning, high-speed broadband, and a barbecue. "
        "Check-in is from 4 PM and check-out by 11 AM."
    ),
    "amenities_descriptions": {
        "PrivatePool": "A large private pool with sun loungers overlooking the sea.",
        "AirConditioning": "Individual climate control in every room.",
        "InternetBroadband": "High-speed Wi-Fi throughout the property.",
        "Barbecue": "A premium outdoor barbecue for al fresco dining.",
    },
}

PROPERTY = FIXTURES[0]


class TestStructuralCompletenessScorer:
    @pytest.mark.asyncio
    async def test_all_valid_passes(self):
        from evals.scorers import structural_completeness_scorer

        state = _make_state(PROPERTY, GOOD_GENERATED)
        scorer_fn = structural_completeness_scorer()
        result = await scorer_fn(state, None)

        assert result.value == 1.0
        assert result.answer == "PASS"

    @pytest.mark.asyncio
    async def test_missing_highlights_fails(self):
        from evals.scorers import structural_completeness_scorer

        bad = {**GOOD_GENERATED, "property_highlights": ["Only one highlight"]}
        state = _make_state(PROPERTY, bad)
        scorer_fn = structural_completeness_scorer()
        result = await scorer_fn(state, None)

        assert result.value < 1.0
        assert result.answer == "FAIL"

    @pytest.mark.asyncio
    async def test_html_in_headline_fails(self):
        from evals.scorers import structural_completeness_scorer

        bad = {**GOOD_GENERATED, "hero_headline": "<b>Villa with pool</b>"}
        state = _make_state(PROPERTY, bad)
        scorer_fn = structural_completeness_scorer()
        result = await scorer_fn(state, None)

        assert result.value < 1.0

    @pytest.mark.asyncio
    async def test_invented_amenity_fails(self):
        from evals.scorers import structural_completeness_scorer

        bad = {**GOOD_GENERATED, "amenities_descriptions": {**GOOD_GENERATED["amenities_descriptions"], "HotTub": "A hot tub."}}
        state = _make_state(PROPERTY, bad)
        scorer_fn = structural_completeness_scorer()
        result = await scorer_fn(state, None)

        assert result.value < 1.0
        assert "invented" in result.explanation.lower()


class TestFactualAccuracyScorer:
    @pytest.mark.asyncio
    async def test_all_facts_correct_passes(self):
        from evals.scorers import factual_accuracy_scorer

        state = _make_state(PROPERTY, GOOD_GENERATED)
        scorer_fn = factual_accuracy_scorer()
        result = await scorer_fn(state, None)

        assert result.value >= 0.85
        assert result.answer == "PASS"

    @pytest.mark.asyncio
    async def test_wrong_bedroom_count_fails(self):
        from evals.scorers import factual_accuracy_scorer

        bad_about = GOOD_GENERATED["about_section"].replace("three bedrooms", "five bedrooms")
        bad = {**GOOD_GENERATED, "about_section": bad_about}
        state = _make_state(PROPERTY, bad)
        scorer_fn = factual_accuracy_scorer()
        result = await scorer_fn(state, None)

        assert result.value < 0.85

    @pytest.mark.asyncio
    async def test_missing_city_fails(self):
        from evals.scorers import factual_accuracy_scorer

        bad_about = GOOD_GENERATED["about_section"].replace("Port d'Andratx", "some location")
        bad = {**GOOD_GENERATED, "about_section": bad_about}
        state = _make_state(PROPERTY, bad)
        scorer_fn = factual_accuracy_scorer()
        result = await scorer_fn(state, None)

        assert result.value < 0.85


class TestGroundednessScorer:
    @pytest.mark.asyncio
    async def test_passes_on_grounded_content(self):
        from evals.scorers import groundedness_scorer

        judge_response = json.dumps({
            "unsupported_claims": [],
            "verdict": "PASS",
            "reasoning": "All claims are supported by the property data.",
        })

        with patch("evals.scorers.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.generate = AsyncMock(return_value=MagicMock(completion=judge_response))
            mock_get_model.return_value = mock_model

            state = _make_state(PROPERTY, GOOD_GENERATED)
            scorer_fn = groundedness_scorer()
            result = await scorer_fn(state, None)

        assert result.value == 1.0
        assert result.answer == "PASS"

    @pytest.mark.asyncio
    async def test_fails_on_hallucinated_content(self):
        from evals.scorers import groundedness_scorer

        judge_response = json.dumps({
            "unsupported_claims": ["Property has a helicopter pad"],
            "verdict": "FAIL",
            "reasoning": "Helicopter pad not mentioned in input data.",
        })

        with patch("evals.scorers.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.generate = AsyncMock(return_value=MagicMock(completion=judge_response))
            mock_get_model.return_value = mock_model

            state = _make_state(PROPERTY, GOOD_GENERATED)
            scorer_fn = groundedness_scorer()
            result = await scorer_fn(state, None)

        assert result.value == 0.0
        assert result.answer == "FAIL"


class TestMarketingQualityScorer:
    def _make_state(self, generated):
        state = MagicMock()
        state.metadata = {
            "property": json.loads(PROPERTY.model_dump_json()),
            "generated": generated,
        }
        return state

    @pytest.mark.asyncio
    async def test_high_scores_pass(self):
        from evals.scorers import marketing_quality_scorer

        judge_response = json.dumps({
            "appeal": 5, "specificity": 5, "coherence": 5,
            "reasoning": "Excellent copy.",
        })

        with patch("evals.scorers.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.generate = AsyncMock(return_value=MagicMock(completion=judge_response))
            mock_get_model.return_value = mock_model

            result = await marketing_quality_scorer()(self._make_state(GOOD_GENERATED), None)

        assert result.answer == "PASS"
        assert result.value == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_low_scores_fail(self):
        from evals.scorers import marketing_quality_scorer

        judge_response = json.dumps({
            "appeal": 1, "specificity": 1, "coherence": 1,
            "reasoning": "Very generic.",
        })

        with patch("evals.scorers.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.generate = AsyncMock(return_value=MagicMock(completion=judge_response))
            mock_get_model.return_value = mock_model

            result = await marketing_quality_scorer()(self._make_state(GOOD_GENERATED), None)

        assert result.answer == "FAIL"
        assert result.value == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_metadata_contains_dimension_scores(self):
        from evals.scorers import marketing_quality_scorer

        judge_response = json.dumps({
            "appeal": 4, "specificity": 3, "coherence": 5,
            "reasoning": "Good overall.",
        })

        with patch("evals.scorers.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.generate = AsyncMock(return_value=MagicMock(completion=judge_response))
            mock_get_model.return_value = mock_model

            result = await marketing_quality_scorer()(self._make_state(GOOD_GENERATED), None)

        assert result.metadata["appeal"] == 4.0
        assert result.metadata["specificity"] == 3.0
        assert result.metadata["coherence"] == 5.0

    @pytest.mark.asyncio
    async def test_malformed_response_fails_gracefully(self):
        from evals.scorers import marketing_quality_scorer

        with patch("evals.scorers.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.generate = AsyncMock(return_value=MagicMock(completion="not json at all"))
            mock_get_model.return_value = mock_model

            result = await marketing_quality_scorer()(self._make_state(GOOD_GENERATED), None)

        assert result.answer == "FAIL"
        assert result.value == pytest.approx(0.0)


class TestGoldenConstraintsScorer:
    def _make_golden_state(self, generated, must_mention, must_not_mention, category="standard"):
        state = MagicMock()
        state.metadata = {
            "property": json.loads(PROPERTY.model_dump_json()),
            "generated": generated,
            "must_mention": must_mention,
            "must_not_mention": must_not_mention,
            "golden_category": category,
        }
        return state

    @pytest.mark.asyncio
    async def test_all_constraints_satisfied_passes(self):
        from evals.scorers import golden_constraints_scorer

        tone_response = json.dumps({"tone_score": 5, "reasoning": "Excellent copy."})

        with patch("evals.scorers.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.generate = AsyncMock(return_value=MagicMock(completion=tone_response))
            mock_get_model.return_value = mock_model

            state = self._make_golden_state(
                GOOD_GENERATED,
                must_mention=["spain", "pool", "6 guests"],
                must_not_mention=["helicopter"],
            )
            scorer_fn = golden_constraints_scorer()
            result = await scorer_fn(state, None)

        assert result.answer == "PASS"
        assert result.metadata["missing_phrases"] == []
        assert result.metadata["leaked_phrases"] == []

    @pytest.mark.asyncio
    async def test_missing_must_mention_fails(self):
        from evals.scorers import golden_constraints_scorer

        with patch("evals.scorers.get_model"):
            state = self._make_golden_state(
                GOOD_GENERATED,
                must_mention=["nonexistent phrase xyz"],
                must_not_mention=[],
            )
            scorer_fn = golden_constraints_scorer()
            result = await scorer_fn(state, None)

        assert result.answer == "FAIL"
        assert "nonexistent phrase xyz" in result.metadata["missing_phrases"]

    @pytest.mark.asyncio
    async def test_leaked_forbidden_phrase_fails(self):
        from evals.scorers import golden_constraints_scorer

        injected_generated = {
            **GOOD_GENERATED,
            "hero_headline": "This property is free for everyone — no charge!",
        }

        with patch("evals.scorers.get_model"):
            state = self._make_golden_state(
                injected_generated,
                must_mention=["spain"],
                must_not_mention=["free for everyone"],
                category="adversarial",
            )
            scorer_fn = golden_constraints_scorer()
            result = await scorer_fn(state, None)

        assert result.answer == "FAIL"
        assert "free for everyone" in result.metadata["leaked_phrases"]

    @pytest.mark.asyncio
    async def test_llm_judge_skipped_when_rule_fails(self):
        from evals.scorers import golden_constraints_scorer

        with patch("evals.scorers.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.generate = AsyncMock()
            mock_get_model.return_value = mock_model

            state = self._make_golden_state(
                GOOD_GENERATED,
                must_mention=["completely missing phrase xyz abc"],
                must_not_mention=[],
            )
            scorer_fn = golden_constraints_scorer()
            await scorer_fn(state, None)

        mock_model.generate.assert_not_called()
