"""Prompts for the three automated analysis steps (stakeholders, hazards, REQ decomposition)."""

from __future__ import annotations

from .scenario import SYSTEM_DESCRIPTION, SYSTEM_NAME, WORLD_MACHINE_RULES


def stakeholder_prompt(n_min: int = 12, n_max: int = 18) -> tuple[str, str]:
    system = (
        "You are a safety/requirements engineer performing stakeholder identification "
        "for an ML-enabled product. Return JSON only."
    )
    user = f"""
Product: {SYSTEM_NAME}

{SYSTEM_DESCRIPTION}

Identify {n_min}-{n_max} distinct stakeholders who care about or are affected by ChildFind.
Include both DIRECT stakeholders (interact with the product) and INDIRECT ones
(affected without using it). Cover at least: end users, the missing child, families,
authorities, the non-profit, OEM partners, the ML contractor, bystanders, lookalikes,
regulators, and any surprising stakeholder the scenario invites (edge partners, fleets).

Return JSON:
{{
  "stakeholders": [
    {{
      "id": "S01",
      "name": "short name",
      "kind": "direct" | "indirect",
      "description": "one sentence",
      "why_included": "one sentence",
      "power": "high" | "medium" | "low",
      "vulnerability": "high" | "medium" | "low"
    }}
  ]
}}
""".strip()
    return system, user


def hazard_prompt(stakeholder: dict) -> tuple[str, str]:
    system = (
        "You are performing the early steps of an STPA-style hazard analysis: "
        "values/goals, losses, then world-level requirements. Return JSON only.\n"
        + WORLD_MACHINE_RULES
    )
    user = f"""
Product: {SYSTEM_NAME}

{SYSTEM_DESCRIPTION}

Analyze ONE stakeholder:
id: {stakeholder.get("id")}
name: {stakeholder.get("name")}
kind: {stakeholder.get("kind")}
description: {stakeholder.get("description")}

Produce:
- 2-4 values (what they care about intrinsically)
- 2-4 goals (what they want the system/world to do for them)
- 5-8 losses: specific harms for THIS stakeholder if the system misbehaves.
  A loss is a world-level harm, not "the model is inaccurate".
- For EACH loss, one REQ that would prevent that loss. REQ is a desired
  condition in the environment only.

Return JSON:
{{
  "stakeholder_id": "{stakeholder.get("id")}",
  "values": ["..."],
  "goals": [
    {{"id": "Gxx", "text": "...", "relates_to_values": ["..."]}}
  ],
  "items": [
    {{
      "id": "Lxx",
      "goal_id": "Gxx",
      "loss": "world-level harm",
      "req_id": "Rxx",
      "req": "world-level requirement that prevents the loss",
      "harm_note": "why this harm matters for this stakeholder"
    }}
  ]
}}
Use ids prefixed with the stakeholder id, e.g. G-S01-1, L-S01-1, R-S01-1.
""".strip()
    return system, user


def decompose_prompt(stakeholder: dict, item: dict) -> tuple[str, str]:
    system = (
        "You decompose a system requirement into environmental assumptions (ASM) "
        "and software specifications (SPEC). Return JSON only.\n"
        + WORLD_MACHINE_RULES
    )
    user = f"""
Product: {SYSTEM_NAME}

{SYSTEM_DESCRIPTION}

Stakeholder: {stakeholder.get("id")} {stakeholder.get("name")}
Goal: {item.get("goal_id")}
Loss: {item.get("loss")}
REQ ({item.get("req_id")}): {item.get("req")}

List 3-6 plausible environmental assumptions that designers commonly (and
sometimes wrongly) rely on to achieve this REQ. Then list 3-6 software
responsibilities (AI and non-AI) on the machine/environment interface that,
together with those ASMs, would establish the REQ.

Prefer assumptions that may FAIL in production (offline dashcam, child faces,
lookalikes, operator overload, abductor adaptation, edge kiosks).

Return JSON:
{{
  "req_id": "{item.get("req_id")}",
  "assumptions": [
    {{"id": "Axx", "text": "...", "why_fragile": "one sentence"}}
  ],
  "specifications": [
    {{"id": "Pxx", "component": "person-recognition model" | "dashcam firmware" | "phone companion app" | "cloud/search coordinator" | "edge kiosk" | "other", "text": "..."}}
  ]
}}
Prefix ids with the req id.
""".strip()
    return system, user


def prioritize_prompt(summary: str) -> tuple[str, str]:
    system = (
        "You rank losses/requirements for an ML product. You do NOT make the final "
        "call — you only surface candidates. Return JSON only."
    )
    user = f"""
Below is a compact list of losses/requirements from a hazard analysis of {SYSTEM_NAME}.

{summary}

Score each item 1-5 on: severity, plausibility, and "easy_for_developers_to_miss".
Flag items that are surprising because they come from a fragile environmental
assumption (connectivity, child-face domain gap, operator behavior, purpose creep)
rather than from "the model should be more accurate".

Return JSON:
{{
  "ranked": [
    {{
      "req_id": "...",
      "severity": 1,
      "plausibility": 1,
      "easy_to_miss": 1,
      "surprising": true,
      "rationale": "one sentence"
    }}
  ]
}}
Include every req_id. Sort by (severity * plausibility * easy_to_miss) descending.
""".strip()
    return system, user
