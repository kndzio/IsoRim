#!/usr/bin/env python3
"""Draws the textures for IsoRim: wall faces and tops, the material swatches used on models, and the ground.

Run from anywhere:  python3 tools/make_textures.py      (needs numpy and Pillow)
Writes PNG files under Textures/IsoRim/ next to this tools folder.

Style follows the game's art: flat fills, a little value variation from piece to piece, thin
dark seams instead of fine detail, and a faint painted mottle. Everything repeats seamlessly.
Wall and "stuff" textures are light grey so the game can tint them with the build material.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Textures", "IsoRim")
CELL = 128               # pixels per map cell
SIDE_W, SIDE_H = 2 * CELL, int(1.25 * CELL)     # wall sides repeat every 2 cells across, 1.25 up
TOP = 2 * CELL                                  # wall tops repeat every 2 x 2 cells


class Canvas:
    """A greyscale (or RGB) float image that wraps at its edges, so whatever is drawn repeats."""

    def __init__(self, w, h, value=0.9, seed=1):
        self.w, self.h = w, h
        self.a = np.full((h, w), float(value), np.float32)
        self.rng = np.random.default_rng(seed)

    def rect(self, x0, y0, x1, y1, value, mul=False):
        """Fills a rectangle; coordinates may run past the edges and wrap round."""
        xs = np.arange(int(round(x0)), int(round(x1))) % self.w
        ys = np.arange(int(round(y0)), int(round(y1))) % self.h
        if len(xs) == 0 or len(ys) == 0:
            return
        if mul:
            self.a[np.ix_(ys, xs)] *= value
        else:
            self.a[np.ix_(ys, xs)] = value

    def shape(self, draw_fn, value, soft=0.0, mul=False):
        """Draws an arbitrary Pillow shape, repeated so it wraps. draw_fn(draw, dx, dy) draws it offset.
        With mul the shape multiplies what is under it by value instead of replacing it."""
        mask = Image.new("L", (self.w * 2, self.h * 2), 0)
        d = ImageDraw.Draw(mask)
        for dx in (-self.w, 0, self.w):
            for dy in (-self.h, 0, self.h):
                draw_fn(d, dx * 2, dy * 2)
        mask = mask.resize((self.w, self.h), Image.LANCZOS)
        if soft:
            mask = mask.filter(ImageFilter.GaussianBlur(soft))
        m = np.asarray(mask, np.float32) / 255.0
        if mul:
            self.a = self.a * (1 + (value - 1) * m)
        else:
            self.a = self.a * (1 - m) + value * m

    def mottle(self, amount=0.03, grain=16):
        """A soft, hand-painted unevenness that also wraps."""
        gw, gh = max(2, self.w // grain), max(2, self.h // grain)
        small = self.rng.uniform(-1, 1, (gh, gw)).astype(np.float32)
        tiled = np.tile(small, (3, 3))
        big = Image.fromarray(tiled).resize((self.w * 3, self.h * 3), Image.BICUBIC)
        n = np.asarray(big, np.float32)[self.h:2 * self.h, self.w:2 * self.w]
        self.a *= 1 + amount * n

    def save(self, folder, name, tint=None):
        os.makedirs(os.path.join(OUT, folder), exist_ok=True)
        a = np.clip(self.a, 0, 1)
        if tint is None:
            rgb = np.stack([a, a, a], axis=-1)
        else:
            rgb = a[..., None] * np.array(tint, np.float32)[None, None, :]
        img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), "RGB")
        img = img.transpose(Image.FLIP_TOP_BOTTOM)      # row 0 of the array is the bottom of the texture
        img.save(os.path.join(OUT, folder, name + ".png"))


SEAM = 0.46      # the dark line between pieces: a darker shade of the fill, as in the game's outlines


# ------------------------------------------------------------------------------- walls

def bricks_side():
    c = Canvas(SIDE_W, SIDE_H, SEAM, seed=11)
    course, length, gap = 40, 64, 2
    for row in range(SIDE_H // course):
        shift = 0 if row % 2 == 0 else length // 2
        for k in range(SIDE_W // length):
            x0, y0 = k * length + shift, row * course
            v = c.rng.uniform(0.80, 0.95)
            c.rect(x0 + gap, y0 + gap, x0 + length - gap, y0 + course - gap, v)
            c.rect(x0 + gap, y0 + course - gap - 3, x0 + length - gap, y0 + course - gap, 1.06, mul=True)   # lit top edge
            c.rect(x0 + gap, y0 + gap, x0 + length - gap, y0 + gap + 3, 0.90, mul=True)                    # shaded bottom
            if c.rng.random() < 0.25:                                                                       # the odd chipped brick
                cx = x0 + c.rng.integers(12, length - 20)
                c.rect(cx, y0 + 16, cx + c.rng.integers(6, 12), y0 + 19, 0.84, mul=True)
    c.mottle(0.025)
    return c


def bricks_top():
    c = Canvas(TOP, TOP, 0.95, seed=12)
    for i in range(2):
        for j in range(2):
            c.rect(i * CELL, j * CELL, (i + 1) * CELL, (j + 1) * CELL, c.rng.uniform(0.92, 0.99))
    for k in range(2):                                          # joints between cap stones
        c.rect(k * CELL - 1, 0, k * CELL + 2, TOP, 0.66)
        c.rect(0, k * CELL - 1, TOP, k * CELL + 2, 0.66)
    c.mottle(0.03)
    return c


def planks_side():
    c = Canvas(SIDE_W, SIDE_H, SEAM, seed=21)
    board = 32
    for k in range(SIDE_W // board):
        x0 = k * board
        v = c.rng.uniform(0.80, 0.95)
        c.rect(x0 + 1, 0, x0 + board - 1, SIDE_H, v)
        c.rect(x0 + 1, 0, x0 + 4, SIDE_H, 1.05, mul=True)                    # lit left edge of each board
        for _ in range(c.rng.integers(2, 5)):                               # a few strokes of grain
            gx = x0 + c.rng.integers(6, board - 5)
            y0 = c.rng.integers(0, SIDE_H)
            c.rect(gx, y0, gx + 2, y0 + c.rng.integers(30, 90), 0.92, mul=True)
        for y in (14, SIDE_H - 14):                                          # nail heads
            c.shape(lambda d, dx, dy, x=x0 + board // 2, y=y: d.ellipse(
                [2 * x - 5 + dx, 2 * y - 5 + dy, 2 * x + 5 + dx, 2 * y + 5 + dy], fill=255), 0.52)
    c.mottle(0.02)
    return c


def planks_top():
    c = Canvas(TOP, TOP, 0.95, seed=22)
    board = 64
    for k in range(TOP // board):
        c.rect(k * board, 0, (k + 1) * board, TOP, c.rng.uniform(0.90, 0.99))
        c.rect(k * board - 1, 0, k * board + 2, TOP, 0.64)
        for _ in range(4):
            gx = k * board + c.rng.integers(8, board - 8)
            y0 = c.rng.integers(0, TOP)
            c.rect(gx, y0, gx + 2, y0 + c.rng.integers(40, 110), 0.94, mul=True)
    c.mottle(0.02)
    return c


def metal_side():
    c = Canvas(SIDE_W, SIDE_H, SEAM, seed=31)
    pw, ph = CELL, SIDE_H // 2
    for i in range(SIDE_W // pw):
        for j in range(SIDE_H // ph):
            x0, y0 = i * pw, j * ph
            c.rect(x0 + 2, y0 + 2, x0 + pw - 2, y0 + ph - 2, c.rng.uniform(0.84, 0.92))
            for r in range(ph - 4):                                          # a soft band of sheen across each plate
                t = r / (ph - 4)
                c.rect(x0 + 2, y0 + 2 + r, x0 + pw - 2, y0 + 3 + r, 1 + 0.07 * np.exp(-((t - 0.68) / 0.16) ** 2), mul=True)
            c.rect(x0 + 2, y0 + ph - 5, x0 + pw - 2, y0 + ph - 2, 1.05, mul=True)
            for rx in (12, pw - 12):                                         # rivets
                for ry in (11, ph - 11):
                    c.shape(lambda d, dx, dy, x=x0 + rx, y=y0 + ry: d.ellipse(
                        [2 * x - 7 + dx, 2 * y - 7 + dy, 2 * x + 7 + dx, 2 * y + 7 + dy], fill=255), 0.55)
                    c.shape(lambda d, dx, dy, x=x0 + rx, y=y0 + ry + 1: d.ellipse(
                        [2 * x - 3 + dx, 2 * y - 3 + dy, 2 * x + 3 + dx, 2 * y + 3 + dy], fill=255), 0.98)
    c.mottle(0.012, grain=32)
    return c


def metal_top():
    c = Canvas(TOP, TOP, 0.96, seed=32)
    for k in range(2):
        c.rect(k * CELL - 1, 0, k * CELL + 2, TOP, 0.68)
        c.rect(0, k * CELL - 1, TOP, k * CELL + 2, 0.68)
    c.mottle(0.012, grain=32)
    return c


def facets(w, h, count, lo, hi, edge, seed, edge_width=2.2):
    """Irregular flat-shaded facets with dark cracks between them (a wrapped Voronoi pattern)."""
    c = Canvas(w, h, 0.9, seed=seed)
    pts = np.column_stack([c.rng.uniform(0, w, count), c.rng.uniform(0, h, count)])
    vals = c.rng.uniform(lo, hi, count)
    ys, xs = np.mgrid[0:h, 0:w]
    best = np.full((h, w), 1e9, np.float32)
    second = np.full((h, w), 1e9, np.float32)
    which = np.zeros((h, w), int)
    for i, (px, py) in enumerate(pts):
        dx = np.abs(xs - px); dx = np.minimum(dx, w - dx)
        dy = np.abs(ys - py); dy = np.minimum(dy, h - dy)
        d = np.sqrt(dx * dx + (dy * 1.15) ** 2)
        closer = d < best
        second = np.where(closer, best, np.minimum(second, d))
        which = np.where(closer, i, which)
        best = np.where(closer, d, best)
    c.a = vals[which].astype(np.float32)
    crack = np.clip((edge_width - (second - best)) / edge_width, 0, 1)
    c.a = c.a * (1 - crack) + edge * crack
    return c


def rock_side():
    c = facets(SIDE_W, SIDE_H, 30, 0.72, 0.98, 0.50, seed=41)
    c.mottle(0.04)
    return c


def rock_top():
    c = facets(TOP, TOP, 34, 0.88, 1.0, 0.74, seed=42, edge_width=1.8)
    c.mottle(0.03)
    return c


def ore(base, seed):
    """Rock with pale nuggets set into it."""
    c = base
    c.a *= 0.84
    rng = np.random.default_rng(seed)
    for _ in range(int(c.w * c.h / 2600)):
        x, y, r = rng.uniform(0, c.w), rng.uniform(0, c.h), rng.uniform(5, 10)
        ang = rng.uniform(0, 6.28, 5); ang.sort()
        pts = [(x + r * np.cos(a) * rng.uniform(0.7, 1.1), y + r * np.sin(a) * rng.uniform(0.7, 1.1)) for a in ang]
        c.shape(lambda d, dx, dy, p=pts: d.polygon([(2 * px + dx, 2 * py + dy) for px, py in p], fill=255), 0.42)
        inner = [(x + (px - x) * 0.62, y + (py - y) * 0.62 + 1) for px, py in pts]
        c.shape(lambda d, dx, dy, p=inner: d.polygon([(2 * px + dx, 2 * py + dy) for px, py in p], fill=255), 1.0)
    return c


def smooth_stone_side():
    c = Canvas(SIDE_W, SIDE_H, 0.58, seed=51)
    bw, bh = CELL, SIDE_H // 2
    for j in range(SIDE_H // bh):
        shift = 0 if j % 2 == 0 else bw // 2
        for i in range(SIDE_W // bw):
            x0, y0 = i * bw + shift, j * bh
            c.rect(x0 + 1, y0 + 1, x0 + bw - 1, y0 + bh - 1, c.rng.uniform(0.86, 0.95))
            c.rect(x0 + 1, y0 + bh - 4, x0 + bw - 1, y0 + bh - 1, 1.04, mul=True)
    c.mottle(0.035, grain=12)
    return c


def smooth_stone_top():
    c = Canvas(TOP, TOP, 0.96, seed=52)
    c.mottle(0.035, grain=12)
    return c


def sandbags_side():
    c = Canvas(SIDE_W, SIDE_H, SEAM, seed=61)
    bw, bh = 64, 40
    for row in range(SIDE_H // bh):
        shift = 0 if row % 2 == 0 else bw // 2
        for k in range(SIDE_W // bw):
            x0, y0 = k * bw + shift, row * bh
            v = c.rng.uniform(0.80, 0.94)
            c.shape(lambda d, dx, dy, x=x0, y=y0: d.rounded_rectangle(
                [2 * x + 4 + dx, 2 * y + 4 + dy, 2 * (x + bw) - 4 + dx, 2 * (y + bh) - 4 + dy], 26, fill=255), v)
            c.shape(lambda d, dx, dy, x=x0, y=y0: d.rounded_rectangle(
                [2 * x + 16 + dx, 2 * (y + bh) - 22 + dy, 2 * (x + bw) - 16 + dx, 2 * (y + bh) - 12 + dy], 5, fill=255), v * 1.06, soft=1.5)
            c.rect(x0 + bw - 12, y0 + 10, x0 + bw - 10, y0 + bh - 10, 0.86, mul=True)                      # the tied end
    c.mottle(0.03)
    return c


def sandbags_top():
    c = Canvas(TOP, TOP, 0.62, seed=62)
    bw, bh = 128, 64
    for row in range(TOP // bh):
        for k in range(TOP // bw):
            x0, y0 = k * bw, row * bh
            v = c.rng.uniform(0.90, 0.99)
            c.shape(lambda d, dx, dy, x=x0, y=y0: d.rounded_rectangle(
                [2 * x + 5 + dx, 2 * y + 5 + dy, 2 * (x + bw) - 5 + dx, 2 * (y + bh) - 5 + dy], 30, fill=255), v)
    c.mottle(0.03)
    return c


# ------------------------------------------------------------------------------- model swatches

def swatch_wood():
    c = Canvas(CELL, CELL, SEAM, seed=71)
    board = 32
    for k in range(CELL // board):
        x0 = k * board
        c.rect(x0 + 1, 0, x0 + board - 1, CELL, c.rng.uniform(0.84, 0.95))
        c.rect(x0 + 1, 0, x0 + 4, CELL, 1.05, mul=True)
        for _ in range(3):
            gx = x0 + c.rng.integers(6, board - 5)
            y0 = c.rng.integers(0, CELL)
            c.rect(gx, y0, gx + 2, y0 + c.rng.integers(24, 70), 0.92, mul=True)
    c.mottle(0.02)
    return c


def swatch_stone():
    c = Canvas(CELL, CELL, 0.93, seed=72)
    c.mottle(0.05, grain=10)
    for _ in range(5):                                                       # a few hairline veins
        x, y = c.rng.integers(0, CELL), c.rng.integers(0, CELL)
        c.rect(x, y, x + c.rng.integers(14, 34), y + 2, 0.90, mul=True)
    return c


def swatch_metal():
    c = Canvas(CELL, CELL, 0.90, seed=73)
    for y in range(CELL):                                                    # brushed, with broad soft bands
        c.rect(0, y, CELL, y + 1, 1 + 0.05 * np.sin(y / CELL * 2 * np.pi) + c.rng.uniform(-0.012, 0.012), mul=True)
    c.mottle(0.012, grain=32)
    return c


def swatch_fabric():
    c = Canvas(CELL, CELL, 0.93, seed=74)
    for k in range(0, CELL, 4):                                              # a faint weave
        c.rect(k, 0, k + 1, CELL, 0.975, mul=True)
        c.rect(0, k, CELL, k + 1, 0.975, mul=True)
    c.mottle(0.03, grain=20)
    return c


def swatch_soil():
    c = Canvas(CELL, CELL, 0.86, seed=75)
    for _ in range(140):
        x, y, s = c.rng.integers(0, CELL), c.rng.integers(0, CELL), c.rng.integers(2, 5)
        c.rect(x, y, x + s, y + s, c.rng.uniform(0.72, 1.12), mul=True)
    c.mottle(0.05)
    return c


def swatch_glow():
    c = Canvas(CELL, CELL, 0.97, seed=76)
    c.mottle(0.02, grain=24)
    return c


def swatch_flame():
    """Runs from deep orange at the bottom to pale yellow at the tip; models stretch it over a flame.
    It is stored divided by the flame material's own pale yellow, which the mod multiplies back in,
    so a flame is still flame-coloured when model textures are switched off."""
    h = CELL
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    lo, hi = np.array([0.96, 0.42, 0.10], np.float32), np.array([1.0, 0.90, 0.48], np.float32)
    rgb = lo[None, None, :] * (1 - t[..., None]) + hi[None, None, :] * t[..., None]
    return np.repeat(rgb / hi[None, None, :], CELL, axis=1)


def swatch_solar():
    """Solar cells: deep blue squares with clipped corners, a slightly different blue each, crossed by
    fine silver wires. Colour is baked in. Two cells to the map cell each way."""
    a = np.zeros((CELL, CELL, 3), np.float32)
    backing = np.array((0.80, 0.83, 0.88), np.float32)
    a[:] = backing * 0.62
    rng = np.random.default_rng(77)
    step = CELL // 2
    ys, xs = np.mgrid[0:step, 0:step]
    edge = np.minimum(np.minimum(xs, step - 1 - xs), np.minimum(ys, step - 1 - ys))
    corner = (np.minimum(xs, step - 1 - xs) + np.minimum(ys, step - 1 - ys))
    inside = (edge >= 2) & (corner >= 9)                                  # a square with its corners cut off
    for i in range(2):
        for j in range(2):
            blue = np.array((0.10, 0.17, 0.36), np.float32) * rng.uniform(0.9, 1.15)
            cell = np.empty((step, step, 3), np.float32)
            cell[:] = a[j * step:(j + 1) * step, i * step:(i + 1) * step]
            sheen = 1 + 0.16 * (ys[..., None] / step) + 0.06 * (xs[..., None] / step)      # lighter toward one corner
            cell[inside] = (blue[None, None, :] * sheen)[inside]
            for k in range(8, step - 4, 7):                               # the fine wires
                cell[inside & (xs == k)] = blue * 1.9
            for k in (step // 3, 2 * step // 3):                          # and the two thick ones across them
                cell[inside & (np.abs(ys - k) <= 0)] = backing * 0.86
            a[j * step:(j + 1) * step, i * step:(i + 1) * step] = cell
    return a


def swatch_rock():
    """Flat-shaded facets with dark cracks, for boulders and anything else made of raw rock."""
    c = facets(CELL, CELL, 16, 0.80, 1.0, 0.56, seed=78, edge_width=2.0)
    c.mottle(0.04)
    return c


def swatch_leaf():
    """Overlapping clumps of leaves: light blobs over darker gaps. Models tint it per species."""
    c = Canvas(CELL, CELL, 0.70, seed=79)
    for _ in range(46):
        x, y = c.rng.uniform(0, CELL), c.rng.uniform(0, CELL)
        rx, ry = c.rng.uniform(9, 17), c.rng.uniform(7, 13)
        v = c.rng.uniform(0.84, 1.0)
        c.shape(lambda d, dx, dy, x=x, y=y, rx=rx, ry=ry: d.ellipse(
            [2 * (x - rx) + dx, 2 * (y - ry) + dy, 2 * (x + rx) + dx, 2 * (y + ry) + dy], fill=255), v * 0.80)
        c.shape(lambda d, dx, dy, x=x, y=y + 2, rx=rx - 2.5, ry=ry - 2.5: d.ellipse(
            [2 * (x - rx) + dx, 2 * (y - ry) + dy, 2 * (x + rx) + dx, 2 * (y + ry) + dy], fill=255), v)
    c.mottle(0.03)
    return c


def swatch_bark():
    c = Canvas(CELL, CELL, 0.86, seed=80)
    for _ in range(26):                                                      # long vertical furrows
        x = c.rng.integers(0, CELL)
        y0 = c.rng.integers(0, CELL)
        c.rect(x, y0, x + c.rng.integers(2, 5), y0 + c.rng.integers(40, 110), c.rng.uniform(0.74, 0.86), mul=True)
    c.mottle(0.04)
    return c


# ------------------------------------------------------------------------------- ground
# Natural terrain, repainted to match: broad flat facets with soft seams, and inside them a
# second, fainter layer of small facets, scattered pebbles, specks and hairline cracks.
# Grass is the exception: it has no facets, only brushed tones and painted blades, with bare
# earth showing through where a noise map says so (see grass_ground). These replace the game's own terrain textures while the 3D view is on.
# They are larger than the other textures because the game stretches one copy over many cells.

GROUND = 1024


def cells(size, grid, seed, reach=2):
    """Facets around one point per square of a grid, each point anywhere in its square. Wraps.
    Returns a value from -1 to 1 for the facet each pixel is in, and how far (in pixels) the
    pixel is from being in the next facet over, which is 0 along the seams."""
    rng = np.random.default_rng(seed)
    step = size / grid
    px = (np.arange(grid)[None, :] + rng.uniform(0.04, 0.96, (grid, grid))) * step
    py = (np.arange(grid)[:, None] + rng.uniform(0.04, 0.96, (grid, grid))) * step
    val = rng.uniform(-1, 1, (grid, grid)).astype(np.float32)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    gx = np.minimum((xs / step).astype(int), grid - 1)
    gy = np.minimum((ys / step).astype(int), grid - 1)
    best = np.full((size, size), 1e9, np.float32)
    second = np.full((size, size), 1e9, np.float32)
    out = np.zeros((size, size), np.float32)
    for oy in range(-reach, reach + 1):
        for ox in range(-reach, reach + 1):
            cx, cy = (gx + ox) % grid, (gy + oy) % grid
            dx = xs - (px[cy, cx] + (gx + ox - cx) * step)       # the neighbour's point, un-wrapped
            dy = ys - (py[cy, cx] + (gy + oy - cy) * step)
            d = np.sqrt(dx * dx + dy * dy)
            closer = d < best
            second = np.where(closer, best, np.minimum(second, d))
            out = np.where(closer, val[cy, cx], out)
            best = np.where(closer, d, best)
    return out, second - best


def smooth_noise(size, grain, seed):
    """Soft blotches from 0 to 1 that wrap, for drifting between two tints."""
    rng = np.random.default_rng(seed)
    g = max(2, size // grain)
    small = rng.uniform(0, 1, (g, g)).astype(np.float32)
    big = Image.fromarray(np.tile(small, (3, 3))).resize((size * 3, size * 3), Image.BICUBIC)
    return np.clip(np.asarray(big, np.float32)[size:2 * size, size:2 * size], 0, 1)


def fractal(size, seed, grains=(256, 128, 64, 32), weights=(1.0, 0.6, 0.35, 0.2)):
    """Blotches within blotches, from 0 to 1, that wrap: broad shapes with ragged edges."""
    total = np.zeros((size, size), np.float32)
    for k, (grain, weight) in enumerate(zip(grains, weights)):
        total += weight * smooth_noise(size, grain, seed + 37 * k)
    total -= total.min()
    return total / max(1e-6, total.max())


def tones(size, seed, levels=3, grains=(200, 90, 40), soft=0.012):
    """A few flat tones from 0 to 1 in organic patches with clean edges."""
    n = fractal(size, seed + 900, grains=grains, weights=(1.0, 0.6, 0.3))
    out = np.zeros((size, size), np.float32)
    for k in range(1, levels):
        cut = np.quantile(n, k / levels)
        out += np.clip((n - cut) / soft * 0.5 + 0.5, 0, 1) / (levels - 1)
    return out


def blur_wrapped(a, radius):
    pad = int(radius * 3) + 1
    padded = (np.clip(np.pad(a, pad, mode="wrap"), 0, 1) * 255).astype(np.uint8)      # expects values from 0 to 1
    big = Image.fromarray(padded, "L").filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(big, np.float32)[pad:-pad, pad:-pad] / 255.0


def draw_wrapped(d, pts, fill, size):
    """Draws a polygon on a Pillow image of the given size, again on the far side if it crosses an edge."""
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    dxs = [0] + ([size] if min(xs) < 0 else []) + ([-size] if max(xs) >= size else [])
    dys = [0] + ([size] if min(ys) < 0 else []) + ([-size] if max(ys) >= size else [])
    for dx in dxs:
        for dy in dys:
            d.polygon([(x + dx, y + dy) for x, y in pts], fill=fill)


def polys(c, shapes, value, mul=False):
    """Draws a whole batch of polygons (lists of points) in one go."""
    if shapes:
        c.shape(lambda d, dx, dy: [d.polygon([(2 * x + dx, 2 * y + dy) for x, y in p], fill=255) for p in shapes], value, mul=mul)


def ground(grid, lo, hi, edge, seed, mottle=0.03, fine=4, fine_amount=0.035, fine_seam=0.07, bevel=0.05,
           stones=0, stone_size=(4, 11), stone_value=(0.86, 1.1), specks=900, cracks=0, tufts=0, tuft_size=(9, 17)):
    c = Canvas(GROUND, GROUND, 0.9, seed=seed)
    rng = np.random.default_rng(seed + 1000)

    if grid:
        # broad facets, and small ones inside them
        v, gap = cells(GROUND, grid, seed)
        a = lo + (hi - lo) * (v * 0.5 + 0.5)
        if fine:
            fv, fgap = cells(GROUND, grid * fine, seed + 500)
            a = a * (1 + fine_amount * fv)
            a = a * (1 - fine_seam * np.clip((1.4 - fgap) / 1.4, 0, 1))
        seam = np.clip((2.4 - gap) / 2.4, 0, 1)
        if bevel:                                           # a lit lip along one side of every seam
            lip = np.clip(np.roll(np.clip((4.0 - gap) / 4.0, 0, 1), (3, -3), axis=(0, 1)) - seam * 2, 0, 1)
            a = a * (1 + bevel * lip)
        c.a = (a * (1 - seam) + edge * seam).astype(np.float32)
    else:
        # no facets at all: soft-edged patches of a few flat tones, as if brushed on
        c.a = (lo + (hi - lo) * tones(GROUND, seed, levels=4)).astype(np.float32)
    c.mottle(mottle, grain=48)

    # hairline cracks: two or three short strokes end to end
    lines = []
    for _ in range(cracks):
        x, y, ang = rng.uniform(0, GROUND), rng.uniform(0, GROUND), rng.uniform(0, 6.28)
        pts = [(x, y)]
        for _ in range(rng.integers(2, 4)):
            ang += rng.uniform(-0.9, 0.9)
            step = rng.uniform(7, 16)
            x, y = x + step * np.cos(ang), y + step * np.sin(ang)
            pts.append((x, y))
        lines.append(pts)
    if lines:
        c.shape(lambda d, dx, dy: [d.line([(2 * x + dx, 2 * y + dy) for x, y in p], fill=255, width=3) for p in lines],
                0.5 + 0.5 * edge, mul=True)

    # specks: grit darker and lighter than the ground
    for factor in (0.86, 1.10):
        dots = [(rng.uniform(0, GROUND), rng.uniform(0, GROUND), rng.uniform(0.9, 2.3)) for _ in range(specks // 2)]
        if dots:
            c.shape(lambda d, dx, dy, dots=dots: [d.ellipse([2 * (x - r) + dx, 2 * (y - r) + dy, 2 * (x + r) + dx, 2 * (y + r) + dy], fill=255)
                                                  for x, y, r in dots], factor, mul=True)

    # loose pebbles: small flat shapes with a dark rim, a shadow below and a lit face
    rims, shadows, faces = [], [], ([], [], [])
    for _ in range(stones):
        x, y, r = rng.uniform(0, GROUND), rng.uniform(0, GROUND), rng.uniform(*stone_size)
        ang = np.sort(rng.uniform(0, 6.28, 6))
        pts = [(x + r * np.cos(t) * rng.uniform(0.7, 1.1), y + r * np.sin(t) * rng.uniform(0.6, 1.0)) for t in ang]
        rims.append(pts)
        shadows.append([(px + 1.5, py - 2.5) for px, py in pts])
        faces[rng.integers(0, 3)].append([(x + (px - x) * 0.72, y + (py - y) * 0.72 + 1.2) for px, py in pts])
    polys(c, shadows, 0.84, mul=True)
    polys(c, rims, edge * 0.82)
    for k, group in enumerate(faces):
        polys(c, group, stone_value[0] + (stone_value[1] - stone_value[0]) * (k + 0.5) / 3)

    # painted tufts: a few blades fanning out from one spot, pointing up the screen
    under, blades = [], ([], [], [])
    for _ in range(tufts):
        x, y = rng.uniform(0, GROUND), rng.uniform(0, GROUND)
        for _ in range(rng.integers(3, 6)):
            lean = rng.uniform(-0.75, 0.75)
            length = rng.uniform(*tuft_size)
            bx = x + rng.uniform(-3, 3)
            tip = (bx + length * np.sin(lean), y + length * np.cos(lean))
            under.append([(bx - 2.6, y - 1.5), (bx + 2.6, y - 1.5), (tip[0] + 0.6, tip[1] + 1.0)])
            blades[rng.integers(0, 3)].append([(bx - 1.6, y), (bx + 1.6, y), tip])
    polys(c, under, 0.78, mul=True)
    for k, group in enumerate(blades):
        polys(c, group, (1.14, 1.27, 1.42)[k], mul=True)
    return c


def paint_ground(c, tint, tint2=None, flowers=0, seed=1):
    """Colours a ground canvas: one tint, or a slow drift between two, plus the odd tiny flower."""
    a = np.clip(c.a, 0, 1.6)[..., None]
    t = np.array(tint, np.float32)[None, None, :]
    if tint2 is not None:
        m = smooth_noise(GROUND, 150, seed + 2000)[..., None]
        m = np.clip((m - 0.3) / 0.4, 0, 1)
        t = t * (1 - m) + np.array(tint2, np.float32)[None, None, :] * m
    img = Image.fromarray((np.clip(a * t, 0, 1) * 255).astype(np.uint8), "RGB")
    if flowers:
        rng = np.random.default_rng(seed + 3000)
        d = ImageDraw.Draw(img)
        petals = ((246, 240, 228), (244, 214, 92), (226, 150, 196))
        for _ in range(flowers):
            x, y, r = rng.uniform(0, GROUND), rng.uniform(0, GROUND), rng.uniform(1.3, 2.2)
            col = petals[rng.integers(0, len(petals))]
            for ox in (-GROUND, 0, GROUND):
                for oy in (-GROUND, 0, GROUND):
                    d.ellipse([x - r - 1 + ox, y - r - 1 + oy, x + r + 1 + ox, y + r + 1 + oy], fill=(40, 58, 30))
                    d.ellipse([x - r + ox, y - r + oy, x + r + ox, y + r + oy], fill=col)
    return np.asarray(img, np.float32) / 255.0


def grass_ground(seed, base, shades, dirt_tint, dirt_share, tufts, flowers, tuft_size=(9, 18), pool_tint=None, pool_share=0.0):
    """Turf with bare earth showing through. Returns an RGB picture.

    There are no facets here: the turf is flat brushed tones under painted tufts of grass. A
    noise map decides where the earth shows (dirt_share of the area), in ragged patches of
    every size. Each tuft is drawn as it looks from straight above, blades fanning out all
    round, so the ground reads the same whichever way the camera is turned.
    base is the turf colour, shades the blade colours from darkest to lightest.
    pool_tint and pool_share add flat pools of standing water (marsh)."""
    rng = np.random.default_rng(seed + 4000)
    size, big = GROUND, GROUND * 2

    # the turf: three flat tones in soft patches, with a faint brushed unevenness
    turf = Canvas(size, size, 1.0, seed=seed)
    turf.a = (0.90 + 0.17 * tones(size, seed, levels=3)).astype(np.float32)
    turf.mottle(0.035, grain=40)
    turf_rgb = np.clip(turf.a, 0, 1.5)[..., None] * np.array(base, np.float32)[None, None, :]

    # the earth: the plain dirt ground without its facets
    dirt = ground(0, 0.90, 1.04, 0.80, seed + 50, mottle=0.04, stones=90, specks=1400, cracks=110)
    dirt_rgb = np.clip(dirt.a, 0, 1.5)[..., None] * np.array(dirt_tint, np.float32)[None, None, :]

    # the noise map: where it is highest, earth shows
    n = fractal(size, seed + 70, grains=(300, 140, 60, 26, 12), weights=(1.0, 0.7, 0.45, 0.28, 0.14))
    cut = np.quantile(n, 1 - dirt_share)
    mask = np.clip((n - cut) / 0.012 * 0.5 + 0.5, 0, 1)
    near = blur_wrapped(mask, 5.0)
    dirt_rgb = dirt_rgb * (1 - 0.42 * np.clip(1 - near, 0, 1) ** 1.5)[..., None]       # shaded where the grass stands over it
    turf_rgb = turf_rgb * (1 - 0.10 * np.clip(blur_wrapped(mask, 9.0) * 2, 0, 1) * (1 - mask))[..., None]
    rgb = turf_rgb * (1 - mask[..., None]) + dirt_rgb * mask[..., None]

    wet = np.zeros((size, size), np.float32)
    if pool_tint is not None and pool_share > 0:
        # standing water: flat pools with a pale line just inside the bank and a darker middle
        n2 = fractal(size, seed + 90, grains=(260, 120, 50, 22), weights=(1.0, 0.7, 0.4, 0.2))
        cut2 = np.quantile(n2, 1 - pool_share)
        wet = np.clip((n2 - cut2) / 0.010 * 0.5 + 0.5, 0, 1)
        depth = blur_wrapped(wet, 7.0)
        tone = 1.0 - 0.16 * np.clip((depth - 0.80) / 0.15, 0, 1) + 0.22 * np.clip(1 - np.abs(depth - 0.62) / 0.07, 0, 1)
        pool_rgb = tone[..., None] * np.array(pool_tint, np.float32)[None, None, :]
        bank = np.clip(blur_wrapped(wet, 4.0) * 2.2, 0, 1) * (1 - wet)             # the ground darkens toward the water
        rgb = rgb * (1 - 0.30 * bank)[..., None]
        rgb = rgb * (1 - wet[..., None]) + pool_rgb * wet[..., None]

    # the tufts, painted at twice the size and shrunk for clean edges; darkest first. Each tuft is
    # a soft, scalloped mound of overlapping rounded lobes with a lighter heart and a few short
    # blade tips poking out round its rim: it reads as a fluffy clump of grass from any side.
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), "RGB").resize((big, big), Image.BICUBIC)
    d = ImageDraw.Draw(img)
    rim = tuple(int(255 * c * 0.86) for c in base)
    passes = len(shades)

    def blob(x, y, r, sides=9):
        # a ragged, leafy outline rather than a clean circle
        return [(2 * (x + r * rng.uniform(0.80, 1.12) * np.cos(t)), 2 * (y + r * rng.uniform(0.80, 1.12) * np.sin(t)))
                for t in np.linspace(0, 6.283, sides + 1)[:-1] + rng.uniform(0, 0.6)]

    for k, shade in enumerate(shades):
        lighter = shades[min(k + 1, passes - 1)]
        for _ in range(tufts // passes):
            x, y = rng.uniform(0, size), rng.uniform(0, size)
            if wet[int(y) % size, int(x) % size] > 0.3:
                continue
            earth = mask[int(y) % size, int(x) % size]
            if earth > 0.7 and rng.random() > 0.035:
                continue                                    # only the odd tuft out on the bare earth
            reach = rng.uniform(*tuft_size) * 0.5 * (0.85 + 0.10 * k)
            wobble = 1 + rng.uniform(-0.05, 0.05)
            col = tuple(int(np.clip(255 * c * wobble, 0, 255)) for c in shade)
            heart = tuple(int(np.clip(255 * c * wobble * 1.04, 0, 255)) for c in lighter)
            lobes = int(rng.integers(4, 7))
            a0 = rng.uniform(0, 6.28)
            parts = [(x, y, reach * 0.50)]
            for j in range(lobes):
                a = a0 + 2 * np.pi * j / lobes + rng.uniform(-0.25, 0.25)
                dist = reach * rng.uniform(0.32, 0.46)
                parts.append((x + dist * np.cos(a), y + dist * np.sin(a), reach * rng.uniform(0.34, 0.46)))
            tips = []
            for j in range(int(rng.integers(5, 9))):
                a = rng.uniform(0, 6.28)
                tips.append((np.cos(a), np.sin(a), reach * rng.uniform(0.95, 1.30)))
            for px, py, pr in parts:                         # a soft dark edge under the whole tuft first
                draw_wrapped(d, blob(px, py, pr + 1.0), rim, big)
            for ca, sa, length in tips:
                draw_wrapped(d, [(2 * (x + ca * reach * 0.5 - sa * 1.6), 2 * (y + sa * reach * 0.5 + ca * 1.6)),
                                 (2 * (x + ca * reach * 0.5 + sa * 1.6), 2 * (y + sa * reach * 0.5 - ca * 1.6)),
                                 (2 * (x + ca * (length + 1.0)), 2 * (y + sa * (length + 1.0)))], rim, big)
            for ca, sa, length in tips:
                draw_wrapped(d, [(2 * (x + ca * reach * 0.5 - sa * 1.0), 2 * (y + sa * reach * 0.5 + ca * 1.0)),
                                 (2 * (x + ca * reach * 0.5 + sa * 1.0), 2 * (y + sa * reach * 0.5 - ca * 1.0)),
                                 (2 * (x + ca * length), 2 * (y + sa * length))], col, big)
            for px, py, pr in parts:
                draw_wrapped(d, blob(px, py, pr), col, big)
            draw_wrapped(d, blob(x + rng.uniform(-1, 1), y + rng.uniform(-1, 1), reach * 0.24, 7), heart, big)

    petals = ((246, 240, 228), (244, 214, 92), (226, 150, 196))
    for _ in range(flowers):
        x, y, r = rng.uniform(0, size), rng.uniform(0, size), rng.uniform(1.3, 2.1)
        if mask[int(y) % size, int(x) % size] > 0.3 or wet[int(y) % size, int(x) % size] > 0.1:
            continue
        col = petals[rng.integers(0, len(petals))]
        ring = [(2 * (x + (r + 1) * np.cos(t)), 2 * (y + (r + 1) * np.sin(t))) for t in np.linspace(0, 6.28, 9)[:-1]]
        dot_ = [(2 * (x + r * np.cos(t)), 2 * (y + r * np.sin(t))) for t in np.linspace(0, 6.28, 9)[:-1]]
        draw_wrapped(d, ring, rim, big)
        draw_wrapped(d, dot_, col, big)

    return np.asarray(img.resize((size, size), Image.LANCZOS), np.float32) / 255.0


# ------------------------------------------------------------------------------- built floors
# Laid floors, repainted in the same hand: flat fills that differ a little from piece to piece,
# dark seams, a lit and a shaded edge on every piece, and sparse detail. One map cell is 64
# pixels, so anything laid to the grid (tiles, slabs) is drawn on multiples of that. All are light
# grey: the game tints stone, carpet and metal floors itself, and the mod tints the rest.

PX = GROUND // 16          # pixels per map cell


def lay(c, x0, y0, x1, y1, value, gap=1.0, lit=1.07, shaded=0.90, edge=2):
    """One piece (board, tile, slab) with a seam left round it, a lit top edge and a shaded bottom edge."""
    c.rect(x0 + gap, y0 + gap, x1 - gap, y1 - gap, value)
    c.rect(x0 + gap, y1 - gap - edge, x1 - gap, y1 - gap, lit, mul=True)
    c.rect(x0 + gap, y0 + gap, x0 + gap + edge, y1 - gap, lit * 0.985, mul=True)
    c.rect(x0 + gap, y0 + gap, x1 - gap, y0 + gap + edge, shaded, mul=True)
    c.rect(x1 - gap - edge, y0 + gap, x1 - gap, y1 - gap, shaded * 1.03, mul=True)


def grit(c, rng, count, lo=0.86, hi=1.10, size=(0.8, 2.0)):
    for factor in (lo, hi):
        dots = [(rng.uniform(0, GROUND), rng.uniform(0, GROUND), rng.uniform(*size)) for _ in range(count // 2)]
        c.shape(lambda d, dx, dy, dots=dots: [d.ellipse([2 * (x - r) + dx, 2 * (y - r) + dy, 2 * (x + r) + dx, 2 * (y + r) + dy], fill=255)
                                              for x, y, r in dots], factor, mul=True)


def hairlines(c, rng, count, value=0.80, reach=(7, 16)):
    lines = []
    for _ in range(count):
        x, y, ang = rng.uniform(0, GROUND), rng.uniform(0, GROUND), rng.uniform(0, 6.28)
        pts = [(x, y)]
        for _ in range(rng.integers(2, 4)):
            ang += rng.uniform(-0.9, 0.9)
            step = rng.uniform(*reach)
            x, y = x + step * np.cos(ang), y + step * np.sin(ang)
            pts.append((x, y))
        lines.append(pts)
    if lines:
        c.shape(lambda d, dx, dy: [d.line([(2 * x + dx, 2 * y + dy) for x, y in p], fill=255, width=3) for p in lines], value, mul=True)


def floor_wood():
    """Boards four to the cell running east-west, in random lengths, with grain, the odd knot and nail heads."""
    c = Canvas(GROUND, GROUND, 0.50, seed=401)
    rng = c.rng
    board = PX // 4
    for row in range(GROUND // board):
        y0 = row * board
        x = int(rng.integers(0, 4 * PX))
        start = x
        while x < start + GROUND:
            length = int(rng.integers(2, 6)) * (PX // 2)
            length = min(length, start + GROUND - x)
            v = rng.uniform(0.80, 1.0)
            lay(c, x, y0, x + length, y0 + board, v, gap=0.75, edge=1)
            for _ in range(rng.integers(2, 5)):                              # grain
                gy = y0 + rng.integers(3, board - 3)
                gx = x + rng.integers(2, max(3, length - 30))
                c.rect(gx, gy, gx + rng.integers(14, 60), gy + 1, rng.uniform(0.88, 0.95), mul=True)
            if rng.random() < 0.18 and length > 40:                          # a knot
                kx, ky = x + rng.integers(10, length - 10), y0 + board / 2
                c.shape(lambda d, dx, dy, kx=kx, ky=ky: d.ellipse([2 * (kx - 4) + dx, 2 * (ky - 2.5) + dy, 2 * (kx + 4) + dx, 2 * (ky + 2.5) + dy], fill=255), v * 0.72)
            for nx in (x + 4, x + length - 5):                               # nail heads at each end
                for ny in (y0 + 4, y0 + board - 5):
                    c.rect(nx, ny, nx + 2, ny + 2, 0.55)
            x += length
    c.mottle(0.025, grain=40)
    return c


def floor_tiles(per_cell, seed, lo=0.88, hi=1.0, grout=0.56, gap=1.0, chips=0.10, cracks=40, gloss=False, specks=500):
    """Square tiles laid to the map grid."""
    c = Canvas(GROUND, GROUND, grout, seed=seed)
    rng = c.rng
    size = PX // per_cell
    chipped = []
    for i in range(GROUND // size):
        for j in range(GROUND // size):
            x0, y0 = i * size, j * size
            v = rng.uniform(lo, hi)
            lay(c, x0, y0, x0 + size, y0 + size, v, gap=gap)
            if gloss:                                                        # a faint shine across one corner
                c.shape(lambda d, dx, dy, x0=x0, y0=y0: d.polygon([(2 * (x0 + 4) + dx, 2 * (y0 + size - 4) + dy), (2 * (x0 + size * 0.55) + dx, 2 * (y0 + size - 4) + dy),
                                                                (2 * (x0 + 4) + dx, 2 * (y0 + size * 0.45) + dy)], fill=255), 1.035, mul=True)
            if rng.random() < chips:                                         # a chipped corner
                cx, cy = x0 + (gap if rng.random() < 0.5 else size - gap), y0 + (gap if rng.random() < 0.5 else size - gap)
                r = rng.uniform(3, 7)
                chipped.append([(cx - r, cy), (cx, cy - r), (cx + r, cy), (cx, cy + r)])
    polys(c, chipped, grout * 1.15)
    hairlines(c, rng, cracks)
    grit(c, rng, specks)
    c.mottle(0.02, grain=40)
    return c


def floor_flagstone():
    """Irregular flat stones fitted together, with wide dark joints."""
    c = ground(40, 0.82, 1.0, 0.50, 402, mottle=0.03, fine=0, bevel=0.09, specks=1400, cracks=110)
    return c


def floor_carpet():
    """A soft weave with a quilted diamond pattern pressed into it."""
    c = Canvas(GROUND, GROUND, 0.93, seed=403)
    ys, xs = np.mgrid[0:GROUND, 0:GROUND]
    c.a *= 1 + 0.035 * (((xs // 2 + ys // 2) % 2) - 0.5)                     # the weave
    c.a *= 1 + 0.02 * (((xs // 2 - ys // 2) % 3 == 0) - 0.33)
    half = PX // 2
    d1, d2 = (xs + ys) % half, (xs - ys) % half
    quilt = np.minimum(np.minimum(d1, half - d1), np.minimum(d2, half - d2)).astype(np.float32)
    c.a *= 1 - 0.085 * np.clip(1 - quilt / 1.6, 0, 1)                        # the pressed lines
    c.a *= 1 + 0.03 * np.clip(quilt / (half / 2.0), 0, 1)                    # each diamond puffs up toward its middle
    c.a = c.a.astype(np.float32)
    c.mottle(0.03, grain=56)
    return c


def floor_concrete():
    """Poured slabs two cells square with a groove between them, pitted and lightly stained."""
    c = Canvas(GROUND, GROUND, 0.55, seed=404)
    rng = c.rng
    size = 2 * PX
    for i in range(GROUND // size):
        for j in range(GROUND // size):
            lay(c, i * size, j * size, (i + 1) * size, (j + 1) * size, rng.uniform(0.90, 0.98), gap=1.5, lit=1.04, shaded=0.94)
    stain = fractal(GROUND, 405, grains=(180, 80, 30), weights=(1.0, 0.6, 0.3))
    c.a = (c.a * (1 - 0.07 * np.clip((stain - 0.55) / 0.2, 0, 1))).astype(np.float32)
    grit(c, rng, 3600, lo=0.84, hi=1.08, size=(0.7, 1.8))
    hairlines(c, rng, 110, reach=(8, 22))
    c.mottle(0.035, grain=40)
    return c


def floor_paved():
    """Paving bricks, two by four to the cell, each row half a brick along from the last."""
    c = Canvas(GROUND, GROUND, 0.54, seed=406)
    rng = c.rng
    w, h = PX // 2, PX // 4
    for row in range(GROUND // h):
        shift = 0 if row % 2 == 0 else w // 2
        for k in range(GROUND // w):
            lay(c, k * w + shift, row * h, (k + 1) * w + shift, (row + 1) * h, rng.uniform(0.80, 1.0), gap=1.0, edge=1)
    grit(c, rng, 1600)
    hairlines(c, rng, 60)
    c.mottle(0.03, grain=40)
    return c


def floor_metal():
    """Plates one cell square with a pressed border, a rivet in each corner and brushed streaks."""
    c = Canvas(GROUND, GROUND, 0.50, seed=407)
    rng = c.rng
    rivets_dark, rivets_light = [], []
    for i in range(16):
        for j in range(16):
            x0, y0 = i * PX, j * PX
            v = rng.uniform(0.90, 1.0)
            lay(c, x0, y0, x0 + PX, y0 + PX, v, gap=1.0)
            c.rect(x0 + 7, y0 + 7, x0 + PX - 7, y0 + 8, 0.90, mul=True)                 # the pressed border
            c.rect(x0 + 7, y0 + PX - 8, x0 + PX - 7, y0 + PX - 7, 1.06, mul=True)
            c.rect(x0 + 7, y0 + 7, x0 + 8, y0 + PX - 7, 1.05, mul=True)
            c.rect(x0 + PX - 8, y0 + 7, x0 + PX - 7, y0 + PX - 7, 0.91, mul=True)
            for _ in range(rng.integers(3, 7)):                                         # brushed streaks
                sy = y0 + rng.integers(10, PX - 10)
                sx = x0 + rng.integers(10, PX - 34)
                c.rect(sx, sy, sx + rng.integers(10, 24), sy + 1, rng.choice((0.95, 1.04)), mul=True)
            for rx in (x0 + 4.5, x0 + PX - 4.5):
                for ry in (y0 + 4.5, y0 + PX - 4.5):
                    rivets_dark.append((rx, ry - 0.6, 2.1))
                    rivets_light.append((rx, ry, 1.5))
    for dots, value in ((rivets_dark, 0.62), (rivets_light, 1.06)):
        c.shape(lambda d, dx, dy, dots=dots: [d.ellipse([2 * (x - r) + dx, 2 * (y - r) + dy, 2 * (x + r) + dx, 2 * (y + r) + dy], fill=255)
                                              for x, y, r in dots], value)
    c.mottle(0.02, grain=40)
    return c


FLOORS = {
    "FloorWood": floor_wood,
    "FloorStoneTile": lambda: floor_tiles(1, 408),
    "FloorFlagstone": floor_flagstone,
    "FloorCarpet": floor_carpet,
    "FloorConcrete": floor_concrete,
    "FloorPaved": floor_paved,
    "FloorMetal": floor_metal,
    "FloorSterile": lambda: floor_tiles(2, 409, lo=0.955, hi=1.0, grout=0.80, gap=0.75, chips=0.0, cracks=0, gloss=True, specks=0),
}


def muted(c, amount=0.30):
    """A colour with some of its saturation taken out (mixed toward its own grey)."""
    g = 0.30 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    return tuple(v + (g - v) * amount for v in c)


def muted_all(colours, amount=0.30):
    return tuple(muted(c, amount) for c in colours)


GRASS = {
    # name: turf colour, blade colours from darkest to lightest, earth colour, share of bare earth, tufts, flowers
    "Grass":     dict(base=muted((0.30, 0.44, 0.20)), shades=muted_all(((0.26, 0.39, 0.18), (0.31, 0.46, 0.20), (0.36, 0.51, 0.22), (0.42, 0.57, 0.25))),
                      dirt_tint=(0.45, 0.32, 0.21), dirt_share=0.17, tufts=4600, flowers=50, tuft_size=(10, 19)),
    "GrassRich": dict(base=muted((0.21, 0.36, 0.17), 0.24), shades=muted_all(((0.18, 0.31, 0.15), (0.22, 0.38, 0.17), (0.26, 0.43, 0.19), (0.32, 0.49, 0.21)), 0.24),
                      dirt_tint=(0.30, 0.21, 0.14), dirt_share=0.10, tufts=5400, flowers=110, tuft_size=(11, 21)),
    # moss: a low, dense, blue-green mat with grey stone showing through
    "Moss":      dict(base=(0.25, 0.36, 0.25), shades=((0.22, 0.32, 0.23), (0.26, 0.38, 0.26), (0.30, 0.42, 0.27), (0.35, 0.46, 0.29)),
                      dirt_tint=(0.40, 0.39, 0.36), dirt_share=0.12, tufts=8000, flowers=0, tuft_size=(5, 10)),
    # marshy soil: wet, dark, mossy mud with flat pools of standing water and a few reeds
    "Marsh":     dict(base=(0.25, 0.30, 0.19), shades=((0.21, 0.27, 0.16), (0.26, 0.33, 0.19), (0.32, 0.39, 0.21), (0.40, 0.45, 0.24)),
                      dirt_tint=(0.27, 0.22, 0.16), dirt_share=0.30, tufts=2600, flowers=0, tuft_size=(12, 22),
                      pool_tint=(0.25, 0.36, 0.38), pool_share=0.20),
}

GROUNDS = {
    # name: (canvas maker, tint or None for a grey texture the game tints itself, extra paint options)
    "Soil":        (lambda: ground(12, 0.90, 1.02, 0.84, 201, stones=110, cracks=160), (0.44, 0.30, 0.20), {}),
    "SoilRich":    (lambda: ground(12, 0.88, 1.02, 0.80, 202, stones=60, cracks=120, fine_amount=0.05), (0.32, 0.22, 0.15), {}),
    "PackedDirt":  (lambda: ground(10, 0.94, 1.02, 0.88, 203, stones=50, cracks=220, fine_seam=0.05), (0.52, 0.41, 0.29), {}),
    "Sand":        (lambda: ground(8, 0.95, 1.03, 0.90, 204, mottle=0.02, fine=6, fine_amount=0.02, fine_seam=0.035,
                                   stones=14, specks=1600), (0.78, 0.69, 0.50), {}),
    "Gravel":      (lambda: ground(33, 0.74, 1.04, 0.56, 205, mottle=0.02, fine=2, fine_amount=0.05, fine_seam=0.10,
                                   bevel=0.08, specks=1400), (0.54, 0.51, 0.47), {}),
    "Mud":         (lambda: ground(8, 0.88, 1.06, 0.80, 206, mottle=0.05, fine=5, cracks=260, specks=500), (0.30, 0.23, 0.17), {}),
    "Ice":         (lambda: ground(7, 0.93, 1.02, 1.06, 209, mottle=0.015, fine=3, fine_amount=0.015, fine_seam=-0.04,
                                   bevel=0.0, cracks=140, specks=300), (0.80, 0.88, 0.94), {}),
    "RoughStone":  (lambda: ground(15, 0.82, 1.0, 0.64, 210, mottle=0.03, fine=3, fine_amount=0.05, fine_seam=0.12,
                                   bevel=0.07, stones=40, cracks=120), None, {}),
    "RoughHewn":   (lambda: ground(11, 0.88, 1.0, 0.72, 211, mottle=0.03, fine=4, fine_seam=0.09, bevel=0.06, cracks=200), None, {}),
    "SmoothStone": (lambda: ground(5, 0.95, 1.0, 0.86, 212, mottle=0.02, fine=5, fine_amount=0.02, fine_seam=0.03, cracks=60,
                                   specks=400), None, {}),
}


def save_rgb(a, folder, name):
    os.makedirs(os.path.join(OUT, folder), exist_ok=True)
    img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "RGB").transpose(Image.FLIP_TOP_BOTTOM)
    img.save(os.path.join(OUT, folder, name + ".png"))


WALLS = {
    "Bricks": (bricks_side, bricks_top),
    "Planks": (planks_side, planks_top),
    "Metal": (metal_side, metal_top),
    "Rock": (rock_side, rock_top),
    "SmoothStone": (smooth_stone_side, smooth_stone_top),
    "Sandbags": (sandbags_side, sandbags_top),
}


# ------------------------------------------------------------------------------- roofs
# Light grey, tinted by the mod with the roof colour picked in the options. One copy covers two
# cells each way; v runs up the slope, so each course of tiles has its lower edge at the bottom
# and sits in the shadow of the course above near its top.

ROOF = 256
ROWS = 6                       # courses per copy (three a cell)


def roof_rows(seed, pieces, gap, piece_fn, shadow=0.20, lip=0.08):
    """Courses of pieces, every other course shifted half a piece. piece_fn(a, x0, x1, y0, y1, rng)
    paints one piece into the array a (rows are y, columns x)."""
    rng = np.random.default_rng(seed)
    a = np.full((ROOF, ROOF), 0.55, np.float32)
    rh = ROOF / ROWS
    w = ROOF / pieces
    for r in range(ROWS):
        y0 = r * rh
        off = (w / 2) * (r % 2) + rng.uniform(-2, 2)
        for i in range(pieces + 1):
            x0 = off + i * w + rng.uniform(-1.5, 1.5)
            piece_fn(a, x0 + gap / 2, x0 + w - gap / 2, y0, y0 + rh, rng)
    # every course: a lit lip along its lower edge, then darker up toward the course above
    ys = np.arange(ROOF) % rh / rh
    shade = (1.0 + lip * (ys < 0.07)) * (1.0 - shadow * np.clip((ys - 0.55) / 0.45, 0, 1))
    return a * shade[:, None]


def wrap_cols(x0, x1):
    return np.arange(int(round(x0)), int(round(x1))) % ROOF


def slate_piece(a, x0, x1, y0, y1, rng):
    v = rng.uniform(0.86, 1.0)
    cols = wrap_cols(x0, x1)
    rows = np.arange(int(y0) + 2, int(y1)) % ROOF
    a[np.ix_(rows, cols)] = v
    a[np.ix_(rows[:3], cols)] = v * 0.62                          # the dark lower edge of the slate


def terracotta_piece(a, x0, x1, y0, y1, rng):
    cols = wrap_cols(x0, x1)
    rows = np.arange(int(y0), int(y1)) % ROOF
    t = (np.arange(len(cols)) + 0.5) / max(1, len(cols))
    round_ = 0.62 + 0.38 * np.sin(np.pi * t) ** 0.7                 # each tile a half round: lit middle, dark sides
    v = rng.uniform(0.90, 1.0)
    a[np.ix_(rows, cols)] = (v * round_)[None, :]
    a[np.ix_(rows[:3], cols)] *= 0.7


def tin_piece(a, x0, x1, y0, y1, rng):
    cols = wrap_cols(x0, x1)
    rows = np.arange(int(y0), int(y1)) % ROOF
    t = np.arange(len(cols))
    ribs = 0.86 + 0.14 * np.cos(2 * np.pi * t / 10.0)               # corrugations
    v = rng.uniform(0.92, 1.0)
    a[np.ix_(rows, cols)] = (v * ribs)[None, :]
    a[np.ix_(rows, cols[:2])] = 0.55                               # the overlap between sheets
    if rng.random() < 0.3:                                       # a rust streak
        k = rng.integers(0, max(1, len(cols) - 4))
        a[np.ix_(rows, cols[k:k + 3])] *= 0.82


def roof_slate():
    return roof_rows(61, 7, 3, slate_piece)


def roof_terracotta():
    return roof_rows(62, 12, 1, terracotta_piece, shadow=0.28, lip=0.0)


def roof_tin():
    a = roof_rows(63, 3, 0, tin_piece, shadow=0.10, lip=0.0)
    return a


def roof_thatch():
    """Bundles of straw: fine streaks running up the slope, in thick layered courses."""
    rng = np.random.default_rng(64)
    a = np.full((ROOF, ROOF), 0.86, np.float32)
    for _ in range(2600):
        x = rng.uniform(0, ROOF)
        y = rng.uniform(0, ROOF)
        length = rng.uniform(14, 34)
        v = rng.uniform(0.70, 1.05)
        cols = np.arange(int(x), int(x) + 2) % ROOF
        rows = np.arange(int(y), int(y + length)) % ROOF
        a[np.ix_(rows, cols)] = v
    rh = ROOF / 4                                                # fewer, deeper courses than tiles
    ys = np.arange(ROOF) % rh / rh
    shade = (1.0 - 0.32 * np.clip((ys - 0.45) / 0.55, 0, 1)) * (1.0 + 0.06 * (ys < 0.08))
    edge = 1.0 - 0.10 * (np.sin(np.arange(ROOF) * 0.9) * 0.5 + 0.5)    # a ragged hem along each course
    a = a * shade[:, None]
    for r in range(4):
        y = int(r * rh)
        a[y:y + 3, :] *= edge[None, :] * 0.85
    return a


def roofs():
    for name, make in (("Slate", roof_slate), ("Terracotta", roof_terracotta), ("Thatch", roof_thatch), ("Tin", roof_tin)):
        c = Canvas(ROOF, ROOF)
        c.a = np.clip(make(), 0, 1).astype(np.float32)
        c.mottle(0.04, grain=24)
        c.save("Roofs", name)


# ------------------------------------------------------------------------------- water
# Two see-through layers the mod slides across its water every frame: soft ripples for still
# water, and long streaks for running water (v runs downstream). Both tile, white crests and
# faint dark troughs on clear.

def water_layer(seed, streak):
    rng = np.random.default_rng(seed)
    n = 256
    light = np.zeros((n, n), np.float32)
    dark = np.zeros((n, n), np.float32)
    img_l = Image.new("L", (n * 2, n * 2), 0)
    img_d = Image.new("L", (n * 2, n * 2), 0)
    dl, dd = ImageDraw.Draw(img_l), ImageDraw.Draw(img_d)
    count = 70 if streak else 55
    for _ in range(count):
        x, y = rng.uniform(0, n), rng.uniform(0, n)
        if streak:
            w, h = rng.uniform(2, 4), rng.uniform(26, 60)
        else:
            w, h = rng.uniform(16, 34), rng.uniform(3, 5)
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                cx, cy = (x + ox) * 2, (y + oy) * 2
                if streak:
                    dl.ellipse((cx - w, cy - h, cx + w, cy + h), fill=int(rng.uniform(150, 255)))
                    dd.ellipse((cx - w * 2.5 + 8, cy - h * 0.8, cx + w * 2.5 + 8, cy + h * 0.8), fill=120)
                else:
                    # a crescent: a lit arc with a shadow just under it
                    dl.chord((cx - w, cy - h * 2, cx + w, cy + h * 2), 200, 340, fill=int(rng.uniform(170, 255)))
                    dd.chord((cx - w, cy - h * 2 + 6, cx + w, cy + h * 2 + 6), 200, 340, fill=110)
    light = np.asarray(img_l.resize((n, n), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.6)), np.float32) / 255
    dark = np.asarray(img_d.resize((n, n), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3.0)), np.float32) / 255
    dark = dark * (1 - light)
    rgba = np.zeros((n, n, 4), np.float32)
    crest = np.array([0.80, 0.90, 0.92])
    trough = np.array([0.08, 0.14, 0.17])
    alpha = light * 0.22 + dark * 0.12
    col = (crest[None, None, :] * (light * 0.22)[..., None] + trough[None, None, :] * (dark * 0.12)[..., None]) / np.maximum(alpha, 1e-4)[..., None]
    rgba[..., :3] = col
    rgba[..., 3] = alpha
    os.makedirs(os.path.join(OUT, "Water"), exist_ok=True)
    out = Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), "RGBA").transpose(Image.FLIP_TOP_BOTTOM)
    out.save(os.path.join(OUT, "Water", "Flow.png" if streak else "Ripples.png"))


def icons():
    """The mod's two buttons for the bottom right corner of the screen: white shapes on clear, as
    the game's own buttons are, drawn large and shrunk for clean edges."""
    folder = os.path.join(OUT, "UI")
    os.makedirs(folder, exist_ok=True)
    big = 256

    def finish(img, name):
        img.resize((64, 64), Image.LANCZOS).save(os.path.join(folder, name + ".png"))

    # 3D view: a cube seen from above and to the side, its three faces in three greys
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy, r = 128, 132, 96
    top = [(cx, cy - r), (cx + r * 0.87, cy - r * 0.5), (cx, cy), (cx - r * 0.87, cy - r * 0.5)]
    left = [(cx - r * 0.87, cy - r * 0.5), (cx, cy), (cx, cy + r), (cx - r * 0.87, cy + r * 0.5)]
    right = [(cx, cy), (cx + r * 0.87, cy - r * 0.5), (cx + r * 0.87, cy + r * 0.5), (cx, cy + r)]
    d.polygon(top, fill=(255, 255, 255, 255))
    d.polygon(left, fill=(196, 202, 210, 255))
    d.polygon(right, fill=(150, 156, 166, 255))
    d.line(top + [top[0]], fill=(40, 44, 50, 255), width=8)
    d.line([left[0], left[3], left[2], right[2], right[1]], fill=(40, 44, 50, 255), width=8)
    d.line([(cx, cy), (cx, cy + r)], fill=(40, 44, 50, 255), width=8)
    finish(img, "View3D")

    # roofs: a house under a pitched roof of slates
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((62, 128, 194, 224), fill=(196, 202, 210, 255), outline=(40, 44, 50, 255), width=8)
    d.rectangle((110, 168, 146, 224), fill=(110, 116, 126, 255))
    roof = [(28, 136), (128, 40), (228, 136)]
    d.polygon(roof, fill=(255, 255, 255, 255))
    for k in range(1, 4):                                     # rows of slates
        y = 40 + k * 24
        half = (y - 40) * 100 / 96
        d.line([(128 - half, y), (128 + half, y)], fill=(150, 156, 166, 255), width=6)
    d.line(roof + [roof[0]], fill=(40, 44, 50, 255), width=8)
    finish(img, "Roofs")


