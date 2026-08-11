#!/usr/bin/env python3
"""WCAG 2.x contrast math. Compute ratios and find the nearest compliant shade.

The nearest-shade search preserves hue and saturation and moves lightness only,
so a fix never changes the color family the designer chose.

Usage:
  contrast.py "#7a9cc6" "#ffffff"                 # ratio + suggested fix at 4.5:1
  contrast.py "#7a9cc6" "#ffffff" --target 3.0    # large text / UI component
  contrast.py --pairs "#7a9cc6,#fff;#888,#000"    # batch, one line per pair

Accepts #rgb, #rrggbb, rgb(r,g,b), or bare hex.
Exit code is 0 always; read the PASS/FAIL column.
"""
import argparse
import colorsys
import re
import sys


def parse_color(s):
    s = s.strip().strip('"').strip("'")
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", s, re.I)
    if m:
        return tuple(int(g) / 255 for g in m.groups())
    h = s.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 8:  # #rrggbbaa -- alpha ignored, caller must flag it
        h = h[:6]
    if len(h) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"cannot parse color: {s!r}")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def to_hex(rgb):
    return "#" + "".join(f"{round(max(0.0, min(1.0, c)) * 255):02x}" for c in rgb)


def luminance(rgb):
    def f(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def nearest_compliant(fg, bg, target):
    """Move fg's lightness (HSL) the minimum distance needed to hit target.

    Tries darkening and lightening; returns whichever compliant result is
    closest to the original lightness. Returns None if neither direction works.
    """
    h, l0, s = colorsys.rgb_to_hls(*fg)
    best = None
    for direction in (-1, 1):
        lo, hi = l0, (0.0 if direction < 0 else 1.0)
        end = colorsys.hls_to_rgb(h, hi, s)
        if ratio(end, bg) < target:
            continue  # this direction can never reach the target
        for _ in range(40):  # binary search on lightness
            mid = (lo + hi) / 2
            if ratio(colorsys.hls_to_rgb(h, mid, s), bg) >= target:
                hi = mid
            else:
                lo = mid
        cand = colorsys.hls_to_rgb(h, hi, s)
        if best is None or abs(hi - l0) < best[0]:
            best = (abs(hi - l0), cand)
    return best[1] if best else None


def report(fg_s, bg_s, target):
    fg, bg = parse_color(fg_s), parse_color(bg_s)
    r = ratio(fg, bg)
    ok = r >= target
    line = f"{to_hex(fg)} on {to_hex(bg)} = {r:.2f}:1  (need {target}:1)  {'PASS' if ok else 'FAIL'}"
    if not ok:
        fix = nearest_compliant(fg, bg, target)
        if fix:
            line += f"\n    nearest compliant (same hue/sat): {to_hex(fix)} = {ratio(fix, bg):.2f}:1"
            shift = abs(colorsys.rgb_to_hls(*fix)[1] - colorsys.rgb_to_hls(*fg)[1])
            if shift > 0.25:
                line += (f"\n    WARNING: lightness shifts {shift * 100:.0f}% -- this reads as a"
                         " different color. Do not apply silently; ask the designer.")
        else:
            line += "\n    no compliant shade at this hue/saturation -- background must change too"
    return line


COLOR_RE = re.compile(r"rgba?\([^)]*\)|#?[0-9a-fA-F]{3,8}")


def main():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("fg", nargs="?")
    p.add_argument("bg", nargs="?")
    p.add_argument("--target", type=float, default=4.5,
                   help="4.5 normal text, 3.0 large text (>=24px, or >=18.66px bold) and UI components")
    p.add_argument("--pairs", help='semicolon-separated "fg,bg" pairs')
    a = p.parse_args()

    if a.pairs:
        for pair in filter(None, (x.strip() for x in a.pairs.split(";"))):
            found = COLOR_RE.findall(pair)
            if len(found) != 2:
                print(f"{pair}  SKIPPED -- expected exactly 2 colors, found {len(found)}")
                continue
            print(report(found[0], found[1], a.target))
    elif a.fg and a.bg:
        print(report(a.fg, a.bg, a.target))
    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
