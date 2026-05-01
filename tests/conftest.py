import json
from unittest.mock import MagicMock

import pytest

from content_generation.fixtures import FIXTURES
from content_generation.golden import GOLDEN_DATASET
from content_generation.models import (
    HouseRules,
    Location,
    MarketingContent,
    Policies,
    PropertyData,
    PropertyDescription,
    RentalInfo,
)

VALID_MARKETING_JSON = {
    "hero_headline": "Stunning 3-bedroom villa with private pool in Mallorca",
    "property_highlights": [
        "Private pool with panoramic sea views",
        "Fully equipped modern kitchen with dishwasher",
        "Ski-in access and rooftop hot tub",
    ],
    "about_section": (
        "Nestled in the hills above Port d'Andratx, Villa Sol Dorado offers an unforgettable "
        "Mallorcan escape for up to six guests. With three spacious bedrooms and three bathrooms, "
        "the villa is ideal for families or groups seeking privacy and luxury in equal measure. "
        "The expansive terrace and private pool overlook the Mediterranean, making every morning "
        "feel like a postcard. Evenings are best spent around the outdoor barbecue as the sun "
        "sinks into the sea. Guests have consistently praised the stunning views and immaculate "
        "interiors, with an average review score of 4.96 from 87 reviews. Located in Spain, "
        "Port d'Andratx offers easy access to the best of Mallorca's west coast."
    ),
    "amenities_descriptions": {
        "PrivatePool": "A large private pool surrounded by sun loungers and sea views.",
        "AirConditioning": "Individual climate control in every room for year-round comfort.",
        "InternetBroadband": "High-speed Wi-Fi throughout the property.",
        "Barbecue": "A premium outdoor barbecue perfect for al fresco dining.",
    },
}


@pytest.fixture
def sample_property() -> PropertyData:
    return FIXTURES[0]


@pytest.fixture
def sample_golden():
    return GOLDEN_DATASET[0]


@pytest.fixture
def sample_marketing_content() -> MarketingContent:
    return MarketingContent.model_validate(VALID_MARKETING_JSON)


@pytest.fixture
def mock_anthropic_client():
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text=json.dumps(VALID_MARKETING_JSON))]
    client.messages.create.return_value = response
    return client


@pytest.fixture
def minimal_property() -> PropertyData:
    return PropertyData(
        property_id=9999,
        property_name="Test Property",
        property_type="NormalApartment",
        description=PropertyDescription(
            name="Test",
            headline="A test property",
            description="Simple test description.",
        ),
        amenities=["InternetBroadband", "TV", "Heating", "EssentialCookware"],
        image_urls=[],
        reviews=[],
        num_of_reviews=0,
        average_review_score=0.0,
        rental_info=RentalInfo(max_guests=2, bedrooms=1, bathrooms=1),
        location=Location(city="TestCity", country="TestCountry", latitude=0.0, longitude=0.0),
        policies=Policies(),
        house_rules=HouseRules(check_in_time="3 PM", check_out_time="11 AM"),
    )
