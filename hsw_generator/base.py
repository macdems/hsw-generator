#!/usr/bin/env python3
from functools import reduce

import cadquery as cq

SCREW_SIZES = {  # diameter, head diameter (0.1 mm clearance included)
    'M3': (3.3, 5.6),
    'M3.5': (3.8, 6.6),
    'M4': (4.3, 7.6),
}


def make_base(
    rows: int,
    cols: int,
    *,
    screws: str = None,
    alternate: bool = False,
    frame_top: bool = True,
    frame_bottom: bool = True,
    frame_left: bool = False,
    frame_right: bool = False,
    hex_corners: bool = False,
    vertical_stack: bool = False,
) -> cq.Workplane:
    """
    Make a HSW base with holes for mounting.

    Args:
        rows: Number of rows of holes.
        cols: Number of columns of holes.
        screws: Screw size for mounting holes ('M3', 'M3.5', or 'M4').
        alternate:  Alternate the hole pattern along the columns (start with a short column).
        frame_top: Include the top edge in the frame.
        frame_bottom: Include the bottom edge in the frame.
        frame_left: Include the left edge in the frame.
        frame_right: Include the right edge in the frame.
        hex_corners: Make hexagonal corners in the frame.
        stack: Add additional profiles at the top to allow stacking multiple bases vertically.
               Only applies if no top frame is included.
    """

    if frame_top: vertical_stack = False

    h = 2 / 3**0.5

    A = 20.0
    D = 3.6

    P = A + D
    Px = P * h
    Py = P

    profile = cq.Workplane("XY")  \
        .polygon(6, (A + 2.0) * h)  \
        .workplane(offset=2.0) \
        .polygon(6, (A + 2.0) * h)  \
        .workplane(offset=0.9) \
        .polygon(6, A * h)  \
        .workplane(offset=4.6) \
        .polygon(6, A * h)  \
        .workplane(offset=0.5) \
        .polygon(6, (A + 0.8) * h)  \
        .loft(combine=True, ruled=True) \
        .translate((0.5 * Px, 0.5 * Py, 0))

    holes = []
    for col in range(cols):
        dy, nr = (0.0, rows) if (col % 2) == alternate else (0.5 * Py, rows - 1)
        holes.extend(profile.translate((col * 0.75 * Px, row * Py + dy, 0)) for row in range(nr))

    right_screw = (cols + 1 if alternate else cols) // 2 - 1

    edges = []
    frame_hex = cq.Workplane("XY").polygon(6, P * h + 0.01).extrude(8.0) \
        .translate((-0.25 * Px, 0, 0))
    left_hex = frame_hex.translate((0, Py / 2 if alternate else 0, 0))
    left_right_rows = rows + (0 if alternate else 1)
    if not frame_left:  # Left edge
        edges = [left_hex.translate((0, row * P, 0)) for row in range(left_right_rows)]
    else:
        edges = []
    if not frame_right:  # Right edge
        if cols % 2 == 0:
            if alternate:
                dy = -0.5 * Py
                left_right_rows += 1
            else:
                dy = 0.5 * Py
                left_right_rows -= 1
        else:
            dy = 0.0
        right_hex = left_hex.translate(((cols + 1) * 0.75 * Px, dy, 0))
        edges.extend(right_hex.translate((0, row * P, 0)) for row in range(left_right_rows))
    tbs, tbe = (1, right_screw) if screws else (0, right_screw + 1)
    bottom_hex = frame_hex.translate((0.75 * Px if alternate else 1.50 * Px, 0, 0))
    if not frame_bottom:  # Bottom edge
        edges.extend(bottom_hex.translate((i * 1.50 * Px, 0, 0)) for i in range(tbs, tbe))
    if not frame_top:  # Top edge
        top_hex = bottom_hex.translate((0, rows * Py, 0))
        edges.extend(top_hex.translate((i * 1.50 * Px, 0, 0)) for i in range(tbs, tbe))

    if hex_corners:
        if frame_left:
            if frame_bottom:
                edges.append(frame_hex)
            if frame_top:
                edges.append(frame_hex.translate((0, rows * Py, 0)))
        if frame_right:
            if frame_bottom:
                edges.append(frame_hex.translate(((cols + 1) * 0.75 * Px, 0, 0)))
            if frame_top:
                edges.append(frame_hex.translate(((cols + 1) * 0.75 * Px, rows * Py, 0)))

    base = cq.Workplane("XY").box((0.75 * cols + 0.25) * Px, rows * Py, 8.0, centered=(False, False, False))
    base = base.cut(cq.Compound.makeCompound(h.val() for h in holes))

    if edges:
        base = base.cut(reduce(lambda a, b: a.union(b), edges))

    if vertical_stack:
        add = frame_hex.translate(((0.75 if alternate else 1.50) * Px, rows * Py, 0)) \
            .cut(profile.translate(((0 if alternate else 0.75) * Px, (rows - 0.5) * Py, 0)))
        start, end = (1, right_screw) if screws else (0, right_screw + 1)
        add_row = cq.Compound.makeCompound(add.translate((1.50 * i * Px, 0, 0)).val() for i in range(start, end))
        base = base.union(add_row)

    screw = SCREW_SIZES.get(screws)

    if screw is not None:
        left_screw_x = 0.50 * Px if alternate else 1.25 * Px
        right_screw_x = 1.50 * Px * right_screw + left_screw_x
        bottom_screw_y = 0.25 * Py
        top_screw_y = (rows - 0.25) * Py
        base = base.faces(">Z").workplane() \
            .pushPoints([(x, y) for x in (left_screw_x, right_screw_x) for y in (bottom_screw_y, top_screw_y)]) \
            .cskHole(screw[0], screw[1], 90)

    return base
