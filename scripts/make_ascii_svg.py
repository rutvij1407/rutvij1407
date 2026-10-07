"""Convert source-prepped.png into a monochrome ASCII portrait that types itself in.

Each row is revealed by a left-to-right clip wipe with a block cursor riding the
edge, staggered top to bottom. Plays once and freezes (SMIL, which GitHub renders).
"""
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "rutvij-ascii.svg"

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space clears the background
COLS = 72
CHAR_ASPECT = 0.5  # glyph width / line height
W = 370
PAD_X, PAD_TOP, PAD_BOTTOM = 18, 46, 18
BG, BORDER, MUTED, INK, CURSOR = "#0d1117", "#30363d", "#7d8590", "#c9d1d9", "#39d353"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
ROW_DUR, ROW_STAGGER, START = 0.22, 0.06, 0.3
STATIC = os.environ.get("STATIC") == "1"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def to_ascii(img):
    rows = round(COLS * img.height / img.width * CHAR_ASPECT)
    small = np.asarray(img.resize((COLS, rows), Image.LANCZOS), dtype=np.float32)
    background = small > 248
    lo, hi = np.percentile(small[~background], [2, 98])
    px = np.clip((small - lo) / max(hi - lo, 1), 0, 1)
    idx = ((1 - px) * (len(RAMP) - 1)).round().astype(int)
    idx[background] = 0
    lines = ["".join(RAMP[i] for i in row).rstrip() for row in idx]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return lines


def main():
    lines = to_ascii(Image.open(SRC).convert("L"))
    text_w = W - 2 * PAD_X
    char_w = text_w / COLS
    line_h = char_w / CHAR_ASPECT
    font_size = line_h * 0.98
    H = round(PAD_TOP + len(lines) * line_h + PAD_BOTTOM)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="ASCII portrait of Rutvij">',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<circle cx="20" cy="18" r="5" fill="#ff5f56"/><circle cx="37" cy="18" r="5" fill="#ffbd2e"/>'
        f'<circle cx="54" cy="18" r="5" fill="#27c93f"/>',
        f'<text x="{W / 2}" y="22" fill="{MUTED}" font-size="12" text-anchor="middle" '
        f'font-family="{FONT}">rutvij.txt</text>',
        f'<line x1="0" y1="34" x2="{W}" y2="34" stroke="{BORDER}"/>',
        "<defs>",
    ]
    body = []
    for i, line in enumerate(lines):
        if not line:
            continue
        y = PAD_TOP + i * line_h
        width = len(line) * char_w
        begin = START + i * ROW_STAGGER
        text = (
            f'<text x="{PAD_X}" y="{y + line_h * 0.8:.2f}" textLength="{width:.2f}" '
            f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{esc(line)}</text>'
        )
        if STATIC:
            body.append(text)
            continue
        parts.append(
            f'<clipPath id="r{i}"><rect x="{PAD_X}" y="{y:.2f}" width="0" height="{line_h:.2f}">'
            f'<animate attributeName="width" from="0" to="{width:.2f}" begin="{begin:.2f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
        )
        body.append(f'<g clip-path="url(#r{i})">{text}</g>')
        # block cursor riding the wipe edge, visible only while this row types
        body.append(
            f'<rect x="{PAD_X}" y="{y:.2f}" width="{char_w:.2f}" height="{line_h:.2f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{PAD_X}" to="{PAD_X + width:.2f}" begin="{begin:.2f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s" dur="{ROW_DUR}s"/></rect>'
        )
    parts.append("</defs>")
    parts.append(f'<g fill="{INK}" font-family="{FONT}" font-size="{font_size:.2f}">')
    parts.extend(body)
    parts.append("</g></svg>")

    OUT.write_text("\n".join(parts) + "\n")
    print(f"wrote {OUT.name} ({W}x{H}, {len(lines)} rows x {COLS} cols)")


if __name__ == "__main__":
    main()
