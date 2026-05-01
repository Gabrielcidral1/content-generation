import json
from unittest.mock import MagicMock, patch

import pytest

from content_generation.generator import (
    AnthropicContentGenerator,
    ContentGeneratorBase,
    _parse_json_response,
)
from content_generation.models import MarketingContent
from tests.conftest import VALID_MARKETING_JSON


class TestAnthropicContentGenerator:
    def test_returns_marketing_content(self, mock_anthropic_client, sample_property):
        gen = AnthropicContentGenerator(client=mock_anthropic_client)
        result = gen.generate(sample_property)
        assert isinstance(result, MarketingContent)

    def test_calls_anthropic_with_property_facts(self, mock_anthropic_client, sample_property):
        gen = AnthropicContentGenerator(client=mock_anthropic_client)
        gen.generate(sample_property)

        call_args = mock_anthropic_client.messages.create.call_args
        user_content = call_args.kwargs["messages"][0]["content"]

        assert sample_property.location.city in user_content
        assert str(sample_property.rental_info.bedrooms) in user_content
        assert str(sample_property.rental_info.max_guests) in user_content

    def test_system_prompt_forbids_invention(self, mock_anthropic_client, sample_property):
        gen = AnthropicContentGenerator(client=mock_anthropic_client)
        gen.generate(sample_property)

        system_prompt = mock_anthropic_client.messages.create.call_args.kwargs["system"]
        assert "NOT" in system_prompt or "ONLY" in system_prompt or "must" in system_prompt.lower()

    def test_custom_model_passed_to_client(self, mock_anthropic_client, sample_property):
        gen = AnthropicContentGenerator(client=mock_anthropic_client, model="claude-opus-4-7")
        gen.generate(sample_property)

        model_used = mock_anthropic_client.messages.create.call_args.kwargs["model"]
        assert model_used == "claude-opus-4-7"

    def test_malformed_json_raises_value_error(self, minimal_property):
        client = MagicMock()
        client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="not valid json {{{")]
        )
        gen = AnthropicContentGenerator(client=client)
        with pytest.raises(ValueError, match="invalid JSON"):
            gen.generate(minimal_property)

    def test_wrong_schema_raises_value_error(self, minimal_property):
        client = MagicMock()
        client.messages.create.return_value = MagicMock(
            content=[MagicMock(text='{"wrong_field": "value"}')]
        )
        gen = AnthropicContentGenerator(client=client)
        with pytest.raises(ValueError, match="schema"):
            gen.generate(minimal_property)


class TestDependencyInjection:
    def test_any_subclass_satisfies_interface(self, sample_property):
        class StubGenerator(ContentGeneratorBase):
            def generate(self, property_data):
                return MarketingContent.model_validate(VALID_MARKETING_JSON)

        gen: ContentGeneratorBase = StubGenerator()
        result = gen.generate(sample_property)
        assert isinstance(result, MarketingContent)

    def test_abstract_base_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            ContentGeneratorBase()  # type: ignore[abstract]


class TestParseJsonResponse:
    def test_parses_plain_json(self):
        result = _parse_json_response(json.dumps(VALID_MARKETING_JSON))
        assert isinstance(result, MarketingContent)

    def test_strips_markdown_fences(self):
        fenced = f"```json\n{json.dumps(VALID_MARKETING_JSON)}\n```"
        result = _parse_json_response(fenced)
        assert isinstance(result, MarketingContent)

    def test_strips_plain_code_fence(self):
        fenced = f"```\n{json.dumps(VALID_MARKETING_JSON)}\n```"
        result = _parse_json_response(fenced)
        assert isinstance(result, MarketingContent)
