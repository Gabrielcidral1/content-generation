import json
import re

from inspect_ai.model import get_model
from inspect_ai.scorer import Score, mean, scorer

from content_generation.models import PropertyData
from content_generation.utils import (
    ABOUT_MAX_WORDS,
    ABOUT_MIN_WORDS,
    HEADLINE_MAX_LEN,
    HEADLINE_MIN_LEN,
    HIGHLIGHT_MAX_LEN,
    has_html,
)


def _all_generated_text(generated: dict) -> str:
    parts = [
        generated.get("hero_headline", ""),
        " ".join(generated.get("property_highlights", [])),
        generated.get("about_section", ""),
        " ".join(generated.get("amenities_descriptions", {}).values()),
    ]
    return " ".join(parts).lower()


# ---------------------------------------------------------------------------
# Scorer 1: Structural Completeness (rule-based)
# ---------------------------------------------------------------------------

@scorer(metrics=[mean()])
def structural_completeness_scorer():
    async def score(state, target) -> Score:
        generated = state.metadata.get("generated", {})
        checks = []
        details = []

        headline = generated.get("hero_headline", "")
        ok = bool(headline) and HEADLINE_MIN_LEN <= len(headline) <= HEADLINE_MAX_LEN and not has_html(headline)
        checks.append(ok)
        details.append(f"hero_headline length {len(headline)} {'OK' if ok else 'FAIL'}{' (has HTML)' if has_html(headline) else ''}")

        highlights = generated.get("property_highlights", [])
        h_ok = (
            isinstance(highlights, list)
            and 3 <= len(highlights) <= 5
            and all(isinstance(h, str) and len(h) <= HIGHLIGHT_MAX_LEN and not has_html(h) for h in highlights)
        )
        checks.append(h_ok)
        details.append(f"property_highlights count={len(highlights)} {'OK' if h_ok else 'FAIL'}")

        about = generated.get("about_section", "")
        word_count = len(about.split())
        a_ok = bool(about) and ABOUT_MIN_WORDS <= word_count <= ABOUT_MAX_WORDS and not has_html(about)
        checks.append(a_ok)
        details.append(f"about_section words={word_count} {'OK' if a_ok else 'FAIL'}{' (has HTML)' if has_html(about) else ''}")

        amenities = generated.get("amenities_descriptions", {})
        am_ok = isinstance(amenities, dict) and len(amenities) >= 3
        checks.append(am_ok)
        details.append(f"amenities_descriptions count={len(amenities)} {'OK' if am_ok else 'FAIL'}")

        property_amenities = set(state.metadata.get("property", {}).get("amenities", []))
        extra = set(amenities.keys()) - property_amenities
        grounded_ok = len(extra) == 0
        checks.append(grounded_ok)
        details.append(f"amenity codes grounded {'OK' if grounded_ok else f'FAIL — invented: {extra}'}")

        result = sum(checks) / len(checks)
        return Score(
            value=round(result, 3),
            answer="PASS" if result > 0.8 else "FAIL",
            explanation="; ".join(details),
        )

    return score


# ---------------------------------------------------------------------------
# Scorer 2: Factual Accuracy (rule-based)
# ---------------------------------------------------------------------------

@scorer(metrics=[mean()])
def factual_accuracy_scorer():
    async def score(state, target) -> Score:
        generated = state.metadata.get("generated", {})
        prop_raw = state.metadata.get("property", {})

        about = generated.get("about_section", "").lower()
        highlights_text = " ".join(generated.get("property_highlights", [])).lower()
        full_text = about + " " + highlights_text

        property_data = PropertyData.model_validate(prop_raw)
        city = property_data.location.city.lower()
        country = property_data.location.country.lower()
        bedrooms = property_data.rental_info.bedrooms
        bathrooms = property_data.rental_info.bathrooms
        max_guests = property_data.rental_info.max_guests

        assertions: list[tuple[str, bool]] = []

        assertions.append(("city present", city in full_text))
        assertions.append(("country present", country in full_text))

        for n, label in [(bedrooms, "bedroom"), (bathrooms, "bathroom"), (max_guests, "guest")]:
            mentioned = str(n) in full_text or _number_word(n) in full_text
            wrong_nums = [
                x for x in range(0, 20)
                if x != n and (f"{x} {label}" in full_text or f"{_number_word(x)} {label}" in full_text)
            ]
            if mentioned or wrong_nums:
                assertions.append((f"{label} count correct", mentioned and not wrong_nums))

        if property_data.average_review_score > 0:
            score_str = str(property_data.average_review_score)
            if score_str in full_text:
                assertions.append(("review score accurate", True))
        else:
            invented_scores = [f"{x:.1f}" for x in [4.5, 4.6, 4.7, 4.8, 4.9, 5.0] if f"{x:.1f}" in full_text]
            if invented_scores:
                assertions.append(("no fabricated score", False))

        if not assertions:
            return Score(value=1.0, answer="PASS", explanation="No verifiable facts found in generated text")

        correct = sum(1 for _, ok in assertions if ok)
        result = correct / len(assertions)
        details = "; ".join(f"{label}: {'OK' if ok else 'FAIL'}" for label, ok in assertions)

        return Score(
            value=round(result, 3),
            answer="PASS" if result >= 0.85 else "FAIL",
            explanation=details,
        )

    return score


