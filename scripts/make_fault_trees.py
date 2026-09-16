#!/usr/bin/env python3
"""Generate FTA figures as SVG (no extra deps)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)


def box(x, y, w, h, text, fill="#fff8e7", stroke="#333", sw=1.5, size=12):
    lines = text.split("\n")
    tspan = "".join(
        f'<tspan x="{x+w/2}" dy="{"0" if i==0 else "1.25em"}">{_esc(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    # vertical center-ish
    ty = y + h / 2 - (len(lines) - 1) * 7
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" ry="8" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        f'<text x="{x+w/2}" y="{ty}" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" '
        f'font-size="{size}" fill="#222">{tspan}</text>'
    )


def gate(x, y, label, fill="#e8eef7"):
    return (
        f'<circle cx="{x}" cy="{y}" r="18" fill="{fill}" stroke="#333" stroke-width="1.5"/>'
        f'<text x="{x}" y="{y+4}" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" '
        f'font-size="11" font-weight="bold">{label}</text>'
    )


def line(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#333" stroke-width="1.4"/>'


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, body, title):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="100%" height="100%" fill="#fafafa"/>
  <text x="24" y="32" font-family="Helvetica,Arial,sans-serif" font-size="16" font-weight="bold" fill="#111">{_esc(title)}</text>
  <text x="24" y="52" font-family="Helvetica,Arial,sans-serif" font-size="11" fill="#555">Top event = violation of REQ R-S02-1 (world). Intermediate events = ASM or SPEC failures. Circles: OR / AND gates.</text>
  {body}
</svg>
'''


def tree_before():
    # layout: top, OR, four intermediate, then basics
    parts = []
    # top
    parts.append(box(430, 70, 500, 70,
                     "TOP: Coordinating LE does not learn of a true\n"
                     "in-view sighting while the child is still nearby\n"
                     "(violation of REQ R-S02-1)",
                     fill="#f8d0d0", sw=2, size=13))
    parts.append(line(680, 140, 680, 175))
    parts.append(gate(680, 193, "OR"))

    # four columns
    cols = [
        (20, "A. Child never captured\nin recorded video", "#ffe6c7"),
        (380, "B. Captured, but software\nemits no match output", "#ffe6c7"),
        (740, "C. Match exists, report not\ndelivered in useful time", "#ffe6c7"),
        (1100, "D. Report arrives but is\nnot treated as a sighting", "#ffe6c7"),
    ]
    ys = 250
    for x, txt, fill in cols:
        cx = x + 160
        parts.append(line(680, 211, cx, ys))
        parts.append(box(x, ys, 320, 56, txt, fill=fill, size=12))
        parts.append(line(cx, ys + 56, cx, ys + 78))
        parts.append(gate(cx, ys + 96, "OR"))

    # basics under A
    basics = [
        (20, 380, "A1 ASM-power/FOV\nDashcam unpowered or\nlens blocked/dirty\n(R-S02-1-A1)"),
        (20, 490, "A2 ASM-occlusion\nFace/clothing covered\nentire time in view\n(R-S02-1-A2)"),
        (380, 380, "B1 SPEC-alert\nSearch-alert never stored\non device / phone\n(R-S02-1-P1)"),
        (380, 490, "B2 SPEC-ML wrong prediction\nPerson-recognition outputs\ntoo-low / wrong score\n(R-S02-1-P2)  ★ ML event"),
        (380, 600, "B3 ASM-photo\nSearch photo no longer\nresembles the child\n(R-S02-1-A4)"),
        (740, 380, "C1 ASM-connectivity\nNo Bluetooth/Wi-Fi/USB\npath in time\n(R-S02-1-A3)"),
        (740, 490, "C2 SPEC-queue\nQueued report dropped\nbefore next radio session\n(R-S02-1-P4)"),
        (740, 600, "C3 SPEC-payload\nReport lacks GPS/time/crop\nso it is not a sighting\n(R-S02-1-P3)"),
        (1100, 380, "D1 SPEC-inbox\nCoordinator drops the\nreport in a second pass\n(R-S02-1-P5)"),
        (1100, 490, "D2 ASM-operator\nOperators ignore the inbox\nas noise\n(R-S02-1-A5)"),
    ]
    # connect basics to parent OR
    parent_or = {0: 180, 1: 180, 2: 540, 3: 540, 4: 540, 5: 900, 6: 900, 7: 900, 8: 1260, 9: 1260}
    for i, (x, y, txt) in enumerate(basics):
        fill = "#fde2e2" if "ML" in txt else "#ffffff"
        sw = 2.2 if "ML" in txt else 1.5
        parts.append(box(x, y, 320, 92, txt, fill=fill, sw=sw, size=11))
        px = parent_or[i]
        py_or = 250 + 96
        parts.append(line(px, py_or + 18, x + 160, y))

    parts.append(box(20, 720, 1400, 40,
                     "Minimal cut sets (examples): {B2}; {C1}; {A1}; {D2}; {B3}; {C2}. A single basic event can violate R-S02-1.  ★ = required ML wrong-prediction event.",
                     fill="#eee", size=12))
    return svg(1460, 790, "\n".join(parts), "Fault tree 1 — before mitigations (REQ R-S02-1)")


def tree_after():
    parts = []
    parts.append(box(380, 60, 700, 70,
                     "TOP: Coordinating LE does not learn of a true in-view sighting\n"
                     "while the child is still nearby  (R-S02-1) — after M1 and M2",
                     fill="#f8d0d0", sw=2, size=13))
    parts.append(line(730, 130, 730, 160))
    parts.append(gate(730, 178, "OR"))

    # intermediates
    items = [
        (20, "A. Never captured\n(unchanged physical ASMs)", "#ffe6c7"),
        (310, "B*. No usable candidate\nreaches a human or a score", "#d8f3dc"),
        (600, "C*. All delivery paths fail\nbefore the child leaves", "#d8f3dc"),
        (890, "D. Arrives but unused\n(operator ASM remains)", "#ffe6c7"),
        (1180, "E. New residual from M2\nReviewer never looks", "#fff3cd"),
    ]
    y = 230
    centers = []
    for x, txt, fill in items:
        cx = x + 130
        centers.append(cx)
        parts.append(line(730, 196, cx, y))
        parts.append(box(x, y, 260, 56, txt, fill=fill, size=11))
        parts.append(line(cx, y + 56, cx, y + 74))

    # A OR
    parts.append(gate(centers[0], y + 92, "OR"))
    parts.append(box(20, 360, 260, 70, "A1 ASM-power/FOV\n(R-S02-1-A1)", size=11))
    parts.append(box(20, 445, 260, 70, "A2 ASM-occlusion\n(R-S02-1-A2)", size=11))
    parts.append(line(centers[0], y + 110, 150, 360))
    parts.append(line(centers[0], y + 110, 150, 445))

    # B* AND — face FN AND clothing miss AND (alert missing OR photo stale)
    parts.append(gate(centers[1], y + 92, "AND"))
    parts.append(box(300, 360, 280, 78,
                     "B2 SPEC-ML wrong prediction\nface score too low / wrong\n(R-S02-1-P2)  ★ still present",
                     fill="#fde2e2", sw=2.2, size=11))
    parts.append(box(300, 450, 280, 70,
                     "M2 residual: clothing/color cue\nalso fails to keep the crop",
                     fill="#fff3cd", size=11))
    parts.append(box(300, 532, 280, 78,
                     "AND (B1 SPEC-alert missing\nOR B3 ASM-photo stale)\n— still can starve matching",
                     size=11))
    parts.append(line(centers[1], y + 110, 440, 360))
    parts.append(line(centers[1], y + 110, 440, 450))
    parts.append(line(centers[1], y + 110, 440, 532))

    # C* AND of three channels
    parts.append(gate(centers[2], y + 92, "AND"))
    parts.append(box(590, 360, 280, 70, "C1a Phone Bluetooth/cellular\npath fails in time", size=11))
    parts.append(box(590, 440, 280, 70, "C1b Wi-Fi / USB home/work\noffload also fails", size=11))
    parts.append(box(590, 520, 280, 78, "C1c No partner kiosk visit\nbefore child leaves area\n(M1 residual)", fill="#fff3cd", size=11))
    parts.append(line(centers[2], y + 110, 730, 360))
    parts.append(line(centers[2], y + 110, 730, 440))
    parts.append(line(centers[2], y + 110, 730, 520))

    # D OR
    parts.append(gate(centers[3], y + 92, "OR"))
    parts.append(box(880, 360, 260, 70, "D1 SPEC-inbox drop\n(R-S02-1-P5)", size=11))
    parts.append(box(880, 445, 260, 78, "D2 ASM-operator ignore\n(R-S02-1-A5) — M2 can\nincrease volume; still a risk", size=11))
    parts.append(line(centers[3], y + 110, 1010, 360))
    parts.append(line(centers[3], y + 110, 1010, 445))

    # E from M2
    parts.append(gate(centers[4], y + 92, "OR"))
    parts.append(box(1170, 360, 270, 70, "E1 Reviewer shift empty\n(volunteer ASM)", fill="#fff3cd", size=11))
    parts.append(box(1170, 445, 270, 78, "E2 Top-k cap already full;\ncrop counted as overflow\nnot shown", fill="#fff3cd", size=11))
    parts.append(line(centers[4], y + 110, 1305, 360))
    parts.append(line(centers[4], y + 110, 1305, 445))

    parts.append(box(20, 640, 1420, 72,
                     "M1 (system, not ML): delay-tolerant multi-path delivery (phone + Wi-Fi/USB + encrypted kiosk offload) + retro-match of retained loop after a late search-alert.\n"
                     "M2 (system, not ML): top-k stills + clothing tags to a reviewer, independent of the face threshold — so B2 alone is no longer a cut set.\n"
                     "Effect: former singleton cut sets {B2} and {C1} become larger AND-combinations. Residual risk moves to reviewer capacity (E) and kiosk routing (C1c).",
                     fill="#e8f5e9", size=12))
    return svg(1460, 740, "\n".join(parts), "Fault tree 2 — after system-level mitigations M1 and M2")


def main():
    (FIG / "fault_tree_before.svg").write_text(tree_before(), encoding="utf-8")
    (FIG / "fault_tree_after.svg").write_text(tree_after(), encoding="utf-8")
    print("wrote", FIG / "fault_tree_before.svg")
    print("wrote", FIG / "fault_tree_after.svg")


if __name__ == "__main__":
    main()
