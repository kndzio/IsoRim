#!/usr/bin/env python3
"""Builds the hand-made 3D models for IsoRim.

Run from anywhere:  python3 tools/make_models.py
Writes Models/*.obj, Models/isorim.mtl and Defs/Models.xml next to this tools folder.

Shapes are described in game axes: X east, Y up, Z north, one unit per map cell, centred on the
thing's footprint and facing north. Files are written as ordinary OBJ (Z flipped), so they open
the right way up in Blender and the mod's loader flips them back.

Every face gets texture coordinates laid flat across it at one texture repeat per cell, so the
swatches in Textures/IsoRim/Swatches keep the same scale on every model.
"""

import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT, "Models")
DEFS_DIR = os.path.join(ROOT, "Defs")

# name -> (colour the texture is multiplied by, texture under Textures/).
# Names starting with "stuff" are also multiplied by the colour of the build material, and
# "{stuff}" becomes Wood, Stone or Metal to match what the thing is built from.
SW = "IsoRim/Swatches/"
MATERIALS = {
    "stuff":        ((1.00, 1.00, 1.00), SW + "{stuff}"),
    "stuff_dark":   ((0.80, 0.80, 0.80), SW + "{stuff}"),
    "stuff_deep":   ((0.62, 0.62, 0.62), SW + "{stuff}"),
    "linen":        ((0.90, 0.88, 0.82), SW + "Fabric"),
    "pillow":       ((0.98, 0.97, 0.94), SW + "Fabric"),
    "blanket":      ((0.44, 0.52, 0.64), SW + "Fabric"),
    "cushion":      ((0.62, 0.34, 0.30), SW + "Fabric"),
    "metal":        ((0.60, 0.62, 0.65), SW + "Metal"),
    "metal_dark":   ((0.32, 0.33, 0.36), SW + "Metal"),
    "glow":         ((1.00, 1.00, 1.00), SW + "Glow"),
    "flame":        ((1.00, 0.90, 0.48), SW + "Flame"),   # the swatch is painted to be multiplied by this
    "flame_core":   ((1.00, 0.95, 0.72), SW + "Glow"),
    "log":          ((0.50, 0.34, 0.21), SW + "Wood"),
    "stone":        ((0.54, 0.54, 0.55), SW + "Stone"),
    "soil":         ((1.00, 1.00, 1.00), SW + "Soil"),
    "solar":        ((1.00, 1.00, 1.00), SW + "Solar"),
    "solar_frame":  ((0.70, 0.72, 0.75), SW + "Metal"),
    "stuff_bag":    ((0.95, 0.92, 0.84), SW + "Fabric"),
    "stuff_bag_dark": ((0.70, 0.67, 0.60), SW + "Fabric"),
    "pit":          ((0.10, 0.08, 0.07), None),
    "solar_line":   ((0.68, 0.70, 0.74), SW + "Metal"),
    "battery":      ((0.38, 0.42, 0.46), SW + "Metal"),
    "terminal":     ((0.92, 0.80, 0.24), SW + "Metal"),
    "ember":        ((0.96, 0.42, 0.18), SW + "Glow"),
    "ash":          ((0.30, 0.28, 0.27), None),
    "log_burnt":    ((0.20, 0.16, 0.14), SW + "Wood"),
    "stuff_plain":  ((1.00, 1.00, 1.00), None),      # takes whatever colour the mod gives it: smoke, skin, cloth, hair
    "stuff_plain_dark": ((0.80, 0.80, 0.80), None),
    "visor":        ((0.14, 0.19, 0.24), None),
    "visor_lit":    ((0.30, 0.62, 0.70), None),      # the faint glow behind a sealed helmet's eye slit
    "stuff_plain_deep": ((0.60, 0.60, 0.60), None),
    "stuff_plain_light": ((1.12, 1.12, 1.12), None),
    "geyser_rock":  ((0.44, 0.42, 0.40), SW + "Rock"),
    "geyser_crust": ((0.84, 0.80, 0.62), SW + "Rock"),
    "water_dark":   ((0.20, 0.34, 0.40), None),
    "blood":        ((0.52, 0.12, 0.10), None),
    "paper":        ((0.92, 0.90, 0.82), None),
    "book_red":     ((0.62, 0.22, 0.18), None),
    "book_blue":    ((0.22, 0.36, 0.58), None),
    "cloth_roll":   ((0.72, 0.56, 0.34), SW + "Fabric"),
    # rocks: takes the colour of the stone
    "stuff_rock":   ((1.00, 1.00, 1.00), SW + "Rock"),
    "slag":         ((0.40, 0.38, 0.36), SW + "Rock"),
    "slag_metal":   ((0.52, 0.47, 0.42), SW + "Metal"),
    # weapons
    "gun_metal":    ((0.36, 0.37, 0.40), SW + "Metal"),
    "gun_dark":     ((0.20, 0.20, 0.22), SW + "Metal"),
    "gun_light":    ((0.66, 0.68, 0.70), SW + "Metal"),
    "gun_white":    ((0.84, 0.86, 0.88), SW + "Metal"),
    "gun_olive":    ((0.36, 0.40, 0.28), SW + "Metal"),
    "gun_wood":     ((0.50, 0.34, 0.21), SW + "Wood"),
    "grip":         ((0.30, 0.22, 0.16), SW + "Fabric"),
    "string":       ((0.86, 0.82, 0.72), SW + "Fabric"),
    "charge":       ((0.45, 0.90, 1.00), SW + "Glow"),
    "warning":      ((0.86, 0.30, 0.20), SW + "Metal"),
    # clothing: takes the colour of the cloth or leather it is made from
    "stuff_fabric": ((0.92, 0.92, 0.92), SW + "Fabric"),
    "stuff_fabric_dark": ((0.72, 0.72, 0.72), SW + "Fabric"),
    "armor":        ((0.74, 0.76, 0.74), SW + "Metal"),
    "armor_dark":   ((0.46, 0.48, 0.46), SW + "Metal"),
    "strap":        ((0.34, 0.26, 0.18), SW + "Fabric"),
    # trees: names starting with "leaf" are left out while a tree is bare
    "bark":         ((0.44, 0.31, 0.21), SW + "Bark"),
    "bark_pale":    ((0.84, 0.82, 0.76), SW + "Bark"),
    "leaf_oak":     ((0.38, 0.54, 0.25), SW + "Leaf"),
    "leaf_poplar":  ((0.44, 0.60, 0.27), SW + "Leaf"),
    "leaf_birch":   ((0.52, 0.64, 0.30), SW + "Leaf"),
    "leaf_pine":    ((0.23, 0.41, 0.25), SW + "Leaf"),
    "leaf_willow":  ((0.42, 0.57, 0.31), SW + "Leaf"),
    "leaf_maple":   ((0.80, 0.43, 0.19), SW + "Leaf"),
    "leaf_cypress": ((0.25, 0.43, 0.27), SW + "Leaf"),
    "leaf_teak":    ((0.31, 0.51, 0.23), SW + "Leaf"),
    "leaf_jungle":  ((0.34, 0.57, 0.27), SW + "Leaf"),
    "leaf_bamboo":  ((0.48, 0.64, 0.31), SW + "Leaf"),
    "leaf_drago":   ((0.29, 0.45, 0.27), SW + "Leaf"),
    "leaf_anima":   ((0.94, 0.88, 0.92), SW + "Leaf"),
    "leaf_gauranlen": ((0.82, 0.88, 0.62), SW + "Leaf"),
    "cactus":       ((0.38, 0.54, 0.32), SW + "Leaf"),
    "bamboo":       ((0.62, 0.70, 0.36), SW + "Bark"),
    # grass, flowers and crops: plain colours, no texture, so that thousands of them stay cheap
    "blade_a":      ((0.45, 0.58, 0.31), None),     # a little less saturated than before, to sit with the ground
    "blade_b":      ((0.36, 0.48, 0.27), None),
    "blade_c":      ((0.52, 0.64, 0.37), None),
    "hay_a":        ((0.66, 0.68, 0.32), None),
    "hay_b":        ((0.56, 0.60, 0.28), None),
    "rice_a":       ((0.54, 0.70, 0.33), None),
    "stem":         ((0.36, 0.50, 0.24), None),
    "moss":         ((0.29, 0.43, 0.23), None),
    "agave":        ((0.29, 0.54, 0.52), None),
    "petal_yellow": ((0.97, 0.82, 0.24), None),
    "petal_pink":   ((0.88, 0.52, 0.74), None),
    "petal_orange": ((0.96, 0.57, 0.21), None),
    "petal_red":    ((0.86, 0.23, 0.25), None),
    "petal_white":  ((0.96, 0.96, 0.91), None),
    "berry":        ((0.33, 0.43, 0.82), None),
    "fruit_red":    ((0.86, 0.20, 0.20), None),
    "corn":         ((0.96, 0.84, 0.32), None),
    "cotton":       ((0.97, 0.97, 0.95), None),
    "cap_red":      ((0.72, 0.21, 0.19), None),
    "cap_glow":     ((0.56, 0.90, 0.74), None),
    "shrub":        ((0.42, 0.53, 0.25), SW + "Leaf"),
    "shrub_dark":   ((0.31, 0.44, 0.22), SW + "Leaf"),
    "bramble":      ((0.42, 0.37, 0.22), SW + "Leaf"),
    "crop_leaf":    ((0.36, 0.53, 0.25), SW + "Leaf"),
    "crop_pale":    ((0.50, 0.62, 0.38), SW + "Leaf"),
    # any plant the mod has no model for: takes the average colour of the plant's own sprite
    "stuff_herb":      ((1.00, 1.00, 1.00), None),
    "stuff_herb_dark": ((0.78, 0.78, 0.78), None),
}


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def add3(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def mul3(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def unit(a):
    n = math.sqrt(dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-9 else (0.0, 0.0, 0.0)


def along(start, direction, distance):
    return add3(start, mul3(direction, distance))


class Shape:
    """A list of flat faces. Each face is (material, [points], [texture coordinates])."""

    def __init__(self):
        self.faces = []

    def face(self, mat, pts, centre, uvs=None):
        """Adds a face, turning it round if it would face the middle of its solid."""
        n = cross(sub(pts[1], pts[0]), sub(pts[2], pts[0]))
        if uvs is None:
            # Lay the texture flat across the face: seen from above for tops, from the side for sides.
            ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2])
            if ay >= ax and ay >= az:
                uvs = [(p[0], p[2]) for p in pts]
            elif az >= ax:
                uvs = [(p[0], p[1]) for p in pts]
            else:
                uvs = [(p[2], p[1]) for p in pts]
        mid = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
        if dot(n, sub(mid, centre)) < 0:
            pts = list(reversed(pts))
            uvs = list(reversed(uvs))
        self.faces.append((mat, list(pts), list(uvs)))

    def box(self, x0, y0, z0, x1, y1, z1, mat, top=None):
        """Axis-aligned block. No underside: nothing in the game looks up from below."""
        c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        self.face(top or mat, [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], c)
        self.face(mat, [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)], c)
        self.face(mat, [(x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (x0, y0, z1)], c)
        self.face(mat, [(x0, y0, z1), (x0, y1, z1), (x0, y1, z0), (x0, y0, z0)], c)
        self.face(mat, [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], c)

    def prism(self, cx, cz, r0, r1, y0, y1, sides, mat, top=None, turn=0.0, fit=False):
        """Upright cylinder, taper or cone (r1 = 0) with the given number of sides.
        fit=True stretches the texture once from the bottom to the top, for flames."""
        c = (cx, (y0 + y1) / 2, cz)

        def ring(r, y):
            return [(cx + r * math.cos(turn + 2 * math.pi * i / sides), y,
                     cz + r * math.sin(turn + 2 * math.pi * i / sides)) for i in range(sides)]

        def wrap(i, y):
            # Texture runs round the outside so side faces join up.
            if fit:
                return (i / sides, 0.02 + 0.96 * (y - y0) / (y1 - y0))
            return (i * 2 * math.pi * max(r0, r1) / sides, y)

        lo = ring(r0, y0)
        if r1 <= 0:
            tip = (cx, y1, cz)
            for i in range(sides):
                self.face(mat, [lo[i], lo[(i + 1) % sides], tip], c,
                          uvs=[wrap(i, y0), wrap(i + 1, y0), wrap(i + 0.5, y1)])
            return
        hi = ring(r1, y1)
        for i in range(sides):
            j = (i + 1) % sides
            self.face(mat, [lo[i], hi[i], hi[j], lo[j]], c,
                      uvs=[wrap(i, y0), wrap(i, y1), wrap(i + 1, y1), wrap(i + 1, y0)])
        self.face(top or mat, hi, (cx, y0, cz))

    def lump(self, cx, cy, cz, rx, ry, rz, mat, rng, sides=6, profile=((0.0, 0.95), (0.38, 1.0), (0.76, 0.66)),
             jitter=0.14, closed=False):
        """A faceted, uneven rounded mass: boulders, tree crowns, helmets.
        profile lists rings from the bottom up as (height fraction, radius fraction);
        closed=True adds an underside, for masses that do not sit on the ground."""
        centre = (cx, cy + ry * 0.45, cz)
        turn = rng.uniform(0, 2 * math.pi / sides)
        rings = []
        for k, (hf, rf) in enumerate(profile):
            ring = []
            for i in range(sides):
                a = turn + 2 * math.pi * (i + rng.uniform(-0.18, 0.18)) / sides
                r = rf * (1 + rng.uniform(-jitter, jitter))
                y = cy + ry * hf * (1 + rng.uniform(-jitter, jitter) * 0.4) if hf > 0 else cy
                ring.append((cx + rx * r * math.cos(a), y, cz + rz * r * math.sin(a)))
            rings.append(ring)
        for lower, upper in zip(rings, rings[1:]):
            for i in range(sides):
                j = (i + 1) % sides
                self.face(mat, [lower[i], upper[i], upper[j]], centre)
                self.face(mat, [lower[i], upper[j], lower[j]], centre)
        tip = (cx + rx * rng.uniform(-0.15, 0.15), cy + ry, cz + rz * rng.uniform(-0.15, 0.15))
        last = rings[-1]
        for i in range(sides):
            self.face(mat, [last[i], tip, last[(i + 1) % sides]], centre)
        if closed:
            under = (cx, cy - ry * 0.12, cz)
            first = rings[0]
            for i in range(sides):
                self.face(mat, [first[i], first[(i + 1) % sides], under], centre)

    def loft(self, stations, sides, mat, under=None, mats=None, cap_start=True, cap_end=True, power=2.0):
        """A tube through a row of stations, each (centre point, half width, half height).
        The cross-section is a flat-topped polygon set square to the way the tube is heading,
        so this makes bodies, necks, heads and tails. A half width of 0 closes to a point.
        under: material for the faces along the underside (a pale belly).
        mats: one material per stretch between stations, in place of mat.
        power: 2 for a round or oval cross-section; higher values square it off (4 is a pillow)."""
        n = len(stations)
        rings, centres = [], []
        for i, (c, hw, hh) in enumerate(stations):
            a, b = stations[max(0, i - 1)][0], stations[min(n - 1, i + 1)][0]
            t = unit(sub(b, a))
            side = cross((0.0, 1.0, 0.0), t)
            side = unit(side) if dot(side, side) > 1e-6 else (1.0, 0.0, 0.0)
            up = unit(cross(t, side))
            ring = []
            for k in range(sides):
                ang = 2 * math.pi * (k + 0.5) / sides
                ca, sa = math.cos(ang), math.sin(ang)
                if power != 2.0:
                    ca = math.copysign(abs(ca) ** (2.0 / power), ca)
                    sa = math.copysign(abs(sa) ** (2.0 / power), sa)
                ring.append(add3(c, add3(mul3(side, hw * ca), mul3(up, hh * sa))))
            rings.append(ring if hw > 1e-6 else None)
            centres.append(c)
        for i in range(n - 1):
            lo, hi = rings[i], rings[i + 1]
            mid = mul3(add3(centres[i], centres[i + 1]), 0.5)
            base = mats[i] if mats else mat
            for k in range(sides):
                j = (k + 1) % sides
                m = under if under and math.sin(2 * math.pi * (k + 1.0) / sides) < -0.6 else base
                if lo is None and hi is None:
                    continue
                if lo is None:
                    self.face(m, [centres[i], hi[k], hi[j]], mid)
                elif hi is None:
                    self.face(m, [lo[k], centres[i + 1], lo[j]], mid)
                else:
                    self.face(m, [lo[k], hi[k], hi[j]], mid)
                    self.face(m, [lo[k], hi[j], lo[j]], mid)
        if cap_start and rings[0] is not None:
            self.face(mats[0] if mats else mat, rings[0], centres[1])
        if cap_end and rings[-1] is not None:
            self.face(mats[-1] if mats else mat, rings[-1], centres[-2])

    def limb(self, start, end, r0, r1, sides, mat):
        """A straight tapering rod between two points: horns, ears, thin tails, legs. r1 = 0 ends in a point."""
        self.loft([(start, r0, r0), (end, r1, r1)], sides, mat)

    def merge(self, other, move=(0.0, 0.0, 0.0), spin_z=0.0):
        """Adds another shape, turned about the north-south axis by spin_z (radians) and then moved."""
        c, k = math.cos(spin_z), math.sin(spin_z)
        for mat, pts, uvs in other.faces:
            self.faces.append((mat, [(x * c - y * k + move[0], x * k + y * c + move[1], z + move[2]) for x, y, z in pts], list(uvs)))

    def wedge(self, x0, z0, x1, z1, y_south, y_north, thick, mat, top=None):
        """A sloping slab: its top runs from y_south at the south edge to y_north at the north edge."""
        ys, yn = y_south, y_north
        c = ((x0 + x1) / 2, (ys + yn) / 2 - thick / 2, (z0 + z1) / 2)
        self.face(top or mat, [(x0, ys, z0), (x0, yn, z1), (x1, yn, z1), (x1, ys, z0)], c)
        self.face(mat, [(x0, ys - thick, z0), (x0, ys, z0), (x1, ys, z0), (x1, ys - thick, z0)], c)
        self.face(mat, [(x1, yn - thick, z1), (x1, yn, z1), (x0, yn, z1), (x0, yn - thick, z1)], c)
        self.face(mat, [(x0, yn - thick, z1), (x0, yn, z1), (x0, ys, z0), (x0, ys - thick, z0)], c)
        self.face(mat, [(x1, ys - thick, z0), (x1, ys, z0), (x1, yn, z1), (x1, yn - thick, z1)], c)

    def legs(self, x0, z0, x1, z1, height, size, mat):
        """Four square legs just inside the given rectangle."""
        for lx in (x0, x1 - size):
            for lz in (z0, z1 - size):
                self.box(lx, 0, lz, lx + size, height, lz + size, mat)

    def separate(self, step=0.003):
        """Faces of different materials that lie in the same plane and overlap would fight over
        which shows, flickering as the camera moves. Each later material in such a plane is
        lifted a hair off it, along the face."""
        planes = {}
        for k, (mat, pts, uvs) in enumerate(self.faces):
            n = cross(sub(pts[1], pts[0]), sub(pts[2], pts[0]))
            ln = math.sqrt(dot(n, n))
            if ln < 1e-12:
                continue
            n = mul3(n, 1.0 / ln)
            key = (round(n[0], 3), round(n[1], 3), round(n[2], 3), round(dot(n, pts[0]), 3))
            planes.setdefault(key, []).append(k)
        for key, ks in planes.items():
            order = []
            for k in ks:
                if self.faces[k][0] not in order:
                    order.append(self.faces[k][0])
            if len(order) < 2:
                continue
            n = key[:3]
            for k in ks:
                mat, pts, uvs = self.faces[k]
                rank = order.index(mat)
                if rank:
                    lift = mul3(n, step * rank)
                    self.faces[k] = (mat, [add3(p, lift) for p in pts], uvs)

    def write(self, name):
        self.separate()
        path = os.path.join(MODELS_DIR, name + ".obj")
        with open(path, "w", newline="\n") as f:
            f.write("# IsoRim model: %s\n" % name)
            f.write("# Generated by tools/make_models.py. One unit = one map cell, +Y up, -Z = north.\n")
            f.write("mtllib isorim.mtl\n")
            f.write("o %s\n" % name)
            index = 1
            current = None
            for mat, pts, uvs in self.faces:
                if mat != current:
                    f.write("usemtl %s\n" % mat)
                    current = mat
                for x, y, z in pts:
                    f.write("v %.4f %.4f %.4f\n" % (x, y, -z))
                for u, v in uvs:
                    f.write("vt %.4f %.4f\n" % (u, v))
                f.write("f " + " ".join("%d/%d" % (index + i, index + i) for i in range(len(pts))) + "\n")
                index += len(pts)
        return path


# ---------------------------------------------------------------------------- models

def bed(width):
    """1 or 2 cells wide, 2 long, pillow end to the north."""
    s = Shape()
    w = width / 2 - 0.05
    s.legs(-w, -0.95, w, 0.95, 0.10, 0.10, "stuff_deep")
    s.box(-w, 0.08, -0.95, w, 0.26, 0.92, "stuff_dark", top="stuff")                # frame
    s.box(-w + 0.04, 0.26, -0.90, w - 0.04, 0.37, 0.88, "linen")                    # mattress
    s.box(-w + 0.02, 0.37, -0.90, w - 0.02, 0.42, 0.30, "blanket")                  # blanket
    s.box(-w + 0.02, 0.42, 0.22, w - 0.02, 0.445, 0.30, "linen")                    # turned-down sheet
    s.box(-w - 0.008, 0.08, 0.90, w + 0.008, 0.72, 0.97, "stuff_dark", top="stuff")  # headboard (a hair wider than the frame)
    s.box(-w - 0.008, 0.08, -0.97, w + 0.008, 0.36, -0.92, "stuff_dark", top="stuff")  # footboard
    if width == 1:
        s.box(-0.30, 0.37, 0.46, 0.30, 0.47, 0.84, "pillow")
    else:
        s.box(-0.82, 0.37, 0.46, -0.14, 0.47, 0.84, "pillow")
        s.box(0.14, 0.37, 0.46, 0.82, 0.47, 0.84, "pillow")
    return s


def table(size_x, size_z):
    s = Shape()
    x, z = size_x / 2 - 0.06, size_z / 2 - 0.06
    s.box(-x, 0.60, -z, x, 0.68, z, "stuff_dark", top="stuff")                      # top
    s.box(-x + 0.08, 0.50, -z + 0.08, x - 0.08, 0.60, z - 0.08, "stuff_deep")       # apron under the top
    s.legs(-x + 0.05, -z + 0.05, x - 0.05, z - 0.05, 0.60, 0.11, "stuff_dark")
    return s


def stool():
    s = Shape()
    s.prism(0, 0, 0.20, 0.16, 0, 0.36, 8, "stuff_deep")
    s.prism(0, 0, 0.30, 0.30, 0.36, 0.44, 10, "stuff_dark", top="stuff")
    return s


def chair(half, seat_y, back_y, arms):
    """The sitter faces north, so the backrest is on the south side."""
    s = Shape()
    s.legs(-half, -half, half, half, seat_y, 0.08, "stuff_deep")
    s.box(-half, seat_y, -half, half, seat_y + 0.08, half, "stuff_dark", top="stuff")
    s.box(-half, seat_y + 0.08, -half, half, back_y, -half + 0.08, "stuff_dark", top="stuff")
    if arms:
        s.box(-half + 0.09, seat_y + 0.08, -half + 0.08, half - 0.09, seat_y + 0.14, half - 0.03, "cushion")
        for x0 in (-half, half - 0.09):
            s.box(x0, seat_y + 0.08, -half + 0.08, x0 + 0.09, seat_y + 0.30, half, "stuff_dark", top="stuff")
    return s


def torch_lamp():
    s = Shape()
    s.box(-0.05, 0, -0.05, 0.05, 0.95, 0.05, "log")
    s.prism(0, 0, 0.11, 0.13, 0.86, 0.98, 6, "metal_dark")
    s.prism(0, 0, 0.12, 0, 0.98, 1.36, 6, "flame", fit=True)
    s.prism(0, 0, 0.06, 0, 0.98, 1.20, 5, "flame_core", turn=0.5)
    return s


def standing_lamp():
    s = Shape()
    s.prism(0, 0, 0.22, 0.18, 0, 0.07, 10, "metal_dark")
    s.prism(0, 0, 0.04, 0.04, 0.07, 1.10, 6, "metal")
    s.prism(0, 0, 0.14, 0.20, 1.10, 1.38, 10, "glow")
    return s


def campfire():
    s = Shape()
    for i in range(8):                                                # ring of stones
        a = 2 * math.pi * i / 8
        cx, cz = 0.36 * math.cos(a), 0.36 * math.sin(a)
        s.prism(cx, cz, 0.11, 0.08, 0, 0.13, 5, "stone", turn=a)
    s.prism(0, 0, 0.27, 0.22, 0, 0.05, 8, "ash")                       # bed of ash and embers
    s.prism(0, 0, 0.15, 0.10, 0.05, 0.09, 6, "ember")
    for i in range(4):                                                # logs leaning together in a cone
        a = 2 * math.pi * i / 4 + 0.4
        s.limb((0.27 * math.cos(a), 0.03, 0.27 * math.sin(a)), (-0.04 * math.cos(a), 0.34, -0.04 * math.sin(a)), 0.055, 0.045, 5, "log")
    s.limb((-0.30, 0.05, 0.10), (0.28, 0.07, -0.06), 0.05, 0.05, 5, "log_burnt")
    return s          # the flames and smoke are drawn moving by the mod (see the fx models)


def end_table():
    s = Shape()
    s.box(-0.36, 0, -0.36, 0.36, 0.46, 0.36, "stuff_dark")
    s.box(-0.40, 0.46, -0.40, 0.40, 0.52, 0.40, "stuff_dark", top="stuff")
    s.box(-0.26, 0.20, -0.38, 0.26, 0.38, -0.36, "stuff_deep")       # drawer front
    s.box(-0.04, 0.27, -0.395, 0.04, 0.31, -0.38, "metal_dark")      # handle
    return s


def dresser():
    """2 cells wide, 1 deep, drawers facing south."""
    s = Shape()
    s.box(-0.90, 0, -0.34, 0.90, 0.78, 0.34, "stuff_dark")
    s.box(-0.94, 0.78, -0.38, 0.94, 0.84, 0.38, "stuff_dark", top="stuff")
    for y in (0.10, 0.44):
        for x0 in (-0.82, 0.06):
            s.box(x0, y, -0.36, x0 + 0.76, y + 0.26, -0.34, "stuff_deep")
            s.box(x0 + 0.33, y + 0.11, -0.375, x0 + 0.43, y + 0.15, -0.36, "metal_dark")
    return s


def plant_pot():
    s = Shape()
    s.prism(0, 0, 0.26, 0.36, 0, 0.40, 10, "stuff_dark", top="soil")
    s.prism(0, 0, 0.38, 0.38, 0.36, 0.42, 10, "stuff", top="soil")
    return s


def battery():
    """1 cell wide, 2 long."""
    s = Shape()
    s.box(-0.40, 0, -0.90, 0.40, 0.55, 0.90, "battery")
    s.box(-0.42, 0.55, -0.92, 0.42, 0.60, 0.92, "metal_dark")
    for z in (-0.50, 0.50):
        s.prism(0, z, 0.12, 0.12, 0.60, 0.74, 8, "terminal")
    return s


def heater():
    s = Shape()
    s.box(-0.32, 0, -0.20, 0.32, 0.58, 0.20, "metal_dark", top="metal")
    for y in (0.12, 0.26, 0.40):
        s.box(-0.24, y, -0.22, 0.24, y + 0.07, -0.20, "ember")
    return s


def solar_generator():
    """4 x 4 cells: six separate panels in a frame, tilted up toward the north on a braced stand.
    The middle pair reaches further than the outer pairs, so the array is not a plain square."""
    s = Shape()

    def top_at(z):
        return 0.42 + (z + 1.8) / 3.6 * 0.72

    for x0, x1, z0, z1 in ((-1.78, -0.66, -1.42, 1.42), (-0.56, 0.56, -1.80, 1.80), (0.66, 1.78, -1.42, 1.42)):
        mid = (z0 + z1) / 2
        for a, b in ((z0, mid - 0.05), (mid + 0.05, z1)):
            s.wedge(x0, a, x1, b, top_at(a), top_at(b), 0.07, "solar_frame", top="solar")
            for fx0, fx1 in ((x0, x0 + 0.05), (x1 - 0.05, x1)):                     # raised frame edges
                s.wedge(fx0, a, fx1, b, top_at(a) + 0.015, top_at(b) + 0.015, 0.03, "solar_frame")
            s.wedge(x0, a, x1, a + 0.05, top_at(a) + 0.015, top_at(a + 0.05) + 0.015, 0.03, "solar_frame")
            s.wedge(x0, b - 0.05, x1, b, top_at(b - 0.05) + 0.015, top_at(b) + 0.015, 0.03, "solar_frame")
    for x in (-1.22, 0.0, 1.22):                                                   # rails under the panels
        z0, z1 = (-1.80, 1.80) if x == 0.0 else (-1.42, 1.42)
        s.wedge(x - 0.06, z0, x + 0.06, z1, top_at(z0) - 0.07, top_at(z1) - 0.07, 0.08, "metal_dark")
    for x in (-1.22, 1.22):                                                        # the stand: short legs in front, tall ones behind, braced
        s.box(x - 0.07, 0, -1.30, x + 0.07, top_at(-1.30) - 0.14, -1.16, "metal_dark")
        s.box(x - 0.07, 0, 1.16, x + 0.07, top_at(1.16) - 0.14, 1.30, "metal_dark")
        s.limb((x, 0.06, 1.23), (x, top_at(0.0) - 0.16, 0.0), 0.04, 0.04, 4, "metal")
        s.box(x - 0.16, 0, -1.40, x + 0.16, 0.05, -1.06, "stone")
        s.box(x - 0.16, 0, 1.06, x + 0.16, 0.05, 1.40, "stone")
    s.limb((-1.22, 0.55, 1.23), (1.22, 0.55, 1.23), 0.035, 0.035, 4, "metal")      # cross bar
    s.box(-0.26, 0, 0.72, 0.26, 0.46, 1.08, "battery", top="metal_dark")           # the inverter box under the high side
    s.box(-0.20, 0.30, 0.70, -0.06, 0.38, 0.72, "terminal")
    s.box(0.06, 0.12, 0.70, 0.20, 0.38, 0.72, "metal_dark")
    return s


def wind_turbine():
    """5 x 2 cells: a concrete pad, a tapering mast and the housing the blades are fixed to.
    The blades are a separate model (wind_rotor) that the game turns."""
    s = Shape()
    s.box(-1.30, 0, -0.80, 1.30, 0.10, 0.80, "stone")
    s.box(-0.62, 0.10, -0.62, 0.62, 0.22, 0.62, "stone")
    s.prism(0, 0, 0.30, 0.26, 0.22, 0.42, 10, "metal_dark")
    s.prism(0, 0, 0.23, 0.13, 0.42, 2.62, 10, "gun_white")
    for y in (1.10, 1.85):                                                          # seams where the mast sections join
        r = 0.23 - 0.10 * (y - 0.42) / 2.20
        s.prism(0, 0, r + 0.012, r + 0.012, y, y + 0.035, 10, "metal")
    s.box(-0.045, 0.30, -0.27, 0.045, 0.80, -0.22, "metal_dark")                    # the door
    s.box(-0.22, 2.56, -0.56, 0.22, 2.94, 0.62, "gun_white", top="gun_light")       # the housing
    s.box(-0.24, 2.60, 0.20, 0.24, 2.80, 0.50, "metal_dark")                        # vents
    s.box(-0.03, 2.94, 0.30, 0.03, 3.14, 0.36, "metal")                             # mast light
    s.box(-0.04, 3.14, 0.29, 0.04, 3.19, 0.37, "warning")
    return s


def wind_rotor():
    """Hub and three blades, built round the origin in the upright plane that faces north-south."""
    s = Shape()
    s.loft([((0, 0, 0.10), 0.20, 0.20), ((0, 0, -0.10), 0.19, 0.19), ((0, 0, -0.26), 0.11, 0.11), ((0, 0, -0.34), 0.0, 0.0)], 8, "gun_white")
    blade = Shape()
    blade.loft([((0, 0.10, -0.05), 0.07, 0.05), ((0, 0.45, -0.05), 0.17, 0.035), ((0, 1.30, -0.05), 0.11, 0.025),
                ((0, 2.02, -0.05), 0.04, 0.015)], 4, "gun_white")      # kept dead straight so the flat of the blade faces the wind
    blade.box(-0.045, 1.86, -0.07, 0.045, 2.00, -0.03, "warning")                   # red tip band
    for k in range(3):
        s.merge(blade, spin_z=2 * math.pi * k / 3)
    return s


def sandbags(seed):
    """One cell of a sandbag wall, running east-west: four courses of heavy, squared-off bags laid
    like bricks, each course half a bag along from the one below so neighbouring cells lock
    together. The bags are flattened by the weight on them, fat in the middle and pinched at the
    tied ends, and the wall steps in a little as it rises."""
    rng = random.Random(seed)
    s = Shape()

    def bag(x, y, z, length, depth, height, lean=0.0):
        """A filled sack lying along x, its underside at y."""
        hl, hd, hh = length / 2, depth / 2, height / 2
        c = y + hh
        sag = rng.uniform(0.004, 0.012)
        stations = [((x - hl, c - hh * 0.15, z), hd * 0.66, hh * 0.55),
                    ((x - hl + 0.05, c, z), hd * 0.95, hh * 0.94),
                    ((x - hl * 0.35, c, z + lean), hd * 1.0, hh * 1.0),
                    ((x + hl * 0.35, c - sag, z + lean), hd * 1.02, hh * 0.96),
                    ((x + hl - 0.05, c, z), hd * 0.95, hh * 0.94),
                    ((x + hl, c - hh * 0.15, z), hd * 0.66, hh * 0.55)]
        s.loft(stations, 8, "stuff_bag", power=3.6)
        # the tied neck at one end, folded down
        end = rng.choice((-1, 1))
        tip = (x + end * hl, c - hh * 0.2, z)
        s.limb(tip, add3(tip, (end * 0.04, -hh * 0.35, 0.0)), 0.034, 0.022, 5, "stuff_bag_dark")
        # a seam round the middle and stitching across the top
        s.box(x - 0.006, c + hh * 0.86, z - hd * 0.8, x + 0.006, c + hh * 1.0 + 0.004, z + hd * 0.8, "stuff_bag_dark")

    courses = ((0.00, 0.40, 0.140), (0.135, 0.37, 0.135), (0.265, 0.34, 0.13), (0.39, 0.31, 0.125))
    for k, (y, depth, height) in enumerate(courses):
        off = 0.25 if k % 2 else 0.0
        for cx in (-0.25 + off, 0.25 + off):
            length = 0.50 + rng.uniform(-0.015, 0.01)
            z = rng.uniform(-0.02, 0.02)
            bag(cx + rng.uniform(-0.01, 0.01), y, z, length, depth + rng.uniform(-0.01, 0.01), height, lean=rng.uniform(-0.015, 0.015))
    return s


def grave(full):
    """1 x 2 cells. Empty: a dark pit edged with thrown-up earth. Filled: a mound of earth with a headstone."""
    rng = random.Random(7 if full else 8)
    s = Shape()
    if full:
        s.lump(0, 0, -0.08, 0.36, 0.24, 0.78, "soil", rng, sides=10, profile=((0.0, 1.0), (0.40, 0.86), (0.78, 0.50)), jitter=0.07)
        for _ in range(5):                                                          # loose clods and stones round the edge
            a = rng.uniform(0, 6.28)
            s.lump(0.38 * math.cos(a), 0, -0.08 + 0.80 * math.sin(a), 0.07, 0.07, 0.07, rng.choice(("soil", "stone")), rng, sides=5, jitter=0.2)
        s.box(-0.24, 0, 0.78, 0.24, 0.10, 0.94, "stone")                            # headstone, on a plinth
        s.box(-0.19, 0.10, 0.82, 0.19, 0.50, 0.91, "stone")
        s.prism(0, 0.865, 0.19, 0.11, 0.50, 0.60, 4, "stone", turn=math.pi / 4)
        s.box(-0.02, 0.22, 0.815, 0.02, 0.44, 0.822, "metal_dark")                  # a cross cut into its face
        s.box(-0.08, 0.34, 0.815, 0.08, 0.38, 0.822, "metal_dark")
    else:
        s.box(-0.30, 0, -0.80, 0.30, 0.012, 0.80, "pit")
        for x0, z0, x1, z1 in ((-0.42, -0.92, 0.42, -0.80), (-0.42, 0.80, 0.42, 0.92), (-0.42, -0.80, -0.30, 0.80), (0.30, -0.80, 0.42, 0.80)):
            s.box(x0, 0, z0, x1, 0.07, z1, "soil")
        for x, z, r in ((0.52, -0.30, 0.20), (0.56, 0.24, 0.24), (-0.50, 0.55, 0.15)):   # the earth that came out of it
            s.lump(x * 0.92, 0, z, r, r * 0.9, r * 1.3, "soil", rng, sides=7, jitter=0.14)
    return s


def wall_light(kind):
    """A light fixed to a wall. Built in the cell in front of the wall, with the wall's face at the
    north edge of the cell (z = 0.5) and the bottom of the fitting at height 0; the game raises it."""
    s = Shape()
    s.box(-0.075, 0.02, 0.46, 0.075, 0.26, 0.50, "metal_dark")                      # back plate
    s.limb((0, 0.12, 0.47), (0, 0.06, 0.30), 0.028, 0.024, 5, "metal_dark")         # arm
    if kind == "torch":
        s.limb((0, 0.0, 0.31), (0, 0.30, 0.27), 0.034, 0.030, 6, "log")
        s.prism(0, 0.27, 0.050, 0.062, 0.26, 0.33, 6, "metal_dark")
        s.prism(0, 0.27, 0.070, 0, 0.33, 0.62, 6, "flame", fit=True)
        s.prism(0, 0.27, 0.036, 0, 0.33, 0.50, 5, "flame_core", turn=0.5)
    else:
        s.prism(0, 0.30, 0.050, 0.050, 0.03, 0.07, 8, "metal_dark")
        s.prism(0, 0.30, 0.085, 0.115, 0.07, 0.25, 8, "glow")
        s.prism(0, 0.30, 0.125, 0.04, 0.25, 0.30, 8, "metal_dark")
    return s


def wood_fired_generator():
    """2 x 2 cells."""
    s = Shape()
    s.box(-0.85, 0, -0.85, 0.85, 0.90, 0.85, "metal_dark", top="metal")
    s.box(-0.45, 0.15, -0.88, 0.45, 0.60, -0.85, "ember")             # firebox door
    s.prism(0.45, 0.40, 0.20, 0.17, 0.90, 1.70, 8, "metal", top="metal_dark")
    return s


def column():
    s = Shape()
    s.box(-0.36, 0, -0.36, 0.36, 0.14, 0.36, "stuff_dark", top="stuff")
    s.prism(0, 0, 0.26, 0.24, 0.14, 1.08, 10, "stuff")
    s.box(-0.36, 1.08, -0.36, 0.36, 1.20, 0.36, "stuff_dark", top="stuff")
    return s


# ---------------------------------------------------------------------------- rocks

def boulder(seed):
    """A loose stone chunk. Several are made so that no two neighbours match."""
    rng = random.Random(seed)
    s = Shape()
    rx, rz, h = rng.uniform(0.30, 0.40), rng.uniform(0.24, 0.32), rng.uniform(0.34, 0.48)
    s.lump(0, 0, 0, rx, h, rz, "stuff_rock", rng, sides=7, profile=((0.0, 0.96), (0.36, 1.0), (0.74, 0.66)), jitter=0.17)
    if seed % 2 == 0:                                                   # a smaller stone leaning against it
        s.lump(rx * 0.85, 0, -rz * 0.75, 0.16, 0.20, 0.14, "stuff_rock", rng, sides=5, profile=((0.0, 0.95), (0.5, 0.9)), jitter=0.2)
    if seed % 3 == 0:
        s.lump(-rx * 0.9, 0, rz * 0.5, 0.12, 0.14, 0.12, "stuff_rock", rng, sides=5, profile=((0.0, 0.95), (0.5, 0.85)), jitter=0.2)
    return s


def slag(seed):
    """A lump of fused scrap: rougher than stone, with bits of plate sticking out."""
    rng = random.Random(seed)
    s = Shape()
    s.lump(0, 0, 0, 0.34, 0.34, 0.28, "slag", rng, sides=6, profile=((0.0, 0.95), (0.4, 1.0), (0.8, 0.55)), jitter=0.26)
    s.box(-0.30, 0.05, -0.05, 0.10, 0.30, 0.00, "slag_metal")
    s.box(0.05, 0.02, 0.06, 0.36, 0.20, 0.12, "slag_metal")
    return s


# ---------------------------------------------------------------------------- weapons
# Built the way they are held: muzzle or blade toward +X, up is +Y, the hand at the origin.
# Lying on the ground they are tipped onto their side by the mod.

def gun(recv=0.30, h=0.07, barrel=0.30, bt=0.03, stock=0.22, mag=0.0, scope=False, wood=True, fat=1.0,
        body="gun_metal", accent=None, bipod=False):
    s = Shape()
    t = 0.028 * fat
    furniture = "gun_wood" if wood else "gun_dark"
    s.box(0, 0, -t, recv, h, t, body)                                               # receiver
    s.box(recv, h * 0.5 - bt / 2, -bt / 2 * fat, recv + barrel, h * 0.5 + bt / 2, bt / 2 * fat, "gun_dark")    # barrel
    s.box(recv + barrel - 0.02, h * 0.5 + bt / 2, -0.008, recv + barrel, h * 0.5 + bt / 2 + 0.02, 0.008, "gun_dark")   # front sight
    if stock > 0:
        s.box(-stock, -0.035, -t * 0.85, 0, h * 0.85, t * 0.85, furniture)
        s.box(-stock - 0.02, -0.05, -t, -stock, h * 0.9, t, "gun_dark")             # butt plate
    s.box(0.01, -0.12, -t * 0.8, 0.07, 0, t * 0.8, furniture)                       # grip
    s.box(0.07, -0.05, -0.008, 0.13, -0.035, 0.008, "gun_dark")                     # trigger guard
    if mag > 0:
        s.box(recv * 0.45, -mag, -t * 0.7, recv * 0.45 + 0.06, 0, t * 0.7, "gun_dark")
    if scope:
        s.box(recv * 0.15, h, -t * 0.5, recv * 0.8, h + 0.04, t * 0.5, "gun_dark")
    if accent:
        s.box(recv * 0.1, h * 0.3, -t - 0.004, recv * 0.9, h * 0.62, t + 0.004, accent)
    if wood and barrel > 0.2:
        s.box(recv, h * 0.08, -t * 0.8, recv + barrel * 0.5, h * 0.5 - bt / 2, t * 0.8, "gun_wood")    # fore-end
    if bipod:
        for z in (-0.05, 0.04):
            s.box(recv + barrel * 0.5, -0.16, z, recv + barrel * 0.5 + 0.015, h * 0.4, z + 0.012, "gun_dark")
    return s


def tube(length=0.55, r=0.055, body="gun_olive", warhead=None):
    """Launchers: a fat tube with a grip and sight."""
    s = Shape()
    s.box(-length * 0.3, 0, -r, length * 0.7, 2 * r, r, body)
    s.box(length * 0.7, -0.01, -r - 0.01, length * 0.7 + 0.03, 2 * r + 0.01, r + 0.01, "gun_dark")
    s.box(0.0, -0.11, -0.022, 0.05, 0, 0.022, "gun_dark")
    s.box(0.1, 2 * r, -0.012, 0.2, 2 * r + 0.035, 0.012, "gun_dark")
    if warhead:
        s.box(length * 0.73, r * 0.3, -r * 0.7, length * 0.73 + 0.10, r * 1.7, r * 0.7, warhead)
    return s


def bow(height):
    s = Shape()
    n, half = 6, height / 2
    for k in range(n):                                               # the stave, curving back toward both tips
        y0 = -half + k * height / n
        mid = (k + 0.5) / n * 2 - 1
        x = 0.11 * (1 - mid * mid) - 0.02
        s.box(x - 0.015, y0, -0.015, x + 0.015, y0 + height / n, 0.015, "gun_wood")
    s.box(-0.034, -half + 0.01, -0.004, -0.026, half - 0.01, 0.004, "string")
    s.box(0.065, -0.05, -0.02, 0.105, 0.05, 0.02, "grip")
    return s


def blade(grip=0.14, guard=0.05, length=0.40, width=0.05):
    """Knives and swords. The blade takes the colour of the metal or stone it is made from."""
    s = Shape()
    s.box(-grip, -0.016, -0.016, 0, 0.016, 0.016, "grip")
    s.box(-grip - 0.025, -0.022, -0.022, -grip, 0.022, 0.022, "gun_dark")           # pommel
    if guard:
        s.box(0, -guard, -0.02, 0.025, guard, 0.02, "gun_dark")
    s.box(0.025, -width / 2, -0.009, 0.025 + length, width / 2, 0.009, "stuff")
    s.box(0.025 + length, -width / 4, -0.007, 0.025 + length + width * 0.7, width / 4, 0.007, "stuff")   # point
    return s


def pole(shaft=0.9, head="spear"):
    """Anything on a shaft: spear, pila, mace, club, axe, hammer."""
    s = Shape()
    x0, x1 = -shaft * 0.35, shaft * 0.65
    s.box(x0, -0.015, -0.015, x1, 0.015, 0.015, "gun_wood")
    if head == "spear":
        s.box(x1, -0.03, -0.008, x1 + 0.12, 0.03, 0.008, "stuff")
        s.box(x1 + 0.12, -0.014, -0.006, x1 + 0.18, 0.014, 0.006, "stuff")
    elif head == "broad":
        s.box(x1, -0.05, -0.008, x1 + 0.16, 0.05, 0.008, "stuff")
        s.box(x1 + 0.16, -0.022, -0.006, x1 + 0.22, 0.022, 0.006, "stuff")
    elif head == "mace":
        s.prism(x1, 0, 0.055, 0.055, -0.05, 0.05, 6, "stuff")
        s.box(x1 - 0.07, -0.07, -0.012, x1 + 0.07, 0.07, 0.012, "stuff")
    elif head == "club":
        s.box(x1 - 0.22, -0.035, -0.035, x1 + 0.02, 0.035, 0.035, "stuff")
    elif head == "axe":
        s.box(x1 - 0.14, 0.0, -0.01, x1 + 0.02, 0.16, 0.01, "stuff")
        s.box(x1 - 0.10, -0.03, -0.014, x1 - 0.02, 0.0, 0.014, "gun_dark")
    elif head == "hammer":
        s.box(x1 - 0.08, -0.10, -0.05, x1 + 0.04, 0.10, 0.05, "stuff")
    return s


def grenade(body="gun_olive", band="gun_dark"):
    s = Shape()
    s.prism(0, 0, 0.045, 0.055, -0.07, 0.0, 7, body)
    s.prism(0, 0, 0.055, 0.04, 0.0, 0.06, 7, body)
    s.prism(0, 0, 0.02, 0.02, 0.06, 0.10, 5, band)
    s.box(0.01, 0.07, -0.006, 0.06, 0.085, 0.006, "gun_light")
    return s


# ---------------------------------------------------------------------------- clothing, as items

def garment(seed):
    """A folded piece of clothing."""
    rng = random.Random(seed)
    s = Shape()
    w, d = rng.uniform(0.24, 0.28), rng.uniform(0.18, 0.21)
    s.box(-w, 0, -d, w, 0.05, d, "stuff_fabric_dark", top="stuff_fabric")
    s.box(-w + 0.02, 0.05, -d + 0.02, w - 0.02, 0.09, d - 0.03, "stuff_fabric_dark", top="stuff_fabric")
    s.box(-w * 0.5, 0.09, d - 0.11, w * 0.5, 0.105, d - 0.03, "stuff_fabric_dark")             # collar
    if seed % 2 == 0:
        s.box(-w + 0.02, 0.09, -d + 0.02, -w * 0.3, 0.115, d - 0.12, "stuff_fabric")            # folded sleeve
    return s


def hat():
    s = Shape()
    s.prism(0, 0, 0.26, 0.26, 0, 0.025, 10, "stuff_fabric_dark", top="stuff_fabric")
    s.prism(0, 0, 0.15, 0.13, 0.025, 0.15, 8, "stuff_fabric")
    s.prism(0, 0, 0.155, 0.155, 0.025, 0.05, 8, "strap")
    return s


def helmet():
    s = Shape()
    rng = random.Random(5)
    s.lump(0, 0, 0, 0.17, 0.20, 0.19, "armor", rng, sides=8, profile=((0.0, 1.0), (0.45, 0.98), (0.8, 0.6)), jitter=0.02)
    s.box(-0.18, 0, -0.21, 0.18, 0.04, -0.17, "armor_dark")                                       # brow
    return s


def vest():
    """Body armour laid flat, neck to the north."""
    s = Shape()
    s.box(-0.22, 0, -0.26, 0.22, 0.09, 0.16, "armor")
    s.box(-0.24, 0, 0.12, -0.10, 0.10, 0.28, "armor")                                             # shoulders
    s.box(0.10, 0, 0.12, 0.24, 0.10, 0.28, "armor")
    s.box(-0.22, 0.09, -0.10, 0.22, 0.105, -0.04, "strap")
    s.box(-0.16, 0.09, -0.22, 0.16, 0.11, -0.14, "armor_dark")                                    # plate
    return s


def pack():
    """Belts and packs."""
    s = Shape()
    s.box(-0.18, 0, -0.12, 0.18, 0.14, 0.12, "stuff_fabric_dark", top="stuff_fabric")
    s.box(-0.19, 0.05, -0.13, 0.19, 0.09, 0.13, "strap")
    s.box(-0.04, 0.045, -0.14, 0.04, 0.095, -0.13, "gun_light")                                   # buckle
    return s


# ---------------------------------------------------------------------------- trees
# One unit tall. The mod scales each tree by how grown it is. Leaves are separate from the
# trunk and branches so that a bare tree in winter keeps its skeleton.

# Trees are built to stand about one cell tall; the mod scales them by the plant's own size.
# Each has a real skeleton (a bent trunk with a root flare, boughs and twigs) so that it still
# reads as a tree of its kind when it is bare in winter, and a crown made of many overlapping
# clumps in three tones of its leaf colour: darker ones tucked underneath, lighter ones on top
# and toward the sun, the way the game's own tree sprites are painted.

for _name in [k for k in MATERIALS if k.startswith("leaf_")]:
    (_r, _g, _b), _tex = MATERIALS[_name]
    MATERIALS[_name + "_dk"] = ((_r * 0.74, _g * 0.76, _b * 0.80), _tex)
    MATERIALS[_name + "_lt"] = ((min(1.0, _r * 1.20), min(1.0, _g * 1.16), min(1.0, _b * 1.06)), _tex)
MATERIALS["bark_dark"] = ((0.30, 0.22, 0.17), SW + "Bark")
MATERIALS["bark_birch"] = ((0.92, 0.91, 0.86), SW + "Bark")
MATERIALS["bark_mark"] = ((0.21, 0.20, 0.19), None)
# Twigs: the same bark, under names starting with "twig". The mod only draws these while the
# tree is bare, so the fine branching costs nothing in summer when the leaves would hide it.
for _name in ("bark", "bark_pale", "bark_dark", "bark_birch"):
    MATERIALS["twig_" + _name] = MATERIALS[_name]
MATERIALS["pod"] = ((0.56, 0.34, 0.16), None)
MATERIALS["pod_pale"] = ((0.90, 0.86, 0.66), None)
MATERIALS["coconut"] = ((0.36, 0.26, 0.17), None)


def trunk(s, r, h, bark, lean=(0.0, 0.0), flare=1.6, sides=7, top=0.62):
    """A tapering trunk with a root flare and a slight bend. Returns the point at its top."""
    lx, lz = lean
    s.loft([((0, 0, 0), r * flare, r * flare), ((lx * 0.10, h * 0.10, lz * 0.10), r * 1.08, r * 1.08),
            ((lx * 0.65, h * 0.58, lz * 0.65), r * 0.86, r * 0.86), ((lx, h, lz), r * top, r * top)], sides, bark, cap_start=False)
    return (lx, h, lz)


def bough(s, rng, start, heading, rise, length, r, bark, twigs=2):
    """A branch leaving start toward a compass heading (radians), rising at the given angle. Returns its tip."""
    d = (math.cos(rise) * math.cos(heading), math.sin(rise), math.cos(rise) * math.sin(heading))
    tip = along(start, d, length)
    s.limb(start, tip, r, r * 0.5, 4, bark)
    twig = "twig_" + bark
    for k in range(twigs):
        base = along(start, d, length * rng.uniform(0.40, 0.85))
        h2 = heading + (1 if k % 2 else -1) * rng.uniform(0.6, 1.2)
        r2 = rise + rng.uniform(0.0, 0.45)
        d2 = (math.cos(r2) * math.cos(h2), math.sin(r2), math.cos(r2) * math.sin(h2))
        reach = length * rng.uniform(0.50, 0.80)
        s.limb(base, along(base, d2, reach), r * 0.40, 0, 4, twig)
        h3 = h2 + rng.choice((-1, 1)) * rng.uniform(0.5, 1.0)                    # and a twiglet off each twig
        mid = along(base, d2, reach * 0.55)
        s.limb(mid, add3(mid, (reach * 0.5 * math.cos(h3), reach * 0.38, reach * 0.5 * math.sin(h3))), r * 0.2, 0, 3, twig)
    s.limb(tip, add3(tip, (d[0] * length * 0.45, length * 0.40, d[2] * length * 0.45)), r * 0.45, 0, 3, twig)   # the bough carries on, thinner
    return tip


CROWN = ((0.0, 0.62), (0.40, 1.0))        # two rings and a peak: enough to read as a ball of leaves


def clump(s, rng, c, r, mat, squash=0.82, sides=6, jitter=0.13):
    """One ball of leaves around point c."""
    s.lump(c[0], c[1] - r * squash, c[2], r, r * 2 * squash, r, mat, rng, sides=sides, profile=CROWN, jitter=jitter, closed=True)


def tree_broadleaf(seed, leaf, bark="bark", trunk_h=0.40, trunk_r=0.085, spread=0.30, crown_r=0.25, boughs=4, rise=0.80,
                   top=1.0, squash=0.82, pods=None):
    """Oak, maple, teak and their like: a few big boughs, each carrying a clump of leaves, round a taller middle."""
    rng = random.Random(seed)
    s = Shape()
    crown_base = trunk(s, trunk_r, trunk_h, bark, lean=(rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04)), sides=6)
    spine = (crown_base[0] * 1.2, trunk_h + (top - trunk_h) * 0.80, crown_base[2] * 1.2)
    s.limb(crown_base, spine, trunk_r * 0.60, trunk_r * 0.12, 5, bark)
    for k in range(4):                                                           # twigs off the leader, for winter
        b = along(crown_base, unit(sub(spine, crown_base)), (0.25 + 0.17 * k) * (spine[1] - crown_base[1]))
        a = rng.uniform(0, 6.28)
        s.limb(b, add3(b, (0.17 * math.cos(a), 0.15, 0.17 * math.sin(a))), trunk_r * 0.20, 0, 3, "twig_" + bark)
    turn = rng.uniform(0, 6.28)
    tips = []
    for i in range(boughs):
        heading = turn + 2 * math.pi * i / boughs + rng.uniform(-0.3, 0.3)
        tips.append(bough(s, rng, (crown_base[0], trunk_h * rng.uniform(0.88, 1.0), crown_base[2]), heading,
                          rise + rng.uniform(-0.15, 0.15), spread * rng.uniform(1.15, 1.40), trunk_r * 0.46, bark, twigs=2))
    mid_y = trunk_h + (top - trunk_h) * 0.50
    for i, tip in enumerate(tips[::2]):                                          # shaded clumps low down between the boughs
        a = math.atan2(tip[2], tip[0]) + math.pi / boughs
        clump(s, rng, (spread * 0.80 * math.cos(a), mid_y - crown_r * 0.50, spread * 0.80 * math.sin(a)), crown_r * 0.78, leaf + "_dk", squash)
    for tip in tips:                                                             # the main clumps, on the boughs
        clump(s, rng, (tip[0] * 0.90, max(tip[1], mid_y - crown_r * 0.2) + crown_r * 0.05, tip[2] * 0.90), crown_r * rng.uniform(0.92, 1.10), leaf, squash)
    clump(s, rng, (spine[0], top - crown_r * 0.82, spine[2]), crown_r * 1.12, leaf, squash)
    for dx, dz, k in ((-0.42, -0.36, 0.60), (0.14, -0.52, 0.46)):                 # sunlit clumps on top, toward the light
        clump(s, rng, (spine[0] + dx * spread, top - crown_r * (0.50 + 0.3 * (1 - k)), spine[2] + dz * spread), crown_r * k, leaf + "_lt", squash)
    if pods:
        for i in range(4):
            a = rng.uniform(0, 6.28)
            y = trunk_h * rng.uniform(0.45, 0.95)
            s.lump(trunk_r * 1.1 * math.cos(a), y, trunk_r * 1.1 * math.sin(a), 0.028, 0.075, 0.028, pods, rng, sides=5, jitter=0.05, closed=True)
    return s


