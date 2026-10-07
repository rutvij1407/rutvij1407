"""Render data/contributions.json as an animated 53-week heatmap SVG.

Cells drop in along a diagonal once on load, then freeze. No looping.
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

# none -> brightest; level 5 is reserved for the best day(s) of the year
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG, BORDER, MUTED, TEXT, ACCENT = "#0d1117", "#30363d", "#7d8590", "#c9d1d9", "#39d353"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

W = 860
CELL, GAP = 12, 3
PITCH = CELL + GAP
GRID_X, GRID_Y = 52, 74
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    data = json.loads(DATA.read_text())
    days = [(date.fromisoformat(d["date"]), d) for d in data["days"]]
    first = days[0][0]
    start = date.fromordinal(first.toordinal() - (first.weekday() + 1) % 7)  # back to Sunday
    best = data["best_day"]["count"]

    cells, month_labels, last_month = [], [], None
    for dt, d in days:
        col = (dt - start).days // 7
        row = (dt.weekday() + 1) % 7
        level = 5 if best > 0 and d["count"] == best else d["level"]
        x, y = GRID_X + col * PITCH, GRID_Y + row * PITCH
        delay = (col + row) * 0.018
        noun = "contribution" if d["count"] == 1 else "contributions"
        cells.append(
            f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[level]}" style="animation-delay:{delay:.3f}s">'
            f'<title>{d["count"]} {noun} on {dt:%b %-d, %Y}</title></rect>'
        )
        if row == 0 and dt.month != last_month and dt.day <= 7:
            month_labels.append((x, MONTHS[dt.month - 1]))
            last_month = dt.month

    grid_bottom = GRID_Y + 7 * PITCH - GAP
    legend_y = grid_bottom + 22
    stats_y = legend_y + 38
    H = stats_y + 28

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{data["total"]} GitHub contributions in the last year">',
        "<style>",
        f"text{{font-family:{FONT};}}",
        ".c{opacity:0;transform-box:fill-box;transform-origin:center;"
        "animation:drop .45s cubic-bezier(.2,.9,.3,1.2) forwards;}",
        "@keyframes drop{from{opacity:0;transform:translateY(-8px) scale(.6)}"
        "to{opacity:1;transform:none}}",
        ".f{opacity:0;animation:fade .6s ease-out forwards;}",
        "@keyframes fade{to{opacity:1}}",
        "@media (prefers-reduced-motion:reduce){.c,.f{animation:none;opacity:1}}",
        "</style>",
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        # terminal title bar
        f'<circle cx="20" cy="18" r="5" fill="#ff5f56"/><circle cx="37" cy="18" r="5" fill="#ffbd2e"/>'
        f'<circle cx="54" cy="18" r="5" fill="#27c93f"/>',
        f'<text x="{W / 2}" y="22" fill="{MUTED}" font-size="12" text-anchor="middle">'
        f'contributions — github.com/{data["username"]}</text>',
        f'<line x1="0" y1="34" x2="{W}" y2="34" stroke="{BORDER}"/>',
    ]
    for x, name in month_labels:
        parts.append(f'<text x="{x}" y="{GRID_Y - 10}" fill="{MUTED}" font-size="11">{name}</text>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="{GRID_X - 10}" y="{GRID_Y + row * PITCH + CELL - 2}" fill="{MUTED}" '
            f'font-size="10" text-anchor="end">{name}</text>'
        )
    parts.extend(cells)

    # Less -> More legend, right-aligned under the grid
    grid_right = GRID_X + ((days[-1][0] - start).days // 7 + 1) * PITCH - GAP
    lx = grid_right - len(PALETTE) * PITCH - 34
    parts.append(f'<g class="f" style="animation-delay:1.4s">')
    parts.append(f'<text x="{lx - 8}" y="{legend_y + 10}" fill="{MUTED}" font-size="11" text-anchor="end">Less</text>')
    for i, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx + i * PITCH}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
    parts.append(f'<text x="{lx + len(PALETTE) * PITCH + 4}" y="{legend_y + 10}" fill="{MUTED}" font-size="11">More</text>')

    # headline total on the legend row, streak stats in the footer
    parts.append(
        f'<text x="{GRID_X}" y="{legend_y + 11}" font-size="14">'
        f'<tspan fill="{ACCENT}" font-weight="bold">{data["total"]:,}</tspan>'
        f'<tspan fill="{TEXT}"> contributions in the last year</tspan></text>'
    )
    bd = date.fromisoformat(data["best_day"]["date"])
    stats = [
        (f'{data["current_streak"]}d', "current streak"),
        (f'{data["longest_streak"]}d', "longest streak"),
        (f'{data["best_day"]["count"]}', f"best day ({bd:%b %-d})"),
        (f'{data["active_days"]}', "active days"),
    ]
    col_w = (grid_right - GRID_X) / len(stats)
    for i, (value, label) in enumerate(stats):
        x = GRID_X + i * col_w
        parts.append(
            f'<text x="{x:.0f}" y="{stats_y + 6}" font-size="12">'
            f'<tspan fill="{ACCENT}" font-weight="bold">{esc(value)}</tspan>'
            f'<tspan fill="{MUTED}"> {esc(label)}</tspan></text>'
        )
    parts.append("</g>")
    parts.append(f'<text x="{W - 14}" y="{H - 8}" fill="{BORDER}" font-size="9" text-anchor="end">'
                 f'updated {data["generated_at"][:10]}</text>')
    parts.append("</svg>")

    OUT.write_text("\n".join(parts) + "\n")
    print(f"wrote {OUT.name} ({W}x{H}, {len(cells)} cells)")


if __name__ == "__main__":
    main()
