#!/bin/sh
# Copies what players need into ../IsoRim_Release, ready to upload to the Steam Workshop.
# Run build.sh first.
cd "$(dirname "$0")" || exit 1
[ -f 1.6/Assemblies/IsoRim.dll ] || { echo "1.6/Assemblies/IsoRim.dll is missing: run build.sh first."; exit 1; }
OUT=../IsoRim_Release
rm -rf "$OUT" && mkdir -p "$OUT"
for d in About 1.5 1.6 Defs Models Textures LUTs Shaders; do cp -r "$d" "$OUT/"; done
cp README.txt "$OUT/"
echo "Done: $OUT"