def tree_umbrella(seed, leaf, bark="bark", trunk_h=0.50, trunk_r=0.10):
    """The dragon tree: a stout trunk forking again and again into a dense, flat-topped dome."""
    rng = random.Random(seed)
    s = Shape()
    base = trunk(s, trunk_r, trunk_h, bark, flare=1.4, top=0.85)
    turn = rng.uniform(0, 6.28)
    for i in range(6):
        heading = turn + 2 * math.pi * i / 6 + rng.uniform(-0.2, 0.2)
        tip = bough(s, rng, base, heading, 0.95, 0.30, trunk_r * 0.55, bark, twigs=1)
        clump(s, rng, (tip[0] * 1.25, 0.80, tip[2] * 1.25), 0.20, leaf if i % 2 else leaf + "_dk", squash=0.55, sides=5)
    clump(s, rng, (0, 0.86, 0), 0.30, leaf, squash=0.50)
    for dx, dz in ((-0.16, -0.14), (0.14, -0.18)):
        clump(s, rng, (dx, 0.93, dz), 0.14, leaf + "_lt", squash=0.5)
    return s


def tree_column(seed, leaf, bark="bark", trunk_r=0.05, radii=(0.17, 0.20, 0.17, 0.11), top=1.05, clear=0.26):
    """Poplar and cypress: one upright leader with short twigs hugging it, clothed in a tall narrow stack of clumps."""
    rng = random.Random(seed)
    s = Shape()
    s.loft([((0, 0, 0), trunk_r * 1.5, trunk_r * 1.5), ((0, 0.08, 0), trunk_r, trunk_r), ((0.01, top * 0.6, 0), trunk_r * 0.6, trunk_r * 0.6),
            ((0, top * 0.94, 0), trunk_r * 0.15, trunk_r * 0.15)], 6, bark, cap_start=False)
    for i in range(9):
        y = clear + (top * 0.84 - clear) * i / 8
        a = i * 2.4 + rng.uniform(-0.3, 0.3)
        reach = 0.16 * (1 - 0.5 * i / 8)
        s.limb((0, y, 0), (reach * math.cos(a), y + reach * 1.5, reach * math.sin(a)), trunk_r * 0.30, 0, 3, "twig_" + bark)
    n = len(radii)
    for i, r in enumerate(radii):
        y = clear + r * 0.8 + (top - clear - 0.16) * i / (n - 1) * 0.92
        off = 0.04 if i % 2 else -0.04
        clump(s, rng, (off, y, -off), r, leaf if i % 2 == 0 else leaf + "_dk", squash=1.25, sides=6, jitter=0.10)
    clump(s, rng, (-0.05, clear + (top - clear) * 0.62, -0.06), radii[1] * 0.62, leaf + "_lt", squash=1.3)
    return s


