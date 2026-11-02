#!/bin/bash
# Build the AppImage. Needs podman (or docker) and appimagetool.
#   packaging/appimage/build.sh /path/to/appimagetool.AppImage
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$HERE/../.." && pwd)"
TOOL="${1:-appimagetool}"; OUT="$REPO/build/appimage"; RT="$(command -v podman || command -v docker)"
mkdir -p "$OUT"
"$RT" run --rm -v "$REPO:/src:ro,Z" -v "$HERE:/c:ro,Z" -v "$OUT:/out:Z" docker.io/library/ubuntu:24.04 /c/build-in-container.sh
cp "$HERE/AppRun" "$OUT/AppDir/AppRun"; chmod +x "$OUT/AppDir/AppRun"
cp "$REPO/data/io.github.metalmike17.ProtonMD.desktop" "$REPO/data/io.github.metalmike17.ProtonMD.svg" "$OUT/AppDir/"
VER=$(python3 -c "import re;print(re.search(r'version = \"(.+?)\"',open('$REPO/pyproject.toml').read()).group(1))")
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$TOOL" --no-appstream "$OUT/AppDir" "$OUT/ProtonMD-$VER-x86_64.AppImage"
echo "Built $OUT/ProtonMD-$VER-x86_64.AppImage"
