#!/usr/bin/env python3
"""Damage marks for IsoRim: Textures/IsoRim/Damage/Marks.png, a 2 x 2 atlas of scratches, cracks,
a chipped hole and dents. Drawn with the game's cutout shader, so alpha is either on or off."""
import math, os, random
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 128
C = 64
DARK = (46, 38, 32, 255)
MID = (84, 72, 62, 255)
LIGHT = (196, 186, 166, 255)


def cell(img, i):
    ox, oy = (i % 2) * C, (i // 2) * C
    return ImageDraw.Draw(img), ox, oy


def scratches(img, rng):
    d, ox, oy = cell(img, 0)
    for k in range(4):
        x0, y0 = ox + rng.uniform(8, 26), oy + rng.uniform(10, 54)
        a = rng.uniform(-0.6, -0.2)
        L = rng.uniform(26, 44)
        x1, y1 = x0 + L * math.cos(a), y0 + L * math.sin(a)
        d.line([(x0, y0 + 1.5), (x1, y1 + 1.5)], fill=LIGHT, width=2)
        d.line([(x0, y0), (x1, y1)], fill=DARK, width=3)


def cracks(img, rng):
    d, ox, oy = cell(img, 1)

    def branch(x, y, a, L, w, depth):
        pts = [(x, y)]
        for _ in range(5):
            a += rng.uniform(-0.5, 0.5)
            x += L / 5 * math.cos(a)
            y += L / 5 * math.sin(a)
            pts.append((x, y))
        d.line(pts, fill=DARK, width=w)
        if depth > 0:
            for _ in range(2):
                j = rng.randint(1, 4)
                branch(pts[j][0], pts[j][1], a + rng.choice((-1, 1)) * rng.uniform(0.6, 1.1), L * 0.55, max(1, w - 1), depth - 1)

    cx, cy = ox + 32, oy + 32
    for k in range(4):
        branch(cx, cy, k * math.pi / 2 + rng.uniform(-0.4, 0.4), 26, 3, 2)


def chip(img, rng):
    d, ox, oy = cell(img, 2)
    cx, cy = ox + 32, oy + 32
    pts_outer = [(cx + (20 + rng.uniform(-5, 4)) * math.cos(a), cy + (17 + rng.uniform(-5, 4)) * math.sin(a))
                 for a in [i * 2 * math.pi / 11 for i in range(11)]]
    d.polygon(pts_outer, fill=LIGHT)
    pts = [(cx + 1 + (14 + rng.uniform(-4, 3)) * math.cos(a), cy + 1 + (11 + rng.uniform(-4, 3)) * math.sin(a))
           for a in [i * 2 * math.pi / 11 for i in range(11)]]
    d.polygon(pts, fill=MID)
    d.polygon([(x * 0.6 + cx * 0.4 + 2, y * 0.6 + cy * 0.4 + 2) for x, y in pts], fill=DARK)


def dents(img, rng):
    d, ox, oy = cell(img, 3)
    for k in range(5):
        x, y = ox + rng.uniform(12, 52), oy + rng.uniform(12, 52)
        r = rng.uniform(4, 8)
        d.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], fill=LIGHT)
        d.ellipse([x - r + 1.5, y - r * 0.8 + 1.5, x + r - 1, y + r * 0.8 - 1], fill=DARK)


img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
rng = random.Random(7)
scratches(img, rng)
cracks(img, rng)
chip(img, rng)
dents(img, rng)
img = img.transpose(Image.FLIP_TOP_BOTTOM)   # texture rows start at the bottom in the game
out = os.path.join(ROOT, "Textures", "IsoRim", "Damage", "Marks.png")
img.save(out)
print("wrote", out)