def tree_birch(seed, leaf):
    """A slender white trunk ringed with dark marks, and small, airy clumps of leaves."""
    rng = random.Random(seed)
    s = Shape()
    lean = (rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06))
    top = trunk(s, 0.045, 0.92, "bark_birch", lean=lean, flare=1.3, sides=6, top=0.35)
    for i in range(6):                                                           # the dark bands
        t = 0.10 + 0.13 * i
        s.prism(lean[0] * t, lean[1] * t, 0.050 * (1 - 0.5 * t), 0.050 * (1 - 0.5 * t), 0.92 * t, 0.92 * t + 0.022, 4, "bark_mark", turn=i)
    tips = [top]
    for i in range(5):
        t = 0.42 + 0.11 * i
        heading = i * 2.2 + rng.uniform(-0.3, 0.3)
        tips.append(bough(s, rng, (lean[0] * t, 0.92 * t, lean[1] * t), heading, 0.75, 0.26 - 0.02 * i, 0.016, "bark_birch", twigs=2))
    for i, tip in enumerate(tips):
        clump(s, rng, (tip[0], tip[1] + 0.03, tip[2]), rng.uniform(0.11, 0.15), (leaf, leaf + "_lt", leaf + "_dk")[i % 3], squash=0.85, sides=5)
    return s


def tree_conifer(seed, leaf, bark="bark_dark"):
    """Pine: a straight dark trunk and drooping tiers of needles, each tier ragged at its rim."""
    rng = random.Random(seed)
    s = Shape()
    s.loft([((0, 0, 0), 0.085, 0.085), ((0, 0.08, 0), 0.055, 0.055), ((0, 1.02, 0), 0.012, 0.012)], 6, bark, cap_start=False)
    skirt = ((0.0, 1.0), (0.30, 0.56))
    tiers = ((0.20, 0.37, 0.34), (0.37, 0.32, 0.32), (0.53, 0.26, 0.30), (0.68, 0.19, 0.27), (0.82, 0.12, 0.26))
    for i, (y, r, h) in enumerate(tiers):
        s.lump(rng.uniform(-0.015, 0.015), y, rng.uniform(-0.015, 0.015), r, h, r, leaf if i % 2 == 0 else leaf + "_dk", rng,
               sides=8, profile=skirt, jitter=0.16, closed=True)
    for i, (y, r, h) in enumerate(tiers[:3]):                                    # a sunlit bough on each of the lower tiers
        a = 3.9 + i * 0.5
        s.lump(r * 0.55 * math.cos(a), y + h * 0.16, r * 0.55 * math.sin(a), r * 0.42, h * 0.5, r * 0.42, leaf + "_lt", rng,
               sides=5, profile=skirt, jitter=0.14, closed=True)
    return s


def tree_willow(seed, leaf):
    """A short, thick, leaning trunk under a dome whose edge hangs down in long curtains."""
    rng = random.Random(seed)
    s = Shape()
    base = trunk(s, 0.10, 0.36, "bark", lean=(rng.uniform(-0.07, 0.07), rng.uniform(-0.07, 0.07)), flare=1.7)
    turn = rng.uniform(0, 6.28)
    for i in range(5):
        tip = bough(s, rng, base, turn + 2 * math.pi * i / 5, 0.55, 0.30, 0.05, "bark", twigs=1)
        s.limb(tip, (tip[0] * 1.5, tip[1] - 0.12, tip[2] * 1.5), 0.02, 0, 4, "bark")       # the bough bending over
    for i in range(6):
        a = turn + 2 * math.pi * i / 6
        clump(s, rng, (0.26 * math.cos(a), 0.62, 0.26 * math.sin(a)), 0.22, leaf if i % 2 else leaf + "_dk", squash=0.75)
    clump(s, rng, (base[0], 0.74, base[2]), 0.30, leaf, squash=0.70)
    clump(s, rng, (-0.14, 0.82, -0.12), 0.16, leaf + "_lt", squash=0.7)
    for i in range(10):                                                          # the curtains
        a = turn + 2 * math.pi * i / 10 + rng.uniform(-0.1, 0.1)
        r0 = rng.uniform(0.36, 0.44)
        low = rng.uniform(0.12, 0.26)
        s.loft([((r0 * 0.9 * math.cos(a), 0.62, r0 * 0.9 * math.sin(a)), 0.085, 0.04),
                ((r0 * 1.08 * math.cos(a), 0.40, r0 * 1.08 * math.sin(a)), 0.070, 0.03),
                ((r0 * 1.10 * math.cos(a), low, r0 * 1.10 * math.sin(a)), 0.0, 0.0)], 3, (leaf + "_lt", leaf, leaf + "_dk")[i % 3])
    return s


def tree_palm(seed, leaf):
    """A slim, curving, ringed trunk topped by arching fronds, with a few coconuts tucked beneath."""
    rng = random.Random(seed)
    s = Shape()
    bend = rng.uniform(0, 6.28)
    bx, bz = 0.16 * math.cos(bend), 0.16 * math.sin(bend)
    stations = []
    for i in range(7):
        t = i / 6
        stations.append(((bx * t * t, 0.86 * t, bz * t * t), 0.058 - 0.022 * t + (0.012 if i % 2 else 0), 0.058 - 0.022 * t + (0.012 if i % 2 else 0)))
    s.loft(stations, 6, "bark", cap_start=False)
    head = (bx, 0.86, bz)
    for i in range(3):
        a = i * 2.1
        s.lump(head[0] + 0.05 * math.cos(a), head[1] - 0.07, head[2] + 0.05 * math.sin(a), 0.035, 0.07, 0.035, "coconut", rng, sides=5, jitter=0.05, closed=True)
    for i in range(9):
        a = 2 * math.pi * i / 9 + rng.uniform(-0.15, 0.15)
        reach = rng.uniform(0.40, 0.52)
        ca, sa = math.cos(a), math.sin(a)
        mat = (leaf, leaf + "_dk", leaf + "_lt")[i % 3]
        s.loft([(head, 0.03, 0.02), (add3(head, (ca * reach * 0.42, 0.10, sa * reach * 0.42)), 0.085, 0.014),
                (add3(head, (ca * reach * 0.80, 0.00, sa * reach * 0.80)), 0.065, 0.012),
                (add3(head, (ca * reach, -0.20, sa * reach)), 0.0, 0.0)], 4, mat)
    s.limb(head, add3(head, (0, 0.20, 0)), 0.035, 0, 5, leaf + "_lt")
    return s


def tree_cecropia(seed, leaf):
    """A thin pale trunk with a few candelabra branches, each ending in a big flat hand of leaves."""
    rng = random.Random(seed)
    s = Shape()
    top = trunk(s, 0.05, 0.62, "bark_pale", lean=(rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)), flare=1.3, top=0.7)
    tips = [add3(top, (0, 0.24, 0))]
    s.limb(top, tips[0], 0.03, 0.015, 5, "bark_pale")
    turn = rng.uniform(0, 6.28)
    for i in range(4):
        tips.append(bough(s, rng, (top[0], 0.50 + 0.04 * i, top[2]), turn + 2 * math.pi * i / 4, 0.85, 0.30, 0.026, "bark_pale", twigs=1))
    for i, tip in enumerate(tips):
        mat = (leaf, leaf + "_lt", leaf + "_dk")[i % 3]
        for k in range(5):                                                       # the fingers of each leaf
            a = 2 * math.pi * k / 5 + i
            s.loft([(tip, 0.03, 0.014), (add3(tip, (0.12 * math.cos(a), 0.03, 0.12 * math.sin(a))), 0.075, 0.014),
                    (add3(tip, (0.23 * math.cos(a), -0.02, 0.23 * math.sin(a))), 0.0, 0.0)], 3, mat)
    return s


def tree_cactus(seed=1):
    """Saguaro: a ribbed column with a rounded top and arms that turn upward."""
    rng = random.Random(seed)
    s = Shape()
    s.loft([((0, 0, 0), 0.085, 0.085), ((0, 0.5, 0), 0.095, 0.095), ((0, 0.94, 0), 0.085, 0.085), ((0, 1.02, 0), 0.045, 0.045)], 8, "cactus", cap_start=False)
    for k in range(8):                                                           # the ribs
        a = 2 * math.pi * (k + 0.5) / 8
        s.limb((0.088 * math.cos(a), 0.02, 0.088 * math.sin(a)), (0.088 * math.cos(a), 0.95, 0.088 * math.sin(a)), 0.012, 0.012, 3, "leaf_cypress_dk")
    for a, y, top, out in ((0.4, 0.40, 0.80, 0.24), (3.4, 0.52, 0.92, 0.22), (1.9, 0.30, 0.56, 0.20)):
        ca, sa = math.cos(a), math.sin(a)
        s.loft([((0.07 * ca, y, 0.07 * sa), 0.055, 0.055), ((out * ca, y + 0.05, out * sa), 0.058, 0.058),
                ((out * 1.04 * ca, top - 0.05, out * 1.04 * sa), 0.055, 0.055), ((out * 1.04 * ca, top, out * 1.04 * sa), 0.028, 0.028)], 6, "cactus")
    return s


def tree_bamboo(seed):
    """A stand of jointed canes, each leaning its own way, with small leaf sprays near the top."""
    rng = random.Random(seed)
    s = Shape()
    for i in range(6):
        a = 2 * math.pi * i / 6 + rng.uniform(-0.4, 0.4)
        r0 = rng.uniform(0.03, 0.2)
        x, z, h = r0 * math.cos(a), r0 * math.sin(a), rng.uniform(0.7, 1.05)
        lx, lz = x * 0.6 + rng.uniform(-0.04, 0.04), z * 0.6 + rng.uniform(-0.04, 0.04)

        def at(t):
            return (x + lx * t, h * t, z + lz * t)

        s.loft([(at(0.0), 0.022, 0.022), (at(0.5), 0.021, 0.021), (at(1.0), 0.016, 0.016)], 4, "bamboo", cap_start=False)
        for t in (0.3, 0.62):                                                    # a dark ring at two of the joints
            p = at(t)
            s.prism(p[0], p[2], 0.027, 0.027, p[1] - 0.008, p[1] + 0.008, 4, "bark_mark")
        for j, t in enumerate((0.70, 0.86, 1.0)):
            p = at(t)
            b = rng.uniform(0, 6.28)
            s.loft([(p, 0.02, 0.012), (add3(p, (0.10 * math.cos(b), 0.03, 0.10 * math.sin(b))), 0.05, 0.012),
                    (add3(p, (0.21 * math.cos(b), -0.04, 0.21 * math.sin(b))), 0.0, 0.0)], 3,
                   ("leaf_bamboo", "leaf_bamboo_lt", "leaf_bamboo_dk")[(i + j) % 3])
    return s


def tree_anima(seed, leaf):
    """The anima tree: a pale twisting trunk, a broad glowing crown and long trailing strands."""
    rng = random.Random(seed)
    s = tree_broadleaf(seed, leaf, bark="bark_pale", trunk_h=0.42, trunk_r=0.095, spread=0.32, crown_r=0.27, boughs=5)
    for i in range(10):
        a = 2 * math.pi * i / 10 + rng.uniform(-0.15, 0.15)
        r0 = rng.uniform(0.38, 0.48)
        s.loft([((r0 * math.cos(a), 0.62, r0 * math.sin(a)), 0.04, 0.02), ((r0 * 1.06 * math.cos(a), 0.42, r0 * 1.06 * math.sin(a)), 0.03, 0.015),
                ((r0 * 1.08 * math.cos(a), rng.uniform(0.24, 0.34), r0 * 1.08 * math.sin(a)), 0.0, 0.0)], 3, leaf + "_lt")
    return s


# ---------------------------------------------------------------------------- ground plants
# Built to fill about one cell at full size; the mod scales them by how grown the plant is.
# The same faceted, outlined look as the trees, kept very simple because there are so many.

def blades(s, rng, n, height, radius, mats, spread, cx=0.0, cz=0.0):
    """A clump of grass blades: thin three-sided spikes."""
    for i in range(n):
        a, d = rng.uniform(0, 2 * math.pi), rng.uniform(0, spread)
        s.prism(cx + d * math.cos(a), cz + d * math.sin(a), radius * rng.uniform(0.8, 1.2), 0, 0,
                height * rng.uniform(0.7, 1.15), 3, mats[i % len(mats)], turn=rng.uniform(0, 2))


def blooms(s, rng, n, height, petal, spread, size=0.05):
    """Flower heads on thin stems."""
    for _ in range(n):
        a, d = rng.uniform(0, 2 * math.pi), rng.uniform(0.04, spread)
        x, z, h = d * math.cos(a), d * math.sin(a), height * rng.uniform(0.8, 1.1)
        s.prism(x, z, 0.014, 0.012, 0, h, 3, "stem")
        s.prism(x, z, size * 0.7, size, h, h + size * 0.8, 5, petal)


def dots(s, rng, n, cx, cy, cz, rx, ry, rz, mat, size=0.045):
    """Small fruit sitting on the upper surface of a rounded bush."""
    for _ in range(n):
        a, up = rng.uniform(0, 2 * math.pi), rng.uniform(0.25, 0.85)
        ring = math.sqrt(max(0.0, 1 - up * up))
        x, y, z = cx + rx * ring * math.cos(a) * 0.95, cy + ry * up * 0.95, cz + rz * ring * math.sin(a) * 0.95
        s.box(x - size / 2, y - size / 2, z - size / 2, x + size / 2, y + size / 2, z + size / 2, mat)


