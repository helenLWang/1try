"""Shared constructors for the reviewed analysis catalog."""

from __future__ import annotations

from typing import Any


def S(
    sid: str,
    name: str,
    kind: str,
    description: str,
    why: str,
    power: str,
    vulnerability: str,
) -> dict[str, Any]:
    return {
        "id": sid,
        "name": name,
        "kind": kind,
        "description": description,
        "why_included": why,
        "power": power,
        "vulnerability": vulnerability,
    }


def G(gid: str, text: str) -> dict[str, Any]:
    return {"id": gid, "text": text, "relates_to_values": []}


def item(lid: str, gid: str, loss: str, rid: str, req: str, note: str) -> dict[str, Any]:
    return {
        "id": lid,
        "goal_id": gid,
        "loss": loss,
        "req_id": rid,
        "req": req,
        "harm_note": note,
    }


def A(aid: str, text: str, fragile: str) -> dict[str, str]:
    return {"id": aid, "text": text, "why_fragile": fragile}


def P(pid: str, component: str, text: str) -> dict[str, str]:
    return {"id": pid, "component": component, "text": text}


def decomp(rid: str, sid: str, gid: str, loss: str, req: str, asms: list, specs: list) -> dict[str, Any]:
    return {
        "req_id": rid,
        "stakeholder_id": sid,
        "goal_id": gid,
        "loss": loss,
        "req": req,
        "assumptions": asms,
        "specifications": specs,
    }
