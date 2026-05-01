from .models import (
    HouseRules,
    Location,
    Policies,
    PropertyData,
    PropertyDescription,
    RentalInfo,
)

FIXTURES: list[PropertyData] = [
    # 1. Luxury Villa — Mallorca, Spain
    PropertyData(
        property_id=1001,
        property_name="Villa Sol Dorado",
        property_type="Villa",
        description=PropertyDescription(
            name="Villa Sol Dorado",
            headline="Exclusive Mallorcan villa with private pool and sea views",
            description=(
                "Nestled on the hillside above Port d'Andratx, Villa Sol Dorado is a "
                "stunning six-bedroom retreat that blends traditional Mallorcan architecture "
                "with modern luxury. Every room is bathed in natural light, and the expansive "
                "terrace offers uninterrupted views across the Mediterranean."
            ),
        ),
        amenities=[
            "PrivatePool", "AirConditioning", "InternetBroadband", "OutdoorFurniture",
            "Barbecue", "EssentialCookware", "DishWasher", "WashingMachine",
            "LinensProvided", "FreeParking", "TV",
        ],
        image_urls=[
            "https://example.com/villa-sol-dorado/01.jpg",
            "https://example.com/villa-sol-dorado/02.jpg",
        ],
        reviews=[
            "Absolutely breathtaking views and immaculate interiors. The pool was perfect and the kitchen had everything we needed. Will definitely return!",
            "Best holiday we've ever had. The villa exceeded every expectation — spacious, clean, and the location is magical.",
            "Outstanding property. The terrace at sunset is something you won't forget. Highly recommended for families or groups.",
        ],
        num_of_reviews=87,
        average_review_score=4.96,
        rental_info=RentalInfo(max_guests=6, bedrooms=3, bathrooms=3),
        location=Location(city="Port d'Andratx", country="Spain", latitude=39.538, longitude=2.385),
        policies=Policies(
            cancellation_policy="Free cancellation up to 30 days before check-in",
            payment_schedule="50% deposit on booking, remainder 30 days before arrival",
            damage_deposit="€500 damage deposit, refunded within 7 days of departure",
        ),
        house_rules=HouseRules(check_in_time="4 PM", check_out_time="11 AM"),
    ),

    # 2. City Apartment — Barcelona, Spain
    PropertyData(
        property_id=1002,
        property_name="Eixample Modern Studio",
        property_type="NormalApartment",
        description=PropertyDescription(
            name="Eixample Modern Studio",
            headline="Stylish studio in the heart of Barcelona's Eixample district",
            description=(
                "A compact, thoughtfully designed studio apartment on the fourth floor of a "
                "classic Eixample building. Steps from Passeig de Gràcia, top restaurants, and "
                "the city's best shopping. Ideal for a couple or solo traveller exploring Barcelona."
            ),
        ),
        amenities=[
            "AirConditioning", "InternetBroadband", "TV", "EssentialCookware",
            "IronAndBoard", "HairDryer", "Heating", "WorkDesk",
        ],
        image_urls=[
            "https://example.com/eixample-studio/01.jpg",
        ],
        reviews=[
            "Great location, everything you need for a short stay in Barcelona.",
            "Clean and well-equipped. The neighbourhood is fantastic — so much to see and do.",
        ],
        num_of_reviews=34,
        average_review_score=4.61,
        rental_info=RentalInfo(max_guests=2, bedrooms=1, bathrooms=1),
        location=Location(city="Barcelona", country="Spain", latitude=41.392, longitude=2.163),
        policies=Policies(
            cancellation_policy="Non-refundable after booking",
            payment_schedule="Full payment on booking",
            damage_deposit=None,
        ),
        house_rules=HouseRules(check_in_time="3 PM", check_out_time="11 AM"),
    ),

    # 3. Countryside Cottage — Cotswolds, UK
    PropertyData(
        property_id=1003,
        property_name="Honeysuckle Cottage",
        property_type="Cottage",
        description=PropertyDescription(
            name="Honeysuckle Cottage",
            headline="Charming stone cottage with walled garden in the Cotswolds",
            description=(
                "A 17th-century stone cottage tucked down a quiet lane in the village of "
                "Bourton-on-the-Water. Features original flagstone floors, exposed beams, and "
                "a wood-burning fireplace. The south-facing walled garden is perfect for lazy "
                "afternoons. Well-behaved dogs welcome."
            ),
        ),
        amenities=[
            "Fireplace", "Garden", "PetsAllowed", "InternetBroadband", "WashingMachine",
            "Heating", "EssentialCookware", "LinensProvided", "FreeParking", "Barbecue",
        ],
        image_urls=[
            "https://example.com/honeysuckle-cottage/01.jpg",
            "https://example.com/honeysuckle-cottage/02.jpg",
        ],
        reviews=[
            "Absolutely magical. The cottage is full of character and the garden is wonderful. Our dog loved it too!",
            "Perfect countryside escape. Cosy, well-equipped, and in a beautiful village. Already planning a return trip.",
            "The fireplace made our winter stay incredibly cosy. Highly recommend for couples or small families.",
            "Lovely host, beautiful property. Walking trails straight from the door.",
        ],
        num_of_reviews=62,
        average_review_score=4.88,
        rental_info=RentalInfo(max_guests=4, bedrooms=2, bathrooms=1),
        location=Location(city="Bourton-on-the-Water", country="United Kingdom", latitude=51.874, longitude=-1.758),
        policies=Policies(
            cancellation_policy="Free cancellation up to 14 days before check-in",
            payment_schedule="Full payment 14 days before arrival",
            damage_deposit="£200 damage deposit",
        ),
        house_rules=HouseRules(check_in_time="4 PM", check_out_time="10 AM"),
    ),

    # 4. Beachfront Bungalow — Bali, Indonesia
    PropertyData(
        property_id=1004,
        property_name="Seminyak Sunrise Bungalow",
        property_type="Bungalow",
        description=PropertyDescription(
            name="Seminyak Sunrise Bungalow",
            headline="Beachfront bungalow with direct ocean access in Seminyak",
            description=(
                "A serene one-bedroom bungalow set directly on Seminyak Beach, with its own "
                "private terrace just metres from the water. Traditional Balinese architecture — "
                "teak wood, open-air bathroom, and tropical garden — creates an authentic island "
                "retreat. Sunsets here are legendary."
            ),
        ),
        amenities=[
            "BeachAccess", "OceanView", "AirConditioning", "InternetBroadband",
            "OutdoorFurniture", "Waterfront", "LinensProvided", "HairDryer",
        ],
        image_urls=[
            "https://example.com/seminyak-bungalow/01.jpg",
            "https://example.com/seminyak-bungalow/02.jpg",
        ],
        reviews=[
            "Waking up to the sound of waves every morning was a dream. The bungalow is beautiful and the location unbeatable.",
            "Perfect romantic escape. The sunset from the terrace is absolutely stunning. Very clean and comfortable.",
        ],
        num_of_reviews=48,
        average_review_score=4.83,
        rental_info=RentalInfo(max_guests=2, bedrooms=1, bathrooms=1),
        location=Location(city="Seminyak", country="Indonesia", latitude=-8.689, longitude=115.162),
        policies=Policies(
            cancellation_policy="Free cancellation up to 7 days before check-in",
            payment_schedule="Full payment on booking",
            damage_deposit="IDR 1,000,000 damage deposit",
        ),
        house_rules=HouseRules(check_in_time="2 PM", check_out_time="12 PM"),
    ),

    # 5. Mountain Chalet — Chamonix, France
    PropertyData(
        property_id=1005,
        property_name="Chalet Les Aiguilles",
        property_type="Chalet",
        description=PropertyDescription(
            name="Chalet Les Aiguilles",
            headline="Ski-in/ski-out alpine chalet for eight with panoramic Mont Blanc views",
            description=(
                "An impressive four-bedroom chalet positioned directly on the Grands Montets ski "
                "run in Chamonix. Enjoy ski-in/ski-out convenience, a large open-plan living area "
                "with a stone fireplace, and floor-to-ceiling windows framing Mont Blanc. After a "
                "day on the slopes, unwind in the sauna or hot tub on the wraparound deck."
            ),
        ),
        amenities=[
            "SkiAccess", "Fireplace", "HotTub", "Sauna", "AirConditioning",
            "InternetBroadband", "EssentialCookware", "DishWasher", "WashingMachine",
            "LinensProvided", "FreeParking", "TV", "OutdoorFurniture",
        ],
        image_urls=[
            "https://example.com/chalet-aiguilles/01.jpg",
            "https://example.com/chalet-aiguilles/02.jpg",
            "https://example.com/chalet-aiguilles/03.jpg",
        ],
        reviews=[
            "Ski-in/ski-out is a complete game changer. The hot tub after a long day on the mountain is perfection.",
            "Stunning property with incredible views of Mont Blanc. Spacious, warm and beautifully equipped.",
            "Best ski chalet we've ever rented. The whole group agreed — already looking at dates for next season.",
        ],
        num_of_reviews=41,
        average_review_score=4.92,
        rental_info=RentalInfo(max_guests=8, bedrooms=4, bathrooms=3),
        location=Location(city="Chamonix", country="France", latitude=45.924, longitude=6.870),
        policies=Policies(
            cancellation_policy="Free cancellation up to 60 days before check-in",
            payment_schedule="30% deposit on booking, remainder 60 days before arrival",
            damage_deposit="€1,000 damage deposit",
        ),
        house_rules=HouseRules(check_in_time="5 PM", check_out_time="10 AM"),
    ),

    # 6. Historic Townhouse — Lisbon, Portugal (HTML in description)
    PropertyData(
        property_id=1006,
        property_name="Alfama Heritage House",
        property_type="Townhouse",
        description=PropertyDescription(
            name="Alfama Heritage House",
            headline="Restored townhouse in the historic Alfama district of Lisbon",
            description=(
                "<p>A beautifully <strong>restored 19th-century townhouse</strong> in the heart of "
                "Lisbon's oldest neighbourhood, Alfama.<br/><br/>The property spans three floors and "
                "features <strong>original azulejo tile work</strong>, high ceilings, and a private "
                "rooftop terrace with <em>sweeping views over the Tagus river</em>.</p>"
                "<p>Just steps from the famous <strong>Miradouro de Santa Luzia</strong> viewpoint "
                "and within walking distance of the Se Cathedral and tram line 28.</p>"
            ),
        ),
        amenities=[
            "AirConditioning", "InternetBroadband", "EssentialCookware", "WashingMachine",
            "LinensProvided", "TV", "Heating", "IronAndBoard",
        ],
        image_urls=[
            "https://example.com/alfama-house/01.jpg",
            "https://example.com/alfama-house/02.jpg",
        ],
        reviews=[
            "The rooftop view over the Tagus is worth it alone. Beautifully decorated with so much character.",
            "Staying in Alfama is the real Lisbon experience. The house itself is stunning — tiles, high ceilings, the lot.",
            "Perfect location for exploring the city on foot. The house has a wonderful sense of history.",
            "The tram stops right nearby and the neighbourhood is full of life. Would absolutely stay again.",
            "Gorgeous property, very well equipped. The rooftop terrace sealed the deal for us.",
        ],
        num_of_reviews=119,
        average_review_score=4.79,
        rental_info=RentalInfo(max_guests=5, bedrooms=2, bathrooms=2),
        location=Location(city="Lisbon", country="Portugal", latitude=38.713, longitude=-9.133),
        policies=Policies(
            cancellation_policy="Free cancellation up to 14 days before check-in",
            payment_schedule="Full payment 14 days before arrival",
            damage_deposit="€300 damage deposit",
        ),
        house_rules=HouseRules(check_in_time="3 PM", check_out_time="11 AM"),
    ),
]
