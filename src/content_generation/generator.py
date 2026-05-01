import json
import re
from abc import ABC, abstractmethod

import anthropic
from pydantic import ValidationError

from .models import MarketingContent, PropertyData
from .prompts import SYSTEM_PROMPT, build_generation_prompt

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class ContentGeneratorBase(ABC):
    @abstractmethod
    def generate(self, property_data: PropertyData) -> MarketingContent:
        ...


class AnthropicContentGenerator(ContentGeneratorBase):
    def __init__(self, client: anthropic.Anthropic, model: str = DEFAULT_MODEL):
        self.client = client
        self.model = model

    def generate(self, property_data: PropertyData) -> MarketingContent:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": build_generation_prompt(property_data)}
            ],
        )
        raw = response.content[0].text
        return _parse_json_response(raw)


def _parse_json_response(text: str) -> MarketingContent:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Generator returned invalid JSON: {e}\n\nRaw response:\n{text}"
        ) from e

    try:
        return MarketingContent.model_validate(data)
    except ValidationError as e:
        raise ValueError(
            f"Generator response does not match MarketingContent schema: {e}\n\nData:\n{data}"
        ) from e
