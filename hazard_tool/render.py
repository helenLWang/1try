"""Render analysis_results.md from the workspace JSON checkpoints."""

from __future__ import annotations

from pathlib import Path

from . import io_util
from .scenario import SYSTEM_NAME


def _goal_text(analysis: dict, goal_id: str) -> str:
    for goal in analysis.get("goals") or []:
        if goal.get("id") == goal_id:
            return goal.get("text") or goal_id
    return goal_id or "(unspecified goal)"


def render_report(out_path: Path | None = None) -> Path:
    stakeholders_doc = io_util.read_json("stakeholders.json")
    hazards_doc = io_util.read_json("hazards.json")
    reqs_doc = io_util.read_json("requirements.json")

    stakeholders = {s["id"]: s for s in stakeholders_doc["stakeholders"]}
    analyses = {a.get("stakeholder_id"): a for a in hazards_doc["analyses"]}
    by_req: dict[str, dict] = {}
    for d in reqs_doc.get("decompositions") or []:
        by_req[d.get("req_id")] = d

    n_stakeholders = len(stakeholders)
    n_losses = 0
    n_asms = 0
    n_specs = 0
    for analysis in hazards_doc["analyses"]:
        n_losses += len(analysis.get("items") or [])
    for d in reqs_doc.get("decompositions") or []:
        n_asms += len(d.get("assumptions") or [])
        n_specs += len(d.get("specifications") or [])

    lines: list[str] = []
    lines.append(f"# ChildFind hazard analysis — {SYSTEM_NAME}")
    lines.append("")
    lines.append(
        "This report is the output of the LLM-assisted pipeline in `hazard_tool/` "
        "after human review of the JSON checkpoints in `workspace/`. It covers the "
        "first four analysis steps: stakeholders, values/goals, losses, world-level "
        "requirements (REQ), environmental assumptions (ASM), and software "
        "specifications (SPEC). Jackson's split: REQ is world-only; ASM is "
        "world/shared; SPEC is interface-only."
    )
    lines.append("")
    lines.append("## Scale")
    lines.append("")
    lines.append(f"- Stakeholders: **{n_stakeholders}**")
    lines.append(f"- Losses / requirements: **{n_losses}**")
    lines.append(f"- Assumptions: **{n_asms}**")
    lines.append(f"- Specifications: **{n_specs}**")
    lines.append("")
    lines.append("Trace: stakeholder → goal → loss → REQ → ASM/SPEC.")
    lines.append("")

    # Index
    lines.append("## Stakeholder index")
    lines.append("")
    lines.append("| ID | Name | Kind | #losses |")
    lines.append("| --- | --- | --- | ---: |")
    for sid, sh in stakeholders.items():
        n = len((analyses.get(sid) or {}).get("items") or [])
        lines.append(f"| {sid} | {sh.get('name')} | {sh.get('kind')} | {n} |")
    lines.append("")

    for sid, sh in stakeholders.items():
        analysis = analyses.get(sid) or {}
        lines.append(f"## {sid}: {sh.get('name')}")
        lines.append("")
        lines.append(f"- **Kind:** {sh.get('kind')}")
        if sh.get("description"):
            lines.append(f"- **Who:** {sh.get('description')}")
        if sh.get("why_included"):
            lines.append(f"- **Why included:** {sh.get('why_included')}")
        lines.append(f"- **Power / vulnerability:** {sh.get('power', '?')} / {sh.get('vulnerability', '?')}")
        lines.append("")
        values = analysis.get("values") or []
        if values:
            lines.append("**Values:** " + "; ".join(values))
            lines.append("")
        goals = analysis.get("goals") or []
        if goals:
            lines.append("**Goals:**")
            for g in goals:
                lines.append(f"- `{g.get('id')}`: {g.get('text')}")
            lines.append("")

        items = analysis.get("items") or []
        if not items:
            lines.append("_No losses recorded for this stakeholder._")
            lines.append("")
            continue
        for item in items:
            req_id = item.get("req_id")
            decomp = by_req.get(req_id, {})
            lines.append(f"### {item.get('id')} / {req_id}")
            lines.append("")
            lines.append(f"- **Goal:** `{item.get('goal_id')}` — {_goal_text(analysis, item.get('goal_id'))}")
            lines.append(f"- **Loss:** {item.get('loss')}")
            lines.append(f"- **REQ:** {item.get('req')}")
            if item.get("harm_note"):
                lines.append(f"- **Harm note:** {item.get('harm_note')}")
            asms = decomp.get("assumptions") or []
            specs = decomp.get("specifications") or []
            if asms:
                lines.append("")
                lines.append("**ASM**")
                for a in asms:
                    extra = f" _(fragile: {a['why_fragile']})_" if a.get("why_fragile") else ""
                    lines.append(f"- `{a.get('id')}`: {a.get('text')}{extra}")
            if specs:
                lines.append("")
                lines.append("**SPEC**")
                for p in specs:
                    comp = f" [{p.get('component')}]" if p.get("component") else ""
                    lines.append(f"- `{p.get('id')}`{comp}: {p.get('text')}")
            lines.append("")

    # Cross-cutting
    lines.append("## Cross-cutting observation (not a substitute for key_results.md)")
    lines.append("")
    lines.append(
        "Many losses collapse to the same two fragile assumptions: (1) the dashcam "
        "has a timely network path, and (2) a face match on an adult-tuned model is "
        "a reliable proxy for 'this child was here'. Those are called out in "
        "`key_results.md` rather than repeated as fifty 'improve the model' items."
    )
    lines.append("")

    out = out_path or (io_util.ROOT / "analysis_results.md")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({n_stakeholders} stakeholders, {n_losses} losses/REQs).")
    return out


def compact_index() -> str:
    """One-line index used by the prioritize step."""
    hazards_doc = io_util.read_json("hazards.json")
    rows = []
    for analysis in hazards_doc["analyses"]:
        for item in analysis.get("items") or []:
            rows.append(
                f"{item.get('req_id')}\t{analysis.get('stakeholder_id')}\t{item.get('loss')}"
            )
    return "\n".join(rows)
