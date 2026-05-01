import re

AMENITY_LABELS: dict[str, str] = {
    "AirConditioning": "Air Conditioning",
    "BathroomAndLaundry": "Bathroom & Laundry",
    "Barbecue": "BBQ / Grill",
    "Balcony": "Balcony",
    "BeachAccess": "Beach Access",
    "Bicycles": "Bicycles Available",
    "ChildrenWelcome": "Children Welcome",
    "DishWasher": "Dishwasher",
    "Dryer": "Dryer",
    "Elevator": "Elevator",
    "EssentialCookware": "Fully Equipped Kitchen",
    "Fireplace": "Fireplace",
    "FitnessRoom": "Fitness Room",
    "FreeParking": "Free Parking",
    "GameRoom": "Game Room",
    "Garden": "Private Garden",
    "HairDryer": "Hair Dryer",
    "Heating": "Heating",
    "HotTub": "Hot Tub",
    "InternetBroadband": "High-Speed Wi-Fi",
    "IronAndBoard": "Iron & Ironing Board",
    "Kayak": "Kayak",
    "LinensProvided": "Linens & Towels Provided",
    "Microwave": "Microwave",
    "OutdoorFurniture": "Outdoor Furniture",
    "OceanView": "Ocean View",
    "PetsAllowed": "Pets Allowed",
    "PrivatePool": "Private Pool",
    "SafetyFeatures": "Safety Features",
    "Sauna": "Sauna",
    "SkiAccess": "Ski-In / Ski-Out Access",
    "SmokingAllowed": "Smoking Allowed",
    "SurfboardStorage": "Surfboard Storage",
    "SwimmingPool": "Shared Swimming Pool",
    "TV": "Smart TV",
    "WashingMachine": "Washing Machine",
    "Waterfront": "Waterfront Location",
    "WheelchairAccessible": "Wheelchair Accessible",
    "WorkDesk": "Work Desk",
}


def human_amenity(code: str) -> str:
    label = AMENITY_LABELS.get(code)
    if label:
        return label
    words = re.sub(r"([a-z])([A-Z])", r"\1 \2", code).replace("_", " ")
    return words.replace(" And ", " & ").title()
