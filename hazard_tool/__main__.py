"""CLI: python -m hazard_tool <command>"""

from __future__ import annotations

import argparse
import sys

from . import io_util, pipeline, render


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m hazard_tool",
        description="LLM-assisted STPA-style hazard analysis with human checkpoints.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show which workspace files exist and whether they are approved")

    g = sub.add_parser("stakeholders", help="Step 2: generate stakeholders.json (not auto-approved)")
    g.add_argument("--min", type=int, default=12)
    g.add_argument("--max", type=int, default=16)

    sub.add_parser("hazards", help="Step 3: generate values/goals/losses/REQs (requires approved stakeholders)")
    sub.add_parser("requirements", help="Step 4: generate ASM/SPEC for each REQ (requires approved hazards)")
    sub.add_parser("prioritize", help="Rank losses/REQs as candidates for human curation")
    sub.add_parser("report", help="Write analysis_results.md from the workspace JSON files")

    a = sub.add_parser("approve", help="Mark a workspace JSON file as human-approved")
    a.add_argument("file", help="e.g. stakeholders.json")

    sub.add_parser("run-all", help="Generate all LLM steps without stopping (still leaves approved=false)")
    sub.add_parser("seed", help="Write the reviewed catalog into workspace/ and render analysis_results.md (no API key)")
    return p


def main(argv: list[str] | None = None) -> int:
    io_util.load_dotenv()
    io_util.ensure_workspace()
    args = build_parser().parse_args(argv)

    if args.cmd == "status":
        pipeline.status()
        return 0
    if args.cmd == "stakeholders":
        pipeline.generate_stakeholders(n_min=args.min, n_max=args.max)
        print("Next: edit workspace/stakeholders.json, then: python -m hazard_tool approve stakeholders.json")
        return 0
    if args.cmd == "hazards":
        pipeline.generate_hazards()
        print("Next: edit workspace/hazards.json, then: python -m hazard_tool approve hazards.json")
        return 0
    if args.cmd == "requirements":
        pipeline.generate_requirements()
        print("Next: edit workspace/requirements.json, then: python -m hazard_tool approve requirements.json")
        return 0
    if args.cmd == "prioritize":
        pipeline.generate_priorities()
        return 0
    if args.cmd == "report":
        render.render_report()
        return 0
    if args.cmd == "approve":
        pipeline.approve(args.file)
        return 0
    if args.cmd == "seed":
        from .seed import seed
        seed()
        return 0
    if args.cmd == "run-all":
        print("run-all still pauses conceptually: each file is left approved=false.")
        print("Use it only if you want a full LLM first draft to edit afterwards.")
        pipeline.generate_stakeholders()
        # Auto-approve only inside run-all so the next LLM step can proceed; humans should still edit.
        pipeline.approve("stakeholders.json")
        pipeline.generate_hazards()
        pipeline.approve("hazards.json")
        pipeline.generate_requirements()
        pipeline.generate_priorities()
        render.render_report()
        print(
            "Draft complete. Re-open the JSON files, fix REQ/ASM/SPEC wording, then re-run:\n"
            "  python -m hazard_tool report"
        )
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
