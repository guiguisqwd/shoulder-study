#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reuse a library chapter figure in a daily pack (standards/daily DL-03).

Library figures draw their hand-drawn wobble with an feTurbulence/feDisplacementMap filter.
The daily figure check rejects displacement filters (seams in Chrome), so the filter is
stripped here; shapes, colours and labels stay as the chapter drew them.
"""
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[3]

__all__ = ["library_svg", "copy_library_figure"]


def library_svg(chapter, name):
    """SVG text of library/<chapter>/figures/<name>.svg without filters."""
    src = REPO / "library" / chapter / "figures" / (name if name.endswith(".svg") else name + ".svg")
    svg = src.read_text(encoding="utf-8")
    svg = re.sub(r"<filter\b.*?</filter>", "", svg, flags=re.S)
    return re.sub(r'\s*filter="url\(#[^)]*\)"', "", svg)


def copy_library_figure(chapter, name, out_dir, out_name):
    """Write the filter-free chapter figure to <out_dir>/<out_name>.svg and return its path."""
    p = pathlib.Path(out_dir) / (out_name if out_name.endswith(".svg") else out_name + ".svg")
    p.write_text(library_svg(chapter, name), encoding="utf-8")
    return p