def fronds(s, rng, n, height, width, mats, spread, cx=0.0, cz=0.0, droop=0.45):
    """Soft blades of grass: each a flat, tapering ribbon that rises from the clump and arches over
    toward its tip, so a tuft reads as a fountain of leaves rather than a bed of spikes."""
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, spread)
        x, z = cx + d * math.cos(a), cz + d * math.sin(a)
        h = height * rng.uniform(0.75, 1.1)
        out = rng.uniform(0.6, 1.0) * height * droop
        ca, sa = math.cos(a), math.sin(a)
        w = width * rng.uniform(0.85, 1.15)
        s.loft([((x, 0.0, z), w * 0.7, w * 0.25),
                ((x + ca * out * 0.30, h * 0.70, z + sa * out * 0.30), w, w * 0.25),
                ((x + ca * out * 0.85, h * 0.86, z + sa * out * 0.85), w * 0.70, w * 0.2),
                ((x + ca * out * 1.30, h * 0.68, z + sa * out * 1.30), 0.0, 0.0)], 3, mats[i % len(mats)], cap_start=False)


def grass(seed, tall=False, mats=("blade_a", "blade_b")):
    """A soft, fluffy tuft: three rounded puffs of leaf, the lightest sitting highest, and a broad
    blade or two arching out of them. Kept to about fifty triangles and drawn without an outline,
    because a meadow holds thousands."""
    rng = random.Random(seed)
    s = Shape()
    h = 0.56 if tall else 0.30
    puff = ((0.0, 0.80), (0.62, 1.0))
    a0 = rng.uniform(0, 6.28)
    for i, mat in enumerate((mats[1], mats[0], "blade_c")):
        a = a0 + 2.1 * i
        d = 0.09 if i < 2 else 0.02
        r = (0.12, 0.115, 0.095)[i]
        y = 0.0 if i < 2 else h * 0.22
        s.lump(d * math.cos(a), y, d * math.sin(a), r, h * (0.55 if i < 2 else 0.50), r, mat, rng, sides=5, profile=puff, jitter=0.16)
    fronds(s, rng, 2 if tall else 1, h * 0.92, 0.055, (mats[0], "blade_c"), 0.06, droop=0.40)
    return s


def grass_card(seed, tall=False):
    """Wild grass kept as light as it can be: a few single-triangle blades standing in a little
    fan, each two-sided, no outline. Five triangles or so, so a meadow costs next to nothing and
    only just breaks up the flat ground."""
    rng = random.Random(seed)
    s = Shape()
    n = 5 if tall else 4
    h = 0.30 if tall else 0.17
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.0, 0.16)
        cx, cz = r * math.cos(a), r * math.sin(a)
        turn = rng.uniform(0, math.pi)
        w = rng.uniform(0.035, 0.055)
        dx, dz = w * math.cos(turn), w * math.sin(turn)
        lean = rng.uniform(0.02, 0.08)
        tip = (cx + lean * math.cos(a), h * rng.uniform(0.65, 1.0), cz + lean * math.sin(a))
        mat = ("blade_a", "blade_b", "blade_c")[i % 3]
        s.face(mat, [(cx - dx, 0.0, cz - dz), (cx + dx, 0.0, cz + dz), tip], (cx + 0.3, 0.05, cz + 0.3))
    return s


def flower(seed, petal, n=3):
    rng = random.Random(seed)
    s = Shape()
    blades(s, rng, 3, 0.2, 0.07, ("blade_a", "blade_b"), 0.18)
    blooms(s, rng, n, 0.26, petal, 0.24)
    return s


def bush(seed, mat="shrub", fruit=None):
    rng = random.Random(seed)
    s = Shape()
    crown = ((0.0, 0.8), (0.4, 1.0), (0.78, 0.6))
    s.lump(0, 0.02, 0, 0.30, 0.42, 0.28, mat, rng, sides=6, profile=crown, jitter=0.14)
    s.lump(0.2, 0.02, -0.14, 0.2, 0.28, 0.2, mat, rng, sides=5, profile=crown, jitter=0.16)
    if fruit:
        dots(s, rng, 7, 0, 0.02, 0, 0.30, 0.42, 0.28, fruit)
    return s


def bramble(seed):
    rng = random.Random(seed)
    s = Shape()
    spiky = ((0.0, 0.9), (0.35, 1.0), (0.7, 0.45))
    for cx, cz, r in ((0, 0, 0.26), (0.22, 0.12, 0.18), (-0.2, -0.1, 0.2)):
        s.lump(cx, 0, cz, r, r * 1.1, r, "bramble", rng, sides=6, profile=spiky, jitter=0.34)
    return s


def moss(seed):
    rng = random.Random(seed)
    s = Shape()
    s.lump(0, 0, 0, 0.40, 0.07, 0.36, "moss", rng, sides=7, profile=((0.0, 1.0), (0.7, 0.7)), jitter=0.16)
    return s


def rosette(seed, mat="agave"):
    """Agave and other spiky plants: a ring of spikes round a taller middle one."""
    rng = random.Random(seed)
    s = Shape()
    s.prism(0, 0, 0.09, 0, 0, 0.46, 4, mat)
    for i in range(6):
        a = 2 * math.pi * i / 6 + rng.uniform(-0.2, 0.2)
        s.prism(0.17 * math.cos(a), 0.17 * math.sin(a), 0.08, 0, 0, rng.uniform(0.2, 0.32), 3, mat, turn=a)
    return s


def round_cactus():
    rng = random.Random(9)
    s = Shape()
    s.lump(0, 0, 0, 0.16, 0.22, 0.16, "cactus", rng, sides=7, profile=((0.0, 0.85), (0.45, 1.0), (0.8, 0.6)), jitter=0.04)
    s.prism(0.02, 0.01, 0.03, 0.045, 0.21, 0.25, 5, "petal_pink")
    return s


def leafy_crop(seed, mat="crop_leaf", fruit=None, height=0.3, petal=None):
    """Potatoes, strawberries, healroot, smokeleaf and the like: a low mound of leaves."""
    rng = random.Random(seed)
    s = Shape()
    s.lump(0, 0, 0, 0.28, height, 0.26, mat, rng, sides=6, profile=((0.0, 0.85), (0.45, 1.0), (0.8, 0.55)), jitter=0.16)
    if fruit:
        dots(s, rng, 6, 0, 0, 0, 0.28, height, 0.26, fruit, size=0.05)
    if petal:
        blooms(s, rng, 3, height + 0.06, petal, 0.18, size=0.04)
    return s


def stalk_crop(seed, height, top=None, cob=None):
    """Corn, hops and cotton: upright stalks with something on them."""
    rng = random.Random(seed)
    s = Shape()
    for x, z in ((-0.14, 0.06), (0.12, -0.08), (0.02, 0.16)):
        h = height * rng.uniform(0.85, 1.05)
        s.prism(x, z, 0.03, 0.02, 0, h, 4, "stem")
        s.box(x - 0.13, h * 0.45, z - 0.012, x + 0.13, h * 0.45 + 0.03, z + 0.012, "blade_a")      # leaves
        s.box(x - 0.012, h * 0.65, z - 0.11, x + 0.012, h * 0.65 + 0.03, z + 0.11, "blade_b")
        if cob:
            s.box(x + 0.02, h * 0.5, z - 0.03, x + 0.08, h * 0.5 + 0.16, z + 0.03, cob)
        if top:
            s.lump(x, h - 0.04, z, 0.07, 0.12, 0.07, top, rng, sides=5, profile=((0.0, 0.8), (0.5, 1.0)), jitter=0.1, closed=True)
    return s


def mushrooms(seed, cap):
    rng = random.Random(seed)
    s = Shape()
    for x, z, h, r in ((0, 0, 0.3, 0.16), (0.2, 0.1, 0.2, 0.11), (-0.16, -0.12, 0.16, 0.09)):
        s.prism(x, z, 0.035, 0.03, 0, h, 5, "petal_white")
        s.lump(x, h - 0.02, z, r, r * 0.8, r, cap, rng, sides=6, profile=((0.0, 1.0), (0.5, 0.75)), jitter=0.08, closed=True)
    return s


def herb(seed):
    """The stand-in for any plant without its own model. Coloured from the plant's own sprite."""
    rng = random.Random(seed)
    s = Shape()
    blades(s, rng, 3, 0.3, 0.08, ("stuff_herb", "stuff_herb_dark"), 0.2)
    s.lump(0.05, 0, -0.04, 0.2, 0.24, 0.18, "stuff_herb", rng, sides=5, profile=((0.0, 0.85), (0.45, 1.0), (0.8, 0.5)), jitter=0.18)
    return s


# ---------------------------------------------------------------------------- doors
# Drawn by the mod every frame so the two leaves can slide. Built for a wall 1.2 cells high;
# the mod stretches them to the wall height setting.

def door_leaf():
    """The east half of a door in an east-west wall: hinge side at x = 0.5, meeting edge at x = 0."""
    s = Shape()
    s.box(0.0, 0, -0.07, 0.5, 1.06, 0.07, "stuff")
    for z0, z1 in ((-0.085, -0.07), (0.07, 0.085)):                    # raised frame on both faces
        s.box(0.02, 0.04, z0, 0.48, 0.10, z1, "stuff_dark")
        s.box(0.02, 0.96, z0, 0.48, 1.02, z1, "stuff_dark")
        s.box(0.02, 0.10, z0, 0.08, 0.96, z1, "stuff_dark")
        s.box(0.42, 0.10, z0, 0.48, 0.96, z1, "stuff_dark")
        s.box(0.02, 0.50, z0, 0.48, 0.55, z1, "stuff_dark")
    s.box(0.04, 0.50, -0.105, 0.075, 0.60, 0.105, "metal_dark")        # handle
    return s


def door_lintel():
    """The beam over the doorway, carrying the wall line across."""
    s = Shape()
    s.box(-0.5, 1.06, -0.16, 0.5, 1.20, 0.16, "stuff_dark", top="stuff")
    return s


def fence_post():
    s = Shape()
    s.box(-0.055, 0, -0.055, 0.055, 0.62, 0.055, "stuff_dark")
    s.prism(0, 0, 0.078, 0, 0.62, 0.70, 4, "stuff", turn=math.pi / 4)      # pointed cap
    return s


def fence_arm():
    """The rails from a fence post to the north edge of its cell, with one picket half way."""
    s = Shape()
    for y in (0.20, 0.44):
        s.box(-0.022, y, 0.05, 0.022, y + 0.075, 0.50, "stuff")
    s.box(-0.03, 0, 0.26, 0.03, 0.56, 0.31, "stuff_dark")
    return s


def gate_leaf():
    """Half of a fence gate, the same way round as door_leaf: hinge at x = 0.5, meeting edge at x = 0."""
    s = Shape()
    for y in (0.14, 0.42):
        s.box(0.01, y, -0.02, 0.47, y + 0.075, 0.02, "stuff")
    for x in (0.03, 0.24):
        s.box(x, 0.06, -0.03, x + 0.055, 0.58, 0.03, "stuff_dark")
    s.limb((0.05, 0.16, 0.0), (0.45, 0.46, 0.0), 0.022, 0.022, 4, "stuff_dark")   # the brace across it
    s.box(-0.01, 0.34, -0.04, 0.05, 0.40, 0.04, "metal_dark")                    # latch
    return s


def gate_posts():
    s = Shape()
    for x in (-0.47, 0.47):
        s.box(x - 0.06, 0, -0.06, x + 0.06, 0.70, 0.06, "stuff_dark")
        s.prism(x, 0, 0.085, 0, 0.70, 0.79, 4, "stuff", turn=math.pi / 4)
    return s


def geyser():
    """2 x 2 cells: a low cone of rock round a dark vent, crusted with pale minerals."""
    rng = random.Random(41)
    s = Shape()
    s.prism(0, 0, 0.36, 0.30, 0, 0.03, 9, "pit")
    for i in range(9):
        a = 2 * math.pi * i / 9 + rng.uniform(-0.15, 0.15)
        r = rng.uniform(0.50, 0.62)
        size = rng.uniform(0.20, 0.30)
        s.lump(r * math.cos(a), 0, r * math.sin(a), size, size * rng.uniform(0.7, 1.15), size, "geyser_rock", rng, sides=6, jitter=0.16)
    for i in range(7):                                                # mineral crust on the inner rim
        a = 2 * math.pi * i / 7 + 0.3
        s.lump(0.36 * math.cos(a), 0.02, 0.36 * math.sin(a), 0.11, 0.09, 0.11, "geyser_crust", rng, sides=5, jitter=0.15)
    for i in range(5):                                                # and stones scattered further out
        a = rng.uniform(0, 6.28)
        r = rng.uniform(0.80, 0.95)
        s.lump(r * math.cos(a), 0, r * math.sin(a), 0.08, 0.07, 0.08, "geyser_rock", rng, sides=5, jitter=0.2)
    return s


def fx_flame(core):
    """A tongue of flame one unit tall and one across, standing on the origin. The mod draws several, flickering."""
    s = Shape()
    if core:
        s.prism(0, 0, 0.5, 0, 0, 1.0, 5, "flame_core", turn=0.6)
    else:
        s.prism(0, 0, 0.5, 0, 0, 1.0, 6, "flame", fit=True)
    return s


def fx_puff():
    """A puff of smoke or steam: a faceted ball one unit across. The mod colours, sizes and moves it."""
    rng = random.Random(77)
    s = Shape()
    s.lump(0, -0.42, 0, 0.5, 0.84, 0.5, "stuff_plain", rng, sides=6, profile=((0.0, 0.55), (0.30, 1.0), (0.70, 0.86)), jitter=0.12, closed=True)
    return s


# ---- colonists -----------------------------------------------------------------------------
# People keep the game's own proportions: a big round head on a simple body with no arms or
# legs. Every part is a separate plain model that the mod colours and stacks up: the lower and
# upper body (trousers and shirt, or skin), a coat over them, the head, hair, beard and hat.
# Bodies come in the game's five builds. One unit is one cell; an adult is about 1.25 tall.

BUILDS = {
    "male":   [(0.0, 0.12, 0.09), (0.04, 0.165, 0.12), (0.28, 0.20, 0.135), (0.50, 0.235, 0.145), (0.66, 0.25, 0.14), (0.74, 0.13, 0.10)],
    "female": [(0.0, 0.11, 0.09), (0.04, 0.155, 0.115), (0.27, 0.205, 0.135), (0.45, 0.165, 0.115), (0.60, 0.215, 0.14), (0.68, 0.205, 0.13), (0.74, 0.115, 0.09)],
    "thin":   [(0.0, 0.10, 0.08), (0.04, 0.135, 0.10), (0.28, 0.165, 0.115), (0.50, 0.19, 0.12), (0.66, 0.205, 0.12), (0.74, 0.11, 0.09)],
    "hulk":   [(0.0, 0.14, 0.10), (0.04, 0.19, 0.13), (0.28, 0.24, 0.155), (0.50, 0.31, 0.175), (0.66, 0.34, 0.17), (0.74, 0.15, 0.11)],
    "fat":    [(0.0, 0.13, 0.10), (0.04, 0.20, 0.16), (0.26, 0.29, 0.22), (0.46, 0.30, 0.22), (0.64, 0.25, 0.16), (0.74, 0.13, 0.10)],
}
WAIST = 0.28


def build_at(sections, y):
    """Half width and half depth of a body at a given height."""
    for (y0, w0, d0), (y1, w1, d1) in zip(sections, sections[1:]):
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return (w0 + (w1 - w0) * t, d0 + (d1 - d0) * t)
    return sections[-1][1:]


def body_part(build, lo, hi, grow=1.0, pad=0.0, flare=1.0, collar=False):
    """The stretch of a body between two heights, optionally swollen into a coat."""
    sections = BUILDS[build]
    heights = sorted(set([lo, hi] + [y for y, _, _ in sections if lo < y < hi]))
    stations = []
    for y in heights:
        w, d = build_at(sections, y)
        k = flare if y == lo else 1.0
        stations.append(((0.0, y, 0.0), (w * grow + pad) * k, (d * grow + pad) * k))
    if collar:
        w, d = build_at(sections, 0.74)
        stations.append(((0.0, 0.775, 0.0), w * 1.25 + pad, d * 1.25 + pad))
    s = Shape()
    s.loft(stations, 8, "stuff_plain", under=None, cap_start=(pad == 0.0), cap_end=True)
    return s


HEAD = [(0.745, 0.11, 0.10), (0.80, 0.20, 0.185), (0.90, 0.25, 0.23), (1.02, 0.255, 0.235), (1.14, 0.22, 0.205), (1.215, 0.13, 0.12)]


def head_shell(grow=1.0, start=0.0, back=0.0):
    """The head, or a shell round it from a given height up (a hat, a helmet, the top of the hair)."""
    # Grown about the middle of the head, upward as well as outward, so a shell clears the crown.
    mid = 0.98
    lift = lambda y: mid + (y - mid) * grow if grow > 1.0 else y
    stations = [((0.0, lift(y), back), w * grow, d * grow) for y, w, d in HEAD if y >= start]
    stations.append(((0.0, lift(1.215) + 0.035 * grow, back), 0.0, 0.0))
    s = Shape()
    s.loft(stations, 8, "stuff_plain", cap_start=True)
    return s


def back_of_head(bottom, grow=1.09, s=None, mat="stuff_plain"):
    """Hair (or a helmet's neck guard) down the back and sides of the head to a given height."""
    s = s or Shape()
    stations = []
    for y, w, d, z in ((0.50, 0.21, 0.09, -0.15), (0.70, 0.25, 0.13, -0.13), (0.84, 0.235, 0.17, -0.085), (0.94, 0.25, 0.20, -0.07), (1.05, 0.255, 0.21, -0.05)):
        if y >= bottom - 1e-6:
            stations.append(((0.0, y, z), w * grow, d * grow))
    s.loft(stations, 8, mat, cap_start=True, cap_end=False)
    return s


def person_hair(kind):
    s = Shape()
    top = head_shell(1.09, start=1.02, back=-0.012)
    if kind in ("short", "ponytail", "spiky", "bun"):
        s.merge(top)
        back_of_head(0.84, s=s)
    elif kind == "medium":
        s.merge(top)
        back_of_head(0.70, 1.11, s=s)
    elif kind == "long":
        s.merge(top)
        back_of_head(0.50, 1.11, s=s)
    elif kind == "afro":
        rng = random.Random(5)
        s.lump(0, 0.99, -0.03, 0.37, 0.50, 0.35, "stuff_plain", rng, sides=8, profile=((0.0, 0.74), (0.34, 1.0), (0.74, 0.74)), jitter=0.07)
        back_of_head(0.84, 1.16, s=s)
    elif kind == "mohawk":
        s.loft([((0, 1.13, 0.21), 0.03, 0.05), ((0, 1.30, 0.04), 0.04, 0.10), ((0, 1.27, -0.12), 0.04, 0.09), ((0, 1.08, -0.25), 0.03, 0.05)], 4, "stuff_plain")
    if kind == "ponytail":
        s.loft([((0, 1.06, -0.25), 0.07, 0.07), ((0, 0.90, -0.36), 0.065, 0.06), ((0, 0.70, -0.34), 0.0, 0.0)], 5, "stuff_plain_dark")
    elif kind == "bun":
        rng = random.Random(6)
        s.lump(0, 1.16, -0.16, 0.10, 0.17, 0.10, "stuff_plain_dark", rng, sides=6, jitter=0.06, closed=True)
    elif kind == "spiky":
        rng = random.Random(7)
        for i in range(8):
            a = 2 * math.pi * i / 8
            r = 0.13 if i % 2 else 0.05
            b = (r * math.cos(a), 1.20, r * math.sin(a) - 0.01)
            s.limb(b, add3(b, (0.07 * math.cos(a), 0.13, 0.07 * math.sin(a))), 0.055, 0, 4, "stuff_plain_dark")
    return s


def person_beard(kind):
    rng = random.Random(8)
    s = Shape()
    if kind == "full":
        s.lump(0, 0.735, 0.13, 0.175, 0.21, 0.115, "stuff_plain", rng, sides=7, profile=((0.0, 0.55), (0.40, 1.0), (0.80, 0.9)), jitter=0.06, closed=True)
    else:
        s.limb((0, 0.87, 0.215), (0, 0.72, 0.235), 0.07, 0.0, 5, "stuff_plain")
    return s


def person_hat(kind):
    s = Shape()
    if kind == "cap":
        s.merge(head_shell(1.13, start=1.02, back=-0.01))
        s.prism(0, -0.01, 0.295, 0.295, 1.035, 1.075, 8, "stuff_plain_dark")          # turned-up band
    elif kind == "brim":
        s.prism(0, 0, 0.44, 0.42, 1.085, 1.11, 10, "stuff_plain_dark")
        s.loft([((0, 1.10, 0), 0.235, 0.215), ((0, 1.27, 0), 0.20, 0.18), ((0, 1.31, 0), 0.12, 0.10)], 8, "stuff_plain")
    elif kind == "tall":
        s.prism(0, 0, 0.33, 0.32, 1.085, 1.11, 10, "stuff_plain_dark")
        s.prism(0, 0, 0.215, 0.225, 1.11, 1.40, 10, "stuff_plain")
    elif kind == "helmet":
        s.merge(head_shell(1.15, start=1.02, back=-0.015))
        back_of_head(0.86, 1.17, s=s, mat="stuff_plain_dark")
        s.box(-0.03, 1.04, -0.30, 0.03, 1.275, 0.27, "stuff_plain_dark")              # the ridge over the top
    elif kind == "fullhelm":
        s.merge(head_shell(1.14, start=0.74))
        s.box(-0.035, 1.02, -0.30, 0.035, 1.27, 0.20, "stuff_plain_dark")
        for sx in (-1, 1):                                                            # cheek plates
            s.box(sx * 0.27 - 0.03, 0.82, -0.08, sx * 0.27 + 0.03, 0.98, 0.10, "stuff_plain_dark")
    elif kind == "hood":
        s.merge(head_shell(1.14, start=1.03, back=-0.02))
        back_of_head(0.70, 1.17, s=s)
    return s


def person_face():
    s = Shape()
    for sx in (-1, 1):
        s.box(sx * 0.095 - 0.026, 0.935, 0.215, sx * 0.095 + 0.026, 1.005, 0.243, "an_dark")
    return s


def person_visor():
    s = Shape()
    s.box(-0.19, 0.90, 0.20, 0.19, 1.01, 0.275, "visor")
    return s


def shoulder_pads():
    """Armour plates for the shoulders, built for the widest part of a 'male' body; the mod widens them to fit."""
    s = Shape()
    for sx in (-1, 1):
        s.box(sx * 0.25 - 0.085, 0.585, -0.125, sx * 0.25 + 0.085, 0.715, 0.125, "stuff_plain_dark", top="stuff_plain")
    s.box(-0.13, 0.36, 0.12, 0.13, 0.62, 0.165, "stuff_plain_dark")                   # chest plate
    return s


# ---- armour --------------------------------------------------------------------------------
# Worn armour is built per body build so it fits, and takes the colour of the armour's own
# sprite (or what it is made from). The shapes follow the game's armour sprites: a boxy flak
# vest, a quilted flak jacket, banded plate with round pauldrons, bulky marine armour with a
# backpack and huge shoulders, sleek ridged recon armour and the even heavier cataphract.

FRONT = 0.924   # the flat front of an eight-sided body sits this far out of its half depth


def band(s, build, y, h, grow, pad, mat):
    """A ring round the body between two heights, standing a little proud of it."""
    w0, d0 = build_at(BUILDS[build], y)
    w1, d1 = build_at(BUILDS[build], y + h)
    s.loft([((0.0, y, 0.0), w0 * grow + pad, d0 * grow + pad), ((0.0, y + h, 0.0), w1 * grow + pad, d1 * grow + pad)],
           8, mat, cap_start=False, cap_end=True)


def front_at(build, y, grow, pad):
    w, d = build_at(BUILDS[build], y)
    return w * grow + pad, (d * grow + pad) * FRONT


def pauldron(s, x, y, rx, ry, rz, mat, seed, trim=None):
    rng = random.Random(seed)
    s.lump(x, y, 0.0, rx, ry, rz, mat, rng, sides=7, profile=((0.0, 0.85), (0.35, 1.0), (0.75, 0.70)), jitter=0.0, closed=True)
    if trim:
        s.prism(x, 0.0, rx * 1.02, rx * 1.02, y, y + ry * 0.12, 7, trim)


