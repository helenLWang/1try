#!/usr/bin/env python3
"""Sanity-check the committed analysis against the assignment scale gates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WS = ROOT / "workspace"


def main() -> int:
    stakeholders = json.loads((WS / "stakeholders.json").read_text())["stakeholders"]
    hazards = json.loads((WS / "hazards.json").read_text())["analyses"]
    reqs = json.loads((WS / "requirements.json").read_text())["decompositions"]
    n_loss = sum(len(a.get("items") or []) for a in hazards)
    print(f"stakeholders={len(stakeholders)} losses={n_loss} decomps={len(reqs)}")
    ok = True
    if len(stakeholders) < 10:
        print("FAIL: need >= 10 stakeholders")
        ok = False
    if n_loss < 50:
        print("FAIL: need >= 50 losses/requirements")
        ok = False
    for d in reqs:
        if len(d.get("assumptions") or []) < 3 or len(d.get("specifications") or []) < 3:
            print("FAIL: ASM/SPEC < 3 for", d.get("req_id"))
            ok = False
            break
    required = ["goals.md", "analysis_results.md", "key_results.md", "fault_tree.md", "README.md"]
    for name in required:
        if not (ROOT / name).exists():
            print("FAIL: missing", name)
            ok = False
    for fig in ["figures/fault_tree_before.svg", "figures/fault_tree_after.svg"]:
        if not (ROOT / fig).exists():
            print("FAIL: missing", fig)
            ok = False
    if ok:
        print("OK")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
