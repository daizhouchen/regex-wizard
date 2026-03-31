#!/usr/bin/env python3
"""
railroad.py - Generate SVG railroad diagrams from regex patterns.

Color coding:
  Blue   (#4A90D9) = literals
  Green  (#27AE60) = character classes
  Orange (#E67E22) = quantifiers
  Purple (#8E44AD) = groups

Usage:
  python railroad.py "<pattern>" [-o output.svg]
"""

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional


# ── Colour palette ──────────────────────────────────────────────────────────

COLORS = {
    "literal": "#4A90D9",
    "char_class": "#27AE60",
    "quantifier": "#E67E22",
    "group": "#8E44AD",
    "anchor": "#E74C3C",
    "alternation": "#95A5A6",
    "track": "#333333",
    "bg": "#FAFAFA",
    "text": "#FFFFFF",
}

# ── AST node types ──────────────────────────────────────────────────────────


@dataclass
class Node:
    """Base AST node."""
    kind: str  # literal, char_class, quantifier, group, alternation, anchor, sequence
    label: str = ""
    children: List["Node"] = field(default_factory=list)
    quantifier: Optional[str] = None  # ?, *, +, {n,m}


# ── Regex parser (simplified) ──────────────────────────────────────────────


_QUANT_RE = re.compile(r"^([?*+]|\{\d+(?:,\d*)?\})\??")

_CHAR_CLASS_NAMES = {
    r"\d": "digit [0-9]",
    r"\D": "non-digit",
    r"\w": "word [a-zA-Z0-9_]",
    r"\W": "non-word",
    r"\s": "whitespace",
    r"\S": "non-whitespace",
    r"\b": "word boundary",
    r"\B": "non-boundary",
}

_ANCHOR_MAP = {
    "^": "start of line",
    "$": "end of line",
}


def _parse_quantifier(pattern: str, pos: int):
    """Try to consume a quantifier at *pos*. Return (label, new_pos) or None."""
    m = _QUANT_RE.match(pattern[pos:])
    if m:
        raw = m.group(0)
        return raw, pos + len(raw)
    return None, pos


def _parse_char_class(pattern: str, pos: int):
    """Parse a [...] character class starting at *pos*."""
    assert pattern[pos] == "["
    end = pos + 1
    if end < len(pattern) and pattern[end] == "^":
        end += 1
    if end < len(pattern) and pattern[end] == "]":
        end += 1
    while end < len(pattern) and pattern[end] != "]":
        if pattern[end] == "\\" and end + 1 < len(pattern):
            end += 2
        else:
            end += 1
    if end < len(pattern):
        end += 1  # consume ']'
    label = pattern[pos:end]
    return Node(kind="char_class", label=label), end


def _parse_group(pattern: str, pos: int):
    """Parse a (...) group starting at *pos*. Returns (Node, new_pos)."""
    assert pattern[pos] == "("
    # Determine group prefix
    prefix = ""
    inner_start = pos + 1
    if pattern[inner_start: inner_start + 2] == "?:":
        prefix = "non-capture"
        inner_start += 2
    elif pattern[inner_start: inner_start + 3] == "?P<":
        end_name = pattern.index(">", inner_start + 3)
        name = pattern[inner_start + 3: end_name]
        prefix = f"named: {name}"
        inner_start = end_name + 1
    elif pattern[inner_start: inner_start + 2] == "?=":
        prefix = "lookahead"
        inner_start += 2
    elif pattern[inner_start: inner_start + 2] == "?!":
        prefix = "neg lookahead"
        inner_start += 2
    elif pattern[inner_start: inner_start + 3] == "?<=":
        prefix = "lookbehind"
        inner_start += 3
    elif pattern[inner_start: inner_start + 3] == "?<!":
        prefix = "neg lookbehind"
        inner_start += 3
    else:
        prefix = "group"

    # Find matching close paren (handling nesting)
    depth = 1
    scan = inner_start
    while scan < len(pattern) and depth > 0:
        ch = pattern[scan]
        if ch == "\\" and scan + 1 < len(pattern):
            scan += 2
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        scan += 1
    inner_end = scan - 1  # position of closing ')'
    inner_pattern = pattern[inner_start:inner_end]
    children = _parse_alternation(inner_pattern)
    return Node(kind="group", label=prefix, children=[children]), scan


