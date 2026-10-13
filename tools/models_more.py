# IsoRim: the rest of the base game's buildings, its items, and the wrecks, ruins and junk that
# turn up on maps. Run as part of make_models.py (it is read into that file's namespace), so
# Shape, add, use, MATERIALS and the helpers there are all available.
#
# Every building here is built for the footprint given as size=(x, z) in its use() line; the mod
# stretches it to the thing's real footprint (and turns it a quarter if the thing is long the
# other way), so a guess that is a cell out still fits.

MATERIALS.update({
    "rust":         ((0.50, 0.32, 0.22), SW + "Metal"),
    "rust_dark":    ((0.30, 0.21, 0.16), SW + "Metal"),
    "rust_light":   ((0.64, 0.44, 0.30), SW + "Metal"),
    "paint_olive":  ((0.40, 0.42, 0.30), SW + "Metal"),
    "paint_red":    ((0.56, 0.24, 0.20), SW + "Metal"),
    "paint_blue":   ((0.30, 0.40, 0.52), SW + "Metal"),
    "paint_cream":  ((0.78, 0.74, 0.62), SW + "Metal"),
    "concrete":     ((0.62, 0.61, 0.58), SW + "Stone"),
    "glass":        ((0.52, 0.70, 0.78), None),
    "glass_dark":   ((0.16, 0.22, 0.27), None),
    "screen":       ((0.10, 0.13, 0.16), None),
    "glow_screen":  ((0.48, 0.86, 0.96), SW + "Glow"),
    "glow_green":   ((0.46, 0.94, 0.52), SW + "Glow"),
    "glow_red":     ((0.98, 0.36, 0.30), SW + "Glow"),
    "glow_amber":   ((1.00, 0.72, 0.30), SW + "Glow"),
    "felt":         ((0.20, 0.44, 0.28), SW + "Fabric"),
    "felt_red":     ((0.52, 0.18, 0.18), SW + "Fabric"),
    "rubber":       ((0.13, 0.13, 0.14), None),
    "hull":         ((0.70, 0.73, 0.76), SW + "Metal"),
    "hull_dark":    ((0.40, 0.43, 0.47), SW + "Metal"),
    "plasteel":     ((0.70, 0.80, 0.84), SW + "Metal"),
    "uranium":      ((0.36, 0.44, 0.32), SW + "Metal"),
    "gold":         ((0.92, 0.74, 0.30), SW + "Metal"),
    "silver":       ((0.82, 0.84, 0.86), SW + "Metal"),
    "jade":         ((0.40, 0.66, 0.46), SW + "Stone"),
    "wood_end":     ((0.78, 0.62, 0.40), SW + "Wood"),
    "chemfuel":     ((0.74, 0.30, 0.16), SW + "Metal"),
    "neutro":       ((0.30, 0.48, 0.72), SW + "Metal"),
    "medicine":     ((0.92, 0.92, 0.90), None),
    "red_cross":    ((0.82, 0.18, 0.16), None),
    "herb_green":   ((0.38, 0.54, 0.28), SW + "Leaf"),
    "meat":         ((0.70, 0.26, 0.24), None),
    "fat":          ((0.92, 0.82, 0.74), None),
    "bowl":         ((0.78, 0.70, 0.58), SW + "Wood"),
    "food_paste":   ((0.66, 0.70, 0.52), None),
    "food_stew":    ((0.66, 0.44, 0.26), None),
    "food_green":   ((0.44, 0.62, 0.30), None),
    "food_yellow":  ((0.92, 0.78, 0.36), None),
    "foil":         ((0.76, 0.76, 0.72), SW + "Metal"),
    "sack":         ((0.74, 0.64, 0.46), SW + "Fabric"),
    "sack_dark":    ((0.56, 0.47, 0.33), SW + "Fabric"),
    "potato":       ((0.72, 0.56, 0.36), None),
    "rice":         ((0.94, 0.92, 0.84), None),
    "fungus":       ((0.80, 0.72, 0.62), None),
    "egg":          ((0.94, 0.90, 0.82), None),
    "milk":         ((0.96, 0.96, 0.94), None),
    "jelly":        ((0.96, 0.74, 0.22), SW + "Glow"),
    "chocolate":    ((0.36, 0.22, 0.14), None),
    "bottle":       ((0.32, 0.22, 0.12), None),
    "hay":          ((0.80, 0.72, 0.38), SW + "Fabric"),
    "pill":         ((0.92, 0.88, 0.80), None),
    "label":        ((0.88, 0.86, 0.78), None),
    "stuff_block":  ((1.00, 1.00, 1.00), SW + "Stone"),
    "stuff_block_dark": ((0.80, 0.80, 0.80), SW + "Stone"),
    "stuff_wool":   ((1.00, 1.00, 1.00), SW + "Fabric"),
    "shell_olive":  ((0.40, 0.44, 0.30), SW + "Metal"),
    "brass":        ((0.80, 0.64, 0.30), SW + "Metal"),
    "spike":        ((0.80, 0.80, 0.80), None),
    "water":        ((0.32, 0.52, 0.62), None),
    "foam_white":   ((0.92, 0.94, 0.94), None),
    "steam_pipe":   ((0.58, 0.56, 0.52), SW + "Metal"),
    "ice":          ((0.82, 0.90, 0.96), None),
})


# ---------------------------------------------------------------------------- small helpers

def planked_box(s, x0, y0, z0, x1, y1, z1, mat, band, bands=2):
    """A crate: a box with a couple of bands round it."""
    s.box(x0, y0, z0, x1, y1, z1, mat)
    for k in range(bands):
        y = y0 + (y1 - y0) * (k + 1) / (bands + 1)
        s.box(x0 - 0.008, y - 0.015, z0 - 0.008, x1 + 0.008, y + 0.015, z1 + 0.008, band)


def screen_on(s, x0, y0, x1, y1, z, mat="glow_screen", frame="gun_dark", facing=-1):
    """A screen in a frame, its face looking south (facing -1) or north (+1)."""
    s.box(x0 - 0.02, y0 - 0.02, z - 0.012, x1 + 0.02, y1 + 0.02, z + 0.012, frame)
    s.box(x0, y0, z + facing * 0.012, x1, y1, z + facing * 0.016, mat)


def pipe(s, a, b, r, mat="steam_pipe", sides=6):
    s.limb(a, b, r, r, sides, mat)


def tank(s, x, z, r, y0, y1, mat, cap=None, sides=10):
    """An upright tank with a domed cap."""
    s.prism(x, z, r, r, y0, y1, sides, mat)
    s.prism(x, z, r, r * 0.55, y1, y1 + r * 0.45, sides, cap or mat)
    s.prism(x, z, r + 0.012, r + 0.012, y0 + (y1 - y0) * 0.2, y0 + (y1 - y0) * 0.2 + 0.03, sides, "gun_dark")


def lying_tank(s, x0, x1, y, z, r, mat, sides=10):
    """A tank on its side, along x."""
    s.loft([((x0, y, z), r * 0.6, r * 0.6), ((x0 + r * 0.25, y, z), r, r), ((x1 - r * 0.25, y, z), r, r), ((x1, y, z), r * 0.6, r * 0.6)], sides, mat)


def wheel(s, x, y, z, r, w, mat="rubber", hub="gun_metal", axis="x"):
    if axis == "x":
        s.loft([((x - w / 2, y, z), r, r), ((x + w / 2, y, z), r, r)], 10, mat)
        s.loft([((x + w / 2, y, z), r * 0.45, r * 0.45), ((x + w / 2 + 0.006, y, z), r * 0.45, r * 0.45)], 8, hub)
    else:
        s.loft([((x, y, z - w / 2), r, r), ((x, y, z + w / 2), r, r)], 10, mat)


# ---------------------------------------------------------------------------- furniture and joy

def hospital_bed():
    """1 x 2: a metal-framed bed with side rails, raised pillow end to the north."""
    s = Shape()
    s.legs(-0.44, -0.95, 0.44, 0.95, 0.20, 0.06, "gun_light")
    for x in (-0.40, 0.40):                                                         # castors
        for z in (-0.88, 0.88):
            s.prism(x, z, 0.04, 0.04, 0.0, 0.05, 6, "rubber")
    s.box(-0.44, 0.20, -0.95, 0.44, 0.30, 0.93, "gun_light", top="metal")
    s.box(-0.40, 0.30, -0.90, 0.40, 0.42, 0.88, "linen")
    s.wedge(-0.40, 0.30, 0.40, 0.88, 0.42, 0.52, 0.10, "linen")                   # raised back
    s.box(-0.41, 0.42, -0.90, 0.41, 0.46, 0.25, "blanket")
    s.box(-0.30, 0.50, 0.50, 0.30, 0.60, 0.84, "pillow")
    for x0 in (-0.47, 0.42):                                                        # side rails
        s.box(x0, 0.30, -0.30, x0 + 0.05, 0.58, 0.40, "gun_white")
    s.box(-0.44, 0.20, 0.90, 0.44, 0.84, 0.96, "gun_white", top="gun_light")     # headboard
    s.box(-0.44, 0.20, -0.97, 0.44, 0.56, -0.92, "gun_white", top="gun_light")
    return s


def bedroll(double):
    """A padded roll laid out on the ground, pillow end to the north."""
    s = Shape()
    w = 0.86 if double else 0.40
    s.box(-w, 0.0, -0.88, w, 0.07, 0.86, "stuff_fabric_dark", top="stuff_fabric")
    s.loft([((-w, 0.10, -0.82), 0.09, 0.09), ((w, 0.10, -0.82), 0.09, 0.09)], 8, "stuff_fabric_dark")   # rolled-back foot
    for x in ((-0.40, 0.40) if double else (0.0,)):
        s.box(x - 0.28, 0.07, 0.48, x + 0.28, 0.15, 0.80, "pillow")
    s.box(-w + 0.02, 0.07, -0.70, w - 0.02, 0.11, 0.30, "blanket")
    return s


def animal_bed():
    """A round, padded basket."""
    s = Shape()
    s.loft([((0, 0.0, 0), 0.44, 0.44), ((0, 0.14, 0), 0.46, 0.46), ((0, 0.20, 0), 0.40, 0.40)], 12, "stuff_dark", cap_start=False, cap_end=False)
    s.loft([((0, 0.20, 0), 0.40, 0.40), ((0, 0.14, 0), 0.34, 0.34)], 12, "stuff", cap_start=False, cap_end=False)
    s.prism(0, 0, 0.34, 0.30, 0.0, 0.12, 12, "cushion")
    return s


def billiards_table():
    """3 x 2: green felt in a deep wooden rail on turned legs, with balls and a cue."""
    s = Shape()
    s.legs(-1.30, -0.80, 1.30, 0.80, 0.56, 0.16, "stuff_dark")
    s.box(-1.40, 0.56, -0.90, 1.40, 0.72, 0.90, "stuff_dark", top="stuff")
    s.box(-1.26, 0.72, -0.76, 1.26, 0.74, 0.76, "felt")
    for x0, x1, z0, z1 in ((-1.40, 1.40, -0.90, -0.76), (-1.40, 1.40, 0.76, 0.90), (-1.40, -1.26, -0.76, 0.76), (1.26, 1.40, -0.76, 0.76)):
        s.box(x0, 0.72, z0, x1, 0.80, z1, "stuff_dark", top="stuff")
    for x in (-1.28, 0.0, 1.28):                                                    # pockets
        for z in (-0.78, 0.78):
            s.prism(x, z, 0.06, 0.06, 0.745, 0.805, 8, "pit")
    rng = random.Random(3)
    for col in ("paint_red", "gun_white", "paint_blue", "food_yellow", "paint_red", "gun_dark", "paint_olive"):
        x, z = rng.uniform(-1.0, 1.0), rng.uniform(-0.6, 0.6)
        s.lump(x, 0.74, z, 0.04, 0.07, 0.04, col, rng, sides=6, profile=((0.0, 0.6), (0.4, 1.0), (0.8, 0.6)), jitter=0.02, closed=True)
    s.limb((-0.80, 0.78, -0.20), (0.60, 0.80, 0.40), 0.018, 0.012, 5, "gun_wood")
    return s


def chess_table():
    """1 x 1 (or 2 x 1): a table with a board and a few pieces."""
    s = Shape()
    s.legs(-0.36, -0.36, 0.36, 0.36, 0.56, 0.08, "stuff_dark")
    s.box(-0.42, 0.56, -0.42, 0.42, 0.62, 0.42, "stuff_dark", top="stuff")
    for i in range(8):
        for j in range(8):
            mat = "gun_white" if (i + j) % 2 == 0 else "gun_dark"
            x0, z0 = -0.30 + i * 0.075, -0.30 + j * 0.075
            s.box(x0, 0.62, z0, x0 + 0.075, 0.628, z0 + 0.075, mat)
    rng = random.Random(5)
    for k in range(10):
        i, j = rng.randrange(8), rng.randrange(8)
        x, z = -0.30 + i * 0.075 + 0.0375, -0.30 + j * 0.075 + 0.0375
        s.prism(x, z, 0.022, 0.015, 0.628, 0.628 + rng.uniform(0.04, 0.08), 6, "gun_white" if k % 2 else "gun_dark")
    return s


