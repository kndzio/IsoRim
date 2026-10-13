#!/usr/bin/env python3
"""Draws contact sheets of IsoRim's models as the isometric camera sees them, for checking shapes
without starting the game. Plain colours only (no textures), flat shading, painter's order.

    python3 tools/preview_models.py OUTDIR [name-prefix ...]

Writes OUTDIR/sheet_N.png, 20 models per sheet, each labelled. With prefixes, only models whose
names start with one of them.
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "Models")
LIGHT = np.array([-0.35, 0.8, -0.5])
LIGHT /= np.linalg.norm(LIGHT)
STUFF = (0.62, 0.50, 0.36)      # what "stuff" materials are shown in: wood


def materials():
    mats, cur = {}, None
    for line in open(os.path.join(MODELS, "isorim.mtl")):
        t = line.split()
        if not t:
            continue
        if t[0] == "newmtl":
            cur = t[1]
            mats[cur] = (0.8, 0.8, 0.8)
        elif t[0] == "Kd" and cur:
            mats[cur] = tuple(float(x) for x in t[1:4])
    return mats


def load(path, mats):
    verts, tris, cur = [], [], None
    for line in open(path):
        t = line.split()
        if not t:
            continue
        if t[0] == "v":
            verts.append((float(t[1]), float(t[2]), -float(t[3])))
        elif t[0] == "usemtl":
            cur = t[1]
        elif t[0] == "f":
            idx = [int(p.split("/")[0]) - 1 for p in t[1:]]
            col = np.array(mats.get(cur, (0.8, 0.8, 0.8)))
            if cur and cur.startswith("stuff"):
                col = col * np.array(STUFF) if "plain" not in cur and "herb" not in cur else col * 0.75
            for i in range(1, len(idx) - 1):
                tris.append(([verts[idx[0]], verts[idx[i]], verts[idx[i + 1]]], col, cur or ""))
    return tris


def render(tris, size=260, yaw=45.0, pitch=35.0):
    img = Image.new("RGB", (size, size), (58, 62, 54))
    if not tris:
        return img
    y, p = math.radians(yaw), math.radians(pitch)
    # camera looking along +forward from the south-west, as the mod's isometric view does
    fwd = np.array([math.sin(y) * math.cos(p), -math.sin(p), math.cos(y) * math.cos(p)])
    right = np.array([math.cos(y), 0.0, -math.sin(y)])
    up = np.cross(fwd, right)
    pts = np.array([v for tri, _, _ in tris for v in tri])
    sx, sy = pts @ right, pts @ up
    span = max(sx.max() - sx.min(), sy.max() - sy.min(), 0.4)
    scale = (size * 0.84) / span
    cx, cy = (sx.max() + sx.min()) / 2, (sy.max() + sy.min()) / 2
    d = ImageDraw.Draw(img)
    order = []
    for tri, col, name in tris:
        a, b, c = (np.array(v) for v in tri)
        n = np.cross(b - a, c - a)
        ln = np.linalg.norm(n)
        if ln < 1e-12:
            continue
        n /= ln
        if np.dot(n, fwd) > 0:            # facing away
            continue
        shade = 1.0 if name.startswith(("glow", "flame", "ember", "charge")) else 0.5 + 0.5 * min(1, max(0, np.dot(n, LIGHT)) / LIGHT[1])
        depth = np.mean([np.dot(v, fwd) for v in (a, b, c)])
        poly = [(size / 2 + (np.dot(v, right) - cx) * scale, size / 2 - (np.dot(v, up) - cy) * scale) for v in (a, b, c)]
        order.append((depth, poly, tuple(int(255 * min(1, v * shade)) for v in col)))
    order.sort(key=lambda o: -o[0])
    for _, poly, col in order:
        d.polygon(poly, fill=col, outline=tuple(int(v * 0.55) for v in col))
    return img


def main():
    out = sys.argv[1]
    prefixes = sys.argv[2:]
    os.makedirs(out, exist_ok=True)
    mats = materials()
    names = sorted(f[:-4] for f in os.listdir(MODELS) if f.endswith(".obj"))
    if prefixes:
        names = [n for n in names if n.startswith(tuple(prefixes))]
    per = 20
    font = ImageFont.load_default()
    for k in range(0, len(names), per):
        sheet = Image.new("RGB", (5 * 260, 4 * 280), (30, 30, 30))
        for i, name in enumerate(names[k:k + per]):
            img = render(load(os.path.join(MODELS, name + ".obj"), mats))
            x, y = (i % 5) * 260, (i // 5) * 280
            sheet.paste(img, (x, y))
            ImageDraw.Draw(sheet).text((x + 4, y + 262), name, fill=(230, 230, 230), font=font)
        sheet.save(os.path.join(out, "sheet_%d.png" % (k // per + 1)))
    print("%d models drawn" % len(names))


if __name__ == "__main__":
    main()