def _parse_alternation(pattern: str) -> Node:
    """Split on top-level '|' and parse each branch."""
    branches: List[str] = []
    depth = 0
    start = 0
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\" and i + 1 < len(pattern):
            i += 2
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "|" and depth == 0:
            branches.append(pattern[start:i])
            start = i + 1
        i += 1
    branches.append(pattern[start:])

    if len(branches) == 1:
        return _parse_sequence(branches[0])
    return Node(
        kind="alternation",
        label="OR",
        children=[_parse_sequence(b) for b in branches],
    )


def _parse_sequence(pattern: str) -> Node:
    """Parse a sequence of atoms (no top-level alternation)."""
    nodes: List[Node] = []
    pos = 0
    while pos < len(pattern):
        ch = pattern[pos]

        # Escaped sequences
        if ch == "\\":
            if pos + 1 < len(pattern):
                esc = pattern[pos: pos + 2]
                if esc in _CHAR_CLASS_NAMES:
                    node = Node(kind="char_class", label=_CHAR_CLASS_NAMES[esc])
                    pos += 2
                elif esc in (r"\b", r"\B"):
                    node = Node(kind="anchor", label=_CHAR_CLASS_NAMES[esc])
                    pos += 2
                else:
                    node = Node(kind="literal", label=esc[1])
                    pos += 2
                q, pos = _parse_quantifier(pattern, pos)
                if q:
                    node = Node(kind="quantifier", label=q, children=[node])
                nodes.append(node)
            else:
                nodes.append(Node(kind="literal", label="\\"))
                pos += 1
            continue

        # Anchors
        if ch in _ANCHOR_MAP:
            nodes.append(Node(kind="anchor", label=_ANCHOR_MAP[ch]))
            pos += 1
            continue

        # Character class
        if ch == "[":
            node, pos = _parse_char_class(pattern, pos)
            q, pos = _parse_quantifier(pattern, pos)
            if q:
                node = Node(kind="quantifier", label=q, children=[node])
            nodes.append(node)
            continue

        # Group
        if ch == "(":
            node, pos = _parse_group(pattern, pos)
            q, pos = _parse_quantifier(pattern, pos)
            if q:
                node = Node(kind="quantifier", label=q, children=[node])
            nodes.append(node)
            continue

        # Dot (any char)
        if ch == ".":
            node = Node(kind="char_class", label="any char")
            pos += 1
            q, pos = _parse_quantifier(pattern, pos)
            if q:
                node = Node(kind="quantifier", label=q, children=[node])
            nodes.append(node)
            continue

        # Plain literal – greedily collect consecutive literal chars
        lit = ""
        while pos < len(pattern) and pattern[pos] not in r"\[().|^$?*+{}":
            lit += pattern[pos]
            pos += 1
        if lit:
            # If next is a quantifier, split last char off so quantifier only applies to it
            q_check, _ = _parse_quantifier(pattern, pos)
            if q_check and len(lit) > 1:
                nodes.append(Node(kind="literal", label=lit[:-1]))
                lit = lit[-1]
            node = Node(kind="literal", label=lit)
            q, pos = _parse_quantifier(pattern, pos)
            if q:
                node = Node(kind="quantifier", label=q, children=[node])
            nodes.append(node)
            continue

        # Fallback – skip unknown
        pos += 1

    if len(nodes) == 0:
        return Node(kind="literal", label="(empty)")
    if len(nodes) == 1:
        return nodes[0]
    return Node(kind="sequence", children=nodes)


# ── SVG renderer ───────────────────────────────────────────────────────────

_UNIT = 16  # base grid unit
_PAD = 8
_BOX_H = 32
_ARROW = 10
_MIN_BOX_W = 40
_FONT_SIZE = 13
_CHAR_W = 7.8  # approximate character width


def _text_width(text: str) -> float:
    return max(len(text) * _CHAR_W + 2 * _PAD, _MIN_BOX_W)


def _color_for(kind: str) -> str:
    return COLORS.get(kind, COLORS["track"])


