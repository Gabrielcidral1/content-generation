import marimo

__generated_with = "0.23.4"
app = marimo.App(width="full")


@app.cell
def _imports():
    import json
    import os
    from pathlib import Path

    import marimo as mo
    import plotly.graph_objects as go

    from inspect_ai.log import list_eval_logs, read_eval_log

    LOGS_DIR = str(Path(__file__).parent / "logs")
    return LOGS_DIR, Path, go, json, list_eval_logs, mo, os, read_eval_log


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

    log_infos = _log_infos
    logs = {info.name: read_eval_log(info) for info in log_infos}
    return log_infos, logs


@app.cell
def _header(mo, logs, log_infos):
    _total = sum(len(log.samples) for log in logs.values() if log.samples)
    mo.md(
        f"""
# Lodgify Content Generation Evaluation

**{len(logs)} evaluation tasks** · **{_total} properties evaluated**

{' · '.join(f'`{name}`' for name in logs)}
"""
    )
    return ()


@app.cell
def _task_tabs(mo, logs):
    task_tabs = mo.ui.tabs({name: mo.md(f"Task: **{name}**") for name in logs})
    task_tabs
    return (task_tabs,)


@app.cell
def _selected_task(task_tabs, logs):
    selected_task_name = task_tabs.value
    selected_log = logs[selected_task_name]
    samples = selected_log.samples or []
    return samples, selected_log, selected_task_name


@app.cell
def _property_selector(mo, samples):
    mo.stop(not samples, mo.md("No samples in this task."))

    _names = {
        s.id: (s.metadata or {}).get("property", {}).get("property_name", s.id)
        for s in samples
    }
    prop_dropdown = mo.ui.dropdown(
        options=_names,
        value=list(_names.keys())[0],
        label="Select property",
    )
    prop_dropdown
    return (prop_dropdown,)


@app.cell
def _selected_sample(prop_dropdown, samples):
    selected_sample = next(
        (s for s in samples if s.id == prop_dropdown.value), samples[0]
    )
    prop_data = (selected_sample.metadata or {}).get("property", {})
    generated = (selected_sample.metadata or {}).get("generated", {})
    return generated, prop_data, selected_sample


@app.cell
def _property_panel(mo, prop_data, generated):
    mo.stop(not prop_data)

    _loc = prop_data.get("location", {})
    _info = prop_data.get("rental_info", {})
    _rules = prop_data.get("house_rules", {})
    _score = prop_data.get("average_review_score", 0)
    _n = prop_data.get("num_of_reviews", 0)
    _review_line = f"⭐ **{_score}** ({_n} reviews)" if _n > 0 else "_(no reviews yet)_"

    _highlights = "\n".join(f"- {h}" for h in generated.get("property_highlights", []))
    _amenities = "\n".join(
        f"- **{k}**: {v}" for k, v in generated.get("amenities_descriptions", {}).items()
    )

    mo.hstack(
        [
            mo.vstack(
                [
                    mo.md("## Property Input"),
                    mo.md(
                        f"**{prop_data.get('property_name')}** · {prop_data.get('property_type')}\n\n"
                        f"📍 {_loc.get('city')}, {_loc.get('country')}\n\n"
                        f"👥 {_info.get('max_guests')} guests · {_info.get('bedrooms')} bed · {_info.get('bathrooms')} bath\n\n"
                        f"🕐 Check-in {_rules.get('check_in_time')} · Check-out {_rules.get('check_out_time')}\n\n"
                        f"{_review_line}\n\n"
                        f"**Amenities:** {', '.join(prop_data.get('amenities', []))}"
                    ),
                ],
                align="start",
            ),
            mo.vstack(
                [
                    mo.md("## Generated Marketing Copy"),
                    mo.md(
                        f"### {generated.get('hero_headline', '_no headline_')}\n\n"
                        f"**Highlights**\n{_highlights}\n\n"
                        f"**About this place**\n\n{generated.get('about_section', '_not generated_')}\n\n"
                        f"**Amenities**\n{_amenities}"
                    ),
                ],
                align="start",
            ),
        ],
        justify="start",
        gap=2,
    )
    return ()


@app.cell
def _scores_panel(mo, selected_sample):
    import pandas as pd

    _scores = selected_sample.scores or {}
    mo.stop(not _scores, mo.md("No scores available for this sample."))

    _rows = [
        {
            "Scorer": name.replace("_scorer", "").replace("_", " ").title(),
            "Score": round(float(s.value), 3) if isinstance(s.value, (int, float)) else s.value,
            "Verdict": s.answer or "—",
            "Explanation": (s.explanation or "")[:200],
        }
        for name, s in _scores.items()
    ]
    mo.vstack(
        [
            mo.md("## Evaluation Scores"),
            mo.ui.dataframe(pd.DataFrame(_rows), page_size=10),
        ]
    )
    return (pd,)


