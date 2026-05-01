import pytest

from content_generation.models import (
    HouseRules,
    Location,
    MarketingContent,
    Policies,
    PropertyData,
    PropertyDescription,
    RentalInfo,
)
from content_generation.template_generator import TemplateContentGenerator
from content_generation.utils import has_html, strip_html

GEN = TemplateContentGenerator()


def _make_property(**overrides) -> PropertyData:
    base = dict(
        property_id=9001,
        property_name="Test Property",
        property_type="Apartment",
        description=PropertyDescription(
            name="Test",
            headline="A fine test property",
            description="Plain text description.",
        ),
        amenities=["InternetBroadband", "TV", "Heating"],
        image_urls=[],
        reviews=[],
        num_of_reviews=0,
        average_review_score=0.0,
        rental_info=RentalInfo(max_guests=4, bedrooms=2, bathrooms=1),
        location=Location(city="Lisbon", country="Portugal", latitude=38.7, longitude=-9.1),
        policies=Policies(),
        house_rules=HouseRules(check_in_time="3 PM", check_out_time="11 AM"),
    )
    base.update(overrides)
    return PropertyData(**base)


class TestTemplateContentGenerator:
    def test_output_is_valid_marketing_content(self):
        result = GEN.generate(_make_property())
        assert isinstance(result, MarketingContent)
        assert result.hero_headline
        assert len(result.property_highlights) == 3
        assert result.about_section
        assert result.amenities_descriptions

    def test_headline_contains_city_and_country(self):
        result = GEN.generate(_make_property())
        assert "Lisbon" in result.hero_headline
        assert "Portugal" in result.hero_headline

    def test_studio_zero_bedrooms_headline(self):
        prop = _make_property(rental_info=RentalInfo(max_guests=1, bedrooms=0, bathrooms=1))
        result = GEN.generate(prop)
        assert "Studio" in result.hero_headline

    def test_studio_zero_bedrooms_about(self):
        prop = _make_property(rental_info=RentalInfo(max_guests=1, bedrooms=0, bathrooms=1))
        result = GEN.generate(prop)
        assert "a studio" in result.about_section.lower()
        assert "0 bedroom" not in result.about_section.lower()

    def test_single_guest_singular(self):
        prop = _make_property(rental_info=RentalInfo(max_guests=1, bedrooms=0, bathrooms=1))
        all_text = result = GEN.generate(prop)
        full = result.about_section + " ".join(result.property_highlights)
        assert "1 guest" in full
        assert "1 guests" not in full

    def test_single_bathroom_singular(self):
        prop = _make_property(rental_info=RentalInfo(max_guests=2, bedrooms=1, bathrooms=1))
        result = GEN.generate(prop)
        full = result.about_section + " ".join(result.property_highlights)
        assert "1 bathroom" in full
        assert "1 bathrooms" not in full

    def test_single_bedroom_singular(self):
        prop = _make_property(rental_info=RentalInfo(max_guests=2, bedrooms=1, bathrooms=1))
        result = GEN.generate(prop)
        full = result.about_section + " ".join(result.property_highlights)
        assert "1 bedroom" in full
        assert "1 bedrooms" not in full

    def test_no_reviews_omits_rating(self):
        prop = _make_property(num_of_reviews=0, average_review_score=0.0)
        result = GEN.generate(prop)
        assert "Rated" not in result.about_section
        assert "out of 5" not in result.about_section

    def test_with_reviews_includes_rating(self):
        prop = _make_property(num_of_reviews=42, average_review_score=4.8)
        result = GEN.generate(prop)
        assert "4.8" in result.about_section
        assert "42" in result.about_section

    def test_no_amenities_fallback_text(self):
        prop = _make_property(amenities=[])
        result = GEN.generate(prop)
        assert "a range of amenities" in result.about_section
        assert result.amenities_descriptions == {}

    def test_headline_truncated_to_120_chars(self):
        prop = _make_property(
            property_name="A" * 80,
            rental_info=RentalInfo(max_guests=2, bedrooms=2, bathrooms=1),
        )
        result = GEN.generate(prop)
        assert len(result.hero_headline) <= 120

    def test_amenity_codes_match_input(self):
        amenities = ["InternetBroadband", "TV", "Heating"]
        prop = _make_property(amenities=amenities)
        result = GEN.generate(prop)
        assert set(result.amenities_descriptions.keys()) == set(amenities)

    def test_no_html_in_output(self):
        prop = _make_property()
        result = GEN.generate(prop)
        assert not has_html(result.hero_headline)
        assert not any(has_html(h) for h in result.property_highlights)
        assert not has_html(result.about_section)


class TestHtmlUtils:
    def test_has_html_detects_tags(self):
        assert has_html("<p>Hello</p>")
        assert has_html("<strong>Bold</strong>")
        assert has_html("<br>")

    def test_has_html_clean_text(self):
        assert not has_html("Plain text with no tags")
        assert not has_html("Price 100 dollars")

    def test_strip_html_removes_tags(self):
        assert strip_html("<p>Hello <strong>world</strong></p>") == "Hello  world"

    def test_strip_html_passthrough_clean(self):
        assert strip_html("No HTML here") == "No HTML here"

    def test_strip_html_handles_nested(self):
        result = strip_html("<div><p>Text <em>here</em></p></div>")
        assert "Text" in result
        assert "<" not in result