class _SvgBuilder:
    """Incrementally builds SVG elements and tracks bounding box."""

    def __init__(self):
        self.elements: List[str] = []
        self.max_x = 0.0
        self.max_y = 0.0

    def _track(self, x, y):
        if x > self.max_x:
            self.max_x = x
        if y > self.max_y:
            self.max_y = y

    def line(self, x1, y1, x2, y2, color=None):
        c = color or COLORS["track"]
        self.elements.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{c}" stroke-width="2"/>'
        )
        self._track(x2, y2)

    def rect(self, x, y, w, h, fill, rx=6):
        self.elements.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{rx}" fill="{fill}"/>'
        )
        self._track(x + w, y + h)

    def text(self, x, y, label, color="#FFFFFF", size=None):
        sz = size or _FONT_SIZE
        escaped = html.escape(label)
        self.elements.append(
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-size="{sz}" '
            f'font-family="monospace, Consolas, Courier New" text-anchor="middle" '
            f'dominant-baseline="central">{escaped}</text>'
        )

    def arrow(self, x, y, direction="right"):
        """Small right-pointing arrowhead at (x, y)."""
        if direction == "right":
            pts = f"{x:.1f},{y - 4:.1f} {x + 8:.1f},{y:.1f} {x:.1f},{y + 4:.1f}"
        else:
            pts = f"{x:.1f},{y - 4:.1f} {x - 8:.1f},{y:.1f} {x:.1f},{y + 4:.1f}"
        self.elements.append(f'<polygon points="{pts}" fill="{COLORS["track"]}"/>')

    def arc(self, x, y, r, start_angle, end_angle, color=None):
        """Quarter-circle arc."""
        import math
        c = color or COLORS["track"]
        x1 = x + r * math.cos(math.radians(start_angle))
        y1 = y + r * math.sin(math.radians(start_angle))
        x2 = x + r * math.cos(math.radians(end_angle))
        y2 = y + r * math.sin(math.radians(end_angle))
        self.elements.append(
            f'<path d="M {x1:.1f} {y1:.1f} A {r} {r} 0 0 1 {x2:.1f} {y2:.1f}" '
            f'fill="none" stroke="{c}" stroke-width="2"/>'
        )
        self._track(max(x1, x2) + r, max(y1, y2) + r)


def _render_node(svg: _SvgBuilder, node: Node, x: float, y: float) -> (float, float):
    """Render *node* at position (x, y). Returns (width, height) consumed."""

    if node.kind in ("literal", "char_class", "anchor"):
        color = _color_for(node.kind)
        w = _text_width(node.label)
        svg.rect(x, y - _BOX_H / 2, w, _BOX_H, color)
        svg.text(x + w / 2, y, node.label, COLORS["text"])
        return w, _BOX_H

    if node.kind == "quantifier":
        # Draw child first, then overlay quantifier badge
        child = node.children[0] if node.children else Node(kind="literal", label="?")
        cw, ch = _render_node(svg, child, x, y)
        badge_w = _text_width(node.label)
        bx = x + cw / 2 - badge_w / 2
        by = y + _BOX_H / 2 + 4
        svg.rect(bx, by, badge_w, 20, COLORS["quantifier"], rx=10)
        svg.text(bx + badge_w / 2, by + 10, node.label, COLORS["text"], size=11)
        return cw, ch + 24

    if node.kind == "group":
        color = COLORS["group"]
        # Render label above
        label_w = _text_width(node.label)
        child = node.children[0] if node.children else Node(kind="literal", label="(empty)")
        # Render inner content with padding
        inner_x = x + _PAD
        inner_y = y
        cw, ch = _render_node(svg, child, inner_x, inner_y)
        total_w = cw + 2 * _PAD
        total_h = ch + 8
        # Draw surrounding rounded rect
        svg.elements.insert(
            0,  # draw behind children
            f'<rect x="{x:.1f}" y="{y - _BOX_H / 2 - 14:.1f}" '
            f'width="{total_w:.1f}" height="{total_h + 14:.1f}" '
            f'rx="8" fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="6,3"/>',
        )
        # Group label
        svg.text(x + total_w / 2, y - _BOX_H / 2 - 4, node.label, color, size=11)
        return total_w, total_h + 14

    if node.kind == "alternation":
        # Stack branches vertically with connecting lines
        branch_results = []
        max_w = 0.0
        for child in node.children:
            tmp = _SvgBuilder()
            w, h = _render_node(tmp, child, 0, 0)
            branch_results.append((tmp, w, h))
            if w > max_w:
                max_w = w

        gap = 12
        left_margin = 20
        right_margin = 20
        total_w = max_w + left_margin + right_margin
        current_y = y - _BOX_H / 2
        total_h = 0
        branch_centers = []

        for tmp, w, h in branch_results:
            cy = current_y + h / 2 + _BOX_H / 2
            branch_centers.append(cy)
            # Offset child elements
            for elem in tmp.elements:
                # Shift by (x + left_margin, current_y + _BOX_H/2) delta
                shifted = _shift_svg(elem, x + left_margin, cy)
                svg.elements.append(shifted)
            # Connecting lines from left junction to branch start
            svg.line(x, cy, x + left_margin, cy)
            # Connecting lines from branch end to right junction
            svg.line(x + left_margin + w, cy, x + total_w, cy)
            current_y += h + gap
            total_h += h + gap

        total_h -= gap  # remove trailing gap

        # Vertical lines on left and right
        if len(branch_centers) > 1:
            svg.line(x, branch_centers[0], x, branch_centers[-1])
            svg.line(x + total_w, branch_centers[0], x + total_w, branch_centers[-1])

        return total_w, total_h + _BOX_H

    if node.kind == "sequence":
        total_w = 0.0
        max_h = _BOX_H
        cx = x
        for i, child in enumerate(node.children):
            if i > 0:
                # Draw connecting line
                svg.line(cx, y, cx + _ARROW, y)
                svg.arrow(cx + _ARROW - 2, y)
                cx += _ARROW
            w, h = _render_node(svg, child, cx, y)
            cx += w
            total_w = cx - x
            if h > max_h:
                max_h = h
        return total_w, max_h

    # Unknown fallback
    w = _text_width(node.kind)
    svg.rect(x, y - _BOX_H / 2, w, _BOX_H, "#999")
    svg.text(x + w / 2, y, node.kind, "#FFF")
    return w, _BOX_H


