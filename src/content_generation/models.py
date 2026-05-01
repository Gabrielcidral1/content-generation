from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PropertyDescription(BaseModel):
    name: str
    headline: str
    description: str


class RentalInfo(BaseModel):
    max_guests: int
    bedrooms: int
    bathrooms: int


class Location(BaseModel):
    city: str
    country: str
    latitude: float
    longitude: float


class Policies(BaseModel):
    cancellation_policy: Optional[str] = None
    payment_schedule: Optional[str] = None
    damage_deposit: Optional[str] = None


class HouseRules(BaseModel):
    check_in_time: str
    check_out_time: str


class PropertyData(BaseModel):
    property_id: int
    property_name: str
    property_type: str
    description: PropertyDescription
    amenities: list[str]
    image_urls: list[str]
    reviews: list[str]
    num_of_reviews: int
    average_review_score: float
    rental_info: RentalInfo
    location: Location
    policies: Policies
    house_rules: HouseRules


class MarketingContent(BaseModel):
    hero_headline: str = Field(description="Compelling 1-line headline, 10-120 characters")
    property_highlights: list[str] = Field(description="3 to 5 bullet points, each under 120 chars")
    about_section: str = Field(description="2-4 paragraphs, 80-600 words")
    amenities_descriptions: dict[str, str] = Field(description="amenity_code -> 1-2 sentence description")


class GoldenSampleCategory(str, Enum):
    STANDARD = "standard"
    EDGE_CASE = "edge_case"
    ADVERSARIAL = "adversarial"


class GoldenSample(BaseModel):
    property: PropertyData
    category: GoldenSampleCategory
    notes: str
    must_mention: list[str] = Field(description="Phrases/facts that must appear in generated content")
    must_not_mention: list[str] = Field(description="Phrases that must NOT appear in generated content")
