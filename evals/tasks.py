import json
import os
import sys
from pathlib import Path

# Inspect AI loads this file with the full path as the module name, so relative
# imports fail. Ensure the project root is on sys.path before any evals imports.
_ROOT = str(Path(__file__).parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import anthropic
from dotenv import load_dotenv
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample

from content_generation.fixtures import FIXTURES
from content_generation.generator import AnthropicContentGenerator
from content_generation.golden import GOLDEN_DATASET
from content_generation.template_generator import TemplateContentGenerator
from evals.scorers import (
    factual_accuracy_scorer,
    golden_constraints_scorer,
    groundedness_scorer,
    marketing_quality_scorer,
    structural_completeness_scorer,
)
from evals.solvers import content_generation_solver

load_dotenv()


def _make_generator() -> AnthropicContentGenerator:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set — cannot run evals")
    return AnthropicContentGenerator(
        client=anthropic.Anthropic(api_key=api_key),
        model=os.environ.get("GENERATOR_MODEL", "claude-haiku-4-5-20251001"),
    )


@task
def fixture_eval() -> Task:
    """Evaluates all 6 mock property fixtures across 4 quality dimensions."""
    generator = _make_generator()

    samples = [
        Sample(
            input=f"Generate marketing content for property: {prop.property_name}",
            metadata={"property": json.loads(prop.model_dump_json())},
            id=f"fixture-{prop.property_id}",
        )
        for prop in FIXTURES
    ]

    return Task(
        dataset=MemoryDataset(samples),
        solver=content_generation_solver(generator=generator),
        scorer=[
            structural_completeness_scorer(),
            factual_accuracy_scorer(),
            groundedness_scorer(),
            marketing_quality_scorer(),
        ],
        name="fixture_eval",
    )


@task
def golden_eval() -> Task:
    """Evaluates the golden dataset — including edge cases and adversarial inputs."""
    generator = _make_generator()

    samples = [
        Sample(
            input=f"Generate marketing content for property: {gs.property.property_name}",
            metadata={
                "property": json.loads(gs.property.model_dump_json()),
                "golden_category": gs.category.value,
                "golden_notes": gs.notes,
                "must_mention": gs.must_mention,
                "must_not_mention": gs.must_not_mention,
            },
            id=f"golden-{gs.property.property_id}",
        )
        for gs in GOLDEN_DATASET
    ]

    return Task(
        dataset=MemoryDataset(samples),
        solver=content_generation_solver(generator=generator),
        scorer=[
            structural_completeness_scorer(),
            factual_accuracy_scorer(),
            groundedness_scorer(),
            marketing_quality_scorer(),
            golden_constraints_scorer(),
        ],
        name="golden_eval",
    )


@task
def fixture_eval_template() -> Task:
    """Template-based baseline for fixture properties — no LLM, no API key required."""
    generator = TemplateContentGenerator()

    samples = [
        Sample(
            input=f"Generate marketing content for property: {prop.property_name}",
            metadata={"property": json.loads(prop.model_dump_json())},
            id=f"fixture-{prop.property_id}",
        )
        for prop in FIXTURES
    ]

    return Task(
        dataset=MemoryDataset(samples),
        solver=content_generation_solver(generator=generator),
        scorer=[
            structural_completeness_scorer(),
            factual_accuracy_scorer(),
            groundedness_scorer(),
            marketing_quality_scorer(),
        ],
        name="fixture_eval_template",
    )


@task
def golden_eval_template() -> Task:
    """Template-based baseline for the golden dataset — no LLM, no API key required."""
    generator = TemplateContentGenerator()

    samples = [
        Sample(
            input=f"Generate marketing content for property: {gs.property.property_name}",
            metadata={
                "property": json.loads(gs.property.model_dump_json()),
                "golden_category": gs.category.value,
                "golden_notes": gs.notes,
                "must_mention": gs.must_mention,
                "must_not_mention": gs.must_not_mention,
            },
            id=f"golden-{gs.property.property_id}",
        )
        for gs in GOLDEN_DATASET
    ]

    return Task(
        dataset=MemoryDataset(samples),
        solver=content_generation_solver(generator=generator),
        scorer=[
            structural_completeness_scorer(),
            factual_accuracy_scorer(),
            groundedness_scorer(),
            marketing_quality_scorer(),
            golden_constraints_scorer(),
        ],
        name="golden_eval_template",
    )