def main():
    for name, (side, top) in WALLS.items():
        side().save("Walls", name + "Side")
        top().save("Walls", name + "Top")
    ore(rock_side(), 43).save("Walls", "RockOreSide")
    ore(rock_top(), 44).save("Walls", "RockOreTop")

    swatch_wood().save("Swatches", "Wood")
    swatch_stone().save("Swatches", "Stone")
    swatch_metal().save("Swatches", "Metal")
    swatch_fabric().save("Swatches", "Fabric")
    swatch_rock().save("Swatches", "Rock")
    swatch_leaf().save("Swatches", "Leaf")
    swatch_bark().save("Swatches", "Bark")
    swatch_soil().save("Swatches", "Soil", tint=(0.36, 0.26, 0.18))
    swatch_glow().save("Swatches", "Glow", tint=(1.0, 0.93, 0.62))
    save_rgb(swatch_flame(), "Swatches", "Flame")
    save_rgb(swatch_solar(), "Swatches", "Solar")

    for seed, (name, (make, tint, extra)) in enumerate(GROUNDS.items()):
        canvas = make()
        if tint is None:
            canvas.save("Ground", name)
        else:
            save_rgb(paint_ground(canvas, tint, seed=seed, **extra), "Ground", name)

    for seed, (name, options) in enumerate(GRASS.items()):
        save_rgb(grass_ground(300 + seed, **options), "Ground", name)
    for name, make in FLOORS.items():
        make().save("Ground", name)
    icons()
    roofs()
    water_layer(71, False)
    water_layer(72, True)

    count = sum(len(files) for _, _, files in os.walk(OUT))
    print("%d textures written to %s" % (count, OUT))


if __name__ == "__main__":
    main()
