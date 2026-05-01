# Lodgify Content Generation — Engineering Assignment

A vacation rental property listing content generator with an **evaluation-first** design.
The primary deliverable is the evaluation suite — the code that measures whether the generated content is grounded, accurate, and useful.

---

## System Flow

```
══════════════════════════════════════════════════════════════
 ONE-TIME SETUP  (requires ANTHROPIC_API_KEY)
══════════════════════════════════════════════════════════════

  fixtures.py                    golden.py
  6 mock properties              5 samples:
  (villa, apartment, cottage,    standard / edge case / adversarial
   bungalow, chalet,
   HTML-description townhouse)
           │                            │
           └──────────────┬─────────────┘
                          │ PropertyData
                          ▼
               ┌──────────────────────┐
               │   Content Generator  │  ← AnthropicContentGenerator
               │   (generator.py)     │    model: claude-haiku-4-5
               └──────────┬───────────┘
                          │ MarketingContent
                          ▼
         ┌────────────────────────────────────────┐
         │           Inspect AI Eval              │
         │                                        │
         │  fixture_eval  (6 samples)             │
         │  golden_eval   (5 samples)             │
         │                                        │
         │  Scorers applied to each sample:       │
         │  ┌─ structural_completeness  (rules)   │
         │  ├─ factual_accuracy         (rules)   │
         │  ├─ groundedness             (LLM judge)│
         │  ├─ marketing_quality        (LLM judge)│
         │  └─ golden_constraints       (hybrid)  │
         │       └─ must_mention / must_not_mention│
         └──────────────┬─────────────────────────┘
                        │
                        ▼
                  logs/*.eval
              (committed to repo)

══════════════════════════════════════════════════════════════
 REVIEW  (no API key — just uv sync && marimo run dashboard.py)
══════════════════════════════════════════════════════════════

                  logs/*.eval
                       │
                       ▼
          ┌────────────────────────┐
          │   Marimo Dashboard     │
          │   (dashboard.py)       │
          └────────────┬───────────┘
                       │
          ┌────────────┼─────────────┐
          ▼            ▼             ▼
    Generated      Scores        Golden
    content        heatmap       dataset
    per property   (all scorers) + adversarial
                                  detection
```

---

## Approach

### Evaluation-first design

The evaluation suite is the core of this project. Content generation is only as good as our ability to measure it. There are three levels at which evaluation matters:

**1. Online quality gates** *(implemented as rule-based scorers)*
Before content is served, fast rule-based checks verify structural completeness and factual accuracy. These are cheap (no API calls) and can be run inline, triggering a fallback to templated content if they fail.

**2. Offline content quality** *(implemented as Inspect AI tasks)*
After generation, LLM-judge scorers evaluate whether content is grounded (no hallucinations), specific (not generic filler), and well-written. The golden dataset adds reference-based assertions (`must_mention` / `must_not_mention`) including adversarial cases that test prompt injection resistance.

**3. Business outcome metrics** *(documented, not instrumented here)*
The metrics we ultimately care about are downstream: booking conversion rate on pages with generated vs. templated copy, time-to-publish (how much manual editing is needed), and manual adjustment rate per property. These require production instrumentation and A/B experiment infrastructure — a natural next step once this pipeline is deployed.

### Evaluation scorers

| Scorer | Type | What it checks |
|--------|------|----------------|
| `structural_completeness` | Rule-based | All required fields present, correct lengths, no HTML tag leakage |
| `factual_accuracy` | Rule-based | City, country, capacity, bedroom/bathroom counts, review score — all traceable to source |
| `groundedness` | LLM judge | No claims unsupported by the input property data |
| `marketing_quality` | LLM judge | Appeal (headline), specificity (highlights), coherence (about section) — rated 1–5 |
| `golden_constraints` | Hybrid | `must_mention` phrases present + `must_not_mention` phrases absent; soft tone check if rule part passes |

### Golden dataset

Five samples designed to stress-test the pipeline:

| Category | What it tests |
|----------|--------------|
| Standard (×2) | Baseline quality — location, capacity, context-appropriate vocabulary |
| Edge case: no reviews | No fabricated social proof ("highly rated", "guests love") |
| Edge case: studio, 1 guest | No hallucinated bedrooms; respects extreme capacity constraints |
| Adversarial: prompt injection | Injection in description field must not appear in generated output |

### HTML handling

Fixture #6 (Lisbon townhouse) has a description field full of `<p>`, `<strong>`, `<br>` HTML tags. The structural completeness scorer explicitly checks that no HTML tags leak into generated marketing copy.

---

## How to Run

### 1. Install dependencies

```bash
uv sync
```

### 2. View the evaluation results (no API key needed)

Evaluation logs are committed to this repository. Just run:

```bash
uv run marimo run dashboard.py
```

Then open the URL shown in your terminal. Use the tabs and dropdown to explore generated content and scores per property.

### 3. Run the tests (no API key needed)

```bash
uv run pytest tests/ -v
```

All 36 tests pass with zero API calls — LLM interactions are fully mocked.

### 4. Re-run the evaluations (requires API key)

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

uv run inspect eval evals/tasks.py --log-dir logs/
```

This regenerates content for all fixtures and golden samples, runs all scorers, and writes new `.eval` log files to `logs/`.

---

## Viewing Inspect AI Logs

Logs are stored in `logs/` as `.eval` files (binary, compressed).

**Via the Marimo dashboard** (recommended):
```bash
uv run marimo run dashboard.py
```

**Via Inspect AI's built-in viewer**:
```bash
uv run inspect view
```

**Programmatically**:
```python
from inspect_ai.log import read_eval_log, list_eval_logs

logs = list_eval_logs("logs/")
log = read_eval_log(logs[0])

for sample in log.samples:
    print(sample.id, {k: v.answer for k, v in (sample.scores or {}).items()})
```

---

## Project Structure

```
content_generation/
├── pyproject.toml
├── .env.example
├── README.md
├── src/
│   └── content_generation/
│       ├── models.py         # PropertyData, MarketingContent, GoldenSample
│       ├── amenities.py      # Amenity code → human-readable label
│       ├── prompts.py        # Generation prompt builder
│       ├── generator.py      # ContentGeneratorBase + AnthropicContentGenerator
│       ├── fixtures.py       # 6 mock PropertyData instances
│       └── golden.py         # 5 GoldenSample instances with must_mention constraints
├── evals/
│   ├── solvers.py            # content_generation_solver
│   ├── scorers.py            # 5 Inspect AI scorers
│   └── tasks.py              # fixture_eval + golden_eval tasks
├── tests/
│   ├── conftest.py           # shared fixtures and mocks
│   ├── test_models.py
│   ├── test_generator.py
│   └── test_scorers.py
├── logs/                     # committed .eval log files
└── dashboard.py              # Marimo results dashboard
```

---

## How I Used AI

**Anthropic API (claude-haiku-4-5)** is used in two places:
1. **Content generation** — the `AnthropicContentGenerator` calls the API with a structured prompt to produce `MarketingContent` JSON from `PropertyData`.
2. **LLM-judge scorers** — `groundedness_scorer` and `marketing_quality_scorer` call the API to evaluate generated content; `golden_constraints_scorer` calls it as a soft quality check when rule-based constraints pass.

**Claude Code** was used to scaffold and iterate on all the code in this repository, including designing the evaluation rubrics, writing tests, and structuring the Marimo dashboard.

---

## What I'd Do Next

- **A/B experiment infrastructure**: use `inspect_ai.eval_set` to compare prompt variants (e.g., Haiku vs Sonnet, different prompt strategies) with a shared scorer suite, producing a ranked leaderboard.
- **Business metric proxies**: add a "publication readiness" scorer (LLM judge rating how much editing the content would need) as a proxy for time-to-publish.
- **Semantic similarity scorer**: embed generated vs. golden content and score cosine similarity as an additional reference-based metric.
- **Caching layer**: add Inspect AI prompt caching to reduce LLM judge API costs on large datasets.
- **CI integration**: run `inspect eval` on every PR that touches prompts or the generator, with a score regression threshold that blocks merges.