def _number_word(n: int) -> str:
    words = {
        0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
        5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
        10: "ten",
    }
    return words.get(n, str(n))


# ---------------------------------------------------------------------------
# Scorer 3: Groundedness — LLM judge
# ---------------------------------------------------------------------------

_GROUNDEDNESS_PROMPT = """\
You are a content auditor for a vacation rental platform.

Given property data and generated marketing copy, identify any specific FACTUAL claims
in the marketing copy that are NOT directly supported by the property data.

Focus only on verifiable facts: amenity names, guest capacity, bedroom/bathroom counts,
location (city/country), review scores, and policies. Ignore tone and marketing language.
Do NOT flag reasonable inferences (e.g. "high-speed" for InternetBroadband is acceptable).

Property data:
{property_data}

Generated marketing copy:
{generated}

Respond ONLY with this exact JSON (no extra text, no markdown):
{{
  "unsupported_claims": ["unsupported fact 1", "unsupported fact 2"],
  "verdict": "PASS or FAIL",
  "reasoning": "one sentence explanation"
}}

Rules:
- unsupported_claims must be an array of plain strings with no special characters or nested quotes
- verdict is PASS when unsupported_claims is empty, FAIL otherwise
"""


@scorer(metrics=[mean()])
def groundedness_scorer():
    judge = get_model("anthropic/claude-haiku-4-5-20251001")

    async def score(state, target) -> Score:
        generated = state.metadata.get("generated", {})
        prop_raw = state.metadata.get("property", {})

        prompt = _GROUNDEDNESS_PROMPT.format(
            property_data=json.dumps(prop_raw, indent=2, ensure_ascii=False),
            generated=json.dumps(generated, indent=2, ensure_ascii=False),
        )

        result = await judge.generate(prompt)
        raw = result.completion.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            parsed = json.loads(raw)
            verdict = parsed.get("verdict", "FAIL")
            unsupported = parsed.get("unsupported_claims", [])
            reasoning = parsed.get("reasoning", "")
        except json.JSONDecodeError:
            verdict_m = re.search(r'"verdict"\s*:\s*"(\w+)"', raw)
            verdict = verdict_m.group(1) if verdict_m else "FAIL"
            reasoning_m = re.search(r'"reasoning"\s*:\s*"([^"]*)"', raw)
            reasoning = reasoning_m.group(1) if reasoning_m else raw[:200]
            unsupported = []

        numeric = 1.0 if verdict == "PASS" else 0.0
        explanation = reasoning
        if unsupported:
            explanation += f" | Unsupported: {'; '.join(unsupported)}"

        return Score(
            value=numeric,
            answer=verdict,
            explanation=explanation,
        )

    return score


# ---------------------------------------------------------------------------
# Scorer 4: Marketing Quality — LLM judge
# ---------------------------------------------------------------------------

_QUALITY_PROMPT = """\
You are a senior marketing reviewer for a vacation rental platform.

Rate the following marketing copy on three dimensions (1-5 each):
- appeal: Does the headline create desire and feel compelling (not generic)?
- specificity: Are the highlights concrete and property-specific (not filler phrases)?
- coherence: Does the about section flow naturally and build a vivid picture?

Marketing copy:
{generated}

Respond ONLY with valid JSON:
{{
  "appeal": <1-5>,
  "specificity": <1-5>,
  "coherence": <1-5>,
  "reasoning": "brief explanation"
}}
"""


