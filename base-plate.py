#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentTypeError
from functools import reduce

import cadquery as cq

SCREW_SIZES = {  # diameter, head diameter (0.1 mm clearance included)
    'M3': (3.3, 5.6),
    'M3.5': (3.8, 6.6),
}


def make_plate(
    rows: int,
    cols: int,
    *,
    screws: str = None,
    alternate: bool = False,
    frame_top: bool = True,
    frame_bottom: bool = True,
    frame_left: bool = False,
    frame_right: bool = False,
) -> cq.Workplane:
    """
    Make a HSW base plate with holes for mounting.

    Args:
        rows: Number of rows of holes.
        cols: Number of columns of holes.
        screws: Screw size for mounting holes (e.g. 'M3', 'M3.5').
        alternate:  Alternate the hole pattern along the columns (start with a short column).
        frame_top: Include the top edge in the frame.
        frame_bottom: Include the bottom edge in the frame.
        frame_left: Include the left edge in the frame.
        frame_right: Include the right edge in the frame.
    """

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
        for row in range(nr):
            hole = profile.translate((col * 0.75 * Px, row * Py + dy, 0))
            holes.append(hole)
    holes = cq.Compound.makeCompound([h.val() for h in holes])

    right_screw = (cols + 1 if alternate else cols) // 2 - 1

    remove_frame_hex = cq.Workplane("XY").polygon(6, P * h + 0.01).extrude(8.0) \
        .translate((-0.25 * Px, 0, 0))
    edges = []
    left_hex = remove_frame_hex.translate((0, Py / 2 if alternate else 0, 0))
    left_right_rows = rows + (0 if alternate else 1)
    if not frame_left:  # Left edge
        for row in range(left_right_rows):
            edge = left_hex.translate((0, row * P, 0))
            edges.append(edge)
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
        for row in range(left_right_rows):
            edge = right_hex.translate((0, row * P, 0))
            edges.append(edge)
    tbs, tbe = (1, right_screw) if screws else (0, right_screw + 1)
    bottom_hex = remove_frame_hex.translate((0.75 * Px if alternate else 1.50 * Px, 0, 0))
    if not frame_bottom:  # Bottom edge
        for i in range(tbs, tbe):
            edges.append(bottom_hex.translate((i * 1.50 * Px, 0, 0)))
    if not frame_top:  # Top edge
        top_hex = bottom_hex.translate((0, rows * Py, 0))
        for i in range(tbs, tbe):
            edges.append(top_hex.translate((i * 1.50 * Px, 0, 0)))
    edges = reduce(lambda a, b: a.union(b), edges) if edges else None

    # Plate

    plate = cq.Workplane("XY").box((0.75 * cols + 0.25) * Px, rows * Py, 8.0, centered=(False, False, False))
    plate = plate.cut(holes)
    if edges: plate = plate.cut(edges)

    screw = SCREW_SIZES.get(screws)

    if screw is not None:
        left_screw_x = 0.50 * Px if alternate else 1.25 * Px
        right_screw_x = 1.50 * Px * right_screw + left_screw_x
        bottom_screw_y = 0.25 * Py
        top_screw_y = (rows - 0.25) * Py
        plate = plate.faces(">Z").workplane() \
            .pushPoints([(x, y) for x in (left_screw_x, right_screw_x) for y in (bottom_screw_y, top_screw_y)]) \
            .cskHole(screw[0], screw[1], 90)

    return plate


def main():

    def frame_type(value):
        if value not in ('t', 'b', 'l', 'r', 'v', 'h', 'a', 'top', 'bottom', 'left', 'right', 'vertical', 'horizontal', 'all'):
            raise ArgumentTypeError(f"Invalid choice: {value}. Use t/b/l/r or top/bottom/left/right.")
        return value[0]  # Return the first character for easier processing

    parser = ArgumentParser(description="Generate a HSW base plate")
    parser.add_argument('--rows', '-r', type=int, default=9, help="Number of rows of holes (default: 9)")
    parser.add_argument('--cols', '-c', type=int, default=9, help="Number of columns of holes (default: 9)")
    parser.add_argument('--screws', '-s', choices=list(SCREW_SIZES.keys()), default='', help="Screw size for mounting holes")
    parser.add_argument(
        '--alternate', '-a', action="store_true", help="Alternate the hole pattern along the columns (start with a short column)"
    )
    parser.add_argument(
        '--frame',
        '-f',
        nargs='*',
        type=frame_type,
        metavar='{t,b,l,r,v,h,a|top,bottom,left,right,vertical,horizontal,all}',
        default=(),
        help="Include edges in the frame"
    )
    parser.add_argument('--no-save', action='store_true', help="Don't save the STEP file")
    parser.add_argument(
        "filename",
        nargs="?",
        default=None,
        help="Output STEP filename (default: base-plate-{cols}x{rows}.step)",
    )
    args = parser.parse_args()

    plate = make_plate(
        args.rows,
        args.cols,
        screws=args.screws,
        alternate=args.alternate,
        frame_top=args.frame.count('t') or args.frame.count('v') or args.frame.count('a'),
        frame_bottom=args.frame.count('b') or args.frame.count('v') or args.frame.count('a'),
        frame_left=args.frame.count('l') or args.frame.count('h') or args.frame.count('a'),
        frame_right=args.frame.count('r') or args.frame.count('h') or args.frame.count('a'),
    )

    if not args.no_save:
        if args.filename is not None:
            filename = args.filename
        else:
            filename = f"base-plate-{args.cols}x{args.rows}.step"
        plate.export(filename)

    return plate


if __name__ == "__main__":
    plate = main()

    # Display in VSCode
    try:
        from ocp_vscode import show as show_object
    except ImportError:
        pass
    show_object(plate)
