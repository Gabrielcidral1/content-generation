from content_generation.amenities import human_amenity
from content_generation.generator import ContentGeneratorBase
from content_generation.models import MarketingContent, PropertyData


def _plural(n: int, word: str) -> str:
    return f"{word}s" if n != 1 else word


class TemplateContentGenerator(ContentGeneratorBase):
    """Deterministic fill-in-the-blank generator. Used as a baseline to measure
    the lift delivered by the LLM generator."""

    def generate(self, property_data: PropertyData) -> MarketingContent:
        loc = property_data.location
        info = property_data.rental_info
        rules = property_data.house_rules
        name = property_data.property_name
        ptype = property_data.property_type

        # --- headline ---
        bed_label = "Studio" if info.bedrooms == 0 else f"{info.bedrooms}-Bedroom"
        headline = f"{name} — {bed_label} {ptype} in {loc.city}, {loc.country}"
        if len(headline) > 120:
            headline = f"{name} — {ptype} in {loc.city}"

        # --- highlights (exactly 3) ---
        if info.bedrooms == 0:
            cap = (
                f"Studio sleeping up to {info.max_guests} {_plural(info.max_guests, 'guest')}"
                f" · {info.bathrooms} {_plural(info.bathrooms, 'bathroom')}"
            )
        else:
            cap = (
                f"Sleeps {info.max_guests}"
                f" · {info.bedrooms} {_plural(info.bedrooms, 'bedroom')}"
                f" · {info.bathrooms} {_plural(info.bathrooms, 'bathroom')}"
            )

        top_amenities = [human_amenity(a) for a in property_data.amenities[:3]]
        amenity_highlight = (
            f"Includes: {', '.join(top_amenities)}"
            if top_amenities
            else f"{ptype} in {loc.city}"
        )

        highlights = [
            cap,
            f"Located in {loc.city}, {loc.country}",
            amenity_highlight,
        ]

        # --- about section ---
        review_str = ""
        if property_data.num_of_reviews > 0 and property_data.average_review_score:
            review_str = (
                f" Rated {property_data.average_review_score} out of 5 "
                f"by {property_data.num_of_reviews} guests."
            )

        checkin_str = ""
        if rules.check_in_time and rules.check_out_time:
            checkin_str = f" Check-in from {rules.check_in_time}, check-out by {rules.check_out_time}."

        bed_phrase = (
            "a studio" if info.bedrooms == 0
            else f"{info.bedrooms} {_plural(info.bedrooms, 'bedroom')}"
        )

        amenity_list = (
            ", ".join(human_amenity(a) for a in property_data.amenities[:6])
            if property_data.amenities
            else "a range of amenities"
        )

        about = (
            f"{name} is a {ptype.lower()} in {loc.city}, {loc.country}. "
            f"The property offers {bed_phrase} and {info.bathrooms} {_plural(info.bathrooms, 'bathroom')}, "
            f"sleeping up to {info.max_guests} {_plural(info.max_guests, 'guest')}."
            f"{review_str}"
            f"{checkin_str} "
            f"The property is equipped with {amenity_list}. "
            f"Whether you are planning a relaxing break or need a comfortable base "
            f"to explore {loc.city}, {name} provides everything required for a pleasant stay. "
            f"Situated in {loc.country}, the property is well-positioned for guests "
            f"looking to experience the best of the area. "
            f"Book {name} today and enjoy a hassle-free stay in {loc.city}."
        )

        # --- amenities ---
        amenities_descriptions = {
            code: human_amenity(code)
            for code in property_data.amenities
        }

        return MarketingContent(
            hero_headline=headline[:120],
            property_highlights=highlights,
            about_section=about,
            amenities_descriptions=amenities_descriptions,
        )