@scorer(metrics=[mean()])
def marketing_quality_scorer():
    judge = get_model("anthropic/claude-haiku-4-5-20251001")

    async def score(state, target) -> Score:
        generated = state.metadata.get("generated", {})

        prompt = _QUALITY_PROMPT.format(
            generated=json.dumps(generated, indent=2, ensure_ascii=False)
        )

        result = await judge.generate(prompt)
        raw = result.completion.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {}
            for key in ("appeal", "specificity", "coherence"):
                m = re.search(rf'"{key}"\s*:\s*(\d+)', raw)
                if m:
                    parsed[key] = int(m.group(1))
            reasoning_m = re.search(r'"reasoning"\s*:\s*"([^"]*)"', raw)
            parsed["reasoning"] = reasoning_m.group(1) if reasoning_m else ""

        try:
            appeal = float(parsed.get("appeal", 1))
            specificity = float(parsed.get("specificity", 1))
            coherence = float(parsed.get("coherence", 1))
            reasoning = parsed.get("reasoning", "")
            avg = (appeal + specificity + coherence) / 3
            normalized = (avg - 1) / 4  # map 1-5 → 0-1
        except (TypeError, ValueError):
            normalized = 0.0
            appeal = specificity = coherence = 0
            reasoning = f"Parse failed: {raw[:200]}"

        return Score(
            value=round(normalized, 3),
            answer="PASS" if normalized >= 0.5 else "FAIL",
            explanation=f"appeal={appeal} specificity={specificity} coherence={coherence} | {reasoning}",
            metadata={"appeal": appeal, "specificity": specificity, "coherence": coherence},
        )

    return score


# ---------------------------------------------------------------------------
# Scorer 5: Golden Constraints — hybrid rule-based + LLM (golden_eval only)
# ---------------------------------------------------------------------------

_GOLDEN_SOFT_PROMPT = """\
Given the following vacation rental marketing copy and the constraints it must satisfy,
rate the overall tone and naturalness of the copy (1-5).

Constraints satisfied: {constraints_summary}
Marketing copy: {generated}

Respond ONLY with valid JSON:
{{
  "tone_score": <1-5>,
  "reasoning": "brief explanation"
}}
"""


@scorer(metrics=[mean()])
def golden_constraints_scorer():
    """Reads must_mention / must_not_mention constraints from sample metadata."""
    judge = get_model("anthropic/claude-haiku-4-5-20251001")

    async def score(state, target) -> Score:
        generated = state.metadata.get("generated", {})
        full_text = _all_generated_text(generated)

        must_mention: list[str] = state.metadata.get("must_mention", [])
        must_not_mention: list[str] = state.metadata.get("must_not_mention", [])

        missing = [phrase for phrase in must_mention if phrase.lower() not in full_text]
        leaked = [phrase for phrase in must_not_mention if phrase.lower() in full_text]

        mention_score = (len(must_mention) - len(missing)) / len(must_mention) if must_mention else 1.0
        avoid_score = (len(must_not_mention) - len(leaked)) / len(must_not_mention) if must_not_mention else 1.0
        rule_score = (mention_score + avoid_score) / 2

        details = []
        if missing:
            details.append(f"missing: {missing}")
        if leaked:
            details.append(f"leaked forbidden phrases: {leaked}")

        soft_score = 0.0
        if mention_score >= 0.8 and not leaked:
            constraints_summary = (
                f"Must mention: {must_mention}. Must not mention: {must_not_mention}."
            )
            prompt = _GOLDEN_SOFT_PROMPT.format(
                constraints_summary=constraints_summary,
                generated=json.dumps(generated, indent=2, ensure_ascii=False),
            )
            result = await judge.generate(prompt)
            raw = result.completion.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            try:
                parsed = json.loads(raw)
                tone = float(parsed.get("tone_score", 3))
                soft_score = (tone - 1) / 4
                details.append(f"tone={tone} | {parsed.get('reasoning', '')}")
            except (json.JSONDecodeError, TypeError, ValueError):
                soft_score = 0.5
                details.append("Could not parse tone score")
        else:
            details.append("Skipped soft eval (rule-based part failed)")

        final = rule_score * 0.7 + soft_score * 0.3 if mention_score >= 0.8 and not leaked else rule_score

        category = state.metadata.get("golden_category", "unknown")
        return Score(
            value=round(final, 3),
            answer="PASS" if mention_score == 1.0 and not leaked else "FAIL",
            explanation="; ".join(details) if details else "All constraints satisfied",
            metadata={
                "mention_score": round(mention_score, 3),
                "avoid_score": round(avoid_score, 3),
                "missing_phrases": missing,
                "leaked_phrases": leaked,
                "category": category,
            },
        )

    return score
