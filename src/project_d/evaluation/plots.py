"""Static SVG figures for the test analysis, drawn with the standard library only.

Usage: python -m project_d.evaluation.plots <analysis dir>

Reads the CSV tables written by `project_d.evaluation.test_analysis` and writes
`figures/*.svg` next to them. Every value shown is also in those tables.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from xml.sax.saxutils import escape

PROTOCOLS = ("N", "F", "R1", "R3", "R3P", "VBC")
SERIES = {"U": "#257de0", "A": "#f47230"}  # validated categorical slots 1-2
LABEL = {"U": "U (no reservation)", "A": "A (atomic reservation)"}
INK, MUTED, GRID, SURFACE = "#1f1f1f", "#6b6b6b", "#e3e3e3", "#ffffff"
SEQUENTIAL = ("#ffffff", "#cce3fd", "#9dc8f7", "#6aabf1", "#338ced", "#2370cd", "#1757ac")
FONT = "font-family='Helvetica, Arial, sans-serif'"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Svg:
    def __init__(self, width: int, height: int, title: str) -> None:
        self.width, self.height = width, height
        self.parts = [
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
            f"viewBox='0 0 {width} {height}' role='img'>",
            f"<title>{escape(title)}</title>",
            f"<rect width='{width}' height='{height}' fill='{SURFACE}'/>",
        ]

    def text(self, x, y, value, size=12, anchor="start", color=INK, weight="normal"):
        self.parts.append(
            f"<text x='{x:.1f}' y='{y:.1f}' font-size='{size}' text-anchor='{anchor}' "
            f"fill='{color}' font-weight='{weight}' {FONT}>{escape(str(value))}</text>"
        )

    def line(self, x1, y1, x2, y2, color=GRID, width=1, dash=""):
        extra = f" stroke-dasharray='{dash}'" if dash else ""
        self.parts.append(
            f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
            f"stroke='{color}' stroke-width='{width}'{extra}/>"
        )

    def bar(self, x, y0, y1, width, color):
        """Vertical bar from baseline y0 up to y1, top corners rounded 4px."""
        top, height = min(y0, y1), abs(y0 - y1)
        if height < 0.5:
            return
        r = min(4.0, width / 2, height)
        self.parts.append(
            f"<path d='M{x:.1f},{y0:.1f} V{top + r:.1f} Q{x:.1f},{top:.1f} {x + r:.1f},{top:.1f} "
            f"H{x + width - r:.1f} Q{x + width:.1f},{top:.1f} {x + width:.1f},{top + r:.1f} "
            f"V{y0:.1f} Z' fill='{color}'/>"
        )

    def rect(self, x, y, w, h, color, stroke=SURFACE):
        self.parts.append(
            f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' fill='{color}' "
            f"stroke='{stroke}' stroke-width='2'/>"
        )

    def circle(self, x, y, r, color):
        self.parts.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r}' fill='{color}' "
            f"stroke='{SURFACE}' stroke-width='2'/>"
        )

    def legend(self, x, y, modes=("U", "A")):
        for mode in modes:
            self.rect(x, y - 9, 10, 10, SERIES[mode], stroke="none")
            self.text(x + 15, y, LABEL[mode], 11, color=MUTED)
            x += 24 + 6.5 * len(LABEL[mode])

    def save(self, path: Path) -> None:
        path.write_text("\n".join([*self.parts, "</svg>"]) + "\n", encoding="utf-8")


def grouped_bars(path, title, subtitle, values, ymax, ticks, fmt):
    """values: {mode: {protocol: value}} for the six E2 protocols."""
    svg = Svg(640, 340, title)
    left, right, top, bottom = 56, 620, 74, 296
    svg.text(16, 24, title, 15, weight="bold")
    svg.text(16, 42, subtitle, 11, color=MUTED)
    svg.legend(left, 62)
    scale = (bottom - top) / ymax
    for tick in ticks:
        y = bottom - tick * scale
        svg.line(left, y, right, y)
        svg.text(left - 8, y + 4, fmt(tick), 10, "end", MUTED)
    group = (right - left) / len(PROTOCOLS)
    width = min(28.0, group / 3)
    for index, protocol in enumerate(PROTOCOLS):
        centre = left + group * (index + 0.5)
        for offset, mode in ((-1, "U"), (1, "A")):
            value = values[mode][protocol]
            x = centre + (offset - 1) * width / 2 + offset * 1  # 2px gap between bars
            svg.bar(x, bottom, bottom - value * scale, width, SERIES[mode])
            svg.text(x + width / 2, bottom - value * scale - 5, fmt(value), 10, "middle", MUTED)
        svg.text(centre, bottom + 18, protocol, 12, "middle")
    svg.line(left, bottom, right, bottom, MUTED)
    svg.save(path)


def forest(path, rows):
    keep = [r for r in rows if r["metric"] == "safe_fraction"]
    height = 96 + 22 * len(keep) + 28
    title = "E2 paired differences in U_safe/U*"
    svg = Svg(720, height, title)
    svg.text(16, 24, title, 15, weight="bold")
    svg.text(
        16,
        42,
        "Mean paired difference over 28 profiles; bar = 2.5-97.5% stratified "
        "profile bootstrap (10 000 draws)",
        11,
        color=MUTED,
    )
    lo = min(float(r["lower"]) for r in keep)
    hi = max(float(r["upper"]) for r in keep)
    lo, hi = min(lo, 0) - 0.05, max(hi, 0) + 0.05
    left, right, top = 250, 660, 76
    scale = (right - left) / (hi - lo)
    bottom = top + 22 * len(keep)
    tick = -0.6
    while tick <= hi:
        if tick >= lo:
            x = left + (tick - lo) * scale
            svg.line(x, top - 6, x, bottom, GRID)
            svg.text(x, bottom + 16, f"{tick:+.1f}" if tick else "0", 10, "middle", MUTED)
        tick = round(tick + 0.2, 1)
    zero = left + (0 - lo) * scale
    svg.line(zero, top - 6, zero, bottom, MUTED, 1.5)
    previous = None
    for index, row in enumerate(keep):
        y = top + 22 * index + 11
        if row["hypothesis"] != previous:
            svg.text(16, y + 4, row["hypothesis"], 11, color=MUTED, weight="bold")
            previous = row["hypothesis"]
        svg.text(left - 12, y + 4, f"{row['variant']} \u2212 {row['reference']}", 11, "end")
        x0 = left + (float(row["lower"]) - lo) * scale
        x1 = left + (float(row["upper"]) - lo) * scale
        crosses = float(row["lower"]) <= 0 <= float(row["upper"])
        color = MUTED if crosses else SERIES["U"]
        svg.line(x0, y, x1, y, color, 2)
        svg.circle(left + (float(row["mean_difference"]) - lo) * scale, y, 4.5, color)
    svg.text(
        16,
        height - 10,
        "Grey: interval includes 0. Descriptive robustness to the profile "
        "sample, not a significance test.",
        10,
        color=MUTED,
    )
    svg.save(path)


def heatmaps(path, cells):
    title = "E4-H1: episodes with a budget violation (of 8)"
    svg = Svg(640, 300, title)
    svg.text(16, 24, title, 15, weight="bold")
    svg.text(
        16,
        42,
        "Rows commit_delay, columns start_gap; test_s1_01 and test_s1_02, 4 repeats each",
        11,
        color=MUTED,
    )
    size = 54
    for panel, variant in enumerate(("U/N", "U/R3P")):
        x0, y0 = 90 + panel * 290, 92
        svg.text(x0 + 1.5 * size, y0 - 20, variant, 13, "middle", weight="bold")
        for col, gap in enumerate((0, 2, 4)):
            svg.text(x0 + size * (col + 0.5), y0 - 4, f"gap {gap}", 10, "middle", MUTED)
        for row, delay in enumerate((0, 1, 3)):
            svg.text(x0 - 8, y0 + size * (row + 0.5) + 4, f"delay {delay}", 10, "end", MUTED)
            for col, gap in enumerate((0, 2, 4)):
                (cell,) = [
                    c
                    for c in cells
                    if c["variant"] == variant
                    and int(c["commit_delay"]) == delay
                    and int(c["start_gap"]) == gap
                ]
                count = int(cell["violations"])
                color = SEQUENTIAL[round(count / 8 * (len(SEQUENTIAL) - 1))]
                svg.rect(x0 + col * size, y0 + row * size, size, size, color, stroke=GRID)
                ink = SURFACE if count >= 5 else INK
                svg.text(
                    x0 + size * (col + 0.5),
                    y0 + size * (row + 0.5) + 5,
                    count,
                    14,
                    "middle",
                    ink,
                    "bold",
                )
    svg.text(
        16,
        288,
        "Violation iff the actual first-submission offset < commit_delay "
        "(46 of 46 episodes; 0 of the other 98).",
        10,
        color=MUTED,
    )
    svg.save(path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", type=Path)
    args = parser.parse_args(argv)
    out = args.analysis / "figures"
    out.mkdir(exist_ok=True)

    variants = {r["variant"]: r for r in _read(args.analysis / "e2_variants.csv")}

    def by_mode(metric, factor=1.0):
        return {
            mode: {p: float(variants[f"{mode}/{p}"][metric]) * factor for p in PROTOCOLS}
            for mode in ("U", "A")
        }

    grouped_bars(
        out / "e2_safe_fraction.svg",
        "E2: U_safe/U* by protocol",
        "Mean over 112 episodes per variant (28 test profiles x 4 repeats)",
        by_mode("safe_fraction"),
        1.0,
        (0, 0.25, 0.5, 0.75, 1.0),
        lambda v: f"{v:.2f}",
    )
    grouped_bars(
        out / "e2_violations.svg",
        "E2: episodes with spent > budget",
        "Count of 112 episodes per variant; every A variant has 0",
        by_mode("violations"),
        100,
        (0, 25, 50, 75, 100),
        lambda v: f"{v:.0f}",
    )
    grouped_bars(
        out / "e2_prompt_tokens.svg",
        "E2: prompt tokens per episode",
        "Mean provider-reported prompt tokens (thousands); cost of each protocol",
        by_mode("prompt_tokens", 1 / 1000),
        150,
        (0, 50, 100, 150),
        lambda v: f"{v:.0f}k",
    )
    forest(out / "e2_bootstrap.svg", _read(args.analysis / "e2_bootstrap.csv"))
    heatmaps(out / "e4_h1_violations.svg", _read(args.analysis / "e4_h1_cells.csv"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