def _shift_svg(elem: str, dx: float, dy: float) -> str:
    """Wrap an SVG element in a <g transform="translate(...)">."""
    return f'<g transform="translate({dx:.1f},{dy:.1f})">{elem}</g>'


def generate_svg(pattern: str) -> str:
    """Parse *pattern* and return an SVG string."""
    ast = _parse_alternation(pattern)
    svg = _SvgBuilder()

    margin = 40
    start_x = margin
    start_y = 80

    # Start circle
    svg.elements.append(
        f'<circle cx="{start_x - 16:.1f}" cy="{start_y:.1f}" r="6" '
        f'fill="{COLORS["track"]}"/>'
    )
    svg.line(start_x - 10, start_y, start_x, start_y)

    w, h = _render_node(svg, ast, start_x, start_y)

    # End circle (double)
    end_x = start_x + w + 12
    svg.line(start_x + w, start_y, end_x, start_y)
    svg.elements.append(
        f'<circle cx="{end_x + 6:.1f}" cy="{start_y:.1f}" r="6" '
        f'fill="none" stroke="{COLORS["track"]}" stroke-width="2"/>'
    )
    svg.elements.append(
        f'<circle cx="{end_x + 6:.1f}" cy="{start_y:.1f}" r="3" '
        f'fill="{COLORS["track"]}"/>'
    )

    # Title
    escaped_pattern = html.escape(pattern)
    svg.elements.append(
        f'<text x="{margin:.1f}" y="24" fill="#333" font-size="14" '
        f'font-family="monospace">Regex: {escaped_pattern}</text>'
    )

    # Legend
    legend_y = max(start_y + h / 2 + 50, 140)
    legend_items = [
        ("Literal", COLORS["literal"]),
        ("Char Class", COLORS["char_class"]),
        ("Quantifier", COLORS["quantifier"]),
        ("Group", COLORS["group"]),
        ("Anchor", COLORS["anchor"]),
    ]
    lx = margin
    for label, color in legend_items:
        svg.rect(lx, legend_y, 14, 14, color, rx=3)
        svg.elements.append(
            f'<text x="{lx + 20:.1f}" y="{legend_y + 11:.1f}" fill="#333" '
            f'font-size="11" font-family="sans-serif">{label}</text>'
        )
        lx += len(label) * 8 + 40

    total_w = max(svg.max_x + margin, end_x + margin + 20)
    total_h = legend_y + 40

    header = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w:.0f}" height="{total_h:.0f}" '
        f'viewBox="0 0 {total_w:.0f} {total_h:.0f}">\n'
        f'  <rect width="100%" height="100%" fill="{COLORS["bg"]}"/>\n'
    )
    body = "\n  ".join(svg.elements)
    footer = "\n</svg>"
    return header + "  " + body + footer


# ── CLI ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Generate SVG railroad diagram from regex")
    parser.add_argument("pattern", help="Regex pattern string")
    parser.add_argument("-o", "--output", help="Output SVG file (default: stdout)")
    args = parser.parse_args()

    svg = generate_svg(args.pattern)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(svg)


if __name__ == "__main__":
    main()
