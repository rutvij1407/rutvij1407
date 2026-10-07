"""Write info-card.svg: a neofetch-style panel that prints in line by line.

STATIC=1 emits a frozen frame (handy for Quick Look previews).
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
PORTRAIT = ROOT / "rutvij-ascii.svg"

W = 490
PAD_X, TOP, BOTTOM = 22, 62, 22
KEY_COLS = 10
BG, BORDER, MUTED, TEXT = "#0d1117", "#30363d", "#7d8590", "#c9d1d9"
KEY, ACCENT, USER = "#39d353", "#69f0a0", "#58a6ff"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
STATIC = os.environ.get("STATIC") == "1"

# (key, value); key "" continues the previous entry, None is a blank spacer line.
ROWS = [
    ("Role", "Data Analytics Engineer"),
    ("Now", "MS Data Analytics Eng. @ George Mason"),
    ("Location", "Fairfax, VA"),
    None,
    ("Prev", "Data Analytics Intern @ Archents India"),
    ("", "Aug 2024 – Jul 2025"),
    ("Prev", "Founder & Data Lead @ Pullulate"),
    ("", "Dec 2022 – Aug 2025"),
    ("Prev", "AWS Intern @ NSIC–IARE · Jun 2023"),
    ("Edu", "B.Tech CSE @ IARE, Hyderabad · 2025"),
    None,
    ("Stack", "Python · SQL · R · Pandas · scikit-learn"),
    ("BI", "Power BI · Tableau · Excel"),
    ("Cloud", "AWS (EC2 · RDS · S3) · Docker · Actions"),
    ("Certs", "AWS Cloud Practitioner · Power BI"),
    None,
    ("Highlights", None),
    ("", "› 100K+ records analyzed with SQL + Power BI"),
    ("", "› Report automation cut manual effort 35%"),
    ("", "› ETL + real-time KPI dashboards on AWS RDS"),
    ("", "› Data-quality mentoring: +20% accuracy"),
    None,
    ("Site", "rutvij-portfolio-six.vercel.app"),
]
SWATCHES = ["#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0", "#58a6ff", "#d2a8ff", "#ffa657"]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def portrait_height(default=574):
    if PORTRAIT.exists():
        m = re.search(r'height="(\d+)"', PORTRAIT.read_text())
        if m:
            return int(m.group(1))
    return default


def main():
    H = portrait_height()
    n_lines = 2 + len(ROWS) + 2  # header + rule, rows, spacer + swatches
    line_h = min(22.0, (H - TOP - BOTTOM) / n_lines)
    font_size = min(13.0, line_h * 0.68)
    char_w = font_size * 0.6
    val_x = PAD_X + KEY_COLS * char_w

    lines = [
        f'<text x="{PAD_X}" y="0"><tspan fill="{USER}" font-weight="bold">rutvij</tspan>'
        f'<tspan fill="{TEXT}">@</tspan><tspan fill="{USER}" font-weight="bold">github</tspan></text>',
        f'<text x="{PAD_X}" y="0" fill="{MUTED}">{"-" * 13}</text>',
    ]
    for row in ROWS:
        if row is None:
            lines.append("")
            continue
        key, value = row
        parts = []
        if key:
            parts.append(f'<tspan x="{PAD_X}" fill="{KEY}" font-weight="bold">{esc(key)}</tspan>')
        if value:
            color = ACCENT if value.startswith("›") else TEXT
            parts.append(f'<tspan x="{val_x:.1f}" fill="{color}">{esc(value)}</tspan>')
        lines.append(f'<text y="0">{"".join(parts)}</text>')
    lines.append("")
    lines.append("".join(
        f'<rect x="{PAD_X + i * 26}" y="{-line_h * 0.72:.1f}" width="22" height="{line_h * 0.8:.1f}" rx="3" fill="{c}"/>'
        for i, c in enumerate(SWATCHES)
    ))

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="Rutvij Reddy Vakati — Data Analytics Engineer">',
        "<style>",
        f"text{{font-family:{FONT};font-size:{font_size:.1f}px;}}",
        ".l{opacity:0;animation:in .35s ease-out forwards;}",
        "@keyframes in{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}",
        "@media (prefers-reduced-motion:reduce){.l{animation:none;opacity:1}}",
        "</style>",
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<circle cx="20" cy="18" r="5" fill="#ff5f56"/><circle cx="37" cy="18" r="5" fill="#ffbd2e"/>'
        f'<circle cx="54" cy="18" r="5" fill="#27c93f"/>',
        f'<text x="{W / 2}" y="22" fill="{MUTED}" font-size="12" text-anchor="middle">rutvij@github: ~ — neofetch</text>',
        f'<line x1="0" y1="34" x2="{W}" y2="34" stroke="{BORDER}"/>',
    ]
    for i, line in enumerate(lines):
        if not line:
            continue
        y = TOP + i * line_h
        if STATIC:
            out.append(f'<g transform="translate(0 {y:.1f})">{line}</g>')
        else:
            # outer <g> positions, inner <g> animates (CSS transform would override the translate)
            out.append(
                f'<g transform="translate(0 {y:.1f})"><g class="l" style="animation-delay:{0.6 + i * 0.09:.2f}s">'
                f"{line}</g></g>"
            )
    out.append("</svg>")

    OUT.write_text("\n".join(out) + "\n")
    print(f"wrote {OUT.name} ({W}x{H}, font {font_size:.1f}px, line {line_h:.1f}px)")


if __name__ == "__main__":
    main()