def worn_armour(build, kind):
    s = Shape()
    if kind == "flakvest":
        g, pad = 1.12, 0.018
        s.merge(body_part(build, 0.30, 0.70, grow=g, pad=pad))
        w, f = front_at(build, 0.55, g, pad)
        for sz in (1, -1):
            s.box(-w * 0.62, 0.38, sz * f - 0.012, w * 0.62, 0.66, sz * (f + 0.03), "stuff_plain_dark")      # plate pockets
        for sx in (-1, 1):
            s.box(sx * w * 0.55 - 0.05, 0.31, f - 0.01, sx * w * 0.55 + 0.05, 0.38, f + 0.035, "stuff_plain_deep")  # pouches
        band(s, build, 0.68, 0.05, 1.2, 0.02, "stuff_plain_dark")                                                # collar
    elif kind == "flakjacket":
        g, pad = 1.14, 0.022
        s.merge(body_part(build, 0.22, 0.72, grow=g, pad=pad, collar=True))
        for y in (0.30, 0.42, 0.54):
            band(s, build, y, 0.03, g + 0.03, pad, "stuff_plain_dark")                                           # quilting
        w, f = front_at(build, 0.5, g, pad)
        s.box(-0.012, 0.24, f - 0.005, 0.012, 0.70, f + 0.02, "stuff_plain_deep")                              # zip
    elif kind == "flakpants":
        s.merge(body_part(build, 0.0, WAIST + 0.03, grow=1.08, pad=0.012))
        w, f = front_at(build, 0.12, 1.08, 0.012)
        for sx in (-1, 1):
            s.box(sx * w * 0.5 - 0.055, 0.08, f - 0.01, sx * w * 0.5 + 0.055, 0.18, f + 0.035, "stuff_plain_dark")  # knee pads
            s.box(sx * (w + 0.005), 0.15, -0.05, sx * (w + 0.04), 0.24, 0.05, "stuff_plain_deep")               # thigh pockets
    elif kind == "plate":
        g, pad = 1.10, 0.015
        s.merge(body_part(build, 0.20, 0.72, grow=g, pad=pad))
        for y in (0.30, 0.38, 0.46):
            band(s, build, y, 0.05, g + 0.04, pad, "stuff_plain_light")                                          # lames
        w, f = front_at(build, 0.58, g, pad)
        s.box(-w * 0.7, 0.50, f - 0.01, w * 0.7, 0.70, f + 0.03, "stuff_plain_light")                           # breastplate
        s.loft([((0.0, 0.30, 0.0), w * 1.02, f * 1.06), ((0.0, 0.10, 0.0), w * 1.18, f * 1.22)], 8, "stuff_plain_dark",
               cap_start=False, cap_end=False)                                                                    # tassets
        for sx in (-1, 1):
            pauldron(s, sx * (w + 0.04), 0.60, 0.12, 0.13, 0.15, "stuff_plain_light", 11 + sx, trim="stuff_plain_dark")
        band(s, build, 0.70, 0.05, 1.25, 0.02, "stuff_plain_dark")                                                # gorget
    elif kind in ("marine", "cataphract"):
        big = kind == "cataphract"
        g, pad = (1.28, 0.035) if big else (1.22, 0.03)
        s.merge(body_part(build, 0.0, 0.74, grow=g, pad=pad, flare=1.06))
        w, f = front_at(build, 0.58, g, pad)
        s.box(-w * 0.78, 0.44, f - 0.01, w * 0.78, 0.70, f + 0.045, "stuff_plain_light")                       # chest plate
        for i, y in enumerate((0.30, 0.355)):
            s.box(-w * 0.55, y, f - 0.01, w * 0.55, y + 0.045, f + 0.03, "stuff_plain_dark")                    # stomach plates
        band(s, build, 0.25, 0.04, g + 0.03, pad, "stuff_plain_deep")                                            # belt
        wl, fl = front_at(build, 0.10, g, pad)
        for sx in (-1, 1):
            s.box(sx * wl * 0.48 - 0.07, 0.04, fl - 0.01, sx * wl * 0.48 + 0.07, 0.20, fl + 0.045, "stuff_plain_light")  # shin plates
            r = 0.17 if big else 0.15
            pauldron(s, sx * (w + r * 0.55), 0.60, r, r * 0.95, r * 1.12, "stuff_plain_light", 21 + sx, trim="stuff_plain_deep")
        bw, bd = build_at(BUILDS[build], 0.55)
        back = -(bd * g + pad) * FRONT
        s.box(-w * 0.62, 0.36, back - 0.14, w * 0.62, 0.74, back + 0.01, "stuff_plain_dark")                     # backpack
        for sx in (-1, 1):
            s.prism(sx * w * 0.35, back - 0.10, 0.04, 0.04, 0.74, 0.80, 6, "stuff_plain_deep")                   # vents
        band(s, build, 0.72, 0.06, 1.35, 0.03, "stuff_plain_dark")                                                # collar ring
        if big:
            s.loft([((0.0, 0.28, 0.0), w * 1.04, f * 1.08), ((0.0, 0.06, 0.0), w * 1.22, f * 1.25)], 8, "stuff_plain_dark",
                   cap_start=False, cap_end=False)                                                                # armoured skirt
    elif kind == "recon":
        g, pad = 1.13, 0.016
        s.merge(body_part(build, 0.02, 0.74, grow=g, pad=pad))
        for y in (0.34, 0.42, 0.50, 0.12):
            band(s, build, y, 0.022, g + 0.03, pad, "stuff_plain_dark")                                          # ridges
        w, f = front_at(build, 0.6, g, pad)
        for sx in (-1, 1):
            s.box(sx * 0.01, 0.52, f - 0.01, sx * w * 0.72, 0.70, f + 0.03, "stuff_plain_light")                 # chest plates
            pauldron(s, sx * (w + 0.03), 0.62, 0.10, 0.09, 0.12, "stuff_plain_light", 31 + sx)
        bw, bd = build_at(BUILDS[build], 0.55)
        back = -(bd * g + pad) * FRONT
        s.box(-w * 0.45, 0.42, back - 0.08, w * 0.45, 0.68, back + 0.01, "stuff_plain_dark")                     # small pack
        band(s, build, 0.70, 0.05, 1.22, 0.02, "stuff_plain_dark")
    return s


def armour_helmet(kind):
    s = Shape()
    if kind == "combat":
        s.merge(head_shell(1.17, start=0.95, back=-0.015))
        s.prism(0, -0.015, 0.30, 0.30, 0.95, 0.975, 10, "stuff_plain_dark")                                    # rim
        s.box(-0.20, 0.925, 0.215, 0.20, 1.005, 0.285, "visor")                                                  # visor
        for sx in (-1, 1):
            s.box(sx * 0.255 - 0.035, 0.84, -0.07, sx * 0.255 + 0.035, 0.97, 0.09, "stuff_plain_dark")         # ear guards
    elif kind in ("marine_helm", "cataphract_helm"):
        big = kind == "cataphract_helm"
        g = 1.26 if big else 1.21
        s.merge(head_shell(g, start=0.74))
        z = 0.235 * g * FRONT
        s.box(-0.21, 0.94, z - 0.03, 0.21, 1.00, z + 0.02, "visor")                                             # T visor
        s.box(-0.035, 0.82, z - 0.03, 0.035, 0.97, z + 0.02, "visor")
        s.box(-0.10, 0.77, z - 0.05, 0.10, 0.84, z + 0.03, "stuff_plain_deep")                                 # breather
        s.box(-0.035, 1.10, -0.30, 0.035, 1.24 + (0.10 if big else 0.0), 0.22, "stuff_plain_dark")            # crest
        for sx in (-1, 1):
            s.prism(sx * 0.27 * g / 1.21, 0.0, 0.07, 0.07, 0.88, 1.00, 8, "stuff_plain_deep", turn=0.2)       # ear pods
    elif kind == "recon_helm":
        s.merge(head_shell(1.16, start=0.76))
        z = 0.235 * 1.16 * FRONT
        s.box(-0.23, 0.93, z - 0.04, 0.23, 1.00, z + 0.02, "visor_lit")                                         # visor band
        for sx in (-1, 1):
            s.box(sx * 0.28 - 0.02, 0.98, -0.18, sx * 0.28 + 0.02, 1.14, 0.06, "stuff_plain_dark")             # fins
        s.box(-0.025, 1.12, -0.24, 0.025, 1.25, 0.12, "stuff_plain_dark")
    return s


# ---- work tools ------------------------------------------------------------------------------
# Held by colonists while they work. The grip is at the origin, the handle runs up +Y and the
# working end faces +Z, so the mod can swing a tool forward and down by turning it about X.

def tool(kind):
    s = Shape()
    if kind == "axe":
        s.limb((0, -0.06, 0), (0, 0.50, 0), 0.020, 0.017, 5, "gun_wood")
        s.box(-0.022, 0.41, -0.05, 0.022, 0.50, 0.05, "gun_metal")
        s.box(-0.012, 0.38, 0.05, 0.012, 0.53, 0.14, "gun_light")                # the blade
    elif kind == "pickaxe":
        s.limb((0, -0.06, 0), (0, 0.56, 0), 0.020, 0.018, 5, "gun_wood")
        s.limb((0, 0.53, -0.04), (0, 0.50, -0.24), 0.030, 0.004, 5, "gun_metal")
        s.limb((0, 0.53, 0.0), (0, 0.48, 0.25), 0.032, 0.004, 5, "gun_metal")
        s.box(-0.03, 0.50, -0.05, 0.03, 0.58, 0.05, "gun_dark")
    elif kind == "hammer":
        s.limb((0, -0.04, 0), (0, 0.36, 0), 0.016, 0.014, 5, "gun_wood")
        s.box(-0.035, 0.32, -0.07, 0.035, 0.40, 0.08, "gun_dark")
        s.box(-0.03, 0.33, 0.08, 0.03, 0.39, 0.10, "gun_metal")                    # striking face
    elif kind == "scythe":
        s.limb((0, -0.10, 0), (0, 0.95, 0), 0.018, 0.016, 5, "gun_wood")
        s.limb((0, 0.45, 0), (0, 0.47, 0.11), 0.014, 0.012, 4, "gun_wood")         # the hand grip
        s.loft([((0, 0.93, 0.0), 0.006, 0.035), ((0, 0.90, 0.16), 0.005, 0.030), ((0, 0.83, 0.30), 0.004, 0.020),
                ((0, 0.74, 0.38), 0.0, 0.0)], 4, "gun_light")
    elif kind == "hoe":
        s.limb((0, -0.08, 0), (0, 0.74, 0), 0.017, 0.015, 5, "gun_wood")
        s.box(-0.07, 0.62, 0.05, 0.07, 0.75, 0.075, "gun_metal")
        s.box(-0.015, 0.70, -0.01, 0.015, 0.75, 0.06, "gun_dark")
    elif kind == "broom":
        s.limb((0, -0.06, 0), (0, 0.76, 0), 0.016, 0.016, 5, "gun_wood")
        s.prism(0, 0, 0.035, 0.035, 0.74, 0.80, 6, "strap")
        s.loft([((0, 0.78, 0), 0.04, 0.03), ((0, 0.90, 0.0), 0.10, 0.04), ((0, 0.98, 0.0), 0.11, 0.045)], 6, "hay_a")
    elif kind == "knife":
        s.limb((0, -0.03, 0), (0, 0.09, 0), 0.016, 0.016, 5, "grip")
        s.box(-0.006, 0.09, -0.012, 0.006, 0.26, 0.03, "gun_light")
    return s


# ---- work benches and other furniture --------------------------------------------------------

def bench_base(s, metal=False, width=3.0, depth=1.0):
    """A long work table: cupboards below, a worktop above. Returns the height of the worktop."""
    x, z = width / 2 - 0.08, depth / 2 - 0.08
    body, top, edge = ("metal", "metal_dark", "gun_light") if metal else ("stuff_deep", "stuff", "stuff_dark")
    s.box(-x + 0.05, 0.05, -z + 0.06, x - 0.05, 0.55, z - 0.04, body)
    s.box(-x, 0, -z + 0.02, x, 0.05, z, edge)                                         # plinth
    s.box(-x, 0.55, -z, x, 0.62, z, edge, top=top)                                    # worktop
    n = int(round(width))
    for i in range(n):                                                                # a door or drawer front per cell
        x0 = -x + 0.10 + i * (2 * x - 0.10) / n
        x1 = x0 + (2 * x - 0.10) / n - 0.10
        s.box(x0, 0.12, -z + 0.035, x1, 0.48, -z + 0.06, edge)
        s.box((x0 + x1) / 2 - 0.04, 0.38, -z + 0.015, (x0 + x1) / 2 + 0.04, 0.41, -z + 0.035, "metal_dark")
    return 0.62


def workbench(kind):
    """3 x 1 cells; whoever works at it stands on the south side."""
    rng = random.Random(sum(ord(c) for c in kind))
    s = Shape()
    metal = kind in ("stove", "machining", "smelter", "electric_tailor", "drug")
    y = bench_base(s, metal=metal)
    if kind in ("stove", "fueled_stove"):
        for x in (-1.0, -0.5):
            s.prism(x, -0.10, 0.15, 0.15, y, y + 0.02, 8, "gun_dark")
            s.prism(x, -0.10, 0.09, 0.09, y + 0.02, y + 0.03, 8, "ember" if x < -0.7 else "metal_dark")
        s.prism(-1.0, -0.10, 0.14, 0.15, y + 0.03, y + 0.20, 8, "metal")              # a pot on the ring
        s.box(-1.22, y + 0.14, -0.12, -0.78, y + 0.17, -0.08, "metal_dark")
        s.box(0.10, y, -0.30, 0.90, y + 0.03, 0.25, "log")                            # chopping board
        s.box(0.95, y, 0.05, 1.30, y + 0.30, 0.38, "metal_dark" if kind == "stove" else "stone")   # flue
        if kind == "fueled_stove":
            s.box(-1.25, 0.14, -0.47, -0.75, 0.40, -0.44, "ember")                    # the fire door
    elif kind == "butcher":
        s.box(-0.90, y, -0.32, 0.30, y + 0.05, 0.30, "log")
        s.box(-0.70, y + 0.05, -0.20, 0.05, y + 0.055, 0.20, "blood")
        s.lump(-0.30, y + 0.05, 0.0, 0.20, 0.14, 0.13, "blood", rng, sides=6, jitter=0.12)
        s.box(0.55, y, -0.05, 0.90, y + 0.015, 0.07, "gun_light")                     # cleaver
        s.box(0.90, y, -0.02, 1.10, y + 0.04, 0.03, "log")
        s.box(0.50, y, 0.18, 1.25, y + 0.45, 0.24, "stuff_dark")                      # rail with hooks
    elif kind in ("tailor", "electric_tailor"):
        for i, mat in enumerate(("cloth_roll", "blanket", "cushion")):
            s.limb((-1.25 + i * 0.26, y + 0.07, -0.30), (-1.25 + i * 0.26, y + 0.07, 0.30), 0.07, 0.07, 6, mat)
        s.box(-0.30, y, -0.25, 0.50, y + 0.015, 0.25, "linen")                        # cloth laid out
        if kind == "electric_tailor":
            s.box(0.70, y, -0.15, 1.20, y + 0.08, 0.15, "gun_white")
            s.box(1.02, y + 0.08, -0.10, 1.18, y + 0.34, 0.10, "gun_white")
            s.box(0.72, y + 0.26, -0.08, 1.18, y + 0.34, 0.08, "gun_white")
        else:
            s.box(0.80, y, -0.10, 1.10, y + 0.02, 0.0, "gun_light")                   # shears
            s.prism(1.15, 0.2, 0.06, 0.06, y, y + 0.10, 6, "book_red")                # pin cushion
    elif kind in ("smithy", "electric_smithy"):
        s.box(-1.30, y, -0.30, -0.55, y + 0.26, 0.30, "stone")                        # the forge
        s.box(-1.20, y + 0.26, -0.20, -0.65, y + 0.29, 0.20, "ember")
        s.box(0.10, y, -0.12, 0.60, y + 0.10, 0.12, "gun_dark")                       # anvil
        s.box(-0.02, y + 0.10, -0.10, 0.72, y + 0.20, 0.10, "gun_dark")
        s.limb((0.95, y + 0.03, -0.20), (1.20, y + 0.03, 0.15), 0.02, 0.02, 4, "log")  # hammer
        s.box(1.14, y, 0.08, 1.28, y + 0.08, 0.20, "gun_metal")
    elif kind == "machining":
        s.box(-1.25, y, -0.20, -0.20, y + 0.10, 0.25, "gun_metal")                    # lathe bed
        s.box(-1.25, y + 0.10, -0.15, -0.90, y + 0.34, 0.20, "gun_dark")
        s.limb((-0.90, y + 0.22, 0.02), (-0.30, y + 0.22, 0.02), 0.05, 0.05, 6, "gun_light")
        s.box(0.30, y, -0.15, 0.60, y + 0.16, 0.10, "gun_dark")                       # vice
        s.box(0.85, y, -0.25, 1.25, y + 0.20, 0.25, "gun_olive")                      # tool box
    elif kind == "stonecutter":
        s.box(-0.95, y, -0.28, -0.15, y + 0.30, 0.28, "stone")                        # a block being cut
        s.box(-0.56, y + 0.10, -0.32, -0.53, y + 0.42, 0.32, "gun_light")             # the saw in its cut
        for _ in range(6):
            s.lump(rng.uniform(0.1, 1.2), y, rng.uniform(-0.3, 0.3), 0.06, 0.05, 0.06, "stone", rng, sides=5, jitter=0.2)
        s.limb((0.70, y + 0.02, -0.25), (1.15, y + 0.02, -0.05), 0.018, 0.018, 4, "log")
    elif kind == "brewery":
        s.loft([((-0.95, y, 0), 0.20, 0.20), ((-0.95, y + 0.20, 0), 0.25, 0.25), ((-0.95, y + 0.42, 0), 0.20, 0.20)], 8, "log")
        for h in (0.07, 0.34):
            s.prism(-0.95, 0, 0.245, 0.245, y + h, y + h + 0.03, 8, "metal_dark")
        s.prism(0.0, 0.0, 0.20, 0.22, y, y + 0.26, 8, "metal")                        # the copper
        s.prism(0.85, 0.05, 0.10, 0.07, y, y + 0.28, 6, "cloth_roll")                 # sack of hops
    elif kind == "drug":
        for i, (x, h) in enumerate(((-1.10, 0.20), (-0.85, 0.28), (-0.60, 0.16), (0.70, 0.24))):
            s.prism(x, 0.05, 0.06, 0.035, y, y + h, 6, ("charge", "leaf_poplar", "petal_pink", "charge")[i])
        s.box(-0.25, y, -0.20, 0.35, y + 0.10, 0.20, "gun_white")                     # scales
        s.box(0.95, y, -0.20, 1.25, y + 0.32, 0.20, "gun_white")
    elif kind == "sculpting":
        s.lump(-0.55, y, 0.0, 0.26, 0.56, 0.24, "stone", rng, sides=7, jitter=0.16)   # a figure emerging from the block
        s.lump(-0.55, y + 0.50, 0.0, 0.13, 0.20, 0.13, "stone", rng, sides=6, jitter=0.10)
        s.limb((0.40, y + 0.02, -0.20), (0.80, y + 0.02, 0.0), 0.018, 0.018, 4, "gun_light")
        s.box(0.95, y, -0.05, 1.20, y + 0.08, 0.10, "log")                            # mallet
    elif kind == "smelter":
        s.box(-1.30, y, -0.38, 0.30, y + 0.62, 0.38, "gun_dark")
        s.box(-0.95, y + 0.10, -0.40, -0.05, y + 0.42, -0.38, "ember")
        s.prism(-0.50, 0.12, 0.13, 0.11, y + 0.62, y + 1.05, 6, "metal_dark")
        s.box(0.60, y, -0.25, 1.25, y + 0.10, 0.25, "gun_metal")                      # ingots cooling
    return s


def research_bench():
    """3 x 2 cells: a broad desk with books, papers and instruments."""
    s = Shape()
    y = bench_base(s, width=3.0, depth=2.0)
    for i, mat in enumerate(("book_red", "book_blue", "book_red", "leaf_pine")):
        s.box(-1.25 + i * 0.09, y, 0.55, -1.18 + i * 0.09, y + 0.30, 0.80, mat)
    s.box(-0.70, y, 0.20, -0.25, y + 0.06, 0.55, "book_blue")
    s.box(-0.67, y + 0.06, 0.23, -0.28, y + 0.075, 0.52, "paper")
    for x, z in ((0.05, -0.30), (0.35, -0.10), (-0.10, 0.05)):
        s.box(x, y, z, x + 0.24, y + 0.008, z + 0.32, "paper")
    s.box(0.85, y, 0.25, 1.20, y + 0.05, 0.60, "gun_dark")                             # microscope
    s.limb((1.02, y + 0.05, 0.50), (1.02, y + 0.34, 0.40), 0.035, 0.035, 5, "gun_dark")
    s.limb((1.02, y + 0.36, 0.42), (1.02, y + 0.20, 0.30), 0.045, 0.03, 6, "gun_light")
    s.prism(0.95, -0.55, 0.07, 0.04, y, y + 0.22, 6, "charge")                         # flask
    return s


def shelf(cells):
    """An open rack 1 cell deep and 1 or 2 wide. Whatever is stored on it rests on the top board."""
    s = Shape()
    x, z = cells / 2 - 0.07, 0.40
    for px in (-x, x - 0.06):
        for pz in (-z, z - 0.06):
            s.box(px - 0.006, 0, pz - 0.006, px + 0.066, 0.60, pz + 0.066, "stuff_dark")   # proud of the boards, so no faces share a plane
    for y in (0.10, 0.34, 0.56):
        s.box(-x, y, -z, x, y + 0.04, z, "stuff", top="stuff")
    s.box(-x + 0.10, 0.14, -0.25, -x + 0.40, 0.30, 0.20, "cloth_roll")                 # a crate and a sack on the lower boards
    s.prism(x - 0.25, 0.0, 0.12, 0.09, 0.38, 0.54, 6, "linen")
    return s


def hydroponics():
    """1 x 4 cells: a raised trough of growing medium on short legs, with a pipe along one side."""
    s = Shape()
    s.box(-0.44, 0.10, -1.94, 0.44, 0.34, 1.94, "gun_metal")
    s.box(-0.36, 0.34, -1.86, 0.36, 0.355, 1.86, "water_dark")
    for z in (-1.7, -0.6, 0.6, 1.7):
        s.box(-0.40, 0, z - 0.06, 0.40, 0.10, z + 0.06, "gun_dark")
    s.limb((0.47, 0.22, -1.90), (0.47, 0.22, 1.90), 0.035, 0.035, 5, "gun_light")
    s.box(-0.30, 0.10, 1.94, 0.30, 0.42, 2.0, "gun_dark")                              # the pump
    return s


def sun_lamp():
    s = Shape()
    s.prism(0, 0, 0.26, 0.20, 0, 0.08, 8, "gun_dark")
    s.prism(0, 0, 0.045, 0.045, 0.08, 1.50, 6, "gun_light")
    s.prism(0, 0, 0.10, 0.40, 1.50, 1.74, 10, "gun_metal", top="glow")                 # the reflector, lit inside
    s.prism(0, 0, 0.12, 0.05, 1.74, 1.84, 8, "glow")
    return s


def sarcophagus():
    """1 x 2 cells: a stone coffin with a ridged lid."""
    s = Shape()
    s.box(-0.40, 0, -0.92, 0.40, 0.08, 0.92, "stuff_deep")
    s.box(-0.34, 0.08, -0.86, 0.34, 0.42, 0.86, "stuff_dark")
    s.box(-0.38, 0.42, -0.90, 0.38, 0.49, 0.90, "stuff")
    s.loft([((0, 0.49, -0.84), 0.30, 0.0), ((0, 0.56, -0.60), 0.26, 0.05), ((0, 0.56, 0.60), 0.26, 0.05), ((0, 0.49, 0.84), 0.30, 0.0)], 4, "stuff")
    s.box(-0.10, 0.60, 0.20, 0.10, 0.63, 0.26, "stuff_dark")
    s.box(-0.03, 0.60, -0.10, 0.03, 0.63, 0.50, "stuff_dark")
    return s


def barrel():
    s = Shape()
    s.loft([((0, 0, 0), 0.26, 0.26), ((0, 0.36, 0), 0.34, 0.34), ((0, 0.72, 0), 0.26, 0.26)], 10, "log", cap_start=False)
    for y in (0.08, 0.34, 0.60):
        r = 0.275 if y != 0.34 else 0.345
        s.prism(0, 0, r, r, y, y + 0.04, 10, "metal_dark")
    s.prism(0, 0, 0.05, 0.05, 0.72, 0.76, 6, "log_burnt")                               # the bung
    return s


# ---------------------------------------------------------------------------- what uses what

SHAPES = {}


def add(name, shape):
    SHAPES[name] = shape
    return name


# Each entry: things or category it applies to, the model(s), and options.
#   surface      where the game's own moving parts and a pawn lying on the thing are drawn;
#                None = the top of the model, 0 = on the ground
#   random       give each one a random turn so neighbours do not line up
#   jitter       vary the size of each one by this fraction
#   grow         scale with how grown a plant is
#   flat         tip the model onto its side when it lies on the ground (weapons)
ENTRIES = []


