#!/usr/bin/env python3
"""The cut face round the edge of the map: Textures/IsoRim/Edge/Strata.png.

A slice through the ground, top to bottom: a fringe of grass, dark topsoil, clay, then rock
layers (sandstone, granite, slate, marble, limestone) with jagged, uneven boundaries, flecks of
ore in the deeper rock, and a broken bottom edge (cut out with alpha) so the map looks like a
chunk lifted out of the earth. Tiles left to right."""
import math, os, random
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 256, 256
rng = random.Random(11)
nrng = np.random.default_rng(11)
x = np.arange(W)


def wavy(base, amp, seed, rough=1.0):
    """A boundary height for each column: smooth periodic swells plus a jagged periodic walk."""
    r = random.Random(seed)
    y = np.full(W, float(base))
    for k in (1, 2, 3, 5, 8):
        y += amp / k * math.sqrt(k) * 0.6 * np.sin(2 * math.pi * k * x / W + r.uniform(0, 6.28))
    steps = np.array([r.uniform(-1, 1) for _ in range(W)])
    walk = np.cumsum(steps - steps.mean())
    y += walk * 0.45 * rough
    # jag: occasional notches
    for _ in range(6):
        c = r.randrange(W)
        w = r.randint(3, 9)
        d = r.uniform(-4, 4) * rough
        for i in range(-w, w + 1):
            y[(c + i) % W] += d * (1 - abs(i) / (w + 1))
    return y


# rows counted from the top of the image (which is the top of the face)
layers = [  # (name, colour, bottom boundary base row, amplitude)
    ("grass",     (86, 112, 58),   7,   2.0),
    ("topsoil",   (78, 58, 42),    34,  4.0),
    ("clay",      (128, 92, 62),   58,  5.0),
    ("sandstone", (150, 126, 96),  92,  7.0),
    ("granite",   (112, 108, 106), 128, 8.0),
    ("slate",     (76, 78, 86),    160, 7.0),
    ("marble",    (168, 164, 156), 186, 6.0),
    ("limestone", (124, 118, 102), 256, 0.0),
]
bounds = [wavy(b, a, 100 + i, rough=1.0 if i else 0.5) for i, (_, _, b, a) in enumerate(layers)]

img = np.zeros((H, W, 4), dtype=np.float32)
rows = np.arange(H)[:, None]
layer_of = np.full((H, W), len(layers) - 1)
for i in range(len(layers) - 2, -1, -1):
    layer_of = np.where(rows < bounds[i][None, :], i, layer_of)

noise = nrng.normal(0, 1, (H, W))
for i, (name, col, _, _) in enumerate(layers):
    m = layer_of == i
    c = np.array(col, dtype=np.float32)
    shade = 1 + noise * (0.06 if name not in ("grass",) else 0.10)
    # faint horizontal bedding inside rock layers
    if i >= 3:
        shade += 0.05 * np.sin(rows * 0.9 + i) * np.ones((1, W))
    for ch in range(3):
        img[..., ch] = np.where(m, c[ch] * shade, img[..., ch])
img[..., 3] = 255

# dark seams along each boundary
for i in range(len(layers) - 1):
    b = bounds[i]
    for xx in range(W):
        yy = int(round(b[xx]))
        for d, k in ((0, 0.55), (1, 0.75)):
            if 0 <= yy + d < H:
                img[yy + d, xx, :3] *= k

# pebbles and boulders in the soil and rock
for _ in range(90):
    cx, cy = rng.randrange(W), rng.randrange(20, H - 30)
    r = rng.uniform(1.5, 4.5)
    li = layer_of[cy, cx]
    base = np.array(layers[li][1], dtype=np.float32) * rng.uniform(0.75, 1.2)
    for yy in range(int(cy - r - 1), int(cy + r + 2)):
        for xx in range(int(cx - r - 1), int(cx + r + 2)):
            if (xx - cx) ** 2 + ((yy - cy) * 1.3) ** 2 <= r * r and 0 <= yy < H:
                img[yy, xx % W, :3] = base * (0.85 if yy > cy else 1.05)

# ore flecks in the deeper rock
ores = [(222, 186, 64), (196, 202, 210), (150, 88, 64), (92, 168, 112), (120, 200, 90)]
for _ in range(70):
    cx, cy = rng.randrange(W), rng.randrange(95, H - 40)
    col = np.array(rng.choice(ores), dtype=np.float32)
    for _ in range(rng.randint(2, 6)):
        px, py = (cx + rng.randint(-3, 3)) % W, cy + rng.randint(-2, 2)
        if 0 <= py < H - 1:
            img[py, px, :3] = col
            img[py + 1, px, :3] = col * 0.55

# grass fringe on top: little blades poking above a ragged line
for xx in range(W):
    top = int(rng.uniform(0, 3))
    img[:top, xx, 3] = 0
    if rng.random() < 0.35:
        h = rng.randint(1, 4)
        img[max(0, top - h):top, xx, :3] = (100, 132, 66)
        img[max(0, top - h):top, xx, 3] = 255

# broken bottom edge
bottom = wavy(H - 22, 9.0, 999, rough=2.2)
for xx in range(W):
    b = int(min(H - 1, max(H - 60, bottom[xx])))
    img[b:, xx, 3] = 0
    for d in range(1, 4):
        if b - d >= 0:
            img[b - d, xx, :3] *= 0.6 + 0.1 * d

out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA")   # image top = top of the face (v = 1)
path = os.path.join(ROOT, "Textures", "IsoRim", "Edge", "Strata.png")
out.save(path)
print("wrote", path)