def poker_table():
    """2 x 2: a round green table with stacks of chips and cards."""
    s = Shape()
    s.prism(0, 0, 0.16, 0.10, 0.0, 0.58, 8, "stuff_dark")
    s.prism(0, 0, 0.40, 0.30, 0.0, 0.06, 10, "stuff_deep")
    s.prism(0, 0, 0.92, 0.92, 0.58, 0.68, 16, "stuff_dark", top="stuff")
    s.prism(0, 0, 0.78, 0.78, 0.68, 0.69, 16, "felt")
    rng = random.Random(9)
    for k in range(6):
        a = k * 1.05
        x, z = 0.50 * math.cos(a), 0.50 * math.sin(a)
        s.prism(x, z, 0.035, 0.035, 0.69, 0.69 + rng.uniform(0.03, 0.08), 8, ("paint_red", "gun_white", "paint_blue")[k % 3])
        s.box(x * 0.6 - 0.04, 0.69, z * 0.6 - 0.06, x * 0.6 + 0.04, 0.694, z * 0.6 + 0.06, "paper")
    return s


def hoopstone_ring():
    """A stone ring set upright in a heavy base, and a few throwing stones."""
    s = Shape()
    s.box(-0.26, 0, -0.14, 0.26, 0.10, 0.14, "stuff_dark", top="stuff")
    n = 12
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p0 = (0.28 * math.cos(a0), 0.40 + 0.28 * math.sin(a0), 0)
        p1 = (0.28 * math.cos(a1), 0.40 + 0.28 * math.sin(a1), 0)
        s.limb(p0, p1, 0.05, 0.05, 6, "stuff")
    rng = random.Random(4)
    for k in range(3):
        s.lump(rng.uniform(-0.4, 0.4), 0, rng.uniform(-0.45, -0.25), 0.05, 0.05, 0.05, "stone", rng, sides=5, jitter=0.2)
    return s


def horseshoes_pin():
    s = Shape()
    s.prism(0, 0, 0.10, 0.12, 0.0, 0.03, 8, "soil")
    s.prism(0, 0, 0.025, 0.02, 0.0, 0.40, 6, "stuff")
    for x, z, a in ((0.25, -0.20, 0.6), (-0.22, 0.18, 2.5)):
        for k in range(6):                                                           # a horseshoe lying flat
            t0, t1 = a + k * 0.75, a + (k + 1) * 0.75
            s.limb((x + 0.08 * math.cos(t0), 0.015, z + 0.08 * math.sin(t0)), (x + 0.08 * math.cos(t1), 0.015, z + 0.08 * math.sin(t1)),
                   0.014, 0.014, 4, "gun_metal")
    s.limb((0.0, 0.10, -0.10), (0.0, 0.32, 0.0), 0.012, 0.012, 4, "gun_metal")      # one ringer on the pin
    return s


def television(kind):
    """Screen to the south. tube: a boxy set on a wooden cabinet; flat: a panel on a stand; mega: a huge panel."""
    s = Shape()
    if kind == "tube":
        s.box(-0.90, 0, -0.36, 0.90, 0.42, 0.36, "stuff_dark", top="stuff")
        s.box(-0.80, 0.10, -0.38, -0.05, 0.34, -0.36, "stuff_deep")
        s.box(-0.55, 0.42, -0.32, 0.55, 0.98, 0.34, "paint_cream", top="gun_light")
        s.box(-0.40, 0.98, 0.0, 0.40, 1.06, 0.30, "gun_dark")
        screen_on(s, -0.44, 0.52, 0.30, 0.90, -0.33, frame="gun_dark")
        s.prism(0.43, -0.34, 0.035, 0.035, 0.62, 0.66, 6, "gun_dark")
        s.limb((-0.10, 1.06, 0.15), (-0.30, 1.40, 0.10), 0.01, 0.006, 4, "gun_light")    # rabbit ears
        s.limb((0.10, 1.06, 0.15), (0.32, 1.38, 0.12), 0.01, 0.006, 4, "gun_light")
    elif kind == "flat":
        s.box(-1.30, 0, -0.30, 1.30, 0.40, 0.30, "stuff_dark", top="stuff")
        s.box(-0.10, 0.40, -0.05, 0.10, 0.56, 0.08, "gun_dark")
        screen_on(s, -1.25, 0.56, 1.25, 1.36, 0.0)
    else:
        for x in (-2.0, 2.0):
            s.box(x - 0.12, 0, -0.20, x + 0.12, 0.30, 0.20, "gun_dark")
            s.box(x - 0.06, 0.30, -0.04, x + 0.06, 0.70, 0.06, "gun_metal")
        screen_on(s, -2.30, 0.70, 2.30, 2.20, 0.0)
        s.box(-0.80, 0.0, -0.40, 0.80, 0.30, 0.20, "gun_dark", top="gun_metal")    # speaker bar
    return s


def telescope():
    """A long tube on a tripod, aimed up toward the north-east."""
    s = Shape()
    top = (0.0, 0.92, 0.0)
    for a in (0.5, 2.6, 4.7):
        s.limb((0.42 * math.cos(a), 0.0, 0.42 * math.sin(a)), top, 0.025, 0.02, 5, "stuff_dark")
    s.box(-0.06, 0.88, -0.06, 0.06, 1.00, 0.06, "gun_dark")
    s.loft([((-0.30, 0.86, -0.36), 0.07, 0.07), ((0.42, 1.30, 0.42), 0.09, 0.09), ((0.46, 1.33, 0.46), 0.11, 0.11)], 8, "brass")
    s.loft([((0.46, 1.33, 0.46), 0.08, 0.08), ((0.47, 1.335, 0.47), 0.08, 0.08)], 8, "glass")
    s.limb((-0.10, 0.98, -0.12), (-0.12, 1.10, -0.18), 0.02, 0.02, 5, "gun_dark")  # finder
    return s


def tool_cabinet():
    """1 x 2: a tall red tool chest with drawers, and tools hung on a board above."""
    s = Shape()
    s.box(-0.42, 0, -0.85, 0.42, 0.95, 0.40, "paint_red", top="gun_dark")
    for k in range(5):
        y = 0.10 + k * 0.16
        s.box(-0.38, y, -0.87, 0.38, y + 0.12, -0.85, "paint_red")
        s.box(-0.10, y + 0.05, -0.89, 0.10, y + 0.07, -0.87, "gun_light")
    s.box(-0.46, 0.95, 0.30, 0.46, 1.70, 0.40, "stuff_dark")
    s.limb((-0.30, 1.10, 0.29), (-0.30, 1.50, 0.29), 0.018, 0.012, 4, "gun_metal")     # spanner, hammer, saw
    s.box(-0.06, 1.20, 0.27, 0.06, 1.55, 0.29, "gun_light")
    s.box(0.18, 1.12, 0.27, 0.36, 1.50, 0.29, "gun_light")
    for x, z in ((-0.30, -0.70), (0.30, -0.70), (-0.30, 0.25), (0.30, 0.25)):
        s.prism(x, z, 0.04, 0.04, -0.0, 0.04, 6, "rubber")
    return s


def vitals_monitor():
    s = Shape()
    s.prism(0, 0, 0.22, 0.18, 0, 0.05, 8, "gun_dark")
    s.prism(0, 0, 0.03, 0.03, 0.05, 1.05, 6, "gun_light")
    s.box(-0.22, 1.00, -0.08, 0.22, 1.34, 0.08, "gun_white")
    screen_on(s, -0.18, 1.04, 0.18, 1.30, -0.085, mat="glow_green")
    s.box(-0.14, 0.60, -0.06, 0.14, 0.72, 0.06, "gun_white")
    return s


def sculpture(seed, size):
    """Abstract art: twisting forms on a plinth, in the sculpture's own material."""
    rng = random.Random(seed)
    s = Shape()
    w = 0.32 * size
    s.box(-w, 0, -w, w, 0.14 * size, w, "stuff_dark", top="stuff")
    kind = seed % 3
    h0 = 0.14 * size
    if kind == 0:                                     # a spiral column
        prev = (0.0, h0, 0.0)
        for k in range(1, 9):
            a = k * 0.9
            p = (0.12 * size * math.cos(a), h0 + k * 0.12 * size, 0.12 * size * math.sin(a))
            s.limb(prev, p, 0.07 * size * (1 - k / 14), 0.06 * size * (1 - k / 14), 6, "stuff")
            prev = p
    elif kind == 1:                                   # stacked stones
        y = h0
        for k in range(4):
            r = (0.24 - 0.04 * k) * size
            s.lump(rng.uniform(-0.04, 0.04), y, rng.uniform(-0.04, 0.04), r, r * 0.9, r, "stuff", rng, sides=7, jitter=0.12, closed=True)
            y += r * 0.75
    else:                                             # a figure, arms raised
        s.loft([((0, h0, 0), 0.10 * size, 0.08 * size), ((0, h0 + 0.40 * size, 0), 0.13 * size, 0.09 * size),
                ((0, h0 + 0.62 * size, 0), 0.07 * size, 0.06 * size)], 7, "stuff")
        s.lump(0, h0 + 0.60 * size, 0, 0.09 * size, 0.17 * size, 0.09 * size, "stuff", rng, sides=7, jitter=0.05, closed=True)
        for sx in (-1, 1):
            s.limb((sx * 0.10 * size, h0 + 0.52 * size, 0), (sx * 0.24 * size, h0 + 0.86 * size, 0.04 * size), 0.035 * size, 0.025 * size, 5, "stuff")
    return s


# ---------------------------------------------------------------------------- production

def paste_dispenser():
    """3 x 4: a big steel machine with a serving hatch on the south face and hopper pipes behind."""
    s = Shape()
    s.box(-1.40, 0, -1.40, 1.40, 1.20, 1.10, "metal", top="gun_light")
    s.box(-1.45, 1.20, -1.45, 1.45, 1.28, 1.15, "gun_metal")
    s.box(-0.45, 0.35, -1.43, 0.45, 0.80, -1.40, "gun_dark")                        # serving hatch
    s.box(-0.35, 0.40, -1.44, 0.35, 0.46, -1.43, "food_paste")
    screen_on(s, 0.70, 0.75, 1.15, 1.05, -1.415, mat="glow_amber")
    for x in (-1.0, 0.0, 1.0):                                                     # pipes to the hoppers
        pipe(s, (x, 0.90, 1.10), (x, 0.90, 1.85), 0.08)
        s.prism(x, 1.10, 0.12, 0.12, 0.84, 0.96, 8, "gun_dark")
    s.prism(-0.90, 0.20, 0.22, 0.22, 1.28, 1.70, 10, "metal")                     # vats on top
    s.prism(0.60, 0.10, 0.30, 0.28, 1.28, 1.60, 10, "metal")
    return s


def hopper():
    s = Shape()
    s.legs(-0.42, -0.42, 0.42, 0.42, 0.66, 0.08, "gun_dark")
    s.box(-0.30, 0.0, -0.30, 0.30, 0.22, 0.30, "gun_metal", top="gun_dark")                # chute box
    s.loft([((0, 0.22, 0), 0.20, 0.20), ((0, 0.66, 0), 0.58, 0.58)], 4, "metal", cap_start=True, cap_end=False)
    s.box(-0.44, 0.62, -0.44, 0.44, 0.68, 0.44, "gun_metal")
    s.box(-0.36, 0.56, -0.36, 0.36, 0.60, 0.36, "food_yellow")                               # grain inside
    return s


def biofuel_refinery():
    """2 x 2: two fat tanks, a still between them, pipes and a gauge."""
    s = Shape()
    s.box(-0.95, 0, -0.95, 0.95, 0.10, 0.95, "concrete")
    tank(s, -0.50, 0.40, 0.36, 0.10, 1.10, "metal", "gun_light")
    tank(s, 0.50, 0.40, 0.30, 0.10, 0.90, "chemfuel", "gun_dark")
    s.box(-0.60, 0.10, -0.85, 0.60, 0.70, -0.20, "gun_dark", top="gun_metal")
    pipe(s, (-0.50, 0.85, 0.05), (-0.20, 0.85, -0.30), 0.05)
    pipe(s, (0.50, 0.70, 0.10), (0.20, 0.60, -0.30), 0.05)
    s.prism(0.30, -0.86, 0.07, 0.07, 0.40, 0.42, 8, "gun_white")
    screen_on(s, -0.40, 0.40, 0.0, 0.60, -0.855, mat="glow_amber")
    return s