def use(models, things=(), category=None, surface=None, random_turn=False, jitter=0.0, grow=False, flat=False, turn=0.0,
        scale=1.0, scatter=0.0, sprite_tint=False, fallback=None, wall=None, along_run=False, when_full=False, shadow=True,
        outline=1.0, linked=False, size=None, match=None, top=None, top_height=None, categories=()):
    """wall: fixed to a wall, at this fraction of the wall's height.  along_run: turned to follow the row it is part of.
    when_full: the second model is used once the thing holds something.  shadow=False: no shading on the ground under it.
    outline: how bold the dark outline is (1 = usual).  linked: the first model stands in the cell and the second is
    added once toward each neighbour it joins up with (fences).  size: the footprint (x, z) in cells the model was built
    for; the mod stretches it to the thing's real size.  match: name fragments, for things known only roughly by name.
    top, top_height: a turret's turning gun and the height of its pivot.  categories: several categories at once."""
    for extra in categories:
        use(models, category=extra, surface=surface, random_turn=random_turn, jitter=jitter, grow=grow, flat=flat, turn=turn,
            scale=scale, scatter=scatter, sprite_tint=sprite_tint, shadow=shadow, outline=outline, size=size)
    ENTRIES.append(dict(models=list(models), things=list(things), category=category, surface=surface,
                        random_turn=random_turn, jitter=jitter, grow=grow, flat=flat, turn=turn, scale=scale,
                        scatter=scatter, sprite_tint=sprite_tint, fallback=fallback, wall=wall, along_run=along_run,
                        when_full=when_full, shadow=shadow, outline=outline, linked=linked, size=size,
                        match=list(match) if match else None, top=top, top_height=top_height))


# furniture
use([add("bed", bed(1))], ["Bed"], surface=0.40, turn=180)             # the game's "north" for a bed is its foot
use([add("bed_double", bed(2))], ["DoubleBed"], surface=0.40, turn=180)
use([add("table_1x2", table(1, 2))], ["Table1x2c"])
use([add("table_2x2", table(2, 2))], ["Table2x2c"])
use([add("table_2x4", table(2, 4))], ["Table2x4c"])
use([add("table_3x3", table(3, 3))], ["Table3x3c"])
use([add("stool", stool())], ["Stool"])
use([add("dining_chair", chair(0.28, 0.36, 0.98, False))], ["DiningChair"])
use([add("armchair", chair(0.38, 0.32, 0.92, True))], ["Armchair"])
use([add("torch_lamp", torch_lamp())], ["TorchLamp"], surface=0.0)
use([add("standing_lamp", standing_lamp())], ["StandingLamp"])
use([add("campfire", campfire())], ["Campfire"], surface=0.0)
use([add("end_table", end_table())], ["EndTable"])
use([add("dresser", dresser())], ["Dresser"])
use([add("plant_pot", plant_pot())], ["PlantPot"])
use([add("battery", battery())], ["Battery"], surface=0.0)
use([add("heater", heater())], ["Heater"])
use([add("solar_generator", solar_generator())], ["SolarGenerator"], surface=0.0)
use([add("wind_turbine", wind_turbine())], ["WindTurbine"], surface=0.0, turn=180)
add("wind_rotor", wind_rotor())                                         # drawn turning by the mod's code
use([add("sandbags_%d" % i, sandbags(i)) for i in (1, 2, 3)], ["Sandbags"], surface=0.52, along_run=True)
use([add("grave_open", grave(False)), add("grave_full", grave(True))], ["Grave"], surface=0.0, turn=180, when_full=True)
use([add("wall_torch", wall_light("torch"))], ["TorchWallLamp"], surface=0.0, wall=0.48, shadow=False)
use([add("wall_lamp", wall_light("lamp"))], ["WallLamp"], surface=0.0, wall=0.52, shadow=False)
use([add("fence_post", fence_post()), add("fence_arm", fence_arm())], ["Fence"], surface=0.0, linked=True)
add("gate_leaf", gate_leaf())                                           # fence gates are doors; drawn by the mod's door code
add("gate_posts", gate_posts())
use([add("geyser", geyser())], ["SteamGeyser"], surface=0.0, shadow=False)
add("fx_flame", fx_flame(False))                                        # moving parts of fires, smoke and steam
add("fx_flame_core", fx_flame(True))
add("fx_puff", fx_puff())
for _kind, _things in (("stove", ["ElectricStove"]), ("fueled_stove", ["FueledStove"]), ("butcher", ["TableButcher"]),
                       ("tailor", ["HandTailoringBench"]), ("electric_tailor", ["ElectricTailoringBench"]),
                       ("smithy", ["FueledSmithy"]), ("electric_smithy", ["ElectricSmithy"]), ("machining", ["TableMachining"]),
                       ("stonecutter", ["TableStonecutter"]), ("brewery", ["Brewery"]), ("drug", ["DrugLab"]),
                       ("sculpting", ["TableSculpting"]), ("smelter", ["ElectricSmelter"])):
    use([add("bench_" + _kind, workbench(_kind))], _things, surface=0.62)
use([add("bench_research", research_bench())], ["SimpleResearchBench"], surface=0.62)
use([add("shelf_small", shelf(1))], ["ShelfSmall"], surface=0.60)
use([add("shelf", shelf(2))], ["Shelf"], surface=0.60)
use([add("hydroponics", hydroponics())], ["HydroponicsBasin"], surface=0.34)
use([add("sun_lamp", sun_lamp())], ["SunLamp"], surface=0.0)
use([add("sarcophagus", sarcophagus())], ["Sarcophagus"], surface=0.0)
use([add("barrel", barrel())], ["FermentingBarrel"], surface=0.0)

# colonists: parts only, put together and coloured by the mod's code
for _build in BUILDS:
    add("person_%s_lower" % _build, body_part(_build, 0.0, WAIST))
    add("person_%s_upper" % _build, body_part(_build, WAIST - 0.01, 0.74))
    add("person_%s_coat_short" % _build, body_part(_build, 0.24, 0.70, grow=1.09, pad=0.012, collar=True))
    add("person_%s_coat_long" % _build, body_part(_build, 0.06, 0.70, grow=1.09, pad=0.012, flare=1.10, collar=True))
add("person_head", head_shell())
add("person_face", person_face())
add("person_visor", person_visor())
add("person_pads", shoulder_pads())
for _kind in ("short", "medium", "long", "afro", "mohawk", "ponytail", "bun", "spiky"):
    add("person_hair_" + _kind, person_hair(_kind))
for _kind in ("full", "goatee"):
    add("person_beard_" + _kind, person_beard(_kind))
for _kind in ("cap", "brim", "tall", "helmet", "fullhelm", "hood"):
    add("person_hat_" + _kind, person_hat(_kind))
for _build in BUILDS:
    for _kind in ("flakvest", "flakjacket", "flakpants", "plate", "marine", "cataphract", "recon"):
        add("person_%s_armor_%s" % (_build, _kind), worn_armour(_build, _kind))
for _kind in ("axe", "pickaxe", "hammer", "scythe", "hoe", "broom", "knife"):
    add("tool_" + _kind, tool(_kind))
for _kind in ("combat", "marine_helm", "cataphract_helm", "recon_helm"):
    add("person_hat_" + _kind, armour_helmet(_kind))
use([add("wood_fired_generator", wood_fired_generator())], ["WoodFiredGenerator"], surface=0.0)
use([add("column", column())], ["Column"])

# rocks
use([add("boulder_%d" % i, boulder(i)) for i in range(1, 7)], category="StoneChunks", random_turn=True, jitter=0.15, scale=1.15)
use([add("slag_%d" % i, slag(i)) for i in range(1, 3)], ["ChunkSlagSteel"], random_turn=True, jitter=0.12)

# ranged weapons
G = dict(flat=True, turn=-18.0)
use([add("revolver", gun(recv=0.16, h=0.07, barrel=0.14, stock=0, wood=True))], ["Gun_Revolver"], **G)
use([add("pistol", gun(recv=0.20, h=0.07, barrel=0.05, stock=0, wood=False, mag=0.02))], ["Gun_Autopistol"], **G)
use([add("machine_pistol", gun(recv=0.22, h=0.08, barrel=0.07, stock=0, wood=False, mag=0.14))], ["Gun_MachinePistol"], **G)
use([add("smg", gun(recv=0.30, h=0.08, barrel=0.12, stock=0.16, wood=False, mag=0.15))], ["Gun_HeavySMG"], **G)
use([add("shotgun", gun(recv=0.28, h=0.07, barrel=0.36, bt=0.04, stock=0.24))], ["Gun_PumpShotgun"], **G)
use([add("chain_shotgun", gun(recv=0.32, h=0.09, barrel=0.26, bt=0.045, stock=0.2, wood=False, mag=0.12, fat=1.3))], ["Gun_ChainShotgun"], **G)
use([add("bolt_rifle", gun(recv=0.30, h=0.065, barrel=0.40, stock=0.28))], ["Gun_BoltActionRifle"], **G)
use([add("assault_rifle", gun(recv=0.34, h=0.08, barrel=0.26, stock=0.22, wood=False, mag=0.14))], ["Gun_AssaultRifle"], **G)
use([add("sniper_rifle", gun(recv=0.32, h=0.07, barrel=0.50, stock=0.26, wood=False, scope=True, mag=0.06))], ["Gun_SniperRifle"], **G)
use([add("lmg", gun(recv=0.40, h=0.09, barrel=0.34, bt=0.035, stock=0.22, wood=False, mag=0.11, fat=1.3, bipod=True))], ["Gun_LMG"], **G)
use([add("minigun", gun(recv=0.30, h=0.14, barrel=0.44, bt=0.09, stock=0, wood=False, mag=0.12, fat=2.0))], ["Gun_Minigun"], **G)
use([add("charge_rifle", gun(recv=0.44, h=0.09, barrel=0.18, stock=0.2, wood=False, body="gun_white", accent="charge", mag=0.08))], ["Gun_ChargeRifle"], **G)
use([add("charge_lance", gun(recv=0.50, h=0.08, barrel=0.34, bt=0.04, stock=0.16, wood=False, body="gun_white", accent="charge"))], ["Gun_ChargeLance"], **G)
use([add("launcher", tube(0.5, 0.05))], ["Gun_IncendiaryLauncher", "Gun_EmpLauncher", "Gun_SmokeLauncher"], **G)
use([add("rocket_launcher", tube(0.75, 0.075, warhead="warning"))], ["Gun_TripleRocket", "Gun_DoomsdayRocket"], **G)
use([add("bow_short", bow(0.62))], ["Bow_Short"], **G)
use([add("bow_recurve", bow(0.78))], ["Bow_Recurve"], **G)
use([add("bow_great", bow(0.98))], ["Bow_Great"], **G)
use([add("pila", pole(0.8, "spear"))], ["Pila"], **G)
use([add("grenade", grenade())], ["Weapon_GrenadeFrag", "Weapon_GrenadeEMP"], **G)
use([add("molotov", grenade(body="gun_wood", band="warning"))], ["Weapon_GrenadeMolotov"], **G)

# melee weapons
use([add("club", pole(0.5, "club"))], ["MeleeWeapon_Club"], **G)
use([add("knife", blade(grip=0.10, guard=0.03, length=0.18, width=0.04))], ["MeleeWeapon_Knife"], **G)
use([add("ikwa", pole(0.45, "broad"))], ["MeleeWeapon_Ikwa"], **G)
use([add("gladius", blade(grip=0.12, guard=0.05, length=0.38, width=0.06))], ["MeleeWeapon_Gladius"], **G)
use([add("spear", pole(1.0, "spear"))], ["MeleeWeapon_Spear"], **G)
use([add("mace", pole(0.5, "mace"))], ["MeleeWeapon_Mace"], **G)
use([add("longsword", blade(grip=0.16, guard=0.07, length=0.62, width=0.055))], ["MeleeWeapon_LongSword"], **G)
use([add("axe", pole(0.6, "axe"))], ["MeleeWeapon_Axe", "MeleeWeapon_BreachAxe"], **G)
use([add("warhammer", pole(0.7, "hammer"))], ["MeleeWeapon_Warhammer"], **G)

# anything else in these groups, including weapons from DLC and other mods
use(["assault_rifle"], category="WeaponsRanged", **G)
use(["gladius"], category="WeaponsMelee", **G)
use(["grenade"], category="Grenades", **G)

# clothing lying on the ground, by kind
use([add("garment_1", garment(1)), add("garment_2", garment(2))], category="Apparel")
use(["garment_1", "garment_2"], category="ApparelNoble")
use([add("hat", hat())], category="Headgear")
use([add("helmet", helmet())], category="ArmorHeadgear")
use([add("vest", vest())], category="ApparelArmor")
use([add("pack", pack())], category="ApparelUtility")

# trees
T = dict(random_turn=True, jitter=0.12, grow=True, surface=0.0, outline=0.55)
use([add("tree_oak_%d" % i, tree_broadleaf(i, "leaf_oak", trunk_r=0.095, spread=0.33, crown_r=0.26)) for i in (1, 2, 3)], ["Plant_TreeOak"], **T)
use([add("tree_maple_%d" % i, tree_broadleaf(10 + i, "leaf_maple", trunk_r=0.07, spread=0.26, crown_r=0.25, rise=0.95, top=1.05)) for i in (1, 2)],
    ["Plant_TreeMaple"], **T)
use([add("tree_teak_%d" % i, tree_broadleaf(20 + i, "leaf_teak", trunk_h=0.60, trunk_r=0.06, spread=0.22, crown_r=0.20, rise=0.90, top=1.12)) for i in (1, 2)],
    ["Plant_TreeTeak"], **T)
use([add("tree_cecropia_%d" % i, tree_cecropia(30 + i, "leaf_jungle")) for i in (1, 2)], ["Plant_TreeCecropia"], **T)
use([add("tree_cocoa", tree_broadleaf(35, "leaf_jungle", trunk_h=0.30, trunk_r=0.05, spread=0.22, crown_r=0.19, boughs=3, top=0.78, pods="pod"))],
    ["Plant_TreeCocoa"], **T)
use([add("tree_drago", tree_umbrella(41, "leaf_drago"))], ["Plant_TreeDrago"], **T)
use([add("tree_anima", tree_anima(51, "leaf_anima"))], ["Plant_TreeAnima"], **T)
use([add("tree_gauranlen", tree_broadleaf(61, "leaf_gauranlen", bark="bark_pale", trunk_r=0.11, spread=0.34, crown_r=0.27, boughs=5, pods="pod_pale"))],
    ["Plant_TreeGauranlen"], **T)
use([add("tree_birch_%d" % i, tree_birch(70 + i, "leaf_birch")) for i in (1, 2)], ["Plant_TreeBirch"], **T)
use([add("tree_poplar_%d" % i, tree_column(80 + i, "leaf_poplar")) for i in (1, 2)], ["Plant_TreePoplar"], **T)
use([add("tree_cypress", tree_column(91, "leaf_cypress", radii=(0.13, 0.16, 0.15, 0.12, 0.08), top=1.12, clear=0.14))], ["Plant_TreeCypress"], **T)
use([add("tree_pine_%d" % i, tree_conifer(95 + i, "leaf_pine")) for i in (1, 2)], ["Plant_TreePine"], **T)
use([add("tree_willow_%d" % i, tree_willow(100 + i, "leaf_willow")) for i in (1, 2)], ["Plant_TreeWillow"], **T)
use([add("tree_palm_%d" % i, tree_palm(105 + i, "leaf_jungle")) for i in (1, 2)], ["Plant_TreePalm"], **T)
use([add("tree_cactus", tree_cactus())], ["Plant_SaguaroCactus"], **T)
use([add("tree_bamboo_%d" % i, tree_bamboo(110 + i)) for i in (1, 2)], ["Plant_TreeBamboo"], **T)

# grass, wild plants and crops
#   scatter   move each plant up to this far (in cells) from the middle of its cell
P = dict(random_turn=True, jitter=0.18, grow=True, surface=0.0, scatter=0.5, shadow=False)
C = dict(random_turn=True, jitter=0.10, grow=True, surface=0.0, scatter=0.16, shadow=False)
use([add("grass_%d" % i, grass_card(200 + i)) for i in range(1, 5)], ["Plant_Grass"], **dict(P, outline=0.0))
use([add("tall_grass_%d" % i, grass_card(210 + i, tall=True)) for i in range(1, 4)], ["Plant_TallGrass"], **dict(P, outline=0.0))
use([add("bush_%d" % i, bush(220 + i)) for i in (1, 2, 3)], ["Plant_Bush"], **P)
use([add("berry_bush_%d" % i, bush(230 + i, mat="shrub_dark", fruit="berry")) for i in (1, 2)], ["Plant_Berry"], **P)
use([add("bramble_%d" % i, bramble(240 + i)) for i in (1, 2)], ["Plant_Brambles"], **P)
use([add("moss_%d" % i, moss(250 + i)) for i in (1, 2)], ["Plant_Moss"], **P)
use([add("dandelion_%d" % i, flower(260 + i, "petal_yellow", n=4)) for i in (1, 2)], ["Plant_Dandelion"], **P)
use([add("astragalus_%d" % i, flower(270 + i, "petal_pink")) for i in (1, 2)], ["Plant_Astragalus"], **P)
use([add("daylily", flower(281, "petal_orange", n=4))], ["Plant_Daylily", "Plant_Clivia"], **P)
use([add("rose", flower(291, "petal_red", n=4))], ["Plant_Rose"], **P)
use([add("agave_%d" % i, rosette(300 + i)) for i in (1, 2)], ["Plant_Agave"], **P)
use([add("alocasia", rosette(311, mat="crop_leaf"))], ["Plant_Alocasia"], **P)
use([add("round_cactus", round_cactus())], ["Plant_PincushionCactus"], **P)
use([add("healroot_%d" % i, leafy_crop(320 + i, mat="crop_pale", height=0.24, petal="petal_white")) for i in (1, 2)],
    ["Plant_Healroot", "Plant_HealrootWild"], **C)
use([add("potato_%d" % i, leafy_crop(330 + i)) for i in (1, 2)], ["Plant_Potato"], **C)
use([add("strawberry_%d" % i, leafy_crop(340 + i, fruit="fruit_red", height=0.22)) for i in (1, 2)], ["Plant_Strawberry"], **C)
use([add("smokeleaf", leafy_crop(351, height=0.46))], ["Plant_Smokeleaf"], **C)
use([add("psychoid", leafy_crop(361, mat="crop_pale", height=0.40, petal="petal_white"))], ["Plant_Psychoid"], **C)
use([add("rice_%d" % i, grass(370 + i, tall=True, mats=("rice_a", "blade_a"))) for i in (1, 2)], ["Plant_Rice"], **C)
use([add("haygrass_%d" % i, grass(380 + i, tall=True, mats=("hay_a", "hay_b"))) for i in (1, 2)], ["Plant_Haygrass"], **C)
use([add("corn_%d" % i, stalk_crop(390 + i, 0.9, cob="corn")) for i in (1, 2)], ["Plant_Corn"], **C)
use([add("cotton", stalk_crop(401, 0.5, top="cotton"))], ["Plant_Cotton"], **C)
use([add("hops", stalk_crop(411, 0.8, top="crop_pale"))], ["Plant_Hops"], **C)
use([add("devilstrand", mushrooms(421, "cap_red"))], ["Plant_Devilstrand"], **C)
use([add("glow_mushroom", mushrooms(431, "cap_glow"))], ["Plant_Agarilux", "Plant_Bryolux", "Glowstool"], **C)

# every other plant that is not a tree
use([add("herb_%d" % i, herb(440 + i)) for i in (1, 2, 3)], fallback="SmallPlants", sprite_tint=True, **P)

# door parts are drawn directly by the mod and need no entry
add("door_leaf", door_leaf())
add("door_lintel", door_lintel())

# Things without a model whose automatic shape needs a nudge: ThingDef name -> height in cells,
# or None to keep it flat.
OVERRIDES = {
    "SleepingSpot": None,
    "DoubleSleepingSpot": None,
    "AnimalSleepingSpot": None,
    "CraftingSpot": None,
    "ButcherSpot": None,
    "PartySpot": None,
    "MarriageSpot": None,
    "CaravanPackingSpot": None,
    "RitualSpot": None,
    "MeditationSpot": None,
}


# The rest of the furniture, machines, items, ruins and wrecks live in their own file.
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "models_more.py")).read())


# ---------------------------------------------------------------------------- animals
# Every animal is two models: a body (trunk, neck, head, ears, horns, tail) facing north, and
# one leg. The game draws the body and a copy of the leg at each hip, and swings the legs as
# the animal walks. Colours are plain, as on the grass and crops, so a herd stays cheap.
# Sizes are given as fractions of the body length L (in cells), so a species is a short list
# of proportions.

MATERIALS["an_dark"] = ((0.11, 0.10, 0.10), None)      # eyes and noses
MATERIALS["an_horn"] = ((0.85, 0.81, 0.69), None)
MATERIALS["an_hoof"] = ((0.21, 0.18, 0.16), None)

ANIMALS = []


def shade(c, k):
    return tuple(max(0.0, min(1.0, v * k)) for v in c)


def paint(name, **colours):
    """Registers one animal's plain-colour materials and returns their names by role."""
    out = {}
    for role, colour in colours.items():
        if colour is not None:
            mat = "an_%s_%s" % (name, role)
            MATERIALS[mat] = (tuple(colour), None)
            out[role] = mat
    return out


def true_size(L):
    """Big animals are drawn a little under life size next to the colonists; small ones are left
    alone so they can still be seen."""
    return L * (0.80 + 0.20 * max(0.0, min(1.0, (0.75 - L) / 0.40)))


def leg_shape(length, half, mat, feet):
    """One leg, standing on the ground with its hip at the top."""
    s = Shape()
    foot = "an_hoof" if feet == "hoof" else mat
    thin = 0.8 if feet != "bird" else 1.0
    s.loft([((0, 0, 0), half * 0.9, half * 0.9), ((0, length * 0.14, 0), half * 0.9, half * 0.9),
            ((0, length * 0.52, 0), half * thin, half * thin), ((0, length, 0), half * 1.3, half * 1.3)],
           5 if feet != "bird" else 4, mat, mats=[foot, mat, mat], cap_start=False)
    if feet == "paw":
        s.box(-half * 0.95, 0, 0, half * 0.95, half * 0.9, half * 2.0, mat)
    elif feet == "bird":
        s.box(-half * 2.2, 0, -half * 1.2, half * 2.2, half * 0.7, half * 3.6, mat)
    return s


