#!/bin/bash
# Run INSIDE ubuntu:24.04 (glibc 2.39, libadwaita 1.5) so the AppImage runs on Ubuntu 24.04+, Debian 13+, Fedora 40+, Arch, etc.
# /src = repo (read-only), /out = output dir. Produces /out/AppDir
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 libgtk-4-1 libadwaita-1-0 \
  libglib2.0-bin librsvg2-common libgdk-pixbuf2.0-0 libgdk-pixbuf2.0-bin shared-mime-info adwaita-icon-theme hicolor-icon-theme binutils >/dev/null
A=/out/AppDir; rm -rf $A; mkdir -p $A/usr/bin $A/usr/lib $A/usr/share
PYV=$(python3 -c 'import sys;print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
cp /usr/bin/python$PYV $A/usr/bin/python3
mkdir -p $A/usr/lib/python$PYV
cp -a /usr/lib/python$PYV/. $A/usr/lib/python$PYV/
rm -rf $A/usr/lib/python$PYV/{test,idlelib,tkinter,turtledemo,lib2to3,ensurepip,distutils/tests} $A/usr/lib/python$PYV/config-*
SP=$A/usr/lib/python$PYV/site-packages; mkdir -p $SP
DP=/usr/lib/python3/dist-packages
cp -a $DP/gi $SP/; for d in $DP/cairo $DP/pycairo* $DP/PyGObject*; do [ -e $d ] && cp -a $d $SP/ || true; done
cp -a /src/protonmd $SP/
find $A -name __pycache__ -type d -prune -exec rm -rf {} +
# typelibs, schemas, icons, pixbuf loaders
cp -a /usr/lib/x86_64-linux-gnu/girepository-1.0 $A/usr/lib/
mkdir -p $A/usr/share/glib-2.0; cp -a /usr/share/glib-2.0/schemas $A/usr/share/glib-2.0/
glib-compile-schemas $A/usr/share/glib-2.0/schemas
mkdir -p $A/usr/share/icons; cp -a /usr/share/icons/Adwaita /usr/share/icons/hicolor $A/usr/share/icons/ 2>/dev/null || true
cp -a /usr/share/mime $A/usr/share/
PL=$A/usr/lib/gdk-pixbuf/loaders; mkdir -p $PL
cp /usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders/*.so $PL/
# shared-library closure (host provides glibc, GL, X11/Wayland, audio, systemd)
EX='^(linux-vdso|ld-linux|libc\.|libm\.|libdl\.|libpthread|librt\.|libutil|libresolv|libnsl|libGL|libEGL|libGLX|libgbm|libdrm|libX11\.|libX11-xcb|libxcb\.|libasound|libpulse|libudev|libsystemd|libstdc\+\+|libgcc_s|libnss)'
TARGETS="$A/usr/bin/python3 /usr/lib/x86_64-linux-gnu/libgtk-4.so.1 /usr/lib/x86_64-linux-gnu/libadwaita-1.so.0 $(find $A/usr/lib -name '*.so*' -type f)"
for f in $TARGETS; do
  ldd $f 2>/dev/null | awk '/=> \//{print $3}' | while read l; do
    b=$(basename $l); echo "$b" | grep -Eq "$EX" && continue
    cp -nL $l $A/usr/lib/
  done
done
cp -nL /usr/lib/x86_64-linux-gnu/libgtk-4.so.1 /usr/lib/x86_64-linux-gnu/libadwaita-1.so.0 $A/usr/lib/
# pixbuf loader cache with placeholder path
GDK_PIXBUF_MODULEDIR=$PL /usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/gdk-pixbuf-query-loaders $PL/*.so 2>/dev/null | sed "s|$PL|@APPDIR@/usr/lib/gdk-pixbuf/loaders|g" > $A/usr/lib/gdk-pixbuf/loaders.cache.in || true
du -sh $A; echo "py $PYV"