def fabrication_bench():
    """5 x 2: a long electric bench with a gantry arm, screens and parts."""
    s = Shape()
    y = bench_base(s, metal=True, width=5.0, depth=2.0)
    for x in (-2.30, 2.30):                                                         # gantry
        s.box(x - 0.08, y, 0.60, x + 0.08, y + 1.00, 0.76, "gun_dark")
    s.box(-2.38, y + 1.00, 0.56, 2.38, y + 1.12, 0.80, "warning")
    s.box(-0.30, y + 0.70, 0.10, 0.10, y + 1.00, 0.70, "gun_metal")                 # the working head
    s.prism(-0.10, 0.10, 0.04, 0.01, y + 0.40, y + 0.70, 6, "glow_screen")
    screen_on(s, 1.20, y + 0.20, 2.10, y + 0.70, 0.70, facing=-1)
    s.box(-2.00, y, -0.60, -1.20, y + 0.20, 0.10, "gun_olive")
    for k in range(5):
        s.box(-0.90 + k * 0.30, y, -0.70, -0.70 + k * 0.30, y + 0.06, -0.50, "terminal")
    return s


def crematorium():
    """2 x 2: a brick furnace with a glowing door and a tall chimney."""
    s = Shape()
    s.box(-0.95, 0, -0.85, 0.95, 1.00, 0.85, "stuff_block_dark", top="stuff_block")
    s.box(-0.45, 0.20, -0.88, 0.45, 0.65, -0.85, "gun_dark")
    s.box(-0.35, 0.28, -0.89, 0.35, 0.58, -0.88, "ember")
    s.box(0.40, 1.00, 0.20, 0.80, 2.10, 0.60, "stuff_block_dark", top="pit")
    s.box(-0.80, 1.00, -0.60, 0.20, 1.10, 0.40, "gun_metal")
    return s


def hitech_research_bench():
    """3 x 2: a research desk with screens, a scanner and a glowing core."""
    s = Shape()
    y = bench_base(s, metal=True, width=3.0, depth=2.0)
    for x in (-0.90, 0.0, 0.90):
        screen_on(s, x - 0.38, y + 0.20, x + 0.38, y + 0.68, 0.60)
        s.box(x - 0.05, y, 0.62, x + 0.05, y + 0.20, 0.72, "gun_dark")
    s.box(-0.40, y, -0.50, 0.40, y + 0.04, -0.20, "gun_dark")                       # keyboard
    s.prism(1.10, -0.40, 0.16, 0.12, y, y + 0.30, 8, "gun_white")
    s.prism(1.10, -0.40, 0.08, 0.08, y + 0.30, y + 0.42, 8, "glow_screen")
    s.box(-1.30, y, -0.60, -0.90, y + 0.25, -0.20, "gun_white")
    return s


def multi_analyzer():
    """3 x 2: a tall machine of panels, lights and a glowing analysis drum."""
    s = Shape()
    s.box(-1.40, 0, -0.30, 1.40, 1.30, 0.90, "gun_white", top="gun_light")
    s.box(-1.45, 0, -0.95, 1.45, 0.50, -0.30, "gun_metal", top="gun_dark")
    for x in (-1.0, 0.0, 1.0):
        screen_on(s, x - 0.35, 0.60, x + 0.35, 1.10, -0.31)
    s.loft([((0.0, 0.50, -0.65), 0.22, 0.22), ((0.0, 0.70, -0.65), 0.22, 0.22)], 10, "glow_screen")
    for k in range(6):
        s.box(-1.30 + k * 0.45, 1.18, -0.32, -1.20 + k * 0.45, 1.24, -0.30, ("glow_green", "glow_red", "glow_amber")[k % 3])
    return s


def deep_drill():
    """A drill tower: a frame of girders over a turning bit and a motor."""
    s = Shape()
    s.box(-0.45, 0, -0.45, 0.45, 0.10, 0.45, "concrete")
    for x in (-0.36, 0.36):
        for z in (-0.36, 0.36):
            s.limb((x, 0.10, z), (x * 0.4, 1.60, z * 0.4), 0.035, 0.03, 4, "warning")
    for y in (0.60, 1.10):
        r = 0.36 * (1 - 0.6 * (y - 0.1) / 1.5)
        for a, b in (((-r, -r), (r, -r)), ((r, -r), (r, r)), ((r, r), (-r, r)), ((-r, r), (-r, -r))):
            s.limb((a[0], y, a[1]), (b[0], y, b[1]), 0.02, 0.02, 4, "warning")
    s.box(-0.20, 0.40, -0.20, 0.20, 0.75, 0.20, "gun_dark")
    s.prism(0, 0, 0.06, 0.02, 0.0, 0.40, 6, "gun_light")
    s.box(-0.18, 1.55, -0.18, 0.18, 1.70, 0.18, "gun_metal")
    return s


def gp_scanner():
    """2 x 2: a squat scanner with a ring of sensor arms over the ground."""
    s = Shape()
    s.prism(0, 0, 0.70, 0.60, 0, 0.20, 12, "gun_metal")
    s.prism(0, 0, 0.40, 0.30, 0.20, 0.70, 10, "gun_white")
    s.prism(0, 0, 0.18, 0.18, 0.70, 0.86, 8, "glow_screen")
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        s.limb((0.35 * math.cos(a), 0.55, 0.35 * math.sin(a)), (0.85 * math.cos(a), 0.10, 0.85 * math.sin(a)), 0.04, 0.03, 5, "gun_dark")
    return s


def mineral_scanner():
    """3 x 3: a big dish on a turntable, aimed at the sky."""
    s = Shape()
    s.box(-1.2, 0, -1.2, 1.2, 0.12, 1.2, "concrete")
    s.prism(0, 0, 0.50, 0.45, 0.12, 0.45, 10, "gun_metal")
    s.prism(0, 0, 0.12, 0.12, 0.45, 1.10, 8, "gun_dark")
    s.loft([((0.0, 1.10, -0.20), 0.15, 0.15), ((0.0, 1.45, 0.05), 1.00, 1.00), ((0.0, 1.50, 0.10), 1.05, 1.05)], 14, "gun_white", cap_start=False, cap_end=True)
    s.limb((0.0, 1.30, -0.05), (0.0, 1.90, 0.60), 0.025, 0.02, 5, "gun_light")
    s.prism(0.0, 0.62, 0.05, 0.05, 1.86, 1.96, 6, "glow_red")
    return s


