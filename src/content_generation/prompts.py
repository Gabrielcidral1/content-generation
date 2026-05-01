import json

from .amenities import human_amenity
from .models import PropertyData

SYSTEM_PROMPT = """\
You are a professional marketing copywriter for vacation rental properties.
Your task is to generate compelling, accurate marketing copy from the provided property data.

CRITICAL RULES:
1. Every claim must be directly traceable to the provided property data — no invention.
2. Do NOT fabricate amenities, features, or characteristics absent from the data.
3. Do NOT invent reviews, ratings, or social proof if reviews data is empty or absent.
4. If the input description contains HTML tags (<p>, <strong>, <br>, etc.), ignore the markup — write clean plain-text marketing copy.
5. Output ONLY valid JSON matching the schema below. No markdown fences, no extra text.
6. Do NOT use em dashes (—) or en dashes in any copy. Use commas, colons, or short sentences instead.
"""

OUTPUT_SCHEMA = """\
{
  "hero_headline": "<compelling 1-line headline, 10-120 characters>",
  "property_highlights": [
    "<highlight 1, under 120 chars>",
    "<highlight 2, under 120 chars>",
    "<highlight 3, under 120 chars>"
  ],
  "about_section": "<2-4 paragraphs describing the property, 80-600 words>",
  "amenities_descriptions": {
    "<amenity_code>": "<1-2 sentence description of this amenity>"
  }
}

Rules:
- property_highlights: 3 to 5 items
- amenities_descriptions: include only codes present in the property amenities list
- about_section: factual, specific, grounded in the data
"""


def build_generation_prompt(property_data: PropertyData) -> str:
    amenity_human = {code: human_amenity(code) for code in property_data.amenities}

    data = {
        "property_name": property_data.property_name,
        "property_type": property_data.property_type,
        "location": {
            "city": property_data.location.city,
            "country": property_data.location.country,
        },
        "description": {
            "headline": property_data.description.headline,
            "description": property_data.description.description,
        },
        "rental_info": property_data.rental_info.model_dump(),
        "amenities": amenity_human,
        "reviews": property_data.reviews,
        "num_of_reviews": property_data.num_of_reviews,
        "average_review_score": property_data.average_review_score,
        "policies": property_data.policies.model_dump(exclude_none=True),
        "house_rules": property_data.house_rules.model_dump(),
    }

    return (
        f"Generate marketing copy for this vacation rental:\n\n"
        f"{json.dumps(data, indent=2, ensure_ascii=False)}\n\n"
        f"Return JSON matching this schema:\n{OUTPUT_SCHEMA}"
    )