@app.cell
def _heatmap(mo, logs, go, pd):
    import pandas as _pd_local

    _rows = []
    for _tname, _log in logs.items():
        if not _log.samples:
            continue
        for _sample in _log.samples:
            _pname = (_sample.metadata or {}).get("property", {}).get("property_name", _sample.id)
            for _sname, _sc in (_sample.scores or {}).items():
                _v = _sc.value
                _num = float(_v) if isinstance(_v, (int, float)) else (1.0 if _v == "PASS" else 0.0)
                _rows.append({
                    "task": _tname,
                    "property": _pname,
                    "scorer": _sname.replace("_scorer", "").replace("_", " ").title(),
                    "score": _num,
                })

    if _rows:
        _df = _pd_local.DataFrame(_rows)
        _figs = []
        for _tname in _df["task"].unique():
            _sub = _df[_df["task"] == _tname]
            _pivot = _sub.pivot_table(index="property", columns="scorer", values="score", aggfunc="mean")
            _fig = go.Figure(data=go.Heatmap(
                z=_pivot.values.tolist(),
                x=_pivot.columns.tolist(),
                y=_pivot.index.tolist(),
                colorscale="RdYlGn",
                zmin=0, zmax=1,
                text=[[f"{v:.2f}" for v in row] for row in _pivot.values.tolist()],
                texttemplate="%{text}",
            ))
            _fig.update_layout(
                title=f"Score Heatmap — {_tname}",
                height=max(300, 80 * len(_pivot)),
                margin={"l": 200, "r": 20, "t": 50, "b": 80},
                xaxis_title="Scorer", yaxis_title="Property",
            )
            _figs.append(mo.as_html(_fig))
        _heatmap_output = mo.vstack([mo.md("## Aggregate Scores Heatmap")] + _figs)
    else:
        _heatmap_output = mo.md("No score data to visualise.")

    _heatmap_output
    return ()


@app.cell
def _golden_section(mo, logs, pd):
    _golden_log = next(
        (log for name, log in logs.items() if "golden" in name.lower()), None
    )
    mo.stop(_golden_log is None)

    _rows = []
    for _sample in (_golden_log.samples or []):
        _meta = _sample.metadata or {}
        _pname = _meta.get("property", {}).get("property_name", _sample.id)
        _gc = (_sample.scores or {}).get("golden_constraints_scorer")
        if _gc:
            _gc_meta = _gc.metadata or {}
            _rows.append({
                "Property": _pname,
                "Category": _meta.get("golden_category", "—"),
                "Verdict": _gc.answer,
                "Score": round(float(_gc.value), 3),
                "Missing Phrases": str(_gc_meta.get("missing_phrases", [])),
                "Leaked Phrases": str(_gc_meta.get("leaked_phrases", [])),
                "Notes": (_meta.get("golden_notes", ""))[:100],
            })

    mo.stop(not _rows, mo.md("No golden constraint results available."))

    _df = pd.DataFrame(_rows)
    _adversarial = _df[_df["Category"] == "adversarial"]
    _injection_blocked = (
        len(_adversarial) > 0
        and len(_adversarial[_adversarial["Verdict"] == "PASS"]) == len(_adversarial)
    )
    _status = (
        "✅ **All adversarial injection attempts were blocked**"
        if _injection_blocked
        else "⚠️ Some adversarial inputs may have succeeded"
    )

    mo.vstack([
        mo.md("## Golden Dataset Results"),
        mo.callout(mo.md(_status), kind="success" if _injection_blocked else "warn"),
        mo.ui.dataframe(_df, page_size=10),
    ])
    return ()


@app.cell
def _raw_logs_section(mo, logs, log_infos, pd):
    _rows = []
    for _info in log_infos:
        _log = logs[_info.name]
        for _sample in (_log.samples or []):
            _pname = (_sample.metadata or {}).get("property", {}).get("property_name", _sample.id)
            for _sname, _sc in (_sample.scores or {}).items():
                _rows.append({
                    "task": _info.name,
                    "sample_id": _sample.id,
                    "property": _pname,
                    "scorer": _sname,
                    "value": _sc.value,
                    "verdict": _sc.answer,
                    "explanation": (_sc.explanation or "")[:300],
                })

    mo.stop(not _rows)

    mo.vstack([
        mo.md("## Raw Log Explorer"),
        mo.md("All scores across all tasks and samples."),
        mo.ui.dataframe(pd.DataFrame(_rows), page_size=20),
    ])
    return ()


if __name__ == "__main__":
    app.run()
