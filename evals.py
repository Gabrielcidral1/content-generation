import marimo

__generated_with = "0.23.4"
app = marimo.App(width="full")


@app.cell
def _imports():
    import json
    import os
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go

    from inspect_ai.log import list_eval_logs, read_eval_log

    from content_generation.amenities import human_amenity

    LOGS_DIR = str(Path(__file__).parent / "logs")
    return LOGS_DIR, Path, go, human_amenity, json, list_eval_logs, mo, np, os, pd, read_eval_log


@app.cell
def _load_logs(LOGS_DIR, list_eval_logs, mo, read_eval_log):
    _log_infos = []
    try:
        _log_infos = list_eval_logs(LOGS_DIR)
    except Exception:
        pass

    mo.stop(
        not _log_infos,
        mo.callout(
            mo.md(
                "**No evaluation logs found.**\n\n"
                "Run the evaluations first:\n"
                "```bash\n"
                "cp .env.example .env  # add your ANTHROPIC_API_KEY\n"
                "uv run inspect eval evals/tasks.py --log-dir logs/\n"
                "```"
            ),
            kind="warn",
        ),
    )

    _by_task = {}
    all_runs = {}  # task_name -> [log, ...] sorted oldest-first
    for _info in sorted(_log_infos, key=lambda x: x.name):
        _log = read_eval_log(_info)
        _task_name = (_log.eval.task if _log.eval else None) or _info.name
        _by_task[_task_name] = _log  # keeps most recent
        all_runs.setdefault(_task_name, []).append(_log)
    logs = _by_task
    return (logs, all_runs)


@app.cell
def _helpers():
    def fmt_scorer(name: str) -> str:
        return name.replace("_scorer", "").replace("_", " ").title()

    def score_to_float(v) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        return 1.0 if v == "PASS" else 0.0

    # Weights sum to 1.0. composite_score normalizes by matched weights, so fixture
    # samples (no Golden Constraints) still produce a valid composite over the 4 others.
    SCORER_WEIGHTS = {
        "Factual Accuracy": 0.30,
        "Marketing Quality": 0.25,
        "Groundedness": 0.20,
        "Golden Constraints": 0.15,
        "Structural Completeness": 0.10,
    }

    def composite_score(scores_dict: dict, fmt_fn) -> float:
        total, wsum = 0.0, 0.0
        for name, sc in scores_dict.items():
            w = SCORER_WEIGHTS.get(fmt_fn(name), 0.0)
            if w:
                wsum += w * score_to_float(sc.value)
                total += w
        return wsum / total if total else 0.0

    return SCORER_WEIGHTS, composite_score, fmt_scorer, score_to_float


@app.cell
def _header(mo, logs):
    _total = sum(len(log.samples) for log in logs.values() if log.samples)
    mo.vstack([
        mo.md("# Lodgify Content Generation Evaluation"),
        mo.md(f"**{len(logs)} evaluation tasks** · **{_total} properties evaluated**"),
        mo.callout(
            mo.md(
                "**How to use this dashboard**\n\n"
                "1. The **Composite Score** card compares the LLM generator against the template baseline "
                "across all evaluated properties.\n"
                "2. Use **Per Property Analysis** to browse the generated marketing copy and individual "
                "scorer results for any fixture property. Switch between generators using the tabs.\n"
                "3. The **Golden Evaluation** section shows constraint satisfaction "
                "(must-mention / must-not-mention) for edge cases and adversarial inputs."
            ),
            kind="info",
        ),
    ])
    return ()


