import pytest
from pydantic import ValidationError

from content_generation.fixtures import FIXTURES
from content_generation.golden import GOLDEN_DATASET
from content_generation.models import (
    GoldenSampleCategory,
    MarketingContent,
    PropertyData,
)


class TestPropertyData:
    def test_fixture_parses_correctly(self, sample_property):
        assert sample_property.property_id == 1001
        assert sample_property.location.city == "Port d'Andratx"
        assert sample_property.rental_info.bedrooms == 3

    def test_all_fixtures_are_valid(self):
        for fixture in FIXTURES:
            assert isinstance(fixture, PropertyData)
            assert fixture.property_id > 0
            assert fixture.property_name
            assert len(fixture.amenities) > 0

    def test_html_fixture_exists(self):
        html_fixture = next(f for f in FIXTURES if f.property_id == 1006)
        assert "<p>" in html_fixture.description.description
        assert "<strong>" in html_fixture.description.description

    def test_property_from_dict_roundtrip(self, sample_property):
        data = sample_property.model_dump()
        restored = PropertyData.model_validate(data)
        assert restored.property_id == sample_property.property_id
        assert restored.location.city == sample_property.location.city

    def test_invalid_property_raises(self):
        with pytest.raises(ValidationError):
            PropertyData.model_validate({"property_id": "not-an-int"})


class TestMarketingContent:
    def test_valid_content_parses(self, sample_marketing_content):
        assert sample_marketing_content.hero_headline
        assert len(sample_marketing_content.property_highlights) == 3
        assert sample_marketing_content.about_section
        assert len(sample_marketing_content.amenities_descriptions) == 4

    def test_invalid_highlights_type_raises(self):
        with pytest.raises(ValidationError):
            MarketingContent.model_validate(
                {
                    "hero_headline": "Test",
                    "property_highlights": "not a list",
                    "about_section": "test",
                    "amenities_descriptions": {},
                }
            )

    def test_roundtrip_serialization(self, sample_marketing_content):
        json_str = sample_marketing_content.model_dump_json()
        restored = MarketingContent.model_validate_json(json_str)
        assert restored.hero_headline == sample_marketing_content.hero_headline


class TestGoldenDataset:
    def test_all_golden_samples_valid(self):
        for gs in GOLDEN_DATASET:
            assert gs.must_mention
            assert gs.must_not_mention
            assert gs.category in GoldenSampleCategory

    def test_adversarial_sample_has_injection(self):
        adversarial = next(gs for gs in GOLDEN_DATASET if gs.category == GoldenSampleCategory.ADVERSARIAL)
        assert "IGNORE PREVIOUS INSTRUCTIONS" in adversarial.property.description.description

    def test_edge_case_no_reviews(self):
        no_reviews = next(
            gs for gs in GOLDEN_DATASET
            if gs.category == GoldenSampleCategory.EDGE_CASE and gs.property.num_of_reviews == 0
        )
        assert "highly rated" in no_reviews.must_not_mention

    def test_standard_samples_have_location_constraints(self):
        standards = [gs for gs in GOLDEN_DATASET if gs.category == GoldenSampleCategory.STANDARD]
        for gs in standards:
            location_terms = [phrase for phrase in gs.must_mention if phrase in gs.property.location.city]
            assert location_terms, f"No city mention constraint for {gs.property.property_name}"