def comms_console():
    """3 x 2: a radio desk with screens, dials, a microphone and an aerial."""
    s = Shape()
    y = bench_base(s, metal=True, width=3.0, depth=2.0)
    s.box(-1.30, y, 0.20, 1.30, y + 0.62, 0.80, "gun_metal", top="gun_dark")
    for x in (-0.80, 0.20):
        screen_on(s, x - 0.32, y + 0.20, x + 0.32, y + 0.52, 0.19)
    for k in range(6):
        s.prism(0.80 + (k % 3) * 0.16, 0.18, 0.04, 0.04, y + 0.20 + (k // 3) * 0.20, y + 0.26 + (k // 3) * 0.20, 6, "gun_light")
    s.limb((0.30, y, -0.30), (0.25, y + 0.25, -0.35), 0.012, 0.012, 4, "gun_dark")
    s.prism(0.25, -0.35, 0.03, 0.03, y + 0.25, y + 0.31, 6, "gun_dark")
    s.limb((1.10, y + 0.62, 0.60), (1.10, y + 1.80, 0.60), 0.02, 0.008, 4, "gun_light")
    return s


def trade_beacon():
    s = Shape()
    s.box(-0.30, 0, -0.30, 0.30, 0.12, 0.30, "gun_metal")
    s.prism(0, 0, 0.10, 0.06, 0.12, 1.10, 6, "gun_white")
    s.prism(0, 0, 0.14, 0.14, 1.10, 1.18, 8, "gun_dark")
    s.prism(0, 0, 0.09, 0.0, 1.18, 1.36, 8, "glow_screen")
    return s


def moisture_pump():
    s = Shape()
    s.box(-0.40, 0, -0.40, 0.40, 0.10, 0.40, "concrete")
    s.box(-0.26, 0.10, -0.26, 0.26, 0.70, 0.26, "gun_metal", top="gun_dark")
    s.prism(0, 0, 0.08, 0.08, 0.70, 0.95, 8, "steam_pipe")
    s.limb((0.0, 0.88, 0.0), (0.38, 0.60, 0.0), 0.04, 0.04, 6, "steam_pipe")
    s.limb((0.38, 0.60, 0.0), (0.38, 0.10, 0.0), 0.04, 0.04, 6, "steam_pipe")
    s.prism(0.38, 0.0, 0.08, 0.08, 0.10, 0.14, 8, "water")
    return s


def cryptosleep_casket(ship=False):
    """1 x 2: a pod with a frosted glass lid, head to the north."""
    s = Shape()
    body = "hull" if ship else "gun_white"
    s.box(-0.44, 0, -0.92, 0.44, 0.40, 0.92, body, top="gun_light")
    s.loft([((0, 0.40, -0.85), 0.36, 0.02), ((0, 0.40, -0.70), 0.38, 0.16), ((0, 0.40, 0.70), 0.38, 0.16), ((0, 0.40, 0.85), 0.36, 0.02)],
           8, "glass", cap_start=False, cap_end=False)
    s.box(-0.30, 0.40, 0.80, 0.30, 0.60, 0.92, body)
    screen_on(s, -0.14, 0.44, 0.14, 0.56, 0.93, mat="glow_screen", facing=1)
    for z in (-0.6, 0.0, 0.6):
        s.box(-0.46, 0.10, z - 0.03, 0.46, 0.30, z + 0.03, "gun_dark")
    return s


def transport_pod():
    s = Shape()
    s.loft([((0, 0.0, 0), 0.36, 0.36), ((0, 0.20, 0), 0.42, 0.42), ((0, 0.70, 0), 0.38, 0.38), ((0, 0.95, 0), 0.20, 0.20), ((0, 1.02, 0), 0.0, 0.0)],
           10, "hull")
    s.box(-0.20, 0.20, -0.42, 0.20, 0.62, -0.38, "hull_dark")
    s.prism(0, 0, 0.44, 0.44, 0.40, 0.46, 10, "warning")
    return s


def pod_launcher():
    """1 x 2: a fuel tank and a launch cradle."""
    s = Shape()
    s.box(-0.45, 0, -0.95, 0.45, 0.12, 0.95, "concrete")
    lying_tank(s, -0.38, 0.38, 0.40, 0.50, 0.26, "chemfuel")
    for x in (-0.30, 0.30):
        s.box(x - 0.05, 0.12, 0.40, x + 0.05, 0.20, 0.60, "gun_dark")
    s.box(-0.40, 0.12, -0.90, 0.40, 0.30, -0.10, "gun_metal")
    for x in (-0.36, 0.36):
        s.limb((x, 0.30, -0.80), (x * 0.7, 1.00, -0.50), 0.03, 0.025, 4, "warning")
    pipe(s, (0.0, 0.40, 0.25), (0.0, 0.30, -0.10), 0.04)
    return s


# ---------------------------------------------------------------------------- power and climate

def geothermal():
    """6 x 6: a plant built over a steam vent: a hall, two cooling towers and pipework."""
    s = Shape()
    s.box(-2.9, 0, -2.9, 2.9, 0.15, 2.9, "concrete")
    s.box(-2.6, 0.15, -2.6, 0.4, 1.40, 0.4, "gun_metal", top="gun_dark")
    s.box(-2.7, 1.40, -2.7, 0.5, 1.50, 0.5, "metal_dark")
    for x, z in ((1.6, 1.6), (1.6, -1.2)):
        s.loft([((x, 0.15, z), 0.95, 0.95), ((x, 1.20, z), 0.70, 0.70), ((x, 2.20, z), 0.80, 0.80)], 14, "concrete", cap_start=False, cap_end=False)
        s.prism(x, z, 0.80, 0.80, 2.18, 2.20, 14, "pit")
    pipe(s, (0.4, 0.80, -1.2), (0.8, 0.80, -1.2), 0.14)
    pipe(s, (0.4, 0.80, 1.6), (0.8, 0.80, 1.6), 0.14)
    pipe(s, (-1.0, 0.40, 0.4), (-1.0, 0.40, 2.4), 0.12)
    pipe(s, (-1.0, 0.40, 2.4), (0.6, 0.40, 2.4), 0.12)
    for k in range(4):
        s.box(-2.4 + k * 0.7, 0.55, -2.62, -2.0 + k * 0.7, 1.05, -2.60, "glass_dark")
    return s


def watermill():
    """6 x 5: a timber mill house beside a big paddle wheel turning in the river."""
    s = Shape()
    s.box(-2.8, 0, 0.6, 2.8, 1.30, 2.3, "stuff_dark", top="stuff")
    s.wedge(-2.9, 0.5, 2.9, 2.4, 1.30, 1.75, 0.08, "stuff_deep", top="stuff_dark")
    for x in (-2.0, 2.0):
        s.box(x - 0.12, 0, -1.8, x + 0.12, 1.20, 0.6, "stuff_dark")                 # supports for the axle
    pipe(s, (-2.2, 1.0, -0.6), (2.2, 1.0, -0.6), 0.10, mat="gun_dark", sides=8)
    n = 12
    for side in (-1.2, 1.2):
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            s.limb((side, 1.0 + 0.95 * math.sin(a0), -0.6 + 0.95 * math.cos(a0)),
                   (side, 1.0 + 0.95 * math.sin(a1), -0.6 + 0.95 * math.cos(a1)), 0.05, 0.05, 4, "stuff_dark")
    for i in range(n):
        a = 2 * math.pi * i / n
        y, z = 1.0 + 0.95 * math.sin(a), -0.6 + 0.95 * math.cos(a)
        s.box(-1.2, y - 0.04, z - 0.14, 1.2, y + 0.04, z + 0.14, "stuff")             # paddles
        s.limb((-1.2, 1.0, -0.6), (-1.2, y, z), 0.025, 0.025, 4, "stuff_dark")
        s.limb((1.2, 1.0, -0.6), (1.2, y, z), 0.025, 0.025, 4, "stuff_dark")
    return s


def chemfuel_generator():
    """2 x 2: a generator engine with an exhaust stack and a red fuel tank."""
    s = Shape()
    s.box(-0.90, 0, -0.85, 0.90, 0.12, 0.85, "concrete")
    s.box(-0.80, 0.12, -0.75, 0.30, 0.85, 0.75, "metal", top="gun_metal")
    for k in range(5):
        s.box(-0.70 + k * 0.2, 0.30, -0.78, -0.62 + k * 0.2, 0.75, -0.75, "gun_dark")   # cooling fins
    lying_tank(s, 0.35, 0.85, 0.40, 0.0, 0.28, "chemfuel")
    s.prism(-0.50, 0.45, 0.10, 0.08, 0.85, 1.65, 8, "gun_dark")
    s.prism(-0.50, 0.45, 0.12, 0.12, 1.55, 1.62, 8, "gun_metal")
    screen_on(s, 0.0, 0.50, 0.25, 0.70, -0.76, mat="glow_amber")
    return s


def power_switch():
    s = Shape()
    s.box(-0.18, 0, -0.14, 0.18, 0.42, 0.14, "gun_metal", top="gun_dark")
    s.box(-0.04, 0.20, -0.18, 0.04, 0.34, -0.14, "gun_dark")
    s.limb((0.0, 0.27, -0.18), (0.0, 0.40, -0.30), 0.02, 0.018, 4, "warning")
    s.prism(0.10, -0.15, 0.025, 0.025, 0.34, 0.36, 6, "glow_green")
    return s


def cooler(vent=False):
    """Set into a wall: a full-height block with a fan or grille on each face."""
    s = Shape()
    s.box(-0.5, 0, -0.5, 0.5, 1.20, 0.5, "gun_metal", top="gun_dark")
    for face in (-1, 1):
        z = face * 0.5
        if vent:
            for k in range(5):
                y = 0.35 + k * 0.10
                s.box(-0.32, y, z, 0.32, y + 0.05, z + face * 0.03, "gun_dark")
        else:
            s.loft([((0, 0.62, z), 0.34, 0.34), ((0, 0.62, z + face * 0.04), 0.34, 0.34)], 12, "gun_dark")
            for k in range(3):
                a = k * 2.094
                s.box(-0.04, 0.62 - 0.28, z + face * 0.045, 0.04, 0.62 + 0.28, z + face * 0.05, "ice" if face < 0 else "gun_light")
    return s


def passive_cooler():
    """A wooden frame holding trays of water and wet cloth."""
    s = Shape()
    s.legs(-0.42, -0.42, 0.42, 0.42, 0.70, 0.06, "stuff_dark")
    for y in (0.20, 0.50):
        s.box(-0.40, y, -0.40, 0.40, y + 0.06, 0.40, "stuff")
        s.box(-0.34, y + 0.06, -0.34, 0.34, y + 0.08, 0.34, "water")
    s.box(-0.44, 0.70, -0.44, 0.44, 0.76, 0.44, "stuff_dark", top="stuff")
    s.box(-0.38, 0.30, -0.43, 0.38, 0.66, -0.41, "linen")
    return s


# ---------------------------------------------------------------------------- security

def turret_base(kind):
    """The fixed part of a turret. Its gun is a separate model the mod turns (turret_gun_*)."""
    s = Shape()
    if kind == "mini":
        for a in (0.4, 2.5, 4.6):
            s.limb((0.40 * math.cos(a), 0.0, 0.40 * math.sin(a)), (0, 0.40, 0), 0.04, 0.03, 5, "gun_dark")
        s.prism(0, 0, 0.14, 0.14, 0.36, 0.46, 8, "gun_metal")
    elif kind == "mortar":
        s.prism(0, 0, 0.45, 0.42, 0.0, 0.08, 10, "gun_metal")
        s.prism(0, 0, 0.18, 0.18, 0.08, 0.26, 8, "gun_dark")
        for x in (-0.25, 0.25):
            s.limb((x, 0.0, 0.25), (x * 0.4, 0.26, 0.0), 0.03, 0.03, 4, "gun_dark")
    else:                                                         # autocannon, sniper: a squat armoured mount
        s.box(-0.85, 0, -0.85, 0.85, 0.20, 0.85, "concrete")
        s.prism(0, 0, 0.62, 0.52, 0.20, 0.55, 8, "gun_metal" if kind == "auto" else "paint_olive", turn=math.pi / 8)
        s.prism(0, 0, 0.30, 0.30, 0.55, 0.66, 8, "gun_dark")
    return s


def turret_gun(kind):
    """A turret's gun, built round its pivot at the origin, muzzle toward +x."""
    s = Shape()
    if kind == "mini":
        s.box(-0.20, -0.06, -0.12, 0.16, 0.12, 0.12, "gun_metal")
        s.box(0.16, 0.0, -0.025, 0.62, 0.05, 0.025, "gun_dark")
        s.box(-0.10, -0.10, -0.14, 0.05, 0.04, -0.12, "terminal")                     # ammo box
    elif kind == "auto":
        s.box(-0.45, -0.10, -0.32, 0.35, 0.28, 0.32, "gun_metal")
        s.box(-0.40, 0.28, -0.24, 0.20, 0.34, 0.24, "gun_dark")
        for z in (-0.12, 0.12):
            s.box(0.35, 0.04, z - 0.045, 1.25, 0.13, z + 0.045, "gun_dark")
            s.box(1.15, 0.02, z - 0.06, 1.28, 0.15, z + 0.06, "gun_dark")
    elif kind == "sniper":
        s.box(-0.40, -0.08, -0.22, 0.30, 0.22, 0.22, "paint_olive")
        s.box(0.30, 0.04, -0.035, 1.55, 0.11, 0.035, "gun_dark")
        s.box(1.45, 0.02, -0.06, 1.62, 0.13, 0.06, "gun_dark")
        s.box(-0.10, 0.22, -0.05, 0.25, 0.30, 0.05, "gun_dark")
    else:                                                         # mortar tube, raised
        s.loft([((-0.15, 0.0, 0.0), 0.11, 0.11), ((0.45, 0.62, 0.0), 0.10, 0.10)], 8, "gun_dark")
        s.prism(-0.15, 0.0, 0.14, 0.14, -0.05, 0.03, 8, "gun_metal")
    return s


def spike_trap():
    rng = random.Random(12)
    s = Shape()
    s.box(-0.44, 0, -0.44, 0.44, 0.05, 0.44, "stuff_dark", top="stuff")
    for k in range(9):
        x, z = -0.30 + (k % 3) * 0.30 + rng.uniform(-0.04, 0.04), -0.30 + (k // 3) * 0.30 + rng.uniform(-0.04, 0.04)
        s.prism(x, z, 0.045, 0.0, 0.05, rng.uniform(0.22, 0.32), 4, "stuff", turn=rng.uniform(0, 1))
    return s


def ied(band):
    """A shell half buried in the earth, with wires to a trigger plate."""
    s = Shape()
    s.prism(0, 0, 0.36, 0.30, 0.0, 0.05, 9, "soil")
    s.loft([((-0.26, 0.10, 0.02), 0.08, 0.08), ((0.12, 0.12, 0.02), 0.09, 0.09), ((0.24, 0.12, 0.02), 0.05, 0.05)], 8, "shell_olive")
    s.loft([((-0.10, 0.11, 0.02), 0.095, 0.095), ((-0.02, 0.115, 0.02), 0.098, 0.098)], 8, band)
    s.box(0.12, 0.04, -0.30, 0.34, 0.06, -0.12, "gun_dark")
    s.limb((0.20, 0.10, 0.02), (0.22, 0.06, -0.18), 0.008, 0.008, 3, "paint_red")
    return s


def firefoam_popper():
    s = Shape()
    tank(s, 0, 0, 0.22, 0.0, 0.55, "paint_red", "gun_light")
    for k in range(4):
        a = k * math.pi / 2
        s.limb((0.0, 0.70, 0.0), (0.24 * math.cos(a), 0.78, 0.24 * math.sin(a)), 0.025, 0.035, 6, "gun_light")
    return s


# ---------------------------------------------------------------------------- the ship

def ship_beam():
    """1 x 3: a structural girder of the starship."""
    s = Shape()
    s.box(-0.45, 0, -1.45, 0.45, 0.20, 1.45, "hull_dark")
    s.box(-0.30, 0.20, -1.45, 0.30, 0.60, 1.45, "hull", top="hull_dark")
    for z in (-1.0, 0.0, 1.0):
        s.box(-0.38, 0.0, z - 0.10, 0.38, 0.66, z + 0.10, "hull_dark")
        s.prism(0.31, z, 0.04, 0.04, 0.38, 0.42, 6, "glow_screen")
    return s


def ship_computer_core():
    s = Shape()
    s.box(-0.90, 0, -0.90, 0.90, 0.20, 0.90, "hull_dark")
    s.prism(0, 0, 0.70, 0.60, 0.20, 1.20, 8, "hull", turn=math.pi / 8)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        s.box(0.62 * math.cos(a) - 0.04, 0.40, 0.62 * math.sin(a) - 0.04, 0.62 * math.cos(a) + 0.04, 1.0, 0.62 * math.sin(a) + 0.04, "glow_screen")
    s.prism(0, 0, 0.30, 0.20, 1.20, 1.50, 8, "glow_screen")
    return s


def ship_reactor():
    """3 x 4: a reactor drum in a cradle of shielding, glowing at the seams."""
    s = Shape()
    s.box(-1.45, 0, -1.90, 1.45, 0.25, 1.90, "hull_dark")
    s.loft([((0, 1.05, -1.70), 0.95, 0.95), ((0, 1.05, -1.30), 1.15, 1.15), ((0, 1.05, 1.30), 1.15, 1.15), ((0, 1.05, 1.70), 0.95, 0.95)],
           12, "hull")
    for z in (-0.80, 0.0, 0.80):
        s.loft([((0, 1.05, z - 0.06), 1.18, 1.18), ((0, 1.05, z + 0.06), 1.18, 1.18)], 12, "glow_screen")
    for x in (-1.2, 1.2):
        s.box(x - 0.15, 0.25, -1.6, x + 0.15, 1.0, 1.6, "hull_dark")
    return s


def ship_engine():
    """3 x 5: a big drive with its nozzle to the south."""
    s = Shape()
    s.loft([((0, 1.05, 2.40), 0.70, 0.70), ((0, 1.05, 1.80), 1.20, 1.20), ((0, 1.05, -0.60), 1.30, 1.30), ((0, 1.05, -1.50), 1.00, 1.00)], 10, "hull")
    s.loft([((0, 1.05, -1.50), 0.95, 0.95), ((0, 1.05, -2.40), 1.30, 1.30)], 10, "hull_dark", cap_start=False, cap_end=False)
    s.loft([((0, 1.05, -2.30), 1.05, 1.05), ((0, 1.05, -1.70), 0.55, 0.55)], 10, "glow_screen", cap_start=False)
    for x in (-1.1, 1.1):
        s.box(x - 0.2, 0, -1.6, x + 0.2, 0.60, 2.0, "hull_dark")
    return s


def ship_sensor():
    s = Shape()
    s.box(-0.45, 0, -0.45, 0.45, 0.20, 0.45, "hull_dark")
    s.prism(0, 0, 0.10, 0.10, 0.20, 0.90, 8, "hull")
    s.loft([((0, 0.90, 0), 0.10, 0.10), ((0, 1.20, 0.15), 0.45, 0.45)], 10, "hull", cap_start=False)
    s.prism(0, 0.25, 0.05, 0.05, 1.20, 1.45, 6, "glow_screen")
    return s


# ---------------------------------------------------------------------------- ruins, wrecks and junk

def ship_chunk(seed):
    """2 x 2: twisted hull plating and broken ribs from a crashed ship."""
    rng = random.Random(seed)
    s = Shape()
    for k in range(4):
        x, z = rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5)
        w, d, h = rng.uniform(0.4, 0.8), rng.uniform(0.3, 0.6), rng.uniform(0.25, 0.7)
        tilt = rng.uniform(-0.25, 0.25)
        s.wedge(x - w / 2, z - d / 2, x + w / 2, z + d / 2, h * (1 + tilt), h * (1 - tilt), 0.06, rng.choice(("hull", "hull_dark")))
        s.box(x - w / 2 + 0.05, 0, z - d / 2 + 0.05, x + w / 2 - 0.05, h * 0.85, z + d / 2 - 0.05, "hull_dark")
    for k in range(3):
        a = rng.uniform(0, 6.28)
        s.limb((0.3 * math.cos(a), 0.0, 0.3 * math.sin(a)), (0.75 * math.cos(a), rng.uniform(0.4, 0.9), 0.75 * math.sin(a)), 0.04, 0.025, 4, "gun_metal")
    s.box(-0.20, 0.30, -0.80, 0.25, 0.40, -0.70, "glow_red")
    return s


def car(kind):
    """Rusted wrecks of old ground cars, 3 x 2, long east-west. kind: sedan, frame (stripped), jeep, truck."""
    rng = random.Random(len(kind))
    s = Shape()
    body = {"sedan": "rust", "frame": "rust_dark", "jeep": "paint_olive", "truck": "paint_blue"}[kind]
    if kind == "frame":
        for z in (-0.40, 0.40):
            s.box(-1.30, 0.20, z - 0.06, 1.30, 0.32, z + 0.06, "rust_dark")
        for x in (-0.90, 0.0, 0.90):
            s.box(x - 0.06, 0.20, -0.46, x + 0.06, 0.30, 0.46, "rust_dark")
        s.box(0.70, 0.30, -0.30, 1.20, 0.60, 0.30, "rust")                            # engine block
        wheel(s, -0.85, 0.14, -0.55, 0.16, 0.12, axis="z")
        s.lump(0.85, 0.0, 0.55, 0.14, 0.10, 0.14, "rubber", rng, sides=6, jitter=0.2)
        return s
    low, top = (0.18, 0.62) if kind != "truck" else (0.22, 0.80)
    s.box(-1.35, low, -0.62, 1.35, top, 0.62, body, top="rust_light" if kind == "sedan" else body)
    if kind in ("sedan", "jeep"):
        s.wedge(-0.55, -0.56, 0.55, 0.56, top + 0.30, top + 0.30, 0.30, body)          # cabin
        s.box(-0.56, top + 0.02, -0.57, 0.56, top + 0.26, -0.55, "glass_dark")
        s.box(-0.56, top + 0.02, 0.55, 0.56, top + 0.26, 0.57, "glass_dark")
        s.box(0.55, top + 0.02, -0.50, 0.57, top + 0.26, 0.50, "glass_dark")
        if kind == "jeep":
            s.box(-1.30, top, -0.60, -0.60, top + 0.10, 0.60, "paint_olive")
            s.limb((-0.55, top, -0.55), (-0.55, top + 0.45, -0.55), 0.02, 0.02, 4, "gun_dark")
    else:
        s.box(0.40, top, -0.60, 1.35, top + 0.45, 0.60, body)                          # cab
        s.box(1.33, top + 0.05, -0.50, 1.36, top + 0.38, 0.50, "glass_dark")
        s.box(-1.35, top, -0.62, 0.35, top + 0.10, 0.62, "rust_dark")                   # flat bed
    for x in (-0.85, 0.85):
        for z in (-0.60, 0.60):
            if rng.random() < 0.8:
                wheel(s, x, 0.17, z, 0.18, 0.12, axis="z")
            else:
                s.lump(x, 0.0, z, 0.12, 0.08, 0.12, "rubber", rng, sides=6, jitter=0.25)
    for _ in range(4):                                                                 # rust holes and dents
        x, z = rng.uniform(-1.2, 1.2), rng.choice((-0.63, 0.63))
        s.box(x - 0.10, low + 0.10, z - 0.004, x + 0.10, low + 0.26, z + 0.004, "rust_dark")
    return s


def tank_wreck(apc=False):
    """3 x 4: a burnt-out armoured vehicle on its tracks, long north-south."""
    s = Shape()
    body = "paint_olive" if not apc else "rust"
    for x in (-1.15, 1.15):
        s.loft([((x, 0.30, -1.85), 0.20, 0.18), ((x, 0.24, -1.55), 0.24, 0.24), ((x, 0.24, 1.55), 0.24, 0.24), ((x, 0.30, 1.85), 0.20, 0.18)],
               8, "rust_dark")
        for z in (-1.2, -0.6, 0.0, 0.6, 1.2):
            wheel(s, x, 0.22, z, 0.17, 0.30)
    s.box(-0.95, 0.30, -1.80, 0.95, 0.85, 1.80, body, top="rust")
    s.wedge(-0.95, -1.95, 0.95, -1.80, 0.30, 0.85, 0.20, body)
    if apc:
        s.box(-0.80, 0.85, -0.90, 0.80, 1.20, 1.60, body, top="rust")
        s.box(-0.30, 0.40, 1.80, 0.30, 0.90, 1.82, "rust_dark")
    else:
        s.prism(0, 0.20, 0.70, 0.62, 0.85, 1.25, 8, body, top="rust", turn=math.pi / 8)
        s.loft([((0.0, 1.05, -0.30), 0.10, 0.10), ((0.15, 1.00, -2.40), 0.09, 0.09)], 8, "rust_dark")
    s.lump(0.4, 0.85, 0.9, 0.25, 0.10, 0.25, "ash", random.Random(2), sides=6, jitter=0.2)
    return s


def warwalker(part):
    """Pieces of a fallen giant war machine. torso 4 x 4, leg 2 x 4, claw 2 x 2, foot 2 x 2."""
    rng = random.Random(len(part) * 7)
    s = Shape()
    if part == "torso":
        s.lump(0, 0, 0, 1.6, 1.4, 1.5, "hull_dark", rng, sides=8, profile=((0.0, 0.85), (0.4, 1.0), (0.8, 0.70)), jitter=0.05)
        s.box(-1.2, 0.9, -1.50, 1.2, 1.3, -1.30, "hull")
        for k in range(3):
            s.box(-0.9 + k * 0.7, 1.0, -1.52, -0.6 + k * 0.7, 1.2, -1.50, "glow_red" if k == 1 else "glass_dark")
        for k in range(5):
            a = rng.uniform(0, 6.28)
            s.limb((1.2 * math.cos(a), 0.6, 1.2 * math.sin(a)), (1.8 * math.cos(a), rng.uniform(0.0, 0.4), 1.8 * math.sin(a)), 0.08, 0.05, 5, "rust")
    elif part == "leg":
        s.loft([((0, 0.40, -1.80), 0.40, 0.40), ((0, 0.55, -0.30), 0.55, 0.50), ((0, 0.50, 0.40), 0.45, 0.45), ((0, 0.35, 1.80), 0.30, 0.30)],
               8, "hull_dark")
        s.lump(0, 0, 0.40, 0.62, 1.0, 0.62, "hull", rng, sides=8, jitter=0.05)
        for z in (-1.2, 1.2):
            pipe(s, (0.42, 0.55, z), (0.42, 0.55, 0.0), 0.06, mat="rust")
    elif part == "claw":
        s.lump(0, 0, 0, 0.6, 0.6, 0.6, "hull_dark", rng, sides=7, jitter=0.08)
        for k in range(3):
            a = k * 2.1
            s.loft([((0.4 * math.cos(a), 0.4, 0.4 * math.sin(a)), 0.14, 0.14), ((0.85 * math.cos(a), 0.6, 0.85 * math.sin(a)), 0.10, 0.10),
                    ((0.95 * math.cos(a), 0.05, 0.95 * math.sin(a)), 0.0, 0.0)], 5, "hull")
    else:
        s.wedge(-0.90, -0.90, 0.90, 0.90, 0.50, 0.70, 0.50, "hull_dark")
        for x in (-0.6, 0.0, 0.6):
            s.box(x - 0.18, 0, -1.0, x + 0.18, 0.30, -0.80, "hull")
        s.prism(0, 0.2, 0.35, 0.30, 0.70, 1.10, 8, "rust")
    return s


def ruin_barrels():
    rng = random.Random(21)
    s = Shape()
    for x, z, lying in ((-0.18, -0.12, False), (0.20, 0.10, False), (0.0, 0.30, True)):
        if lying:
            lying_tank(s, x - 0.30, x + 0.30, 0.17, z, 0.17, rng.choice(("rust", "paint_blue", "chemfuel")), sides=9)
        else:
            mat = rng.choice(("rust", "paint_blue", "chemfuel"))
            s.prism(x, z, 0.17, 0.17, 0.0, 0.55, 9, mat, top="rust_dark")
            for y in (0.15, 0.40):
                s.prism(x, z, 0.18, 0.18, y, y + 0.03, 9, "rust_dark")
    return s


def ruin_crate(spacer=False):
    s = Shape()
    if spacer:
        s.box(-0.42, 0, -0.30, 0.42, 0.48, 0.30, "hull", top="hull_dark")
        s.box(-0.44, 0.20, -0.32, 0.44, 0.26, 0.32, "glow_screen")
        s.box(-0.10, 0.30, -0.31, 0.10, 0.40, -0.30, "gun_dark")
    else:
        planked_box(s, -0.40, 0, -0.32, 0.40, 0.55, 0.32, "rust", "rust_dark")
        planked_box(s, -0.25, 0.55, -0.20, 0.20, 0.85, 0.18, "stuff_dark", "rust_dark", bands=1)
    return s


def ruin_pipe():
    """A length of big pipeline lying on concrete saddles, long east-west."""
    s = Shape()
    lying_tank(s, -1.45, 1.45, 0.40, 0.0, 0.36, "rust", sides=12)
    for x in (-1.0, 1.0):
        s.box(x - 0.15, 0, -0.38, x + 0.15, 0.20, 0.38, "concrete")
    s.loft([((1.45, 0.40, 0.0), 0.40, 0.40), ((1.50, 0.40, 0.0), 0.40, 0.40)], 12, "rust_dark")
    return s


def ruin_engine():
    """A big engine block with its manifold and loose parts."""
    s = Shape()
    s.box(-0.70, 0, -0.45, 0.70, 0.70, 0.45, "rust", top="rust_dark")
    for k in range(4):
        s.prism(-0.50 + k * 0.33, 0.0, 0.11, 0.11, 0.69, 0.90, 8, "rust_dark")
    lying_tank(s, -0.70, 0.70, 0.55, -0.48, 0.08, "rust_light")
    s.loft([((0.75, 0.35, 0.0), 0.28, 0.28), ((0.85, 0.35, 0.0), 0.28, 0.28)], 10, "rust_dark")
    return s


def ruin_machine():
    """Dead machinery: cabinets, a broken screen and cables."""
    s = Shape()
    s.box(-0.90, 0, -0.40, 0.90, 1.00, 0.40, "rust_light", top="rust")
    screen_on(s, -0.70, 0.45, -0.10, 0.85, -0.41, mat="glass_dark", frame="rust_dark")
    for k in range(3):
        s.box(0.15 + k * 0.22, 0.10, -0.42, 0.30 + k * 0.22, 0.80, -0.40, "rust_dark")
    pipe(s, (0.9, 0.2, 0.0), (1.3, 0.0, 0.3), 0.04, mat="rubber")
    return s


def ruin_lamppost():
    s = Shape()
    s.prism(0, 0, 0.16, 0.12, 0, 0.10, 8, "concrete")
    s.prism(0, 0, 0.05, 0.04, 0.10, 2.20, 6, "rust")
    s.limb((0, 2.15, 0), (0.0, 2.25, -0.45), 0.035, 0.03, 5, "rust")
    s.box(-0.10, 2.10, -0.60, 0.10, 2.22, -0.38, "rust_dark")
    s.box(-0.07, 2.08, -0.57, 0.07, 2.10, -0.41, "glass_dark")
    return s


def ruin_cannon():
    """A huge ruined gun barrel lying on the ground, long east-west."""
    s = Shape()
    s.loft([((-2.4, 0.55, 0), 0.55, 0.55), ((-1.6, 0.55, 0), 0.62, 0.62), ((2.2, 0.45, 0), 0.40, 0.40), ((2.4, 0.45, 0), 0.48, 0.48)], 12, "rust")
    s.loft([((2.4, 0.45, 0), 0.30, 0.30), ((2.42, 0.45, 0), 0.30, 0.30)], 12, "pit")
    for x in (-1.0, 0.6):
        s.loft([((x, 0.55, 0), 0.66, 0.66), ((x + 0.15, 0.55, 0), 0.66, 0.66)], 12, "rust_dark")
    return s


def ruin_tripod():
    s = Shape()
    for a in (0.3, 2.4, 4.5):
        s.limb((1.2 * math.cos(a), 0.0, 1.2 * math.sin(a)), (0, 1.6, 0), 0.12, 0.09, 6, "rust")
    s.lump(0, 1.4, 0, 0.45, 0.45, 0.45, "rust_dark", random.Random(4), sides=7, jitter=0.06, closed=True)
    return s


def concrete_barrier():
    s = Shape()
    s.wedge(-0.48, -0.30, 0.48, 0.30, 0.20, 0.20, 0.20, "concrete")
    s.box(-0.48, 0.20, -0.14, 0.48, 0.75, 0.14, "concrete")
    s.box(-0.30, 0.50, -0.15, -0.10, 0.60, -0.14, "warning")
    s.box(0.10, 0.50, -0.15, 0.30, 0.60, -0.14, "warning")
    return s


def razor_wire():
    """Coils of wire along the cell, east-west."""
    s = Shape()
    n = 14
    for k in range(n):
        x0 = -0.5 + k / n
        x1 = -0.5 + (k + 1) / n
        a0, a1 = k * 1.4, (k + 1) * 1.4
        s.limb((x0, 0.25 + 0.20 * math.sin(a0), 0.20 * math.cos(a0)), (x1, 0.25 + 0.20 * math.sin(a1), 0.20 * math.cos(a1)), 0.012, 0.012, 3, "gun_light")
    for x in (-0.45, 0.45):
        s.limb((x, 0.0, 0.0), (x, 0.50, 0.0), 0.02, 0.02, 4, "rust")
    return s


def junk(seed):
    """A heap of scrap: plates, bars and a wheel half buried in it."""
    rng = random.Random(seed)
    s = Shape()
    s.lump(0, 0, 0, 0.45, 0.30, 0.40, "rust_dark", rng, sides=7, jitter=0.25)
    for k in range(6):
        x, z = rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35)
        w, d = rng.uniform(0.15, 0.35), rng.uniform(0.10, 0.25)
        s.wedge(x - w / 2, z - d / 2, x + w / 2, z + d / 2, rng.uniform(0.1, 0.35), rng.uniform(0.1, 0.35), 0.03, rng.choice(("rust", "rust_light", "gun_metal")))
    for k in range(3):
        a = rng.uniform(0, 6.28)
        s.limb((0.1 * math.cos(a), 0.15, 0.1 * math.sin(a)), (0.45 * math.cos(a), rng.uniform(0.3, 0.55), 0.45 * math.sin(a)), 0.02, 0.02, 4, "rust")
    wheel(s, rng.uniform(-0.2, 0.2), 0.14, rng.uniform(-0.2, 0.2), 0.14, 0.08, axis="z")
    return s


# ---------------------------------------------------------------------------- items
# Lying on the ground, filling about a cell, kept low: a stack or pile that shows what it is.

def ingot_stack(mat, rows=3, width=0.13, length=0.42, height=0.075):
    """Bars stacked in crossing layers: steel, plasteel, uranium, gold."""
    s = Shape()
    for r in range(rows):
        y = r * height
        n = 3 if r % 2 == 0 else 2
        for i in range(n):
            off = (i - (n - 1) / 2) * (width + 0.02)
            if r % 2 == 0:
                s.wedge(off - width / 2, -length / 2, off + width / 2, length / 2, y + height, y + height, height, mat)
            else:
                s.wedge(-length / 2, off - width / 2, length / 2, off + width / 2, y + height, y + height, height, mat)
    return s


def coin_stacks():
    rng = random.Random(31)
    s = Shape()
    for k in range(7):
        x, z = rng.uniform(-0.28, 0.28), rng.uniform(-0.28, 0.28)
        s.prism(x, z, 0.075, 0.075, 0.0, rng.uniform(0.05, 0.18), 10, "silver")
    return s


def jade_chunks():
    rng = random.Random(33)
    s = Shape()
    for k in range(4):
        x, z = rng.uniform(-0.22, 0.22), rng.uniform(-0.22, 0.22)
        s.lump(x, 0, z, 0.13, 0.15, 0.11, "jade", rng, sides=6, jitter=0.2)
    return s


def log_pile():
    """Logs stacked in a little pyramid, ends showing to east and west."""
    s = Shape()
    r = 0.075
    rows = ((-0.30, -0.15, 0.0, 0.15, 0.30), (-0.22, -0.075, 0.075, 0.22), (-0.15, 0.0, 0.15))
    for k, row in enumerate(rows):
        for z in row:
            y = r + k * r * 1.7
            s.loft([((-0.42, y, z), r, r), ((0.42, y, z), r, r)], 7, "log")
            s.loft([((0.42, y, z), r * 0.85, r * 0.85), ((0.425, y, z), r * 0.85, r * 0.85)], 7, "wood_end")
            s.loft([((-0.425, y, z), r * 0.85, r * 0.85), ((-0.42, y, z), r * 0.85, r * 0.85)], 7, "wood_end")
    return s


def components(spacer=False):
    """A small crate of machine parts: gears, circuit boards and coils."""
    s = Shape()
    body, band = ("hull", "glow_screen") if spacer else ("paint_olive", "terminal")
    s.box(-0.30, 0, -0.22, 0.30, 0.20, 0.22, body)
    s.box(-0.31, 0.06, -0.23, 0.31, 0.09, 0.23, band)
    s.prism(-0.12, 0.0, 0.10, 0.10, 0.20, 0.25, 8, "gun_light" if not spacer else "glow_screen")
    s.box(0.04, 0.20, -0.14, 0.24, 0.24, 0.10, "food_green" if not spacer else "gun_white")
    s.prism(0.15, 0.12, 0.05, 0.05, 0.24, 0.30, 6, "brass")
    return s


def fuel_cans(mat):
    s = Shape()
    for x, z in ((-0.17, 0.0), (0.17, 0.05)):
        s.box(x - 0.13, 0, z - 0.20, x + 0.13, 0.40, z + 0.20, mat)
        s.box(x - 0.05, 0.40, z + 0.05, x + 0.05, 0.47, z + 0.15, "gun_dark")
        s.box(x - 0.10, 0.40, z - 0.18, x + 0.10, 0.44, z - 0.02, mat)
    return s


def medicine(kind):
    s = Shape()
    if kind == "herbal":
        rng = random.Random(41)
        for k in range(3):
            a = k * 2.1
            s.lump(0.12 * math.cos(a), 0, 0.12 * math.sin(a), 0.16, 0.12, 0.12, "herb_green", rng, sides=6, jitter=0.2)
        s.prism(0, 0, 0.06, 0.06, 0.10, 0.14, 6, "string")
    elif kind == "industrial":
        s.box(-0.24, 0, -0.17, 0.24, 0.18, 0.17, "medicine")
        s.box(-0.04, 0.18, -0.10, 0.04, 0.186, 0.10, "red_cross")
        s.box(-0.10, 0.18, -0.03, 0.10, 0.186, 0.03, "red_cross")
        s.box(-0.10, 0.18, -0.17, 0.10, 0.20, -0.12, "gun_dark")
    else:
        s.box(-0.26, 0, -0.16, 0.26, 0.14, 0.16, "gun_white", top="gun_light")
        s.box(-0.20, 0.14, -0.10, 0.20, 0.15, 0.10, "glow_screen")
        s.box(-0.27, 0.05, -0.17, 0.27, 0.08, 0.17, "charge")
    return s


def meal(kind):
    s = Shape()
    if kind == "survival":
        for k, (x, z) in enumerate(((-0.03, -0.02), (0.02, 0.03), (-0.01, 0.0))):
            s.box(x - 0.15, k * 0.05, z - 0.11, x + 0.15, k * 0.05 + 0.05, z + 0.11, "foil")
            s.box(x - 0.15, k * 0.05 + 0.02, z - 0.115, x - 0.10, k * 0.05 + 0.03, z + 0.115, "paint_olive")
        return s
    if kind == "pemmican":
        for k in range(4):
            s.box(-0.25 + k * 0.13, 0, -0.10, -0.15 + k * 0.13, 0.06, 0.10, "food_stew")
            s.box(-0.25 + k * 0.13, 0.025, -0.11, -0.15 + k * 0.13, 0.035, 0.11, "string")
        return s
    if kind == "kibble":
        s.loft([((0, 0.0, 0), 0.22, 0.16), ((0, 0.20, 0), 0.24, 0.17), ((0, 0.34, 0), 0.14, 0.10)], 8, "sack")
        s.prism(0, 0, 0.10, 0.12, 0.34, 0.37, 6, "food_stew")
        return s
    food = {"simple": "food_stew", "fine": "food_stew", "lavish": "food_stew", "paste": "food_paste"}[kind]
    s.loft([((0, 0.0, 0), 0.12, 0.12), ((0, 0.08, 0), 0.22, 0.22)], 10, "bowl", cap_start=True, cap_end=False)
    s.prism(0, 0, 0.20, 0.17, 0.05, 0.09, 10, food)
    if kind in ("fine", "lavish"):
        s.prism(0.06, 0.04, 0.05, 0.03, 0.09, 0.13, 6, "food_green")
        s.box(-0.10, 0.09, -0.06, -0.02, 0.12, 0.02, "meat")
    if kind == "lavish":
        s.prism(-0.05, -0.08, 0.04, 0.0, 0.09, 0.15, 5, "food_yellow")
        s.loft([((0.30, 0.0, 0.10), 0.05, 0.05), ((0.30, 0.16, 0.10), 0.05, 0.05)], 8, "glass")
    return s


def produce(kind):
    rng = random.Random(len(kind) * 13)
    s = Shape()
    if kind in ("potato", "fungus", "berries", "corn", "agave", "eggs"):
        if kind == "berries":
            s.loft([((0, 0.0, 0), 0.20, 0.20), ((0, 0.16, 0), 0.26, 0.26)], 10, "log", cap_start=True, cap_end=False)
            for k in range(12):
                a, d = rng.uniform(0, 6.28), rng.uniform(0, 0.18)
                s.lump(d * math.cos(a), 0.10, d * math.sin(a), 0.04, 0.07, 0.04, "berry", rng, sides=5, jitter=0.1, closed=True)
            return s
        if kind == "eggs":
            s.prism(0, 0, 0.26, 0.28, 0, 0.06, 10, "hay")
            for k in range(5):
                a = k * 1.26
                s.lump(0.11 * math.cos(a), 0.04, 0.11 * math.sin(a), 0.06, 0.12, 0.05, "egg", rng, sides=6,
                       profile=((0.0, 0.7), (0.4, 1.0), (0.8, 0.7)), jitter=0.02, closed=True)
            return s
        if kind == "corn":
            for k in range(5):
                z = -0.20 + k * 0.10
                s.loft([((-0.25, 0.06, z), 0.05, 0.05), ((0.20, 0.06, z), 0.06, 0.06), ((0.28, 0.06, z), 0.0, 0.0)], 6, "corn")
                s.limb((-0.25, 0.06, z), (-0.40, 0.08, z + 0.03), 0.03, 0.0, 3, "hay")
            return s
        mat = {"potato": "potato", "fungus": "fungus", "agave": "agave"}[kind]
        for k in range(8):
            a, d = rng.uniform(0, 6.28), rng.uniform(0.0, 0.22)
            s.lump(d * math.cos(a), 0, d * math.sin(a), 0.08, 0.09, 0.07, mat, rng, sides=6, jitter=0.18)
        return s
    if kind in ("rice", "hops", "leaves", "psychoid", "smokeleaf"):
        mat = {"rice": "sack", "hops": "sack_dark", "leaves": "herb_green", "psychoid": "crop_pale", "smokeleaf": "herb_green"}[kind]
        if kind == "rice":
            s.loft([((0, 0.0, 0), 0.24, 0.18), ((0, 0.22, 0), 0.26, 0.19), ((0, 0.34, 0), 0.12, 0.10)], 8, mat)
            s.prism(0, 0, 0.13, 0.11, 0.33, 0.36, 6, "rice")
            return s
        for k in range(3):
            s.lump(rng.uniform(-0.15, 0.15), 0, rng.uniform(-0.15, 0.15), 0.18, 0.12, 0.14, mat, rng, sides=6, jitter=0.2)
        s.prism(0, 0, 0.05, 0.05, 0.09, 0.13, 6, "string")
        return s
    if kind == "meat":
        for k in range(3):
            x, z = rng.uniform(-0.15, 0.15), rng.uniform(-0.12, 0.12)
            s.lump(x, k * 0.05, z, 0.20, 0.10, 0.13, "meat", rng, sides=6, jitter=0.15, closed=k > 0)
            s.box(x - 0.16, k * 0.05 + 0.07, z - 0.02, x + 0.14, k * 0.05 + 0.10, z + 0.02, "fat")
        return s
    if kind == "milk":
        for x, z in ((-0.12, -0.06), (0.10, 0.08), (0.12, -0.14)):
            s.prism(x, z, 0.07, 0.07, 0.0, 0.24, 8, "milk")
            s.prism(x, z, 0.07, 0.03, 0.24, 0.30, 8, "milk")
            s.prism(x, z, 0.03, 0.03, 0.30, 0.33, 6, "paint_blue")
        return s
    if kind == "jelly":
        for x, z in ((-0.12, 0.0), (0.12, 0.05), (0.0, -0.15)):
            s.prism(x, z, 0.08, 0.08, 0.0, 0.18, 8, "jelly")
            s.prism(x, z, 0.085, 0.085, 0.18, 0.22, 8, "gun_light")
        return s
    if kind == "chocolate":
        for k in range(3):
            s.box(-0.20 + k * 0.03, k * 0.04, -0.12, 0.20 + k * 0.03, k * 0.04 + 0.04, 0.12, "chocolate")
            s.box(-0.10 + k * 0.03, k * 0.04, -0.125, 0.12 + k * 0.03, k * 0.04 + 0.042, 0.125, "paper")
        return s
    if kind == "beer":
        planked_box(s, -0.30, 0, -0.22, 0.30, 0.16, 0.22, "log", "log_burnt", bands=1)
        for k in range(6):
            x, z = -0.18 + (k % 3) * 0.18, -0.09 + (k // 3) * 0.18
            s.prism(x, z, 0.05, 0.05, 0.16, 0.34, 7, "bottle")
            s.prism(x, z, 0.05, 0.02, 0.34, 0.40, 7, "bottle")
            s.prism(x, z, 0.022, 0.022, 0.40, 0.43, 5, "gun_light")
        return s
    if kind == "hay":
        s.box(-0.40, 0, -0.26, 0.40, 0.36, 0.26, "hay")
        for x in (-0.20, 0.20):
            s.box(x - 0.015, -0.005, -0.27, x + 0.015, 0.365, 0.27, "string")
        return s
    return s


def textile_bolt(kind):
    """Cloth folded in a stack, leather as a hide, wool as a fluffy bundle; all in the item's own colour."""
    rng = random.Random(len(kind) * 17)
    s = Shape()
    if kind == "cloth":
        for k in range(3):
            w = 0.34 - k * 0.03
            s.box(-w, k * 0.05, -0.22 + k * 0.01, w, k * 0.05 + 0.05, 0.22 - k * 0.01, "stuff_fabric_dark", top="stuff_fabric")
        s.loft([((-0.30, 0.20, 0.0), 0.06, 0.06), ((0.30, 0.20, 0.0), 0.06, 0.06)], 8, "stuff_fabric")
    elif kind == "leather":
        pts = []
        for k in range(10):
            a = 2 * math.pi * k / 10
            r = 0.36 * rng.uniform(0.75, 1.05)
            pts.append((r * math.cos(a), 0.04 + rng.uniform(0, 0.03), r * math.sin(a) * 0.8))
        for k in range(10):
            s.face("stuff_fabric", [(0.0, 0.07, 0.0), pts[k], pts[(k + 1) % 10]], (0.0, -1.0, 0.0))
            s.face("stuff_fabric_dark", [pts[k], (pts[k][0], 0.0, pts[k][2]), (pts[(k + 1) % 10][0], 0.0, pts[(k + 1) % 10][2]), pts[(k + 1) % 10]],
                   (0.0, 0.03, 0.0))
    else:
        for k in range(4):
            a = k * 1.6
            s.lump(0.14 * math.cos(a), 0, 0.14 * math.sin(a), 0.16, 0.18, 0.15, "stuff_wool", rng, sides=7,
                   profile=((0.0, 0.85), (0.4, 1.0), (0.8, 0.7)), jitter=0.12)
    return s


def block_stack():
    """Cut stone blocks, stacked in courses, in the colour of their stone."""
    s = Shape()
    for k in range(3):
        n = 3 - k
        for i in range(n):
            x = (i - (n - 1) / 2) * 0.24
            s.box(x - 0.11, k * 0.13, -0.20, x + 0.11, k * 0.13 + 0.12, 0.20, "stuff_block_dark", top="stuff_block")
    return s


def drug(kind):
    s = Shape()
    if kind == "pills":
        s.prism(0, 0, 0.09, 0.09, 0.0, 0.22, 8, "pill")
        s.prism(0, 0, 0.095, 0.095, 0.22, 0.27, 8, "gun_white")
        s.prism(0, 0, 0.092, 0.092, 0.07, 0.15, 8, "label")
        for x, z in ((0.18, 0.08), (0.20, -0.04)):
            s.prism(x, z, 0.03, 0.03, 0.0, 0.015, 6, "pill")
    elif kind == "flake":
        s.box(-0.14, 0, -0.10, 0.14, 0.04, 0.10, "gun_white")
        s.lump(0, 0.04, 0, 0.10, 0.04, 0.07, "pill", random.Random(2), sides=6, jitter=0.1)
    elif kind == "syringe":
        s.loft([((-0.18, 0.04, 0), 0.03, 0.03), ((0.10, 0.04, 0), 0.03, 0.03)], 7, "glass")
        s.loft([((-0.10, 0.04, 0), 0.026, 0.026), ((0.08, 0.04, 0), 0.026, 0.026)], 7, "glow_green")
        s.limb((0.10, 0.04, 0), (0.22, 0.04, 0), 0.006, 0.003, 3, "gun_light")
        s.box(-0.22, 0.0, -0.04, -0.18, 0.08, 0.04, "gun_white")
    elif kind == "luciferium":
        s.prism(0, 0, 0.10, 0.10, 0.0, 0.16, 8, "glass")
        for k in range(5):
            a = k * 1.25
            s.lump(0.05 * math.cos(a), 0.02, 0.05 * math.sin(a), 0.03, 0.05, 0.03, "glow_red", random.Random(k), sides=5, jitter=0.05, closed=True)
        s.prism(0, 0, 0.105, 0.105, 0.16, 0.20, 8, "gun_dark")
    elif kind == "tea":
        s.prism(0, 0, 0.09, 0.11, 0.0, 0.16, 9, "paint_cream")
        s.prism(0, 0, 0.10, 0.10, 0.12, 0.15, 9, "food_stew")
        s.limb((0.11, 0.05, 0), (0.17, 0.11, 0), 0.02, 0.02, 4, "paint_cream")
    else:                                              # joints
        for k in range(4):
            z = -0.12 + k * 0.08
            s.loft([((-0.14, 0.02, z), 0.02, 0.02), ((0.14, 0.02, z + 0.02), 0.025, 0.025)], 5, "paper")
            s.loft([((0.14, 0.02, z + 0.02), 0.025, 0.025), ((0.15, 0.02, z + 0.02), 0.02, 0.02)], 5, "ember")
    return s


def mortar_shells(band):
    s = Shape()
    for x, z in ((-0.14, -0.10), (0.12, -0.08), (0.0, 0.14)):
        s.prism(x, z, 0.08, 0.09, 0.0, 0.30, 8, "shell_olive")
        s.prism(x, z, 0.09, 0.0, 0.30, 0.44, 8, "shell_olive")
        s.prism(x, z, 0.092, 0.092, 0.20, 0.25, 8, band)
        s.prism(x, z, 0.06, 0.06, 0.0, 0.04, 8, "brass")
    return s


def gadget(kind):
    """Small technical items: neurotrainers, techprints, artificial body parts, artifacts."""
    s = Shape()
    if kind == "neuro":
        s.box(-0.18, 0, -0.12, 0.18, 0.08, 0.12, "gun_white")
        s.prism(0, 0, 0.09, 0.07, 0.08, 0.16, 8, "glow_screen")
        s.box(-0.20, 0.0, -0.13, -0.16, 0.10, 0.13, "gun_dark")
    elif kind == "techprint":
        s.loft([((-0.25, 0.05, -0.05), 0.05, 0.05), ((0.25, 0.05, -0.05), 0.05, 0.05)], 8, "paint_blue")
        s.box(-0.25, 0.0, 0.0, 0.25, 0.01, 0.30, "paint_blue")
        s.box(-0.20, 0.01, 0.05, 0.20, 0.012, 0.25, "gun_white")
    elif kind == "bionic":
        s.box(-0.30, 0, -0.18, 0.30, 0.16, 0.18, "gun_white", top="gun_light")
        s.box(-0.24, 0.16, -0.12, 0.24, 0.17, 0.12, "glass")
        s.limb((-0.18, 0.20, 0.0), (0.18, 0.20, 0.0), 0.04, 0.03, 6, "gun_metal")
    elif kind == "natural":
        s.box(-0.24, 0, -0.18, 0.24, 0.22, 0.18, "gun_white", top="paint_blue")
        s.box(-0.06, 0.12, -0.19, 0.06, 0.16, -0.18, "red_cross")
    else:                                              # an archotech artifact: a strange glowing stone
        s.lump(0, 0, 0, 0.14, 0.24, 0.12, "hull_dark", random.Random(6), sides=6, jitter=0.1)
        s.prism(0, 0, 0.05, 0.0, 0.10, 0.30, 4, "glow_screen")
    return s


# ---------------------------------------------------------------------------- what uses what

# furniture and joy
use([add("hospital_bed", hospital_bed())], ["HospitalBed"], surface=0.46, turn=180, size=(1, 2))
use([add("bedroll", bedroll(False))], ["Bedroll"], surface=0.08, turn=180, size=(1, 2))
use([add("bedroll_double", bedroll(True))], ["BedrollDouble"], surface=0.08, turn=180, size=(2, 2))
use([add("animal_bed", animal_bed())], ["AnimalBed", "AnimalSleepingBox"], surface=0.12, size=(1, 1))
use([add("billiards_table", billiards_table())], ["BilliardsTable"], size=(3, 2))
use([add("chess_table", chess_table())], ["ChessTable"], size=(1, 1))
use([add("poker_table", poker_table())], ["PokerTable"], size=(2, 2))
use([add("hoopstone_ring", hoopstone_ring())], ["HoopstoneRing"], surface=0.0, size=(1, 1))
use([add("horseshoes_pin", horseshoes_pin())], ["HorseshoesPin"], surface=0.0, size=(1, 1))
use([add("tv_tube", television("tube"))], ["TubeTelevision"], surface=0.0, size=(2, 1))
use([add("tv_flat", television("flat"))], ["FlatscreenTelevision"], surface=0.0, size=(3, 1))
use([add("tv_mega", television("mega"))], ["MegascreenTelevision"], surface=0.0, size=(5, 1))
use([add("telescope", telescope())], ["Telescope"], surface=0.0, size=(1, 1))
use([add("tool_cabinet", tool_cabinet())], ["ToolCabinet"], surface=0.0, size=(1, 2))
use([add("vitals_monitor", vitals_monitor())], ["VitalsMonitor"], surface=0.0, size=(1, 1))
use(["standing_lamp"], ["StandingLamp_Red", "StandingLamp_Green", "StandingLamp_Blue", "Darklight"])
use([add("sculpture_small_%d" % i, sculpture(i, 0.9)) for i in range(3)], ["SculptureSmall"], surface=0.0, size=(1, 1))
use([add("sculpture_large_%d" % i, sculpture(3 + i, 1.6)) for i in range(3)], ["SculptureLarge"], surface=0.0, size=(2, 2))
use([add("sculpture_grand_%d" % i, sculpture(6 + i, 2.4)) for i in range(3)], ["SculptureGrand"], surface=0.0, size=(3, 3))

# production and research
use([add("paste_dispenser", paste_dispenser())], ["NutrientPasteDispenser"], surface=0.0, size=(3, 4))
use([add("hopper", hopper())], ["Hopper"], surface=0.62, size=(1, 1))
use([add("biofuel_refinery", biofuel_refinery())], ["BiofuelRefinery"], surface=0.0, size=(2, 2))
use([add("fabrication_bench", fabrication_bench())], ["FabricationBench"], surface=0.62, size=(5, 2))
use([add("crematorium", crematorium())], ["ElectricCrematorium"], surface=0.0, size=(2, 2))
use([add("bench_hitech_research", hitech_research_bench())], ["HiTechResearchBench"], surface=0.62, size=(3, 2))
use([add("multi_analyzer", multi_analyzer())], ["MultiAnalyzer"], surface=0.0, size=(3, 2))
use([add("deep_drill", deep_drill())], ["DeepDrill"], surface=0.0, size=(1, 1))
use([add("gp_scanner", gp_scanner())], ["GroundPenetratingScanner"], surface=0.0, size=(2, 2))
use([add("mineral_scanner", mineral_scanner())], ["LongRangeMineralScanner"], surface=0.0, size=(3, 3))
use([add("comms_console", comms_console())], ["CommsConsole"], surface=0.0, size=(3, 2))
use([add("trade_beacon", trade_beacon())], ["OrbitalTradeBeacon"], surface=0.0, size=(1, 1))
use([add("moisture_pump", moisture_pump())], ["MoisturePump"], surface=0.0, size=(1, 1))
use([add("cryptosleep_casket", cryptosleep_casket())], ["CryptosleepCasket", "AncientCryptosleepCasket"], surface=0.40, size=(1, 2))
use([add("ship_cryptosleep_casket", cryptosleep_casket(True))], ["Ship_CryptosleepCasket"], surface=0.40, size=(1, 2))
use([add("transport_pod", transport_pod())], ["TransportPod"], surface=0.0, size=(1, 1))
use([add("pod_launcher", pod_launcher())], ["PodLauncher"], surface=0.0, size=(1, 2))

# power and climate
use([add("geothermal", geothermal())], ["GeothermalGenerator"], surface=0.0, size=(6, 6))
use([add("watermill", watermill())], ["WatermillGenerator"], surface=0.0, size=(6, 5))
use([add("chemfuel_generator", chemfuel_generator())], ["ChemfuelPoweredGenerator"], surface=0.0, size=(2, 2))
use([add("power_switch", power_switch())], ["PowerSwitch"], surface=0.0, size=(1, 1))
use([add("cooler", cooler())], ["Cooler"], surface=0.0, size=(1, 1), shadow=False)
use([add("vent", cooler(vent=True))], ["Vent"], surface=0.0, size=(1, 1), shadow=False)
use([add("passive_cooler", passive_cooler())], ["PassiveCooler"], surface=0.0, size=(1, 1))

# security
add("turret_gun_mini", turret_gun("mini"))
add("turret_gun_auto", turret_gun("auto"))
add("turret_gun_sniper", turret_gun("sniper"))
add("turret_gun_mortar", turret_gun("mortar"))
use([add("turret_mini", turret_base("mini"))], ["Turret_MiniTurret"], surface=0.0, size=(1, 1), top="turret_gun_mini", top_height=0.46)
use([add("turret_auto", turret_base("auto"))], ["Turret_Autocannon"], surface=0.0, size=(2, 2), top="turret_gun_auto", top_height=0.66)
use([add("turret_sniper", turret_base("sniper"))], ["Turret_Sniper"], surface=0.0, size=(2, 2), top="turret_gun_sniper", top_height=0.66)
use([add("turret_mortar", turret_base("mortar"))], ["Turret_Mortar"], surface=0.0, size=(1, 1), top="turret_gun_mortar", top_height=0.26)
use([add("spike_trap", spike_trap())], ["TrapSpike"], surface=0.0, size=(1, 1))
for _name, _band in (("TrapIED_HighExplosive", "paint_red"), ("TrapIED_Incendiary", "chemfuel"), ("TrapIED_EMP", "glow_screen"),
                     ("TrapIED_Smoke", "gun_light"), ("TrapIED_Firefoam", "warning"), ("TrapIED_AntigrainWarhead", "glow_green"),
                     ("TrapIED_ToxGas", "food_green"), ("TrapIED_Deadlife", "gun_dark")):
    use([add("ied_" + _name[8:].lower(), ied(_band))], [_name], surface=0.0, size=(1, 1))
use([add("firefoam_popper", firefoam_popper())], ["FirefoamPopper"], surface=0.0, size=(1, 1))

# the ship
use([add("ship_beam", ship_beam())], ["Ship_Beam"], surface=0.0, size=(1, 3))
use([add("ship_computer_core", ship_computer_core())], ["Ship_ComputerCore"], surface=0.0, size=(2, 2))
use([add("ship_reactor", ship_reactor())], ["Ship_Reactor"], surface=0.0, size=(3, 4))
use([add("ship_engine", ship_engine())], ["Ship_Engine"], surface=0.0, size=(3, 5))
use([add("ship_sensor", ship_sensor())], ["Ship_SensorCluster"], surface=0.0, size=(1, 1))

# chunks, ruins, wrecks and junk. Exact names first, then by name fragment (first match wins).
use([add("ship_chunk_%d" % i, ship_chunk(i)) for i in (1, 2)], ["ShipChunk"], surface=0.0, size=(2, 2))
use(["slag_1", "slag_2"], ["ChunkMechanoidSlag"], random_turn=True, jitter=0.12)
use([add("wreck_car", car("sedan"))], surface=0.0, size=(3, 2), match=["RustedCar", "CarWreck", "WreckedCar", "AncientCar"])
use([add("wreck_car_frame", car("frame"))], surface=0.0, size=(3, 2), match=["CarFrame", "Chassis"])
use([add("wreck_jeep", car("jeep"))], surface=0.0, size=(3, 2), match=["Jeep"])
use([add("wreck_truck", car("truck"))], surface=0.0, size=(3, 2), match=["Truck", "Lorry", "Hauler"])
use([add("wreck_apc", tank_wreck(apc=True))], surface=0.0, size=(3, 4), match=["APC", "Transporter"])
use([add("wreck_tank", tank_wreck())], surface=0.0, size=(3, 4), match=["AncientTank", "TankWreck", "WreckedTank"])
use([add("warwalker_torso", warwalker("torso"))], surface=0.0, size=(4, 4), match=["WarwalkerTorso", "MechTorso"])
use([add("warwalker_leg", warwalker("leg"))], surface=0.0, size=(2, 4), match=["WarwalkerLeg", "MechLeg"])
use([add("warwalker_claw", warwalker("claw"))], surface=0.0, size=(2, 2), match=["WarwalkerClaw", "MechClaw"])
use([add("warwalker_foot", warwalker("foot"))], surface=0.0, size=(2, 2), match=["WarwalkerFoot", "MechFoot", "Warwalker", "MiniWarwalker"])
use([add("ruin_cannon", ruin_cannon())], surface=0.0, size=(5, 2), match=["MegaCannonBarrel", "CannonBarrel"])
use([add("ruin_tripod", ruin_tripod())], surface=0.0, size=(3, 3), match=["MegaCannonTripod", "Tripod"])
use([add("ruin_barrels", ruin_barrels())], surface=0.0, size=(1, 1), match=["AncientBarrel", "RustedBarrel", "Barrels", "OilDrum"])
use([add("ruin_crate_spacer", ruin_crate(True))], surface=0.0, size=(1, 1), match=["SpacerCrate", "SpacerContainer", "HiTechCrate"])
use([add("ruin_crate", ruin_crate())], surface=0.0, size=(1, 1), match=["AncientCrate", "RustedCrate", "SupplyCrate"])
use([add("ruin_pipe", ruin_pipe())], surface=0.0, size=(3, 1), match=["Pipeline", "PipeSection", "AncientPipe"])
use([add("ruin_engine", ruin_engine())], surface=0.0, size=(2, 1), match=["EngineBlock", "AncientEngine", "RustedEngine"])
use([add("ruin_machine", ruin_machine())], surface=0.0, size=(2, 1), match=["AncientMachine", "AncientGenerator", "AncientTerminal",
                                                                         "AncientComputer", "AncientEquipment", "AncientMachinery"])
use([add("ruin_lamppost", ruin_lamppost())], surface=0.0, size=(1, 1), match=["Lamppost", "StreetLamp", "AncientLamp"])
use([add("concrete_barrier", concrete_barrier())], surface=0.0, size=(1, 1), match=["ConcreteBarrier", "AncientBarricade", "JerseyBarrier"])
use([add("razor_wire", razor_wire())], surface=0.0, size=(1, 1), along_run=True, match=["RazorWire", "BarbedWire"])
use([add("junk_%d" % i, junk(i)) for i in (1, 2, 3)], surface=0.0, size=(1, 1), random_turn=True,
    match=["Wreck", "Junk", "Scrap", "Debris", "Rubble", "AncientRusted", "Rusted"])

# items: resources
I = dict(random_turn=False, jitter=0.0)
use([add("item_steel", ingot_stack("metal"))], ["Steel"], **I)
use([add("item_plasteel", ingot_stack("plasteel"))], ["Plasteel"], **I)
use([add("item_uranium", ingot_stack("uranium", rows=2, width=0.14))], ["Uranium"], **I)
use([add("item_gold", ingot_stack("gold", rows=2, width=0.10, length=0.24, height=0.06))], ["Gold"], **I)
use([add("item_silver", coin_stacks())], ["Silver"], **I)
use([add("item_jade", jade_chunks())], ["Jade"], **I)
use([add("item_wood", log_pile())], ["WoodLog"], **I)
use([add("item_component", components())], ["ComponentIndustrial"], **I)
use([add("item_component_spacer", components(True))], ["ComponentSpacer"], **I)
use([add("item_chemfuel", fuel_cans("chemfuel"))], ["Chemfuel"], **I)
use([add("item_neutroamine", fuel_cans("neutro"))], ["Neutroamine"], **I)
use([add("item_medicine_herbal", medicine("herbal"))], ["MedicineHerbal"], **I)
use([add("item_medicine", medicine("industrial"))], ["MedicineIndustrial"], **I)
use([add("item_medicine_glitter", medicine("ultra"))], ["MedicineUltratech"], **I)
use([add("item_blocks", block_stack())], category="StoneBlocks", **I)
use([add("item_cloth", textile_bolt("cloth"))], ["Cloth", "Synthread", "DevilstrandCloth", "Hyperweave"], **I)
use(["item_cloth"], category="Textiles", **I)
use([add("item_leather", textile_bolt("leather"))], category="Leathers", **I)
use([add("item_wool", textile_bolt("wool"))], category="Wools", **I)
# items: food
use([add("meal_simple", meal("simple"))], ["MealSimple"], **I)
use([add("meal_fine", meal("fine"))], ["MealFine", "MealFine_Veg", "MealFine_Meat"], **I)
use([add("meal_lavish", meal("lavish"))], ["MealLavish", "MealLavish_Veg", "MealLavish_Meat"], **I)
use([add("meal_paste", meal("paste"))], ["MealNutrientPaste"], **I)
use([add("meal_survival", meal("survival"))], ["MealSurvivalPack"], **I)
use([add("meal_pemmican", meal("pemmican"))], ["Pemmican"], **I)
use([add("meal_kibble", meal("kibble"))], ["Kibble"], **I)
use(["meal_simple"], category="FoodMeals", **I)
use([add("food_potato", produce("potato"))], ["RawPotatoes"], **I)
use([add("food_rice", produce("rice"))], ["RawRice"], **I)
use([add("food_corn", produce("corn"))], ["RawCorn"], **I)
use([add("food_berries", produce("berries"))], ["RawBerries"], **I)
use([add("food_fungus", produce("fungus"))], ["RawFungus"], **I)
use([add("food_agave", produce("agave"))], ["RawAgave"], **I)
use([add("food_hops", produce("hops"))], ["RawHops"], **I)
use([add("food_leaves", produce("smokeleaf"))], ["SmokeleafLeaves"], **I)
use([add("food_psychoid", produce("psychoid"))], ["PsychoidLeaves"], **I)
use(["food_potato"], category="PlantFoodRaw", **I)
use([add("food_meat", produce("meat"))], category="MeatRaw", **I)
use([add("food_eggs", produce("eggs"))], category="EggsUnfertilized", **I)
use(["food_eggs"], category="EggsFertilized", **I)
use([add("food_milk", produce("milk"))], ["Milk"], **I)
use([add("food_jelly", produce("jelly"))], ["InsectJelly"], **I)
use([add("food_chocolate", produce("chocolate"))], ["Chocolate"], **I)
use([add("food_beer", produce("beer"))], ["Beer", "Ambrosia"], **I)
use([add("food_hay", produce("hay"))], ["Hay"], **I)
# items: drugs, shells and gadgets
use([add("drug_pills", drug("pills"))], ["Penoxycyline", "WakeUp", "Yayo"], **I)
use([add("drug_flake", drug("flake"))], ["Flake"], **I)
use([add("drug_syringe", drug("syringe"))], ["GoJuice"], **I)
use([add("drug_luciferium", drug("luciferium"))], ["Luciferium"], **I)
use([add("drug_tea", drug("tea"))], ["PsychiteTea"], **I)
use([add("drug_joints", drug("joints"))], ["SmokeleafJoint"], **I)
use(["drug_pills"], category="Drugs", **I)
use([add("shells_he", mortar_shells("paint_red"))], ["Shell_HighExplosive", "Shell_AntigrainWarhead"], **I)
use([add("shells_other", mortar_shells("gun_light"))], category="MortarShells", **I)
use([add("item_neurotrainer", gadget("neuro"))], match=["Neurotrainer", "Psytrainer"], **I)
use([add("item_techprint", gadget("techprint"))], match=["Techprint"], **I)
use([add("item_bionic", gadget("bionic"))], category="BodyPartsBionic", categories=("BodyPartsProsthetic", "BodyPartsUltra", "BodyPartsArchotech"), **I)
use([add("item_organ", gadget("natural"))], category="BodyPartsNatural", **I)
use([add("item_artifact", gadget("artifact"))], category="Artifacts", **I)
