#!/usr/bin/env python3
"""Writes the colour lookup tables (LUTs) for IsoRim's looks into the mod's LUTs folder.

Run from anywhere:  python3 tools/make_luts.py   (needs numpy and Pillow)

Each LUT is a 1024 x 32 PNG strip: 32 slices of 32 x 32, blue picks the slice, red runs across a
slice and green runs up it. A file named after a look (Gentle.png, Filmic.png ...) is used for that
look when the shader bundle is installed; any other strip of the same layout put in the folder can
be picked by name in the options. Here the looks are worked out exactly: true desaturation, a
smooth S-shaped contrast curve, lift for the shadows and gain for the highlights. The blended
fallback in the mod approximates the same looks with what plain blending can do.
"""

import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "LUTs")
N = 32

# name: desaturation, contrast, brightness, gain (highlights), lift (shadows), exposure
LOOKS = {
    "Gentle":        dict(desat=0.15, bright=0.95),
    "WarmAfternoon": dict(desat=0.06, contrast=0.2, gain=(1.0, 0.95, 0.85), lift=(0.03, 0.015, 0.0)),
    "CoolMorning":   dict(desat=0.12, gain=(0.90, 0.96, 1.0), lift=(0.0, 0.012, 0.035)),
    "Filmic":        dict(desat=0.18, contrast=0.5, gain=(1.0, 0.97, 0.93), lift=(0.025, 0.02, 0.03)),
    "Bleak":         dict(desat=0.45, contrast=0.25, bright=0.95, gain=(0.92, 0.95, 0.98), lift=(0.02, 0.025, 0.03)),
    "Vivid":         dict(desat=-0.18, contrast=0.45, exposure=0.06),
    "Autumn":        dict(desat=0.10, contrast=0.25, gain=(1.0, 0.90, 0.78), lift=(0.03, 0.01, 0.0)),
    "Moonlight":     dict(desat=0.5, bright=0.9, gain=(0.72, 0.82, 1.0), lift=(0.0, 0.01, 0.04)),
    "Toxic":         dict(desat=0.2, gain=(0.88, 1.0, 0.80), lift=(0.01, 0.03, 0.0)),
    "Sepia":         dict(desat=0.85, gain=(1.0, 0.88, 0.70), lift=(0.04, 0.025, 0.01)),
    "Noir":          dict(desat=1.0, contrast=0.6),
    # extras, only as LUTs
    "Neutral":       dict(),
    "Pastel":        dict(desat=0.30, bright=1.0, lift=(0.06, 0.06, 0.07), contrast=0.0),
    "Cinematic":     dict(desat=0.12, contrast=0.4, gain=(1.0, 0.96, 0.88), lift=(0.0, 0.03, 0.05)),
}


def grade(rgb, desat=0.0, contrast=0.0, bright=1.0, gain=(1, 1, 1), lift=(0, 0, 0), exposure=0.0):
    c = rgb.copy()
    lum = (c * np.array([0.299, 0.587, 0.114])).sum(axis=-1, keepdims=True)
    c = c + (lum - c) * desat                          # negative desat adds colour
    c = np.clip(c, 0, 1)
    s_curve = c * c * (3 - 2 * c)
    c = c + (s_curve - c) * (contrast * 0.8)
    c = c * bright
    c = c * np.array(gain)
    c = c + np.array(lift) * (1 - c)
    c = c * (1 + exposure)
    return np.clip(c, 0, 1)


def strip(look):
    v = np.arange(N) / (N - 1)
    out = np.zeros((N, N * N, 3))
    for b in range(N):
        r, g = np.meshgrid(v, v)                       # g varies down the rows, r across
        rgb = np.stack([r, g, np.full_like(r, v[b])], axis=-1)
        out[:, b * N:(b + 1) * N, :] = grade(rgb, **look)
    # Row 0 of the picture is its top; the shader reads green upward from the bottom.
    return np.flipud(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, look in LOOKS.items():
        img = Image.fromarray((strip(look) * 255 + 0.5).astype(np.uint8), "RGB")
        img.save(os.path.join(OUT, name + ".png"))
    print("%d LUTs written to %s" % (len(LOOKS), OUT))


if __name__ == "__main__":
    main()
