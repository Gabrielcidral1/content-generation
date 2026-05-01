import json
from pathlib import Path

from .models import PropertyData

_DATA_DIR = Path(__file__).parent / "data" / "fixtures"

FIXTURES: list[PropertyData] = [
    PropertyData.model_validate(json.loads(path.read_text()))
    for path in sorted(_DATA_DIR.glob("*.json"))
]
