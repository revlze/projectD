"""Static SVG figures for the test analysis, drawn with the standard library only.

Usage: python -m project_d.evaluation.plots <analysis dir>

Reads the existing analysis tables. Pass --test-results and --e5-summary together to add
the matched E2/E3/E5 figures, including the root report generated from the saved journals.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from itertools import pairwise
from math import ceil
from pathlib import Path
from statistics import fmean
from xml.sax.saxutils import escape

from project_d.evaluation.test_analysis import FAMILIES, Row, family_table
from project_d.experiments.matrix import E2_VARIANTS, E3_VARIANTS

PROTOCOLS = ("N", "F", "R1", "R3", "R3P", "VBC")
SERIES = {"U": "#257de0", "A": "#f47230"}  # validated categorical slots 1-2
LABEL = {"U": "U (no reservation)", "A": "A (atomic reservation)"}
INK, MUTED, GRID, SURFACE = "#1f1f1f", "#6b6b6b", "#e3e3e3", "#ffffff"
SEQUENTIAL = ("#ffffff", "#cce3fd", "#9dc8f7", "#6aabf1", "#338ced", "#2370cd", "#1757ac")
FONT = "font-family='Helvetica, Arial, sans-serif'"
AGREEMENT_COLORS = ("#107b68", "#b24c25", "#bfc5cf")
ROOT_COLORS = ("#bfc5cf", "#b24c25", "#895499", "#d8a42a", "#107b68")


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
        path.write_text("\n".join([*self.parts, "</svg>"]) + "\n", encoding="utf-8", newline="\n")


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


def _matched_runs(test_results: Path, e5_summary: Path) -> tuple[list[Row], list[Row]]:
    """Return 28-profile E2/E5 and 12-profile E2/E3/E5 cohorts with matched repeats."""
    conditions: dict[tuple[str, int], tuple[object, ...]] = {}
    settings = None
    cohorts = {}
    for series, summary, variants, profile_count in (
        ("E2", _summary_path(test_results / "e2"), E2_VARIANTS, 28),
        ("E3", _summary_path(test_results / "e3"), E3_VARIANTS, 12),
        ("E5", e5_summary, ("A/VBC-F",), 28),
    ):
        manifest = json.loads((summary.parent / "run_manifest.json").read_bytes())
        runtime = manifest["runtime"]
        config = (
            manifest["scenario_manifest_sha256"],
            runtime["provider"],
            runtime["llm"],
            runtime["llm_base_seed"],
            runtime["context_length"],
        )
        if settings is None:
            settings = config
        elif settings != config:
            raise ValueError(f"{series}: model, seeds or scenario manifest differ from E2")
        rows = _read(summary)
        cells: dict[str, set[tuple[str, int]]] = defaultdict(set)
        for row in rows:
            spec = manifest["episodes"][row["episode"]]
            profile, repeat, variant = row["profile"], int(row["repeat"]), row["variant"]
            key = (profile, repeat)
            saved = spec["spec"]
            if (
                row["series"] != series
                or saved["series"] != series
                or Path(saved["profile"]).stem != profile
                or saved["repeat"] != repeat
                or saved["variant"] != variant
                or row["failure"]
                or row["audit_issues"] != "0"
                or key in cells[variant]
            ):
                raise ValueError(f"{row['episode']}: invalid or duplicate episode")
            metadata = spec["metadata"]
            if any(
                row[field] != str(metadata[field])
                for field in (
                    "first_agent",
                    "role_swap",
                    "start_gap",
                    "commit_delay",
                    "message_delay",
                )
            ):
                raise ValueError(f"{row['episode']}: summary does not match the run manifest")
            comparable = (
                spec["scenario_sha256"],
                spec["llm_seed"],
                row["family"],
                spec["user_sha256"],
                {
                    k: v
                    for k, v in metadata.items()
                    if k not in ("mode", "variant", "protocol_version")
                },
            )
            if series == "E2":
                conditions.setdefault(key, comparable)
            if conditions.get(key) != comparable:
                raise ValueError(f"{row['episode']}: setup differs from the matched E2 key")
            cells[variant].add(key)
        profiles = {key[0] for keys in cells.values() for key in keys}
        expected = {(p, repeat) for p in profiles for repeat in range(4)}
        if (
            len(profiles) != profile_count
            or set(cells) != set(variants)
            or any(keys != expected for keys in cells.values())
        ):
            raise ValueError(f"{series}: incomplete profile/repeat matrix")
        if series == "E3":
            common = profiles
        cohorts[series] = rows
    full = cohorts["E2"] + cohorts["E5"]
    return full, [r for r in full if r["profile"] in common] + cohorts["E3"]


def _summary_path(folder: Path) -> Path:
    (summary,) = sorted(folder.glob("*/summary.csv"))
    return summary


def _safe_mean(rows: list[Row]) -> float:
    return fmean(float(row["safe_fraction"]) for row in rows)


def _mean_tokens(rows: list[Row]) -> float:
    return fmean(int(row["prompt_tokens"]) + int(row["completion_tokens"]) for row in rows)


def _variants(rows: list[Row]) -> dict[str, list[Row]]:
    grouped: dict[str, list[Row]] = defaultdict(list)
    for row in rows:
        grouped[row["variant"]].append(row)
    return dict(grouped)


def pareto_front(points: dict[str, tuple[float, float]]) -> set[str]:
    """Minimize tokens and maximize safe utility, retaining exact ties."""
    return {
        variant
        for variant, (tokens, utility) in points.items()
        if not any(
            other_tokens <= tokens
            and other_utility >= utility
            and (other_tokens < tokens or other_utility > utility)
            for other_tokens, other_utility in points.values()
        )
    }


def _heading(svg: Svg, title: str, subtitle: str) -> None:
    svg.text(16, 24, title, 16, weight="bold")
    svg.text(16, 44, subtitle, 11, color=MUTED)


def _point_label(svg: Svg, x, y, label, bounds, used, markers) -> None:
    panel_left, panel_right = bounds
    size = len(label) * 5.7 + 4
    for offset in (-7, 15, 28, -20, 41, -33, 54, -46):
        for lx in (x + 7, x - size - 7):
            ly = y + offset
            if not (panel_left <= lx <= panel_right - size and 88 <= ly <= 320):
                continue
            if any(
                lx < right and lx + size > left and abs(ly - baseline) < 12
                for left, right, baseline in used
            ) or any(lx - 5 < px < lx + size + 5 and ly - 14 < py < ly + 7 for px, py in markers):
                continue
            used.append((lx, lx + size, ly))
            if abs(offset) > 15:
                svg.line(x, y, lx + (size if lx < x else 0), ly - 3, MUTED, 0.7)
            svg.text(lx, ly, label, 10)
            return
    svg.text(min(x + 7, panel_right - size), y - 7, label, 10)


def utility_tokens(path: Path, rows: list[Row], *, split: bool) -> None:
    title = "Safe utility and total tokens"
    profiles = len({r["profile"] for r in rows})
    series = "E2 + E3 + E5" if split else "E2 + E5"
    svg = Svg(1000 if split else 790, 384, title)
    _heading(
        svg,
        title,
        f"{series} | {profiles} matched profiles x 4 repeats | "
        "Dashed line: nondominated methods within each panel",
    )
    svg.legend(62, 63)
    points = {v: (_mean_tokens(g) / 1000, _safe_mean(g)) for v, g in _variants(rows).items()}
    upper = ceil(max(tokens for tokens, _ in points.values()) / 20) * 20
    modes = ("U", "A") if split else ("",)
    panel_width = (svg.width - 46) / len(modes)
    for index, mode in enumerate(modes):
        panel = {v: p for v, p in points.items() if v.startswith(mode)}
        left, right = 60 + index * panel_width, 18 + (index + 1) * panel_width
        top, bottom = 101, 326
        if mode:
            svg.text((left + right) / 2, 84, LABEL[mode], 11, "middle", weight="bold")
        for tick in range(0, 5):
            y = bottom - tick / 4 * (bottom - top)
            svg.line(left, y, right, y)
            svg.text(left - 8, y + 4, f"{tick / 4:.2f}", 10, "end", MUTED)
        for tick in range(0, upper + 1, 20 if upper <= 140 else 40):
            x = left + tick / upper * (right - left)
            svg.line(x, top, x, bottom)
            svg.text(x, bottom + 17, tick, 10, "middle", MUTED)

        positions = {
            v: (left + tokens / upper * (right - left), bottom - score * (bottom - top))
            for v, (tokens, score) in panel.items()
        }
        frontier = sorted({positions[v] for v in pareto_front(panel)})
        for start, end in pairwise(frontier):
            svg.line(*start, *end, MUTED, 1.4, "5 3")
        used = []
        for variant, (x, y) in sorted(positions.items(), key=lambda item: item[1][1]):
            svg.circle(x, y, 5, SERIES[variant[0]])
            _point_label(svg, x, y, variant, (left, right), used, positions.values())
    svg.text(15, 88, "U_safe/U*", 10, color=MUTED)
    svg.text(
        svg.width / 2,
        369,
        "Mean input + output tokens per episode (thousands)",
        12,
        "middle",
        MUTED,
    )
    svg.save(path)


def family_heatmap(path: Path, rows: list[Row]) -> None:
    table = family_table(rows, "safe_fraction")
    title = "Safe utility by scenario family"
    svg = Svg(650, 104 + 28 * len(table), title)
    _heading(svg, title, "E2 + E5 | 28 test profiles | Cells show mean U_safe/U*")
    for j, family in enumerate(FAMILIES):
        svg.text(190 + j * 88, 68, family, 12, "middle", weight="bold")
    for i, row in enumerate(table):
        y = 79 + 28 * i
        svg.text(133, y + 18, row["variant"], 11, "end")
        for j, family in enumerate(FAMILIES):
            value = float(row[family])
            index = round(value * (len(SEQUENTIAL) - 1))
            x = 146 + j * 88
            svg.rect(x, y, 88, 28, SEQUENTIAL[index])
            svg.text(x + 44, y + 18, f"{value:.3f}", 11, "middle", SURFACE if index >= 5 else INK)
    svg.save(path)


def _strip_chart(path, title, subtitle, panels, labels, colors):
    height = 99 + sum(32 + 27 * len(rows) for _, rows in panels)
    svg = Svg(800, height, title)
    _heading(svg, title, subtitle)
    x = 24
    for label, color in zip(labels, colors, strict=True):
        svg.rect(x, 56, 11, 11, color, stroke="none")
        svg.text(x + 16, 66, label, 11, color=MUTED)
        x += 27 + len(label) * 6.4
    y = 86
    for heading, rows in panels:
        if heading:
            svg.text(18, y + 10, heading, 12, weight="bold")
            y += 22
        for variant, counts in rows:
            width = 555
            total = sum(counts)
            svg.text(139, y + 16, variant, 11, "end")
            left = 151
            for count, color in zip(counts, colors, strict=True):
                segment = width * count / total
                if count:
                    svg.rect(left, y, segment, 21, color)
                    if segment >= (9 if count < 10 else 18):
                        svg.text(
                            left + segment / 2,
                            y + 15,
                            count,
                            11,
                            "middle",
                            INK if color in ("#bfc5cf", "#d8a42a") else SURFACE,
                        )
                    left += segment
            svg.text(716, y + 16, f"n={total}", 10, color=MUTED)
            y += 27
        y += 10
    svg.save(path)


def _agreement_counts(rows: list[Row]) -> tuple[int, int, int]:
    within = sum(row["agreed_within_budget"] == "True" for row in rows)
    over = sum(row["agreed_over_budget"] == "True" for row in rows)
    return within, over, len(rows) - within - over


def _trend_panel(svg: Svg, left, width, title, categories, metrics, limits, fmt):
    top, bottom = 82, 246
    lo, hi = limits
    svg.text(left + width / 2, 65, title, 12, "middle", weight="bold")
    for tick in range(5):
        yy = bottom - tick / 4 * (bottom - top)
        svg.line(left, yy, left + width, yy)
        svg.text(left - 7, yy + 4, fmt(lo + (hi - lo) * tick / 4), 10, "end", MUTED)
    xs = [left + (index + 0.5) * width / len(categories) for index in range(len(categories))]
    for xx, category in zip(xs, categories, strict=True):
        svg.text(xx, bottom + 17, category, 11, "middle")
    for label, values, color in metrics:
        ys = [bottom - (v - lo) / (hi - lo) * (bottom - top) for v in values]
        for (x1, y1), (x2, y2) in pairwise(zip(xs, ys, strict=True)):
            svg.line(x1, y1, x2, y2, color, 2)
        for xx, yy in zip(xs, ys, strict=True):
            svg.circle(xx, yy, 4.5, color)
        if label:
            svg.text(xs[-1] + 8, ys[-1] + 4, label, 10, color=color)


def _extended_figures(out: Path, test_results: Path, e5_summary: Path, root_table: Path) -> None:
    full, common = _matched_runs(test_results, e5_summary)
    utility_tokens(out / "e2_e5_utility_tokens.svg", full, split=False)
    utility_tokens(out / "e2_e3_e5_utility_tokens.svg", common, split=True)
    family_heatmap(out / "e2_e5_family_utility.svg", full)
    groups, full_groups = _variants(common), _variants(full)
    title = "E3 factorial ablation of verification and guard"
    svg = Svg(520, 287, title)
    _heading(svg, title, "12 matched profiles x 4 repeats | U_safe/U*")
    _trend_panel(
        svg,
        65,
        395,
        "Mean safe utility",
        ("V off", "V on"),
        [
            ("", [_safe_mean(groups[v]) for v in ("A/S", "A/S+V")], SERIES["U"]),
            ("", [_safe_mean(groups[v]) for v in ("A/S+G", "A/VBC")], SERIES["A"]),
        ],
        (0.75, 1.0),
        lambda value: f"{value:.2f}",
    )
    for x, mode, label in ((165, "U", "G off"), (255, "A", "G on")):
        svg.line(x, 274, x + 19, 274, SERIES[mode], 2)
        svg.text(x + 25, 278, label, 11, color=MUTED)
    svg.save(out / "e3_v_g_factorial.svg")
    e3 = ("A/S", "A/S+V", "A/S+G", "A/VBC-r0", "A/VBC", "A/VBC-r2")
    _strip_chart(
        out / "e3_e5_agreements.svg",
        "Agreement outcomes",
        "Counts among all episodes",
        [
            ("E3 | 12 profiles", [(v, _agreement_counts(groups[v])) for v in e3]),
            (
                "E5 comparison | 28 profiles",
                [(v, _agreement_counts(full_groups[v])) for v in ("A/VBC", "A/VBC-F")],
            ),
        ],
        ("Within budget", "Over budget", "No agreement"),
        AGREEMENT_COLORS,
    )
    title = "E3 VBC message rounds"
    svg = Svg(960, 291, title)
    _heading(svg, title, "12 matched profiles x 4 repeats | One plan revision in every variant")
    rounds = [groups[v] for v in ("A/VBC-r0", "A/VBC", "A/VBC-r2")]
    categories = ("0", "1", "2")
    _trend_panel(
        svg,
        60,
        245,
        "Mean U_safe/U*",
        categories,
        [("", [_safe_mean(g) for g in rounds], SERIES["A"])],
        (0.75, 1),
        lambda v: f"{v:.2f}",
    )
    _trend_panel(
        svg,
        370,
        245,
        "Share of episodes with agreement",
        categories,
        [
            ("All", [sum(_agreement_counts(g)[:2]) / len(g) for g in rounds], SERIES["A"]),
            (
                "Within budget",
                [_agreement_counts(g)[0] / len(g) for g in rounds],
                AGREEMENT_COLORS[0],
            ),
        ],
        (0, 1),
        lambda v: f"{v:.0%}",
    )
    high = ceil(max(_mean_tokens(g) for g in rounds) / 20000) * 20
    _trend_panel(
        svg,
        714,
        224,
        "Mean total tokens (thousands)",
        categories,
        [("", [_mean_tokens(g) / 1000 for g in rounds], SERIES["A"])],
        (0, high),
        lambda v: f"{v:.0f}",
    )
    svg.text(480, 283, "Assigned message rounds", 11, "middle", MUTED)
    svg.save(out / "e3_vbc_rounds.svg")
    root_fields = (
        "not_submitted",
        "budget_refused",
        "other_refusal",
        "accepted_incomplete",
        "completed",
    )
    roots = {}
    for row in _read(root_table):
        variant = row["variant"]
        if variant.startswith("A/"):
            if variant in roots or variant not in full_groups:
                raise ValueError(f"{variant}: unexpected root report cohort")
            counts = tuple(int(row[field]) for field in root_fields)
            expected = sum(r["root_conflict"] == "True" for r in full_groups[variant])
            if int(row["episodes"]) != expected or sum(counts) != 2 * expected:
                raise ValueError(f"{variant}: root outcomes do not match the experiment cohort")
            roots[variant] = counts
    if roots.keys() != {v for v in full_groups if v.startswith("A/")}:
        raise ValueError("Root report must include all atomic E2 and E5 methods")
    _strip_chart(
        out / "e2_e5_root_conflicts.svg",
        "Main-job outcomes when both cheapest options cannot fit",
        "Atomic E2 and E5 methods | Counts are jobs; two jobs per conflict episode",
        [("", [(v, roots[v]) for v in full_groups if v in roots])],
        ("No submission", "Budget refusal", "Other refusal", "Accepted, unfinished", "Completed"),
        ROOT_COLORS,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("--test-results", type=Path)
    parser.add_argument("--e5-summary", type=Path)
    args = parser.parse_args(argv)
    if bool(args.test_results) != bool(args.e5_summary):
        parser.error("--test-results and --e5-summary must be supplied together")
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
    if args.test_results:
        _extended_figures(
            out, args.test_results, args.e5_summary, args.analysis / "root_conflict_e2_e5.csv"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
