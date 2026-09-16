"""Human-in-the-loop pipeline: generate → edit JSON → approve → next step."""

from __future__ import annotations

from typing import Any

from . import io_util, llm
from .prompts import decompose_prompt, hazard_prompt, prioritize_prompt, stakeholder_prompt
from .scenario import SYSTEM_DESCRIPTION, SYSTEM_NAME


def generate_stakeholders(*, n_min: int = 12, n_max: int = 16) -> dict[str, Any]:
    system, user = stakeholder_prompt(n_min, n_max)
    result = llm.complete_json(system, user)
    stakeholders = result.get("stakeholders") if isinstance(result, dict) else result
    if not isinstance(stakeholders, list) or len(stakeholders) < 10:
        raise llm.LLMError(f"Expected >=10 stakeholders, got {stakeholders!r}"[:400])
    payload = {
        "approved": False,
        "instructions": (
            "Edit this list before generating losses. Delete hallucinations, merge "
            "duplicates, add missing stakeholders (especially indirect ones). Then set "
            "approved to true or run: python -m hazard_tool approve stakeholders.json"
        ),
        "system": SYSTEM_NAME,
        "stakeholders": stakeholders,
    }
    path = io_util.write_json("stakeholders.json", payload)
    print(f"Wrote {path} with {len(stakeholders)} stakeholders (approved=false).")
    return payload


def generate_hazards() -> dict[str, Any]:
    data = io_util.require_approved("stakeholders.json")
    stakeholders = data["stakeholders"]
    analyses = []
    for i, sh in enumerate(stakeholders, 1):
        print(f"[{i}/{len(stakeholders)}] hazards for {sh.get('id')} {sh.get('name')}...")
        system, user = hazard_prompt(sh)
        result = llm.complete_json(system, user)
        result["stakeholder_id"] = sh.get("id")
        analyses.append(result)
    payload = {
        "approved": False,
        "instructions": (
            "Review losses and REQs. Delete generic 'model inaccurate' items. Rewrite any "
            "REQ that mentions software/models so it is world-only. Set approved=true "
            "before decomposing into ASM/SPEC."
        ),
        "analyses": analyses,
    }
    path = io_util.write_json("hazards.json", payload)
    n_items = sum(len(a.get("items") or []) for a in analyses)
    print(f"Wrote {path} with {n_items} losses/requirements (approved=false).")
    return payload


def generate_requirements() -> dict[str, Any]:
    stakeholders = {s["id"]: s for s in io_util.require_approved("stakeholders.json")["stakeholders"]}
    hazards = io_util.require_approved("hazards.json")
    decompositions = []
    total = sum(len(a.get("items") or []) for a in hazards["analyses"])
    done = 0
    for analysis in hazards["analyses"]:
        sh = stakeholders.get(analysis.get("stakeholder_id"), {"id": analysis.get("stakeholder_id"), "name": "?"})
        for item in analysis.get("items") or []:
            done += 1
            print(f"[{done}/{total}] ASM/SPEC for {item.get('req_id')}...")
            system, user = decompose_prompt(sh, item)
            result = llm.complete_json(system, user)
            result["stakeholder_id"] = sh.get("id")
            result["goal_id"] = item.get("goal_id")
            result["loss"] = item.get("loss")
            result["req"] = item.get("req")
            decompositions.append(result)
    payload = {
        "approved": False,
        "instructions": (
            "Check that every REQ is world-only, every ASM is world/shared, every SPEC is "
            "interface-only. Fix wording, then approve."
        ),
        "decompositions": decompositions,
    }
    path = io_util.write_json("requirements.json", payload)
    print(f"Wrote {path} with {len(decompositions)} decompositions (approved=false).")
    return payload


def generate_priorities() -> dict[str, Any]:
    hazards = io_util.require_approved("hazards.json")
    lines = []
    for analysis in hazards["analyses"]:
        sid = analysis.get("stakeholder_id")
        for item in analysis.get("items") or []:
            lines.append(
                f"{item.get('req_id')} | stakeholder={sid} | goal={item.get('goal_id')} | "
                f"LOSS: {item.get('loss')} | REQ: {item.get('req')}"
            )
    system, user = prioritize_prompt("\n".join(lines))
    result = llm.complete_json(system, user, temperature=0.2)
    payload = {
        "approved": False,
        "instructions": (
            "This ranking is only a candidate list. Humans must pick the four key results. "
            "Do not copy the top-4 blindly. Set approved=true after you have used it as input "
            "to key_results.md."
        ),
        "ranking": result.get("ranked", result),
    }
    path = io_util.write_json("priorities.json", payload)
    print(f"Wrote {path}. Use it as input to human curation in key_results.md.")
    return payload


def approve(filename: str) -> None:
    payload = io_util.read_json(filename)
    if not isinstance(payload, dict):
        raise SystemExit(f"{filename} is not a JSON object")
    payload["approved"] = True
    io_util.write_json(filename, payload)
    print(f"Marked workspace/{filename} as approved.")


def status() -> None:
    files = [
        "stakeholders.json",
        "hazards.json",
        "requirements.json",
        "priorities.json",
    ]
    print(f"Scenario: {SYSTEM_NAME}")
    print(SYSTEM_DESCRIPTION.splitlines()[0][:80], "...")
    for name in files:
        path = io_util.WORKSPACE / name
        if not path.exists():
            print(f"  {name}: missing")
            continue
        payload = io_util.read_json(name)
        approved = payload.get("approved") if isinstance(payload, dict) else "?"
        extra = ""
        if name == "stakeholders.json":
            extra = f", n={len(payload.get('stakeholders', []))}"
        elif name == "hazards.json":
            extra = f", losses={sum(len(a.get('items') or []) for a in payload.get('analyses', []))}"
        elif name == "requirements.json":
            extra = f", reqs={len(payload.get('decompositions', []))}"
        print(f"  {name}: approved={approved}{extra}")
