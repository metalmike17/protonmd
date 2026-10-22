#!/bin/sh
# Build protonmd_<version>_all.deb from the working tree. Needs dpkg-deb.
set -eu
cd "$(dirname "$0")/../.."
VER=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' protonmd/__init__.py)
ROOT=$(mktemp -d)
PKG=$ROOT/protonmd_${VER}_all
install -d "$PKG/DEBIAN" "$PKG/usr/bin" "$PKG/usr/lib/python3/dist-packages"
cp -r protonmd "$PKG/usr/lib/python3/dist-packages/"
find "$PKG" -name __pycache__ -prune -exec rm -rf {} +
cat > "$PKG/usr/bin/protonmd" <<'LAUNCH'
#!/usr/bin/python3
import sys
from protonmd.launcher import main
sys.exit(main())
LAUNCH
chmod 755 "$PKG/usr/bin/protonmd"
install -Dm644 data/io.github.metalmike17.ProtonMD.desktop -t "$PKG/usr/share/applications/"
install -Dm644 data/io.github.metalmike17.ProtonMD.metainfo.xml -t "$PKG/usr/share/metainfo/"
install -Dm644 data/io.github.metalmike17.ProtonMD.svg -t "$PKG/usr/share/icons/hicolor/scalable/apps/"
install -Dm644 LICENSE "$PKG/usr/share/doc/protonmd/copyright"
cat > "$PKG/DEBIAN/control" <<CTRL
Package: protonmd
Version: $VER
Architecture: all
Maintainer: metalmike17 <michaeljg0717@gmail.com>
Depends: python3 (>= 3.10), python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1
Recommends: vulkan-tools
Suggests: gamemode, winetricks
Section: utils
Priority: optional
Homepage: https://github.com/metalmike17/protonmd
Description: Diagnose why Linux games won't run
 ProtonMD checks GPU drivers, Vulkan setup and kernel limits, then inspects
 each Steam game's Wine prefix, Proton version, launch options and shader
 cache. It explains what is wrong and offers confirmed fixes.
 .
 Unofficial. Not affiliated with Valve or Proton AG.
CTRL
dpkg-deb --root-owner-group --build "$PKG" "${OUT:-.}/protonmd_${VER}_all.deb"