def creature(name, things, L, col, w=0.40, h=0.44, leg=0.50, legw=0.11, chest=1.06, rump=0.94, sag=0.0,
             neck=0.30, neck_up=45, neckw=0.20, head=0.34, headw=0.24, headh=0.24, snout=0.55, head_tilt=-18,
             ears=("point", 0.10), horns=None, tail=("thin", 0.3), feet="paw", legs=4, legz=(0.30, -0.33),
             splay=0, swing=26, belly=None, headcol=None, legcol=None, acc=None, muzzle=None, tailcol=None,
             beak=None, extras=(), sides=8):
    """Builds one animal. Lengths are fractions of L unless they say otherwise; angles are degrees.
    ears, horns and tail are (kind, size); extras is a list of (kind, ...) add-ons."""
    L = true_size(L)
    # The game draws its animals chunky and a little toy-like: big heads, round bodies and
    # short, sturdy legs. The proportions given for each species are pushed that way here.
    head, headw, headh = head * 1.24, headw * 1.30, headh * 1.28
    w, h = w * 1.15, h * 1.10
    leg, legw = leg * 0.80, legw * 1.34
    neck, neckw = neck * 0.80, neckw * 1.16
    rng = random.Random(sum(ord(ch) for ch in name) * 7 + 3)
    m = paint(name, body=col, belly=belly, head=headcol or col, leg=legcol or shade(col, 0.84), acc=acc,
              muzzle=muzzle, tail=tailcol, beak=beak[1] if beak else None)
    body_mat, head_mat = m["body"], m["head"]
    acc_mat = m.get("acc", "an_dark")
    s = Shape()

    yc = (leg + h / 2) * L                               # height of the middle of the trunk
    s.loft([((0, yc + 0.02 * L, -0.50 * L), w * 0.34 * L, h * 0.36 * L),
            ((0, yc, -0.36 * L), w * 0.5 * rump * L, h * 0.5 * rump * L),
            ((0, yc - sag * L, 0.0), w * 0.5 * L, h * 0.5 * L),
            ((0, yc + 0.01 * L, 0.32 * L), w * 0.5 * chest * L, h * 0.5 * chest * L),
            ((0, yc + 0.05 * L, 0.50 * L), w * 0.36 * L, h * 0.38 * L)], sides, body_mat, under=m.get("belly"))

    # neck and head
    nu = math.radians(neck_up)
    nd = (0.0, math.sin(nu), math.cos(nu))
    nb = (0.0, yc + h * 0.20 * L, 0.40 * L)
    nt = along(nb, nd, neck * L)
    s.loft([(along(nb, nd, -0.10 * L), neckw * 0.66 * L, neckw * 0.74 * L), (nt, neckw * 0.46 * L, neckw * 0.52 * L)],
           6, m.get("neck", body_mat), under=m.get("belly"))

    ht = math.radians(head_tilt)
    hd = (0.0, math.sin(ht), math.cos(ht))
    hup = (0.0, math.cos(ht), -math.sin(ht))
    HL = head * L
    h0 = add3(along(nt, hd, -0.20 * HL), (0.0, headh * 0.10 * L, 0.0))

    def hp(t, lift=0.0, side=0.0):
        """A point on the head: t along it from the back of the skull, lift up from its middle line."""
        return add3(add3(along(h0, hd, t * HL), mul3(hup, lift * headh * L)), (side * headw * L, 0.0, 0.0))

    hw, hh = headw * 0.5 * L, headh * 0.5 * L
    if beak:
        s.loft([(hp(-0.04), hw * 0.6, hh * 0.66), (hp(0.26), hw, hh), (hp(0.62), hw * 0.66, hh * 0.7)], 6, head_mat)
        s.loft([(hp(0.56, -0.06), hw * 0.50, hh * 0.38), (hp(0.60 + beak[0], -0.14), 0, 0)], 4, m["beak"])
    else:
        muzzle_mat = m.get("muzzle", head_mat)
        s.loft([(hp(-0.04), hw * 0.6, hh * 0.68), (hp(0.22), hw, hh),
                (hp(0.56, -0.04), hw * (0.45 + 0.55 * snout), hh * (0.5 + 0.5 * snout)),
                (hp(0.96, -0.10), hw * snout, hh * snout * 0.9),
                (hp(1.03, -0.10), hw * snout * 0.78, hh * snout * 0.70)],
               6, head_mat, mats=[head_mat, head_mat, muzzle_mat, "an_dark"])

    e = max(0.016, 0.062 * HL)                             # big, simple, dark eyes
    for sx in (-1, 1):
        c = hp(0.36, 0.12, sx * 0.47)
        s.box(c[0] - e * 0.5, c[1] - e * 1.15, c[2] - e, c[0] + e * 0.5, c[1] + e * 1.15, c[2] + e, "an_dark")

    if ears:
        kind, es = ears[0], ears[1] * L
        ear_mat = m.get("acc") if len(ears) > 2 else head_mat
        for sx in (-1, 1):
            b = hp(0.10, 0.40, sx * 0.30)
            if kind == "point":
                s.limb(b, add3(b, (sx * es * 0.35, es, -es * 0.15)), es * 0.36, 0, 4, ear_mat)
            elif kind == "round":
                s.limb(b, add3(b, (sx * es * 0.35, es * 0.75, 0)), es * 0.46, es * 0.30, 5, ear_mat)
            elif kind == "long":
                s.limb(b, add3(b, (sx * es * 0.22, es, -es * 0.35)), es * 0.20, es * 0.07, 4, ear_mat)
            elif kind == "flop":
                s.limb(b, add3(b, (sx * es * 0.85, -es * 0.50, 0)), es * 0.28, es * 0.14, 4, ear_mat)
            elif kind == "plate":
                s.loft([(b, 0.02 * L, es * 0.30), (add3(b, (sx * es * 0.55, -es * 0.45, -es * 0.80)), 0.02 * L, es * 0.62)], 4, ear_mat)

    if horns:
        kind, hs = horns[0], horns[1] * L
        horn_mat = "an_horn"
        for sx in (-1, 1):
            a = hp(0.16, 0.46, sx * 0.22)
            if kind == "antler":
                b = add3(a, (sx * 0.35 * hs, 0.55 * hs, -0.25 * hs))
                c = add3(b, (sx * 0.25 * hs, 0.45 * hs, 0.10 * hs))
                s.limb(a, b, 0.055 * hs, 0.045 * hs, 4, horn_mat)
                s.limb(b, c, 0.045 * hs, 0, 4, horn_mat)
                s.limb(b, add3(b, (sx * 0.05 * hs, 0.35 * hs, 0.32 * hs)), 0.04 * hs, 0, 4, horn_mat)
                half = mul3(add3(a, b), 0.5)
                s.limb(half, add3(half, (-sx * 0.04 * hs, 0.26 * hs, 0.30 * hs)), 0.04 * hs, 0, 4, horn_mat)
            elif kind == "curl":
                b = add3(a, (sx * 0.15 * hs, 0.45 * hs, -0.25 * hs))
                c = add3(b, (sx * 0.20 * hs, 0.15 * hs, -0.45 * hs))
                d = add3(c, (sx * 0.10 * hs, -0.28 * hs, -0.30 * hs))
                s.loft([(a, 0.10 * hs, 0.10 * hs), (b, 0.085 * hs, 0.085 * hs), (c, 0.06 * hs, 0.06 * hs), (d, 0, 0)], 4, horn_mat)
            elif kind == "short":
                b = add3(a, (sx * 0.55 * hs, 0.12 * hs, 0))
                c = add3(b, (sx * 0.15 * hs, 0.42 * hs, 0.06 * hs))
                s.loft([(a, 0.10 * hs, 0.10 * hs), (b, 0.08 * hs, 0.08 * hs), (c, 0, 0)], 4, horn_mat)
            elif kind == "straight":
                s.limb(a, add3(a, (sx * 0.12 * hs, 0.95 * hs, -0.30 * hs)), 0.05 * hs, 0, 4, horn_mat)
            elif kind == "tusk":
                a = hp(0.74, -0.30, sx * 0.30 * snout)
                b = add3(a, (sx * 0.10 * hs, -0.35 * hs, 0.42 * hs))
                c = add3(b, (sx * 0.05 * hs, 0.25 * hs, 0.45 * hs))
                s.loft([(a, 0.09 * hs, 0.09 * hs), (b, 0.07 * hs, 0.07 * hs), (c, 0, 0)], 4, horn_mat)
        if kind == "nose":
            a = hp(0.80, 0.25)
            s.limb(a, add3(add3(a, mul3(hd, 0.25 * hs)), mul3(hup, hs)), 0.24 * hs, 0, 5, horn_mat)
            a = hp(0.52, 0.38)
            s.limb(a, add3(a, mul3(hup, 0.45 * hs)), 0.16 * hs, 0, 5, horn_mat)
        elif kind == "thrumbo":
            a = hp(0.40, 0.40)
            s.limb(a, add3(add3(a, mul3(hd, 0.50 * hs)), mul3(hup, 0.90 * hs)), 0.11 * hs, 0, 5, horn_mat)
        elif kind == "casque":
            a = hp(0.30, 0.40)
            s.loft([(a, 0.03 * L, 0.01 * L), (add3(a, mul3(hup, hs)), 0.02 * L, hs * 0.30)], 4, horn_mat)

    if tail:
        kind, tl = tail[0], tail[1] * L
        tail_mat = m.get("tail", body_mat)
        tip_mat = m.get("acc", tail_mat) if len(tail) > 2 else tail_mat
        R = (0.0, yc + h * 0.18 * L, -0.49 * L)

        def tp(dy, dz):
            return add3(R, (0.0, dy * tl, dz * tl))

        if kind == "thin":
            s.limb(R, tp(-0.75, -0.45), 0.022 * L, 0.012 * L, 4, tail_mat)
        elif kind == "tuft":
            s.limb(R, tp(-0.75, -0.40), 0.022 * L, 0.014 * L, 4, tail_mat)
            s.limb(tp(-0.75, -0.40), tp(-1.0, -0.44), 0.034 * L, 0.012 * L, 4, tip_mat)
        elif kind == "hair":
            s.loft([(R, 0.035 * L, 0.035 * L), (tp(-0.35, -0.30), 0.05 * L, 0.05 * L), (tp(-0.95, -0.38), 0.02 * L, 0.02 * L)], 5, tip_mat)
        elif kind == "bushy":
            tw = 0.20 * tl
            s.loft([(R, tw * 0.35, tw * 0.35), (tp(-0.12, -0.45), tw, tw), (tp(-0.30, -0.92), tw * 0.62, tw * 0.62),
                    (tp(-0.34, -1.08), 0, 0)], 6, tail_mat, mats=[tail_mat, tail_mat, tip_mat])
        elif kind == "up":
            tw = 0.22 * tl
            s.loft([(R, tw * 0.4, tw * 0.4), (tp(0.35, -0.35), tw, tw), (tp(0.85, -0.18), tw * 0.9, tw * 0.9),
                    (tp(1.05, 0.12), 0, 0)], 6, tail_mat, mats=[tail_mat, tail_mat, tip_mat])
        elif kind == "stub":
            s.limb(R, tp(0.25, -1.0), 0.05 * L, 0.028 * L, 5, tail_mat)
        elif kind == "long":
            s.loft([(R, 0.03 * L, 0.03 * L), (tp(-0.45, -0.45), 0.026 * L, 0.026 * L), (tp(-0.56, -0.95), 0.022 * L, 0.022 * L),
                    (tp(-0.36, -1.20), 0.016 * L, 0.016 * L)], 5, tail_mat, mats=[tail_mat, tail_mat, tip_mat])
        elif kind == "lizard":
            s.loft([(R, w * 0.26 * L, h * 0.26 * L), (tp(-0.10, -0.50), w * 0.14 * L, h * 0.14 * L), (tp(-0.16, -1.0), 0, 0)], 6, tail_mat)
        elif kind == "feathers":
            s.loft([(R, 0.12 * L, 0.06 * L), (tp(0.22, -1.0), 0.16 * L, 0.025 * L)], 4, tip_mat)
        elif kind == "fan":
            s.loft([(R, 0.10 * L, 0.03 * L), (tp(0.75, -0.35), 0.50 * tl, 0.025 * L)], 6, tip_mat)

    for extra in extras:
        kind = extra[0]
        if kind == "wool":
            k = extra[1]
            s.lump(0, yc - h * 0.50 * L * k, -0.02 * L, w * 0.62 * L * k, h * 1.10 * L * k, 0.56 * L, body_mat, rng,
                   sides=8, jitter=0.09, closed=True)
        elif kind == "hump":
            hz, size = extra[1], extra[2]
            s.lump(0, yc + h * 0.22 * L, hz * L, w * 0.40 * L, size * L, 0.26 * L, m.get("acc", body_mat) if len(extra) > 3 else body_mat,
                   rng, sides=7, jitter=0.08, closed=True)
        elif kind == "mane":
            off = (0.0, neckw * 0.62 * L, -neckw * 0.30 * L)
            s.loft([(add3(nb, off), 0.03 * L, 0.05 * L), (add3(nt, off), 0.03 * L, 0.06 * L)], 4, acc_mat)
        elif kind == "ridge":
            s.loft([((0, yc + h * 0.47 * L, -0.38 * L), 0.025 * L, 0.03 * L), ((0, yc + h * 0.52 * L, 0.36 * L), 0.03 * L, 0.06 * L)], 4, acc_mat)
        elif kind == "boom":
            for z, r in ((-0.26, 0.20), (0.0, 0.25), (0.24, 0.19)):
                s.lump(rng.uniform(-0.03, 0.03) * L, yc + h * 0.18 * L, z * L, r * L, r * 1.5 * L, r * L, acc_mat, rng,
                       sides=7, jitter=0.08, closed=True)
        elif kind == "patches":
            for sx, z, r in ((-1, -0.22, 0.17), (1, 0.14, 0.19), (-1, 0.26, 0.13), (1, -0.30, 0.13)):
                s.lump(sx * w * 0.30 * L, yc - h * 0.12 * L, z * L, w * 0.25 * L, h * 0.60 * L, r * L, acc_mat, rng,
                       sides=6, jitter=0.10, closed=True)
        elif kind == "shell":
            s.lump(0, leg * L * 0.85, 0, w * 0.64 * L, h * 1.25 * L, 0.56 * L, acc_mat, rng, sides=8,
                   profile=((0.0, 1.0), (0.35, 0.92), (0.72, 0.56)), jitter=0.05, closed=True)
        elif kind == "trunk":
            r = hw * snout
            s.loft([(hp(0.90, -0.10), r, r), (hp(1.22, -0.75), r * 0.8, r * 0.8), (hp(1.26, -1.65), r * 0.6, r * 0.6),
                    (hp(1.42, -2.30), r * 0.42, r * 0.42)], 6, head_mat)
        elif kind == "crest":
            for i in range(7):
                z = (0.40 - i * 0.13) * L
                s.limb((0, yc + h * 0.46 * L, z), (0, yc + h * 0.46 * L + 0.09 * L, z - 0.04 * L), 0.035 * L, 0, 3, acc_mat)
        elif kind == "comb":
            c = hp(0.34, 0.50)
            s.box(c[0] - 0.012 * L, c[1], c[2] - 0.30 * HL, c[0] + 0.012 * L, c[1] + 0.26 * headh * L * 1.6, c[2] + 0.24 * HL, acc_mat)
        elif kind == "wattle":
            c = hp(0.62, -0.42)
            s.limb(c, add3(c, (0, -0.55 * headh * L, 0.02 * L)), 0.22 * hw, 0.14 * hw, 4, acc_mat)
        elif kind == "beard":
            c = hp(0.70, -0.42)
            s.limb(c, add3(c, (0, -0.60 * headh * L, -0.04 * L)), 0.20 * hw, 0, 4, acc_mat if len(extra) > 1 else head_mat)
        elif kind == "wings":
            for sx in (-1, 1):
                s.lump(sx * w * 0.47 * L, yc - h * 0.22 * L, -0.06 * L, 0.05 * L, h * 0.55 * L, 0.36 * L,
                       m.get("acc", body_mat) if len(extra) > 1 else body_mat, rng, sides=6, jitter=0.06, closed=True)

    add("animal_" + name, s)
    hip_y = (leg + h * 0.22) * L
    add("animal_%s_leg" % name, leg_shape(hip_y, legw * L / 2, m["leg"], feet))
    hx = w * L * 0.5 * (0.62 if splay == 0 else 0.90)
    if legs == 2:
        rows = [legz[0]]
    elif legs == 4:
        rows = [legz[0], legz[1]]
    else:
        rows = [0.30 - 0.60 * i / (legs // 2 - 1) for i in range(legs // 2)]
    hips = [(sx * hx, hip_y, z * L) for z in rows for sx in (-1, 1)]
    ANIMALS.append(dict(name=name, things=list(things), hips=hips, leg_len=hip_y, centre=yc, half=w * L / 2, length=L * 0.62,
                        stride=max(0.35, hip_y * 2.4), swing=swing, splay=splay))
    return s


def insect(name, things, L, col, legs, parts, legcol=None, head=0.16, acc=None, jaws=True, leg=0.22, legw=0.05, w=0.5):
    """Megaspiders and their kin: a row of rounded segments, a small head and splayed legs.
    parts lists the segments from the back as (middle along the body, length, width, height), fractions of L."""
    L = true_size(L)
    rng = random.Random(sum(ord(ch) for ch in name) * 5 + 1)
    m = paint(name, body=col, leg=legcol or shade(col, 0.7), acc=acc)
    s = Shape()
    y0 = leg * L
    for i, (z, length, width, height) in enumerate(parts):
        mat = m["acc"] if acc and i == 0 else m["body"]
        s.lump(0, y0 - height * L * 0.1, z * L, width * L / 2, height * L, length * L / 2, mat, rng, sides=8,
               profile=((0.0, 0.72), (0.34, 1.0), (0.72, 0.70)), jitter=0.06, closed=True)
    front = max(z + length / 2 for z, length, _, _ in parts)
    hz = (front + head * 0.3) * L
    s.lump(0, y0, hz, head * L * 0.5, head * L * 0.8, head * L * 0.5, m["leg"], rng, sides=6, jitter=0.05, closed=True)
    for sx in (-1, 1):
        s.box(sx * head * L * 0.30 - 0.012 * L, y0 + head * L * 0.45, hz + head * L * 0.25,
              sx * head * L * 0.30 + 0.012 * L, y0 + head * L * 0.45 + 0.03 * L, hz + head * L * 0.25 + 0.03 * L, "an_dark")
        if jaws:
            a = (sx * head * L * 0.22, y0 + head * L * 0.2, hz + head * L * 0.4)
            s.limb(a, add3(a, (-sx * 0.03 * L, -0.02 * L, 0.14 * L)), 0.025 * L, 0, 4, "an_horn")
    add("animal_" + name, s)
    hip_y = y0 + 0.06 * L
    add("animal_%s_leg" % name, leg_shape(hip_y * 1.25, legw * L / 2, m["leg"], "none"))
    rows = [0.26 - 0.50 * i / (legs // 2 - 1) for i in range(legs // 2)]
    hips = [(sx * w * L * 0.42, hip_y, z * L) for z in rows for sx in (-1, 1)]
    ANIMALS.append(dict(name=name, things=list(things), hips=hips, leg_len=hip_y * 1.25, centre=y0 + 0.1 * L, half=w * L / 2, length=L * 0.6,
                        stride=max(0.35, L * 0.6), swing=24, splay=48))


def snake(name, things, L, col, belly, hood):
    """A coiled snake with its head and hood raised. No legs."""
    m = paint(name, body=col, belly=belly, hood=hood)
    s = Shape()
    r = 0.045 * L
    path = []
    for i in range(15):                                     # the coil, winding inward
        a = i * 0.62
        rad = (0.30 - 0.012 * i) * L
        path.append(((rad * math.cos(a), r * 0.95 + 0.0015 * i * L, rad * math.sin(a) - 0.05 * L), r, r * 0.9))
    x, y, z = path[-1][0]
    for k, (dy, dz, hw, hh) in enumerate(((0.10, 0.06, 1.0, 1.0), (0.24, 0.07, 1.3, 0.9), (0.36, 0.10, 2.6, 0.7),
                                           (0.46, 0.15, 2.4, 0.7), (0.52, 0.22, 1.2, 0.9), (0.52, 0.30, 0.9, 0.8), (0.50, 0.36, 0.0, 0.0))):
        path.append(((0.0 + x * max(0, 1 - k * 0.5), dy * L, z + dz * L), r * hw, r * hh))
    mats = [m["body"]] * 16 + [m["hood"], m["hood"], m["body"], m["body"], m["body"]]
    s.loft(path, 6, m["body"], under=m["belly"], mats=mats[:len(path) - 1], cap_start=True, cap_end=False)
    for sx in (-1, 1):
        c = (sx * r * 0.9, 0.53 * L, z + 0.27 * L)
        s.box(c[0] - 0.008 * L, c[1], c[2], c[0] + 0.008 * L, c[1] + 0.018 * L, c[2] + 0.02 * L, "an_dark")
    add("animal_" + name, s)
    ANIMALS.append(dict(name=name, things=list(things), hips=[], leg_len=0.0, centre=r, half=0.3 * L, length=0.36 * L, stride=1.0, swing=0, splay=0))


WHITE, BLACK = (0.92, 0.91, 0.87), (0.17, 0.16, 0.17)
BIRD = dict(legs=2, legz=(-0.04,), feet="bird", w=0.52, h=0.54, chest=1.0, rump=0.86, ears=None, snout=0.5, headw=0.22, headh=0.24,
            head=0.26, neckw=0.16, legw=0.06, swing=30)

# farm animals
creature("chicken", ["Chicken"], 0.32, WHITE, leg=0.42, neck=0.26, neck_up=72, tail=("feathers", 0.45), acc=(0.80, 0.18, 0.16),
         legcol=(0.90, 0.72, 0.26), beak=(0.45, (0.92, 0.70, 0.22)), extras=(("comb",), ("wattle",), ("wings",)), **BIRD)
creature("duck", ["Duck"], 0.36, (0.60, 0.48, 0.36), leg=0.24, neck=0.30, neck_up=68, tail=("feathers", 0.30), headcol=(0.22, 0.40, 0.30),
         legcol=(0.92, 0.56, 0.20), belly=(0.82, 0.78, 0.70), beak=(0.60, (0.92, 0.66, 0.20)), extras=(("wings",),), **BIRD)
creature("goose", ["Goose"], 0.44, (0.84, 0.83, 0.80), leg=0.34, neck=0.52, neck_up=74, tail=("feathers", 0.28), legcol=(0.92, 0.56, 0.20),
         acc=(0.62, 0.60, 0.58), beak=(0.55, (0.92, 0.56, 0.20)), extras=(("wings", 1),), **BIRD)
creature("turkey", ["Turkey"], 0.50, (0.33, 0.25, 0.20), leg=0.40, neck=0.34, neck_up=70, tail=("fan", 0.85), headcol=(0.46, 0.56, 0.74),
         legcol=(0.62, 0.50, 0.42), acc=(0.78, 0.20, 0.18), tailcol=(0.52, 0.38, 0.26), beak=(0.40, (0.88, 0.76, 0.46)),
         extras=(("wattle",), ("wings",)), **BIRD)
creature("cow", ["Cow"], 1.45, WHITE, w=0.42, h=0.46, leg=0.40, legw=0.12, neck=0.20, neck_up=22, neckw=0.26, head=0.30, snout=0.72,
         ears=("flop", 0.10), horns=("short", 0.15), tail=("tuft", 0.50, 1), feet="hoof", acc=BLACK, muzzle=(0.86, 0.66, 0.62),
         extras=(("patches",),))
creature("pig", ["Pig"], 1.00, (0.90, 0.68, 0.66), w=0.46, h=0.46, leg=0.26, legw=0.12, neck=0.10, neck_up=12, neckw=0.32, head=0.36,
         headw=0.30, headh=0.30, snout=0.66, ears=("point", 0.10), tail=("stub", 0.10), feet="hoof", muzzle=(0.94, 0.60, 0.60))
creature("sheep", ["Sheep"], 0.95, (0.90, 0.87, 0.80), w=0.44, h=0.46, leg=0.38, legw=0.09, neck=0.18, neck_up=38, head=0.30,
         headcol=(0.26, 0.23, 0.21), legcol=(0.26, 0.23, 0.21), ears=("flop", 0.10), tail=("stub", 0.10), feet="hoof", extras=(("wool", 1.0),))
creature("goat", ["Goat"], 0.90, (0.84, 0.80, 0.72), w=0.34, h=0.38, leg=0.50, legw=0.075, neck=0.26, neck_up=50, neckw=0.17, head=0.30,
         ears=("flop", 0.10), horns=("straight", 0.20), tail=("stub", 0.10), feet="hoof", extras=(("beard",),))
creature("horse", ["Horse"], 1.55, (0.50, 0.33, 0.22), w=0.34, h=0.40, leg=0.64, legw=0.085, neck=0.42, neck_up=50, neckw=0.22, head=0.36,
         headw=0.18, headh=0.22, snout=0.62, ears=("point", 0.07), tail=("hair", 0.70, 1), feet="hoof", acc=(0.20, 0.14, 0.11),
         extras=(("mane",),))
creature("donkey", ["Donkey"], 1.20, (0.56, 0.52, 0.48), w=0.36, h=0.42, leg=0.56, legw=0.085, neck=0.36, neck_up=48, neckw=0.22, head=0.38,
         headw=0.19, headh=0.23, snout=0.66, ears=("long", 0.20), tail=("tuft", 0.50, 1), feet="hoof", acc=(0.26, 0.23, 0.21),
         belly=(0.84, 0.82, 0.78), muzzle=(0.86, 0.84, 0.80), extras=(("mane",),))
creature("alpaca", ["Alpaca"], 0.95, (0.84, 0.74, 0.60), w=0.40, h=0.44, leg=0.60, legw=0.085, neck=0.58, neck_up=76, neckw=0.24, head=0.24,
         headw=0.22, headh=0.24, snout=0.55, ears=("point", 0.08), tail=("stub", 0.10), extras=(("wool", 0.92),))
creature("dromedary", ["Dromedary"], 1.60, (0.80, 0.65, 0.45), w=0.32, h=0.38, leg=0.66, legw=0.075, neck=0.60, neck_up=56, neckw=0.18,
         head=0.28, headw=0.16, headh=0.20, snout=0.66, ears=("point", 0.05), tail=("tuft", 0.30), extras=(("hump", -0.04, 0.26),))
creature("muffalo", ["Muffalo"], 1.55, (0.47, 0.56, 0.66), w=0.50, h=0.52, leg=0.32, legw=0.13, neck=0.14, neck_up=8, neckw=0.34, head=0.30,
         headw=0.26, headh=0.28, snout=0.70, head_tilt=-28, headcol=(0.34, 0.40, 0.48), legcol=(0.32, 0.37, 0.44), ears=("flop", 0.08),
         horns=("short", 0.16), tail=("stub", 0.08), feet="hoof", extras=(("wool", 1.04), ("hump", 0.20, 0.14)))
creature("bison", ["Bison"], 1.50, (0.40, 0.29, 0.21), w=0.44, h=0.48, leg=0.40, legw=0.11, rump=0.82, neck=0.16, neck_up=4, neckw=0.36,
         head=0.30, headw=0.27, headh=0.30, snout=0.66, head_tilt=-34, headcol=(0.24, 0.18, 0.15), acc=(0.27, 0.20, 0.16),
         ears=("flop", 0.07), horns=("short", 0.15), tail=("tuft", 0.36, 1), feet="hoof", extras=(("hump", 0.22, 0.24, 1), ("beard", 1)))
creature("yak", ["Yak"], 1.45, (0.27, 0.22, 0.20), w=0.48, h=0.50, leg=0.34, legw=0.12, neck=0.14, neck_up=8, neckw=0.34, head=0.30,
         headw=0.26, headh=0.28, snout=0.68, head_tilt=-26, ears=("flop", 0.07), horns=("short", 0.26), tail=("hair", 0.45), feet="hoof",
         extras=(("wool", 1.0),))
creature("guineapig", ["GuineaPig"], 0.38, (0.74, 0.54, 0.36), w=0.50, h=0.50, leg=0.12, legw=0.10, neck=0.04, neck_up=10, neckw=0.36,
         head=0.36, headw=0.36, headh=0.36, snout=0.62, ears=("round", 0.07), tail=None, belly=WHITE)

# pets
creature("cat", ["Cat"], 0.50, (0.82, 0.60, 0.36), w=0.30, h=0.32, leg=0.42, legw=0.08, neck=0.14, neck_up=45, head=0.34, headw=0.30,
         headh=0.30, snout=0.50, ears=("point", 0.13), tail=("long", 0.85), belly=(0.94, 0.90, 0.82))
creature("husky", ["Husky"], 0.85, (0.56, 0.58, 0.63), w=0.32, h=0.36, leg=0.52, legw=0.09, neck=0.24, neck_up=44, head=0.34, snout=0.48,
         ears=("point", 0.12), tail=("up", 0.42), belly=WHITE, muzzle=WHITE, legcol=(0.88, 0.88, 0.88))
creature("labrador", ["LabradorRetriever"], 0.85, (0.86, 0.73, 0.48), w=0.33, h=0.37, leg=0.50, legw=0.09, neck=0.24, neck_up=42, head=0.34,
         snout=0.52, ears=("flop", 0.12), tail=("thin", 0.50))
creature("yorkie", ["YorkshireTerrier"], 0.42, (0.66, 0.50, 0.32), w=0.40, h=0.42, leg=0.28, legw=0.10, neck=0.14, neck_up=45, head=0.36,
         headw=0.32, headh=0.32, snout=0.50, ears=("point", 0.13), tail=("stub", 0.14), headcol=(0.74, 0.58, 0.36), extras=(("wool", 0.80),))

# wild grazers
DEER = dict(w=0.30, h=0.36, leg=0.60, legw=0.065, neck=0.38, neck_up=56, neckw=0.16, head=0.30, headw=0.17, headh=0.20, snout=0.52,
            ears=("point", 0.11), tail=("stub", 0.08), feet="hoof")
creature("deer", ["Deer"], 1.15, (0.64, 0.46, 0.30), horns=("antler", 0.32), belly=(0.90, 0.86, 0.78), **DEER)
creature("elk", ["Elk"], 1.45, (0.54, 0.40, 0.28), horns=("antler", 0.48), belly=(0.72, 0.62, 0.48), acc=(0.32, 0.23, 0.17),
         extras=(("mane",),), **DEER)
creature("caribou", ["Caribou"], 1.35, (0.58, 0.52, 0.46), horns=("antler", 0.44), belly=(0.88, 0.86, 0.82), **DEER)
creature("ibex", ["Ibex"], 1.05, (0.68, 0.56, 0.42), w=0.33, h=0.38, leg=0.52, legw=0.075, neck=0.28, neck_up=50, neckw=0.18, head=0.30,
         ears=("point", 0.08), horns=("curl", 0.52), tail=("stub", 0.08), feet="hoof", belly=(0.86, 0.80, 0.70), extras=(("beard",),))
creature("gazelle", ["Gazelle"], 0.95, (0.82, 0.63, 0.42), w=0.26, h=0.32, leg=0.74, legw=0.055, neck=0.40, neck_up=60, neckw=0.14,
         head=0.28, headw=0.16, headh=0.19, ears=("point", 0.10), horns=("straight", 0.34), tail=("stub", 0.08), feet="hoof", belly=WHITE)
creature("boomalope", ["Boomalope"], 1.25, (0.74, 0.60, 0.50), w=0.42, h=0.42, leg=0.50, legw=0.08, neck=0.26, neck_up=40, head=0.26,
         ears=("point", 0.08), tail=("stub", 0.08), feet="hoof", acc=(0.88, 0.80, 0.44), extras=(("boom",),))
creature("wildboar", ["WildBoar"], 1.00, (0.36, 0.28, 0.24), w=0.44, h=0.46, leg=0.30, legw=0.11, neck=0.10, neck_up=10, neckw=0.32, head=0.38,
         headw=0.28, headh=0.30, snout=0.60, ears=("point", 0.10), horns=("tusk", 0.12), tail=("tuft", 0.22), feet="hoof",
         acc=(0.22, 0.17, 0.15), extras=(("ridge",),))
creature("capybara", ["Capybara"], 0.85, (0.56, 0.42, 0.30), w=0.44, h=0.46, leg=0.24, legw=0.11, neck=0.08, neck_up=12, neckw=0.34, head=0.36,
         headw=0.30, headh=0.32, snout=0.82, ears=("round", 0.05), tail=None)

# small animals
SMALL = dict(w=0.40, h=0.40, leg=0.20, legw=0.08, neck=0.08, neck_up=20, neckw=0.28, head=0.38, headw=0.30, headh=0.30)
creature("rat", ["Rat"], 0.38, (0.50, 0.44, 0.40), snout=0.34, ears=("round", 0.09), tail=("long", 0.90), tailcol=(0.84, 0.64, 0.62), **SMALL)
creature("boomrat", ["Boomrat"], 0.42, (0.74, 0.40, 0.36), snout=0.34, ears=("round", 0.09), tail=("long", 0.80), acc=(0.94, 0.72, 0.36),
         extras=(("boom",),), **SMALL)
creature("squirrel", ["Squirrel"], 0.36, (0.68, 0.42, 0.26), snout=0.42, ears=("point", 0.10), tail=("up", 0.95), belly=(0.92, 0.86, 0.76), **SMALL)
creature("hare", ["Hare"], 0.44, (0.62, 0.50, 0.38), snout=0.50, ears=("long", 0.32), tail=("stub", 0.10), tailcol=WHITE, **SMALL)
creature("snowhare", ["Snowhare"], 0.44, (0.95, 0.95, 0.96), snout=0.50, ears=("long", 0.32), tail=("stub", 0.10), **SMALL)
creature("raccoon", ["Raccoon"], 0.54, (0.52, 0.52, 0.52), snout=0.40, ears=("round", 0.09), tail=("bushy", 0.70, 1), acc=(0.20, 0.19, 0.19),
         headcol=(0.34, 0.33, 0.33), muzzle=WHITE, **SMALL)
creature("chinchilla", ["Chinchilla"], 0.38, (0.66, 0.66, 0.71), snout=0.60, ears=("round", 0.15), tail=("bushy", 0.60), belly=WHITE,
         **dict(SMALL, w=0.50, h=0.52, leg=0.14))
creature("monkey", ["Monkey"], 0.50, (0.50, 0.36, 0.26), w=0.34, h=0.40, leg=0.48, legw=0.08, neck=0.14, neck_up=50, head=0.36, headw=0.32,
         headh=0.34, snout=0.72, ears=("round", 0.09), tail=("long", 1.20), muzzle=(0.84, 0.68, 0.54))

# hunters
FOX = dict(w=0.30, h=0.34, leg=0.46, legw=0.075, neck=0.20, neck_up=40, head=0.36, headw=0.26, headh=0.26, snout=0.36)
creature("fox_fennec", ["Fox_Fennec"], 0.46, (0.88, 0.74, 0.54), ears=("point", 0.32), tail=("bushy", 0.75), belly=WHITE, **FOX)
creature("fox_red", ["Fox_Red"], 0.66, (0.82, 0.44, 0.20), ears=("point", 0.15), tail=("bushy", 0.85, 1), acc=WHITE, belly=WHITE,
         legcol=(0.24, 0.18, 0.15), **FOX)
creature("fox_arctic", ["Fox_Arctic"], 0.62, (0.94, 0.94, 0.96), ears=("point", 0.12), tail=("bushy", 0.80), **FOX)
WOLF = dict(w=0.30, h=0.36, leg=0.56, legw=0.085, neck=0.24, neck_up=34, neckw=0.22, head=0.36, headw=0.24, headh=0.25, snout=0.44,
            ears=("point", 0.11), tail=("bushy", 0.55))
creature("wolf_timber", ["Wolf_Timber"], 1.00, (0.52, 0.50, 0.48), belly=(0.80, 0.78, 0.74), **WOLF)
creature("wolf_arctic", ["Wolf_Arctic"], 1.00, (0.92, 0.92, 0.94), **WOLF)
creature("warg", ["Warg"], 1.35, (0.38, 0.25, 0.23), acc=(0.22, 0.15, 0.14), extras=(("mane",), ("ridge",)),
         **dict(WOLF, w=0.38, h=0.44, legw=0.10, neckw=0.28, headw=0.28, headh=0.29))
CAT = dict(w=0.30, h=0.34, leg=0.50, legw=0.09, neck=0.20, neck_up=30, neckw=0.22, head=0.28, headw=0.26, headh=0.26, snout=0.58)
creature("cougar", ["Cougar"], 1.15, (0.78, 0.62, 0.42), ears=("round", 0.07), tail=("long", 0.80), belly=(0.92, 0.86, 0.76), **CAT)
creature("panther", ["Panther"], 1.15, (0.17, 0.17, 0.20), ears=("round", 0.07), tail=("long", 0.80), **CAT)
creature("lynx", ["Lynx"], 0.80, (0.72, 0.64, 0.52), ears=("point", 0.14), tail=("stub", 0.12), belly=(0.92, 0.88, 0.80), **CAT)
BEAR = dict(w=0.48, h=0.52, leg=0.38, legw=0.15, neck=0.16, neck_up=18, neckw=0.32, head=0.30, headw=0.28, headh=0.28, snout=0.46,
            ears=("round", 0.07), tail=("stub", 0.07))
creature("bear_grizzly", ["Bear_Grizzly"], 1.50, (0.42, 0.30, 0.22), muzzle=(0.62, 0.48, 0.34), extras=(("hump", 0.20, 0.10),), **BEAR)
creature("bear_polar", ["Bear_Polar"], 1.70, (0.94, 0.93, 0.89), **BEAR)

# giants
creature("megasloth", ["Megasloth"], 2.10, (0.46, 0.36, 0.28), w=0.50, h=0.56, leg=0.34, legw=0.16, neck=0.20, neck_up=34, neckw=0.30, head=0.26,
         headw=0.24, headh=0.26, snout=0.62, ears=("round", 0.04), tail=("stub", 0.10), headcol=(0.62, 0.52, 0.40), extras=(("wool", 1.0),))
creature("thrumbo", ["Thrumbo"], 2.50, (0.90, 0.92, 0.95), w=0.46, h=0.50, leg=0.60, legw=0.105, chest=1.10, rump=0.90, neck=0.50, neck_up=66,
         neckw=0.33, head=0.27, headw=0.21, headh=0.25, snout=0.62, head_tilt=-24, ears=("point", 0.06), horns=("thrumbo", 0.64),
         tail=("tuft", 0.36, 1), feet="hoof", belly=(0.72, 0.77, 0.85), legcol=(0.64, 0.69, 0.77), headcol=(0.84, 0.87, 0.92),
         acc=(0.78, 0.82, 0.89), muzzle=(0.62, 0.66, 0.74),
         extras=(("wool", 0.90), ("hump", 0.36, 0.30), ("hump", -0.30, 0.16), ("mane",), ("beard", 1)))
creature("elephant", ["Elephant"], 2.30, (0.55, 0.54, 0.56), w=0.50, h=0.56, leg=0.44, legw=0.17, neck=0.10, neck_up=14, neckw=0.38, head=0.34,
         headw=0.36, headh=0.42, snout=0.52, ears=("plate", 0.30), horns=("tusk", 0.30), tail=("tuft", 0.34), feet="none", extras=(("trunk",),))
creature("rhinoceros", ["Rhinoceros"], 2.00, (0.52, 0.50, 0.48), w=0.48, h=0.50, leg=0.32, legw=0.16, neck=0.14, neck_up=2, neckw=0.38, head=0.40,
         headw=0.26, headh=0.30, snout=0.74, head_tilt=-22, ears=("point", 0.06), horns=("nose", 0.20), tail=("thin", 0.25), feet="none")

# big birds
creature("emu", ["Emu"], 0.78, (0.42, 0.36, 0.32), leg=0.92, neck=0.62, neck_up=76, tail=("feathers", 0.22), headcol=(0.36, 0.44, 0.56),
         legcol=(0.36, 0.33, 0.30), beak=(0.45, (0.26, 0.24, 0.22)), **BIRD)
creature("ostrich", ["Ostrich"], 0.92, (0.18, 0.17, 0.17), leg=1.05, neck=0.82, neck_up=80, tail=("feathers", 0.30), tailcol=WHITE,
         headcol=(0.86, 0.70, 0.66), legcol=(0.86, 0.70, 0.66), beak=(0.45, (0.80, 0.62, 0.42)), extras=(("wings",),),
         **dict(BIRD, neckw=0.12))
creature("cassowary", ["Cassowary"], 0.86, (0.15, 0.15, 0.17), leg=0.80, neck=0.56, neck_up=74, tail=("feathers", 0.18), headcol=(0.22, 0.42, 0.80),
         legcol=(0.40, 0.38, 0.34), acc=(0.82, 0.20, 0.18), horns=("casque", 0.10), beak=(0.45, (0.28, 0.26, 0.24)),
         extras=(("wattle",),), **BIRD)

# reptiles
creature("iguana", ["Iguana"], 0.75, (0.42, 0.60, 0.30), w=0.28, h=0.22, leg=0.12, legw=0.06, neck=0.12, neck_up=14, neckw=0.20, head=0.26,
         headw=0.20, headh=0.18, snout=0.60, ears=None, tail=("lizard", 1.10), splay=40, acc=(0.30, 0.46, 0.24), belly=(0.70, 0.78, 0.46),
         extras=(("crest",),))
creature("tortoise", ["Tortoise"], 0.60, (0.54, 0.52, 0.34), w=0.60, h=0.30, leg=0.14, legw=0.13, neck=0.24, neck_up=14, neckw=0.20, head=0.22,
         headw=0.20, headh=0.20, snout=0.70, ears=None, tail=("stub", 0.08), splay=25, swing=18, acc=(0.44, 0.40, 0.24), feet="none",
         extras=(("shell",),))
snake("cobra", ["Cobra"], 1.0, (0.60, 0.50, 0.32), (0.86, 0.80, 0.60), (0.50, 0.40, 0.26))

# insects
insect("megascarab", ["Megascarab"], 0.60, (0.26, 0.30, 0.38), 6, [(0.0, 0.80, 0.62, 0.36)], leg=0.16)
insect("megaspider", ["Megaspider"], 1.10, (0.56, 0.42, 0.28), 8, [(-0.28, 0.56, 0.56, 0.38), (0.14, 0.36, 0.40, 0.26)], acc=(0.72, 0.62, 0.42),
       leg=0.22, legw=0.06)
insect("spelopede", ["Spelopede"], 1.10, (0.62, 0.56, 0.40), 6, [(-0.34, 0.36, 0.34, 0.24), (-0.02, 0.36, 0.38, 0.26), (0.28, 0.32, 0.34, 0.24)],
       leg=0.18)



def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(DEFS_DIR, exist_ok=True)

    for old in os.listdir(MODELS_DIR):
        if old.endswith(".obj") and old[:-4] not in SHAPES:
            os.remove(os.path.join(MODELS_DIR, old))

    with open(os.path.join(MODELS_DIR, "isorim.mtl"), "w", newline="\n") as f:
        f.write("# Materials for the IsoRim models.\n")
        f.write("# Kd is the colour, map_Kd the texture under the mod's Textures folder (no extension).\n")
        f.write("# Names starting with \"stuff\" are also multiplied by the colour of the build material,\n")
        f.write("# and {stuff} becomes Wood, Stone or Metal to match it.\n")
        f.write("# Names starting with \"leaf\" are left out while a tree is bare,\n")
        f.write("# and names starting with \"twig\" are only drawn while it is bare.\n")
        for name, ((r, g, b), tex) in MATERIALS.items():
            f.write("\nnewmtl %s\nKd %.3f %.3f %.3f\n" % (name, r, g, b))
            if tex:
                f.write("map_Kd %s\n" % tex)

    total = 0
    for name, shape in SHAPES.items():
        shape.write(name)
        total += sum((len(pts) - 2) for _, pts, _ in shape.faces)

    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<Defs>", "",
             "  <!-- Per-thing settings for the 3D view. Generated by tools/make_models.py.",
             "",
             "       A thing with no entry is shaped automatically from its own sprite. An entry names",
             "       one thing with <thingDef>, or every thing in a category with <thingCategory>",
             "       (a thing's own entry wins over its category's). It can set:",
             "         <model>Models/x.obj</model>   use a hand-made model",
             "         <models><li>...</li></models> several models; each thing picks one and keeps it",
             "         <height>0.3</height>          set the height of the automatic shape, in cells",
             "         <flat>true</flat>             leave it as a flat sprite",
             "       Extras for models:",
             "         <scale>1</scale> <offset>(0,0,0)</offset> <rotation>0</rotation>",
             "         <surfaceHeight>0.4</surfaceHeight>   where things on top of it are drawn",
             "         <randomRotation>true</randomRotation> <scaleJitter>0.15</scaleJitter>",
             "         <growthScale>true</growthScale>      scale with how grown a plant is",
             "         <layFlat>true</layFlat>              built as held; tipped on its side on the ground",
             "         <scatter>0.5</scatter>               move each one off the middle of its cell",
             "         <spriteTint>true</spriteTint>        colour 'stuff' parts from the thing's own sprite",
             "         <wallMounted>true</wallMounted> <mountHeight>0.5</mountHeight>   fixed to the wall it faces",
             "         <alongRun>true</alongRun>            turned to follow the row of the same thing it is in",
             "         <fullVariant>true</fullVariant>      the second model is used once the thing holds something",
             "         <groundShadow>false</groundShadow>   no soft shadow on the ground under it",
             "         <outline>0.6</outline>               how bold the dark outline is (1 = usual)",
             "         <linked>true</linked>                first model in the cell, second once toward each neighbour it joins",
             "         <builtFor>(3, 2)</builtFor>         the footprint the model was made for; stretched to fit the thing",
             "         <topModel>Models/x.obj</topModel> <topHeight>0.6</topHeight>   a turret's turning gun",
             "       <match><li>Wreck</li></match> in place of <thingDef> covers every building or item whose",
             "       name contains one of these and that has no entry of its own (first match wins).",
             "       <fallback>SmallPlants</fallback> in place of <thingDef> covers every plant that is",
             "       not a tree and has no entry of its own.",
             "       Animals (<animal>true</animal>, <thingDef> is the animal's race): <model> is the body,",
             "       facing north; <legModel> one leg, standing with its hip at the top; <legs> where the",
             "       hips are on the body; <legLength>, <legSwing> and <legSplay> (degrees), <stride>",
             "       (cells walked per swing of the legs), <bodyCentre> and <bodyHalfWidth> for lying down. -->", ""]

    def entry(def_name, target_tag, target, e):
        lines.append("  <IsoRim.ModelDef>")
        lines.append("    <defName>R3D_%s</defName>" % def_name)
        if target_tag == "match":
            lines.append("    <match>")
            for m in target:
                lines.append("      <li>%s</li>" % m)
            lines.append("    </match>")
        else:
            lines.append("    <%s>%s</%s>" % (target_tag, target, target_tag))
        if len(e["models"]) == 1:
            lines.append("    <model>Models/%s.obj</model>" % e["models"][0])
        else:
            lines.append("    <models>")
            for m in e["models"]:
                lines.append("      <li>Models/%s.obj</li>" % m)
            lines.append("    </models>")
        if e["surface"] is not None:
            lines.append("    <surfaceHeight>%.2f</surfaceHeight>" % e["surface"])
        if e["scale"] != 1.0:
            lines.append("    <scale>%.2f</scale>" % e["scale"])
        if e["turn"]:
            lines.append("    <rotation>%.0f</rotation>" % e["turn"])
        if e["random_turn"]:
            lines.append("    <randomRotation>true</randomRotation>")
        if e["jitter"]:
            lines.append("    <scaleJitter>%.2f</scaleJitter>" % e["jitter"])
        if e["grow"]:
            lines.append("    <growthScale>true</growthScale>")
        if e["flat"]:
            lines.append("    <layFlat>true</layFlat>")
        if e["scatter"]:
            lines.append("    <scatter>%.2f</scatter>" % e["scatter"])
        if e["sprite_tint"]:
            lines.append("    <spriteTint>true</spriteTint>")
        if e["wall"] is not None:
            lines.append("    <wallMounted>true</wallMounted>")
            lines.append("    <mountHeight>%.2f</mountHeight>" % e["wall"])
        if e["along_run"]:
            lines.append("    <alongRun>true</alongRun>")
        if e["when_full"]:
            lines.append("    <fullVariant>true</fullVariant>")
        if not e["shadow"]:
            lines.append("    <groundShadow>false</groundShadow>")
        if e["outline"] != 1.0:
            lines.append("    <outline>%.2f</outline>" % e["outline"])
        if e["linked"]:
            lines.append("    <linked>true</linked>")
        if e.get("size"):
            lines.append("    <builtFor>(%g, %g)</builtFor>" % e["size"])
        if e.get("top"):
            lines.append("    <topModel>Models/%s.obj</topModel>" % e["top"])
            lines.append("    <topHeight>%.2f</topHeight>" % (e["top_height"] or 0.5))
        if e.get("match") and target_tag == "match":
            pass
        lines.append("  </IsoRim.ModelDef>")
        lines.append("")

    things = 0
    for e in ENTRIES:
        for thing in e["things"]:
            entry(thing, "thingDef", thing, e)
            things += 1
        if e["category"]:
            entry("Category_" + e["category"], "thingCategory", e["category"], e)
        if e["fallback"]:
            entry("Fallback_" + e["fallback"], "fallback", e["fallback"], e)
        if e.get("match"):
            entry("Match_%d_%s" % (ENTRIES.index(e), e["models"][0]), "match", e["match"], e)
    for a in ANIMALS:
        for thing in a["things"]:
            lines.append("  <IsoRim.ModelDef>")
            lines.append("    <defName>R3D_Animal_%s</defName>" % thing)
            lines.append("    <thingDef>%s</thingDef>" % thing)
            lines.append("    <model>Models/animal_%s.obj</model>" % a["name"])
            lines.append("    <animal>true</animal>")
            if a["hips"]:
                lines.append("    <legModel>Models/animal_%s_leg.obj</legModel>" % a["name"])
                lines.append("    <legs>")
                for x, y, z in a["hips"]:
                    lines.append("      <li>(%.3f, %.3f, %.3f)</li>" % (x, y, z))
                lines.append("    </legs>")
                lines.append("    <legLength>%.3f</legLength>" % a["leg_len"])
                lines.append("    <legSwing>%.0f</legSwing>" % a["swing"])
                if a["splay"]:
                    lines.append("    <legSplay>%.0f</legSplay>" % a["splay"])
            lines.append("    <stride>%.2f</stride>" % a["stride"])
            lines.append("    <bodyCentre>%.3f</bodyCentre>" % a["centre"])
            lines.append("    <bodyHalfWidth>%.3f</bodyHalfWidth>" % a["half"])
            lines.append("    <bodyHalfLength>%.3f</bodyHalfLength>" % a["length"])
            lines.append("  </IsoRim.ModelDef>")
            lines.append("")
            things += 1
    for thing, height in OVERRIDES.items():
        lines.append("  <IsoRim.ModelDef>")
        lines.append("    <defName>R3D_%s</defName>" % thing)
        lines.append("    <thingDef>%s</thingDef>" % thing)
        lines.append("    <flat>true</flat>" if height is None else "    <height>%.2f</height>" % height)
        lines.append("  </IsoRim.ModelDef>")
        lines.append("")
    lines.append("</Defs>")
    with open(os.path.join(DEFS_DIR, "Models.xml"), "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("%d models (%d triangles), %d things named, %d categories, %d overrides"
          % (len(SHAPES), total, things, sum(1 for e in ENTRIES if e["category"]), len(OVERRIDES)))


if __name__ == "__main__":
    main()