@app.cell
def _composite_summary(mo, logs, go, np, SCORER_WEIGHTS, composite_score, fmt_scorer):
    def _samples_for(task_filter):
        return [
            (
                (s.metadata or {}).get("property", {}).get("property_name", s.id),
                composite_score(s.scores or {}, fmt_scorer),
            )
            for task_name, log in logs.items()
            for s in (log.samples or [])
            if s.scores and task_filter(task_name)
        ]

    _is_template = lambda name: name.endswith("_template")
    _is_llm = lambda name: not _is_template(name)

    _llm_samples = _samples_for(_is_llm)
    _tpl_samples = _samples_for(_is_template)

    mo.stop(not _llm_samples)

    def _avg(pairs): return sum(v for _, v in pairs) / len(pairs) if pairs else None

    _llm_avg = _avg(_llm_samples)
    _tpl_avg = _avg(_tpl_samples)

    def _grade_color(v):
        if v >= 0.80: return "#16a34a"
        if v >= 0.60: return "#d97706"
        return "#dc2626"

    def _grade_label(v):
        if v >= 0.80: return "Strong"
        if v >= 0.60: return "Moderate"
        return "Weak"

    _weight_pills = " ".join(
        f'<span style="background:#f3f4f6;border-radius:4px;padding:3px 8px;font-size:12px;color:#374151;">'
        f'{k} <strong>{round(v*100)}%</strong></span>'
        for k, v in SCORER_WEIGHTS.items()
    )

    _llm_color = _grade_color(_llm_avg)
    _llm_pct = round(_llm_avg * 100)

    if _tpl_avg is not None:
        _lift = _llm_avg - _tpl_avg
        _lift_sign = "+" if _lift >= 0 else ""
        _lift_color = "#16a34a" if _lift > 0.01 else ("#dc2626" if _lift < -0.01 else "#9ca3af")
        _baseline_block = f"""
        <div style="text-align:center;min-width:90px;padding-left:20px;border-left:1px solid #e5e7eb;">
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">Template</div>
          <div style="font-size:32px;font-weight:700;line-height:1;color:{_grade_color(_tpl_avg)};">{_tpl_avg:.2f}</div>
          <div style="font-size:11px;color:#9ca3af;margin-top:2px;">{_grade_label(_tpl_avg)}</div>
        </div>
        <div style="text-align:center;min-width:80px;padding-left:20px;border-left:1px solid #e5e7eb;">
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">Lift</div>
          <div style="font-size:32px;font-weight:700;line-height:1;color:{_lift_color};">{_lift_sign}{_lift:.2f}</div>
          <div style="font-size:11px;color:#9ca3af;margin-top:2px;">LLM vs template</div>
        </div>"""
    else:
        _baseline_block = ""

    _tpl_by_name = dict(_tpl_samples)
    _llm_by_name = dict(_llm_samples)
    _paired = [
        (name, _llm_by_name[name], _tpl_by_name[name])
        for name in set(_llm_by_name) & set(_tpl_by_name)
    ]

    if _paired:
        _names  = [n for n, _, _ in _paired]
        _llm_sc = [l for _, l, _ in _paired]
        _tpl_sc = [t for _, _, t in _paired]
        _lifts  = [l - t for l, t in zip(_llm_sc, _tpl_sc)]

        _scatter = go.Figure()
        _scatter.add_shape(
            type="line", x0=0, y0=0, x1=1, y1=1,
            line=dict(color="#d1d5db", width=1, dash="dot"),
        )
        _scatter.add_annotation(x=0.92, y=0.80, text="LLM wins ▲",
            showarrow=False, font=dict(size=10, color="#9ca3af"))
        _scatter.add_annotation(x=0.80, y=0.92, text="Template wins ▲",
            showarrow=False, font=dict(size=10, color="#9ca3af"), textangle=-45)
        _scatter.add_trace(go.Scatter(
            x=_tpl_sc, y=_llm_sc,
            mode="markers",
            text=_names,
            marker=dict(
                size=12,
                color=_lifts,
                colorscale=[[0, "#ef4444"], [0.5, "#f59e0b"], [1, "#22c55e"]],
                cmid=0,
                showscale=True,
                colorbar=dict(title="Lift", thickness=12, len=0.8),
                line=dict(width=1, color="white"),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "LLM: %{y:.3f}<br>"
                "Template: %{x:.3f}<br>"
                "Lift: %{marker.color:+.3f}"
                "<extra></extra>"
            ),
        ))
        _scatter.update_layout(
            xaxis=dict(title="Template score", range=[0, 1], gridcolor="#f3f4f6"),
            yaxis=dict(title="LLM score", range=[0, 1], gridcolor="#f3f4f6"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=340,
            margin=dict(l=50, r=60, t=20, b=50),
        )

        # Histogram: 0 is always a bin boundary — split into two traces
        _min_lift, _max_lift = min(_lifts), max(_lifts)
        _raw_step = (_max_lift - _min_lift) / max(6, len(_lifts) // 2)
        # Round to nearest 0.05 for clean axis labels
        _step = max(0.05, round(round(_raw_step / 0.05) * 0.05, 10))

        _neg_lifts = [v for v in _lifts if v < 0]
        _pos_lifts = [v for v in _lifts if v >= 0]

        _hist = go.Figure()
        if _neg_lifts:
            _hist.add_trace(go.Histogram(
                x=_neg_lifts,
                xbins=dict(start=_min_lift - _step / 2, end=0, size=_step),
                marker_color="#ef4444",
                showlegend=False,
                hovertemplate="Lift %{x:.2f}: %{y} properties<extra></extra>",
            ))
        if _pos_lifts:
            _hist.add_trace(go.Histogram(
                x=_pos_lifts,
                xbins=dict(start=0, end=_max_lift + _step / 2, size=_step),
                marker_color="#22c55e",
                showlegend=False,
                hovertemplate="Lift %{x:.2f}: %{y} properties<extra></extra>",
            ))
        _hist.add_vline(x=0, line_width=1, line_dash="dot", line_color="#9ca3af")
        _hist.update_layout(
            xaxis=dict(title="Lift (LLM − template)", gridcolor="#f3f4f6"),
            yaxis=dict(title="# properties", gridcolor="#f3f4f6", dtick=1),
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=340,
            margin=dict(l=50, r=20, t=20, b=50),
            bargap=0.05,
            showlegend=False,
        )

        _charts = mo.hstack([mo.as_html(_scatter), mo.as_html(_hist)], gap=1)
    else:
        _charts = mo.md("")

    mo.vstack([
        mo.Html(f"""
        <div style="font-family:system-ui,-apple-system,sans-serif;border:1px solid #e5e7eb;border-radius:10px;padding:20px 24px;margin:12px 0;">
          <div style="display:flex;gap:24px;align-items:flex-start;margin-bottom:16px;">
            <div style="text-align:center;min-width:110px;">
              <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">LLM Generator</div>
              <div style="font-size:52px;font-weight:800;line-height:1;color:{_llm_color};">{_llm_avg:.2f}</div>
              <div style="font-size:13px;font-weight:600;color:{_llm_color};margin-top:4px;">{_grade_label(_llm_avg)}</div>
              <div style="font-size:11px;color:#9ca3af;margin-top:2px;">{len(_llm_samples)} properties</div>
              <div style="background:#f3f4f6;border-radius:4px;height:6px;overflow:hidden;margin-top:8px;">
                <div style="width:{_llm_pct}%;height:100%;background:{_llm_color};border-radius:4px;"></div>
              </div>
            </div>
            {_baseline_block}
            <div style="flex:1;padding-left:20px;border-left:1px solid #e5e7eb;">
              <div style="font-size:12px;color:#6b7280;margin-bottom:6px;font-weight:500;">WEIGHTS — factual integrity first, then booking appeal</div>
              <div style="display:flex;flex-wrap:wrap;gap:6px;">{_weight_pills}</div>
            </div>
          </div>
        </div>
        """),
        _charts,
    ])
    return ()


# ---------------------------------------------------------------------------
# Per-property analysis — fixture evals only
# ---------------------------------------------------------------------------

@app.cell
def _fixture_tabs(mo, logs):
    _label_map = {
        "fixture_eval": "LLM Generator",
        "fixture_eval_template": "Template Baseline",
    }
    _fixture_names = [n for n in logs if "golden" not in n]
    mo.stop(not _fixture_names)
    # Map display label → task name so we can resolve .value downstream
    fixture_display_to_task = {_label_map.get(n, n): n for n in _fixture_names}
    fixture_task_tabs = mo.ui.tabs({
        _label_map.get(n, n): mo.md("") for n in _fixture_names
    })
    return (fixture_task_tabs, fixture_display_to_task)


@app.cell
def _selected_fixture(fixture_task_tabs, fixture_display_to_task, logs):
    _task_name = fixture_display_to_task.get(fixture_task_tabs.value, fixture_task_tabs.value)
    _log = logs.get(_task_name)
    fixture_samples = (_log.samples or []) if _log else []
    return (fixture_samples,)


@app.cell
def _fixture_property_selector(mo, fixture_samples):
    mo.stop(not fixture_samples)
    _names = {
        (s.metadata or {}).get("property", {}).get("property_name", s.id): s.id
        for s in fixture_samples
    }
    fixture_prop_dropdown = mo.ui.dropdown(
        options=_names,
        value=list(_names.keys())[0],
        label="Select property",
    )
    return (fixture_prop_dropdown,)


@app.cell
def _per_property_section(mo, fixture_task_tabs, fixture_samples, pd, fmt_scorer, fixture_prop_dropdown, SCORER_WEIGHTS, composite_score, human_amenity):
    mo.stop(not fixture_samples)

    _selected = next((s for s in fixture_samples if s.id == fixture_prop_dropdown.value), fixture_samples[0])
    _prop_data = (_selected.metadata or {}).get("property", {})
    _generated = (_selected.metadata or {}).get("generated", {})

    _loc = _prop_data.get("location", {})
    _info = _prop_data.get("rental_info", {})
    _rules = _prop_data.get("house_rules", {})
    _desc_data = _prop_data.get("description", {})
    _policies = _prop_data.get("policies", {})
    _reviews = _prop_data.get("reviews", [])
    _image_urls = _prop_data.get("image_urls", [])
    _amenities = _prop_data.get("amenities", [])
    _n = _prop_data.get("num_of_reviews", 0)

    def _esc(s: str) -> str:
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _section_label(text):
        return f'<div style="font-size:10px;color:#9ca3af;font-weight:700;text-transform:uppercase;letter-spacing:.07em;margin-bottom:4px;">{text}</div>'

    _desc_raw = _desc_data.get("description", "")
    _has_html_in_desc = "<" in _desc_raw and ">" in _desc_raw
    _html_tag = (
        '<span style="display:inline-block;margin-left:6px;padding:1px 6px;border-radius:3px;'
        'background:#fef3c7;color:#92400e;font-size:10px;font-weight:600;">HTML</span>'
        if _has_html_in_desc else ""
    )

    _amenity_chips = "".join(
        f'<code style="display:inline-block;background:#f3f4f6;border-radius:3px;padding:2px 6px;'
        f'font-size:11px;color:#374151;margin:2px;">{a}</code>'
        for a in _amenities
    )

    _reviews_html = ""
    for _i, _rev in enumerate(_reviews):
        _reviews_html += (
            f'<details style="margin-bottom:4px;">'
            f'<summary style="cursor:pointer;font-size:12px;color:#6366f1;user-select:none;">'
            f'Review {_i + 1}</summary>'
            f'<div style="padding:6px 0 4px 0;color:#374151;font-size:12px;line-height:1.55;">'
            f'{_esc(_rev)}</div></details>'
        )

    _images_html = "".join(
        f'<div style="font-size:11px;color:#6b7280;overflow:hidden;text-overflow:ellipsis;'
        f'white-space:nowrap;margin-bottom:2px;" title="{_esc(url)}">{_esc(url)}</div>'
        for url in _image_urls
    ) or '<span style="color:#9ca3af;font-size:12px;">—</span>'

    _score_str = (
        f'⭐ {_prop_data.get("average_review_score")} · {_n} reviews'
        if _n > 0 else "No reviews yet"
    )

    _input_html = f"""
    <div style="font-family:system-ui,-apple-system,sans-serif;font-size:14px;">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;
                  padding-bottom:12px;border-bottom:1px solid #f3f4f6;">
        <span style="font-size:16px;font-weight:700;color:#111827;">
          {_esc(_prop_data.get("property_name", ""))}</span>
        <span style="padding:2px 8px;background:#f3f4f6;border-radius:4px;
                     font-size:12px;color:#374151;">
          {_esc(_prop_data.get("property_type", ""))}</span>
        <span style="margin-left:auto;font-size:11px;color:#9ca3af;">
          ID: {_prop_data.get("property_id", "—")}</span>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">

        <!-- Left column: structured facts -->
        <div>
          <div style="margin-bottom:12px;">
            {_section_label("Location")}
            <div style="font-size:13px;color:#374151;">
              {_esc(_loc.get("city", ""))}, {_esc(_loc.get("country", ""))}
            </div>
            <div style="font-size:11px;color:#9ca3af;margin-top:2px;">
              {_loc.get("latitude", "")}, {_loc.get("longitude", "")}
            </div>
          </div>

          <div style="margin-bottom:12px;">
            {_section_label("Rental Info")}
            <div style="font-size:13px;color:#374151;">
              {_info.get("max_guests", "—")} guests ·
              {_info.get("bedrooms", "—")} bed ·
              {_info.get("bathrooms", "—")} bath
            </div>
          </div>

          <div style="margin-bottom:12px;">
            {_section_label("House Rules")}
            <div style="font-size:13px;color:#374151;">
              Check-in {_esc(str(_rules.get("check_in_time") or "—"))} ·
              Check-out {_esc(str(_rules.get("check_out_time") or "—"))}
            </div>
          </div>

          <div style="margin-bottom:12px;">
            {_section_label("Reviews")}
            <div style="font-size:13px;color:#374151;">{_score_str}</div>
          </div>

          <div style="margin-bottom:12px;">
            {_section_label("Policies")}
            <div style="font-size:12px;color:#374151;line-height:1.7;">
              <div><span style="color:#6b7280;">Cancellation:</span>
                   {_esc(str(_policies.get("cancellation_policy") or "—"))}</div>
              <div><span style="color:#6b7280;">Payment:</span>
                   {_esc(str(_policies.get("payment_schedule") or "—"))}</div>
              <div><span style="color:#6b7280;">Damage deposit:</span>
                   {_esc(str(_policies.get("damage_deposit") or "—"))}</div>
            </div>
          </div>

          <div style="margin-bottom:12px;">
            {_section_label(f"Amenities ({len(_amenities)})")}
            <div style="margin-top:4px;display:flex;flex-wrap:wrap;gap:2px;">
              {_amenity_chips}
            </div>
          </div>

          <div>
            {_section_label(f"Image URLs ({len(_image_urls)})")}
            <div style="margin-top:4px;">{_images_html}</div>
          </div>
        </div>

        <!-- Right column: description + reviews -->
        <div>
          <div style="margin-bottom:14px;">
            {_section_label("Description")}
            <div style="font-size:12px;color:#6b7280;margin-bottom:2px;">
              <span style="color:#374151;">name:</span>
              {_esc(_desc_data.get("name", "—"))}
            </div>
            <div style="font-size:12px;color:#6b7280;margin-bottom:6px;">
              <span style="color:#374151;">headline:</span>
              {_esc(_desc_data.get("headline", "—"))}
            </div>
            <details>
              <summary style="cursor:pointer;font-size:12px;color:#6366f1;user-select:none;">
                description text {_html_tag}
              </summary>
              <div style="padding:8px;margin-top:6px;background:#f9fafb;border:1px solid #e5e7eb;
                          border-radius:4px;font-size:12px;color:#374151;line-height:1.55;
                          white-space:pre-wrap;word-break:break-word;">
                {_esc(_desc_raw)}
              </div>
            </details>
          </div>

          <div>
            {_section_label(f"Guest Reviews ({_n})")}
            <div style="margin-top:4px;">
              {_reviews_html or '<span style="color:#9ca3af;font-size:12px;">No reviews</span>'}
            </div>
          </div>
        </div>

      </div>
    </div>
    """

    _highlights = "\n".join(f"- {h}" for h in _generated.get("property_highlights", []))
    _amenities_md = "\n".join(
        f"- **{human_amenity(k)}**: {v}" for k, v in _generated.get("amenities_descriptions", {}).items()
    )

    _panel = mo.hstack(
        [
            mo.vstack(
                [
                    mo.md("### Property Input"),
                    mo.Html(_input_html),
                ],
                align="start",
            ),
            mo.vstack(
                [
                    mo.md("### Generated Marketing Copy"),
                    mo.md(
                        f"#### {_generated.get('hero_headline', '_no headline_')}\n\n"
                        f"**Highlights**\n{_highlights}\n\n"
                        f"**About this place**\n\n{_generated.get('about_section', '_not generated_')}\n\n"
                        f"**Amenities**\n{_amenities_md}"
                    ),
                ],
                align="start",
            ),
        ],
        justify="start",
        align="start",
        gap=2,
    )

    _SCORER_DESC = {
        "Structural Completeness": "Required fields present, correct lengths, no HTML leakage",
        "Factual Accuracy": "City, country, guest capacity, bedroom/bathroom counts match source data",
        "Groundedness": "No claims unsupported by property data (LLM judge)",
        "Marketing Quality": "Appeal, specificity and coherence rated 1–5 (LLM judge)",
        "Golden Constraints": "must_mention phrases present + must_not_mention phrases absent (hybrid rule + LLM)",
    }

    def _bar_color(v):
        if v >= 0.85:
            return "#22c55e"
        if v >= 0.5:
            return "#f59e0b"
        return "#ef4444"

    _prop_composite = composite_score(_selected.scores or {}, fmt_scorer)
    _comp_color = _bar_color(_prop_composite)
    _comp_pct = round(_prop_composite * 100)

    # Effective normalized weights: raw_weight / sum(matched raw weights)
    _total_w = sum(
        SCORER_WEIGHTS.get(fmt_scorer(_n), 0.0)
        for _n in (_selected.scores or {})
        if SCORER_WEIGHTS.get(fmt_scorer(_n), 0.0)
    )

    _rows_html = ""
    for _name, _sc in (_selected.scores or {}).items():
        _label = fmt_scorer(_name)
        _v = round(float(_sc.value), 3) if isinstance(_sc.value, (int, float)) else 0.0
        _verdict = _sc.answer or "—"
        _expl = (_sc.explanation or "")
        _pct = round(_v * 100)
        _color = _bar_color(_v)
        _is_pass = _verdict == "PASS"
        _badge_bg = "#dcfce7" if _is_pass else "#fee2e2"
        _badge_fg = "#16a34a" if _is_pass else "#dc2626"
        _desc = _SCORER_DESC.get(_label, "")
        _raw_w = SCORER_WEIGHTS.get(_label, 0.0)
        _eff_w = _raw_w / _total_w if _total_w else 0.0
        _contribution = _eff_w * _v
        _rows_html += f"""
        <tr style="border-bottom:1px solid #f3f4f6;">
          <td style="padding:12px 14px;">
            <div style="font-weight:500;color:#111827;">{_label}</div>
            <div style="font-size:12px;color:#9ca3af;margin-top:3px;">{_desc}</div>
          </td>
          <td style="padding:12px 14px;font-weight:700;color:{_color};font-variant-numeric:tabular-nums;">{_v:.3f}</td>
          <td style="padding:12px 14px;min-width:150px;">
            <div style="background:#f3f4f6;border-radius:4px;height:8px;overflow:hidden;">
              <div style="width:{_pct}%;height:100%;background:{_color};border-radius:4px;"></div>
            </div>
          </td>
          <td style="padding:12px 14px;">
            <span style="display:inline-block;padding:3px 10px;border-radius:9999px;font-size:12px;font-weight:600;background:{_badge_bg};color:{_badge_fg};">{_verdict}</span>
          </td>
          <td style="padding:12px 14px;text-align:center;font-size:13px;color:#374151;font-weight:600;">{"—" if not _raw_w else f"{round(_eff_w*100)}%"}</td>
          <td style="padding:12px 14px;text-align:center;font-size:13px;color:{_color};font-weight:600;">{"—" if not _raw_w else f"{_contribution:.3f}"}</td>
          <td style="padding:12px 14px;color:#6b7280;font-size:13px;" title="{_expl}">{_expl[:120]}{"…" if len(_expl) > 120 else ""}</td>
        </tr>"""

    _scores_widget = mo.Html(f"""
    <div style="font-family:system-ui,-apple-system,sans-serif;margin-top:8px;">
      <div style="display:flex;align-items:center;gap:16px;padding:14px 16px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px 8px 0 0;border-bottom:none;">
        <div>
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Composite Score</div>
          <div style="font-size:28px;font-weight:800;color:{_comp_color};line-height:1.1;">{_prop_composite:.2f}</div>
        </div>
        <div style="flex:1;max-width:220px;">
          <div style="background:#e5e7eb;border-radius:4px;height:8px;overflow:hidden;">
            <div style="width:{_comp_pct}%;height:100%;background:{_comp_color};border-radius:4px;"></div>
          </div>
          <div style="font-size:11px;color:#9ca3af;margin-top:4px;">weighted average of scores below</div>
        </div>
      </div>
      <div style="border:1px solid #e5e7eb;border-radius:0 0 8px 8px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <thead>
            <tr style="background:#f9fafb;border-bottom:2px solid #e5e7eb;">
              <th style="padding:10px 14px;text-align:left;color:#6b7280;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Scorer</th>
              <th style="padding:10px 14px;text-align:left;color:#6b7280;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;width:65px;">Score</th>
              <th style="padding:10px 14px;width:150px;"></th>
              <th style="padding:10px 14px;text-align:left;color:#6b7280;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;width:75px;">Verdict</th>
              <th style="padding:10px 14px;text-align:center;color:#6b7280;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;width:65px;">Weight</th>
              <th style="padding:10px 14px;text-align:center;color:#6b7280;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;width:80px;">Contribution</th>
              <th style="padding:10px 14px;text-align:left;color:#6b7280;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Explanation</th>
            </tr>
          </thead>
          <tbody>{_rows_html}</tbody>
        </table>
      </div>
    </div>
    """) if (_selected.scores) else mo.md("_No scores._")

    mo.accordion(
        {
            "Per Property Analysis": mo.vstack([
                fixture_task_tabs,
                fixture_prop_dropdown,
                _panel,
                mo.md("### Evaluation Scores"),
                _scores_widget,
            ])
        },
        multiple=True,
    )
    return ()


# ---------------------------------------------------------------------------
# Golden evaluation — constraint satisfaction metrics
# ---------------------------------------------------------------------------

@app.cell
def _golden_property_selector(mo, logs):
    _golden_log = logs.get("golden_eval")
    mo.stop(
        not _golden_log,
        mo.md("_No `golden_eval` log found. Run `inspect eval evals/tasks.py --log-dir logs/` to generate it._"),
    )
    golden_samples_all = _golden_log.samples or []
    mo.stop(not golden_samples_all)
    _names = {
        (s.metadata or {}).get("property", {}).get("property_name", s.id): s.id
        for s in golden_samples_all
    }
    golden_dropdown = mo.ui.dropdown(
        options=_names,
        value=list(_names.keys())[0],
        label="Select property",
    )
    return (golden_dropdown, golden_samples_all)


@app.cell
def _golden_section(mo, logs, golden_dropdown, golden_samples_all):
    _selected_id = golden_dropdown.value

    _llm_sample = next((s for s in golden_samples_all if s.id == _selected_id), None)
    mo.stop(not _llm_sample)

    _meta = _llm_sample.metadata or {}
    _must_mention = _meta.get("must_mention", [])
    _must_not_mention = _meta.get("must_not_mention", [])
    _category = _meta.get("golden_category", "unknown")
    _notes = _meta.get("golden_notes", "")
    _prop_name = _meta.get("property", {}).get("property_name", _llm_sample.id)

    # LLM golden constraints score
    _llm_gc = (_llm_sample.scores or {}).get("golden_constraints_scorer")
    _llm_gc_meta = (_llm_gc.metadata or {}) if _llm_gc else {}
    _llm_missing = set(_llm_gc_meta.get("missing_phrases", []))
    _llm_leaked = set(_llm_gc_meta.get("leaked_phrases", []))
    _llm_mention_score = _llm_gc_meta.get("mention_score", None)
    _llm_avoid_score = _llm_gc_meta.get("avoid_score", None)
    _llm_verdict = (_llm_gc.answer or "—") if _llm_gc else "—"
    _llm_score_val = float(_llm_gc.value) if _llm_gc and isinstance(_llm_gc.value, (int, float)) else None

    # Template golden constraints score
    _tpl_log = logs.get("golden_eval_template")
    _tpl_sample = next(
        (s for s in (_tpl_log.samples or []) if s.id == _selected_id), None
    ) if _tpl_log else None
    _tpl_gc = (_tpl_sample.scores or {}).get("golden_constraints_scorer") if _tpl_sample else None
    _tpl_gc_meta = (_tpl_gc.metadata or {}) if _tpl_gc else {}
    _tpl_missing = set(_tpl_gc_meta.get("missing_phrases", []))
    _tpl_leaked = set(_tpl_gc_meta.get("leaked_phrases", []))
    _tpl_verdict = (_tpl_gc.answer or "—") if _tpl_gc else "—"
    _tpl_score_val = float(_tpl_gc.value) if _tpl_gc and isinstance(_tpl_gc.value, (int, float)) else None

    def _verdict_badge(verdict):
        if verdict == "PASS":
            return '<span style="padding:2px 8px;border-radius:9999px;background:#dcfce7;color:#16a34a;font-size:12px;font-weight:600;">PASS</span>'
        if verdict == "FAIL":
            return '<span style="padding:2px 8px;border-radius:9999px;background:#fee2e2;color:#dc2626;font-size:12px;font-weight:600;">FAIL</span>'
        return f'<span style="padding:2px 8px;border-radius:9999px;background:#f3f4f6;color:#6b7280;font-size:12px;">{verdict}</span>'

    def _found_badge(found):
        if found:
            return '<span style="padding:2px 8px;border-radius:9999px;background:#dcfce7;color:#16a34a;font-size:12px;font-weight:600;">FOUND</span>'
        return '<span style="padding:2px 8px;border-radius:9999px;background:#fee2e2;color:#dc2626;font-size:12px;font-weight:600;">MISSING</span>'

    def _clean_badge(clean):
        if clean:
            return '<span style="padding:2px 8px;border-radius:9999px;background:#dcfce7;color:#16a34a;font-size:12px;font-weight:600;">CLEAN</span>'
        return '<span style="padding:2px 8px;border-radius:9999px;background:#fee2e2;color:#dc2626;font-size:12px;font-weight:600;">LEAKED</span>'

    _has_tpl = _tpl_gc is not None
    _tpl_col_header = '<th style="padding:8px 12px;text-align:center;color:#6b7280;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Template</th>' if _has_tpl else ""

    # Must-mention table rows
    _mm_rows = ""
    for _phrase in _must_mention:
        _llm_found = _phrase.lower() not in _llm_missing
        _tpl_col = f'<td style="padding:8px 12px;text-align:center;">{_found_badge(_phrase.lower() not in _tpl_missing)}</td>' if _has_tpl else ""
        _mm_rows += f"""
        <tr style="border-bottom:1px solid #f3f4f6;">
          <td style="padding:8px 12px;font-family:monospace;font-size:13px;color:#374151;">"{_phrase}"</td>
          <td style="padding:8px 12px;text-align:center;">{_found_badge(_llm_found)}</td>
          {_tpl_col}
        </tr>"""

    # Must-not-mention table rows
    _mn_rows = ""
    for _phrase in _must_not_mention:
        _llm_clean = _phrase.lower() not in _llm_leaked
        _tpl_col = f'<td style="padding:8px 12px;text-align:center;">{_clean_badge(_phrase.lower() not in _tpl_leaked)}</td>' if _has_tpl else ""
        _mn_rows += f"""
        <tr style="border-bottom:1px solid #f3f4f6;">
          <td style="padding:8px 12px;font-family:monospace;font-size:13px;color:#374151;">"{_phrase}"</td>
          <td style="padding:8px 12px;text-align:center;">{_clean_badge(_llm_clean)}</td>
          {_tpl_col}
        </tr>"""

    # Category colors
    _cat_colors = {
        "standard": ("#dbeafe", "#1d4ed8"),
        "edge_case": ("#fef3c7", "#92400e"),
        "adversarial": ("#fee2e2", "#991b1b"),
    }
    _cat_bg, _cat_fg = _cat_colors.get(_category, ("#f3f4f6", "#374151"))
    _cat_label = _category.replace("_", " ").title()

    # Score summary row
    def _score_cell(val, verdict):
        if val is None:
            return '<span style="color:#9ca3af;font-size:13px;">—</span>'
        _c = "#16a34a" if val >= 0.85 else ("#d97706" if val >= 0.5 else "#dc2626")
        return f'<span style="font-size:20px;font-weight:800;color:{_c};">{val:.2f}</span> {_verdict_badge(verdict)}'

    _tpl_score_cell = f"""
      <div style="text-align:center;padding:12px 20px;border-left:1px solid #e5e7eb;">
        <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">Template</div>
        {_score_cell(_tpl_score_val, _tpl_verdict)}
      </div>""" if _has_tpl else ""

    _mm_table = f"""
    <table style="width:100%;border-collapse:collapse;font-size:14px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#f9fafb;border-bottom:2px solid #e5e7eb;">
          <th style="padding:8px 12px;text-align:left;color:#6b7280;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Phrase</th>
          <th style="padding:8px 12px;text-align:center;color:#6b7280;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;">LLM</th>
          {_tpl_col_header}
        </tr>
      </thead>
      <tbody>{_mm_rows if _mm_rows else '<tr><td colspan="3" style="padding:12px;color:#9ca3af;text-align:center;">No must-mention constraints</td></tr>'}</tbody>
    </table>""" if _must_mention else '<p style="color:#9ca3af;font-size:13px;">No must-mention constraints defined.</p>'

    _mn_table = f"""
    <table style="width:100%;border-collapse:collapse;font-size:14px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#f9fafb;border-bottom:2px solid #e5e7eb;">
          <th style="padding:8px 12px;text-align:left;color:#6b7280;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Phrase</th>
          <th style="padding:8px 12px;text-align:center;color:#6b7280;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;">LLM</th>
          {_tpl_col_header}
        </tr>
      </thead>
      <tbody>{_mn_rows if _mn_rows else '<tr><td colspan="3" style="padding:12px;color:#9ca3af;text-align:center;">No must-not-mention constraints</td></tr>'}</tbody>
    </table>""" if _must_not_mention else '<p style="color:#9ca3af;font-size:13px;">No must-not-mention constraints defined.</p>'

    _content = mo.Html(f"""
    <div style="font-family:system-ui,-apple-system,sans-serif;">

      <!-- Property header -->
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <span style="font-size:17px;font-weight:700;color:#111827;">{_prop_name}</span>
        <span style="padding:3px 10px;border-radius:9999px;background:{_cat_bg};color:{_cat_fg};font-size:12px;font-weight:600;">{_cat_label}</span>
      </div>
      <div style="color:#6b7280;font-size:14px;margin-bottom:20px;">{_notes}</div>

      <!-- Score summary -->
      <div style="display:flex;align-items:center;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-bottom:20px;background:#f9fafb;">
        <div style="padding:12px 20px;text-align:center;">
          <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">LLM Generator</div>
          {_score_cell(_llm_score_val, _llm_verdict)}
        </div>
        {_tpl_score_cell}
        <div style="flex:1;padding:12px 20px;border-left:1px solid #e5e7eb;">
          <div style="font-size:12px;color:#6b7280;line-height:1.6;">
            <strong>Mention score</strong> (LLM): {f"{_llm_mention_score:.0%}" if _llm_mention_score is not None else "—"}<br>
            <strong>Avoid score</strong> (LLM): {f"{_llm_avoid_score:.0%}" if _llm_avoid_score is not None else "—"}
          </div>
        </div>
      </div>

      <!-- Constraint tables -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
        <div>
          <div style="font-weight:600;color:#111827;margin-bottom:8px;font-size:14px;">
            Must-Mention Phrases <span style="font-weight:400;color:#9ca3af;">({len(_must_mention)})</span>
          </div>
          {_mm_table}
        </div>
        <div>
          <div style="font-weight:600;color:#111827;margin-bottom:8px;font-size:14px;">
            Must-Not-Mention Phrases <span style="font-weight:400;color:#9ca3af;">({len(_must_not_mention)})</span>
          </div>
          {_mn_table}
        </div>
      </div>

    </div>
    """)

    mo.accordion(
        {
            "Golden Evaluation — Constraint Satisfaction": mo.vstack([
                golden_dropdown,
                _content,
            ])
        },
        multiple=True,
    )
    return ()


# ---------------------------------------------------------------------------
# Reproducibility — compare scores across multiple runs of the same task
# ---------------------------------------------------------------------------

@app.cell
def _reproducibility_section(mo, all_runs, go, fmt_scorer, composite_score):
    _multi = {
        t: runs for t, runs in all_runs.items()
        if len(runs) > 1 and not t.endswith("_template")
    }

    if not _multi:
        mo.accordion(
            {"Reproducibility Analysis": mo.md(
                "_Run evaluations more than once to see score variance here._\n\n"
                "```bash\n"
                "uv run inspect eval evals/tasks.py -T fixture_eval -T golden_eval --log-dir logs/\n"
                "```"
            )},
            multiple=True,
        )
    else:
        def _grade_color(v):
            if v >= 0.80: return "#16a34a"
            if v >= 0.60: return "#d97706"
            return "#dc2626"

        _all_charts = []

        for _task_name, _runs in sorted(_multi.items()):
            _n_runs = len(_runs)

            # Collect composite scores per property per run (ordered)
            _by_prop = {}
            for _run_idx, _log in enumerate(_runs):
                for _s in (_log.samples or []):
                    _name = (_s.metadata or {}).get("property", {}).get("property_name", _s.id)
                    _score = composite_score(_s.scores or {}, fmt_scorer)
                    _by_prop.setdefault(_name, {})[_run_idx] = _score

            # Include any property that appeared in at least 2 runs
            _props = [n for n, d in _by_prop.items() if len(d) >= 2]
            if not _props:
                continue

            _score_matrix = [
                [_by_prop[n][r] for r in sorted(_by_prop[n].keys())]
                for n in _props
            ]
            _means = [sum(row) / len(row) for row in _score_matrix]
            _stds = [
                (sum((x - m) ** 2 for x in row) / len(row)) ** 0.5
                for row, m in zip(_score_matrix, _means)
            ]
            _max_delta = [max(row) - min(row) for row in _score_matrix]

            _avg_delta = sum(_max_delta) / len(_max_delta)
            _stable_pct = round(100 * sum(1 for d in _max_delta if d < 0.05) / len(_max_delta))
            _delta_color = "#16a34a" if _avg_delta < 0.05 else ("#d97706" if _avg_delta < 0.15 else "#dc2626")
            _run_counts = sorted({len(_by_prop[n]) for n in _props})
            _run_label = f"{_run_counts[0]}–{_run_counts[-1]}" if len(_run_counts) > 1 else str(_run_counts[0])

            _summary_html = (
                f'<div style="font-family:system-ui;font-size:13px;color:#374151;'
                f'display:flex;gap:24px;margin-bottom:12px;">'
                f'<span><strong>{_run_label}</strong> runs · '
                f'<strong>{len(_props)}</strong> properties</span>'
                f'<span>Avg max-delta: <strong style="color:{_delta_color};">{_avg_delta:.3f}</strong></span>'
                f'<span>Stable (Δ&lt;0.05): <strong>{_stable_pct}%</strong></span>'
                f'</div>'
            )

            # Scatter: 2 most recent runs for all properties that have them
            _scatter_props = [n for n in _props if len(_by_prop[n]) >= 2]
            _r1 = [_by_prop[n][sorted(_by_prop[n].keys())[-2]] for n in _scatter_props]
            _r2 = [_by_prop[n][sorted(_by_prop[n].keys())[-1]] for n in _scatter_props]
            _deltas = [abs(a - b) for a, b in zip(_r1, _r2)]

            _scatter_fig = go.Figure()
            _scatter_fig.add_shape(
                type="line", x0=0, y0=0, x1=1, y1=1,
                line=dict(color="#d1d5db", width=1, dash="dot"),
            )
            _scatter_fig.add_trace(go.Scatter(
                x=_r1, y=_r2,
                mode="markers+text",
                text=_scatter_props,
                textposition="top center",
                textfont=dict(size=9, color="#6b7280"),
                marker=dict(
                    size=11,
                    color=_deltas,
                    colorscale=[[0, "#22c55e"], [0.5, "#f59e0b"], [1, "#ef4444"]],
                    cmin=0, cmax=0.2,
                    showscale=True,
                    colorbar=dict(title="|Δ|", thickness=10, len=0.7),
                    line=dict(width=1, color="white"),
                ),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Last run: %{y:.3f}<br>"
                    "Prev run: %{x:.3f}<br>"
                    "Δ: %{marker.color:.3f}"
                    "<extra></extra>"
                ),
            ))
            _scatter_fig.update_layout(
                xaxis=dict(title="Previous run", range=[0, 1], gridcolor="#f3f4f6"),
                yaxis=dict(title="Latest run", range=[0, 1], gridcolor="#f3f4f6"),
                plot_bgcolor="white", paper_bgcolor="white",
                height=360, margin=dict(l=50, r=70, t=10, b=50),
            )

            # Std dev bar: historical variance across all runs
            _sorted_pairs = sorted(zip(_props, _stds), key=lambda x: -x[1])
            _sp, _ss = zip(*_sorted_pairs) if _sorted_pairs else ([], [])
            _bar_colors = ["#dc2626" if s > 0.1 else ("#f59e0b" if s > 0.05 else "#22c55e") for s in _ss]

            _std_fig = go.Figure()
            _std_fig.add_trace(go.Bar(
                x=list(_sp), y=list(_ss),
                marker_color=_bar_colors,
                hovertemplate="%{x}<br>std dev: %{y:.3f}<extra></extra>",
            ))
            _std_fig.add_hline(y=0.05, line_width=1, line_dash="dot", line_color="#9ca3af",
                               annotation_text="0.05 threshold", annotation_position="right")
            _std_fig.update_layout(
                yaxis=dict(title="Std dev (all runs)", gridcolor="#f3f4f6"),
                plot_bgcolor="white", paper_bgcolor="white",
                height=280, margin=dict(l=50, r=20, t=10, b=100),
                xaxis=dict(tickangle=-30),
                showlegend=False,
            )

            _all_charts.append(mo.vstack([
                mo.md(f"**{_task_name}**"),
                mo.Html(_summary_html),
                mo.hstack([mo.as_html(_scatter_fig), mo.as_html(_std_fig)], gap=1),
            ]))

        mo.accordion(
            {"Reproducibility Analysis": mo.vstack(_all_charts)},
            multiple=True,
        )
    return ()


if __name__ == "__main__":
    app.run()
