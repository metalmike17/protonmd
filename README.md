<div align="center">

<img src="docs/banner.svg" alt="ProtonMD: diagnose why a Linux game will not run" width="100%">

<br>

<a href="https://github.com/metalmike17/protonmd/actions/workflows/test.yml"><img src="https://github.com/metalmike17/protonmd/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
<a href="https://github.com/metalmike17/protonmd/releases/latest"><img src="https://img.shields.io/github/v/release/metalmike17/protonmd?style=for-the-badge&labelColor=0D0F14&color=FF2BD6&label=release" alt="Latest release"></a>
<img src="https://img.shields.io/badge/license-GPL--3.0-00C8D6?style=for-the-badge&labelColor=0D0F14" alt="License">
<img src="https://img.shields.io/badge/GTK4-libadwaita-FF2BD6?style=for-the-badge&labelColor=0D0F14" alt="GTK4 + libadwaita">
<a href="https://github.com/metalmike17/protonmd/stargazers"><img src="https://img.shields.io/github/stars/metalmike17/protonmd?style=for-the-badge&labelColor=0D0F14&color=FF2BD6" alt="Stars"></a>

<br><br>

**[⬇️ Download](https://github.com/metalmike17/protonmd/releases/latest)** &nbsp;·&nbsp; **[🔍 What it checks](#what-it-checks)** &nbsp;·&nbsp; **[🚀 Install](#install)** &nbsp;·&nbsp; **[🤝 Contribute](#contributing)**

<br>

<img src="docs/screenshot.png" alt="ProtonMD checking a game" width="760">

</div>

<img src="docs/divider.svg" width="100%" alt="">

**Diagnose why a Linux game won't run.**

ProtonMD checks your GPU driver, Vulkan setup and kernel limits, then inspects each Steam game's
Wine prefix, Proton version, launch options and shader cache. It explains what is wrong and offers
safe fixes, each one shown and confirmed before it runs.

> Unofficial. Not affiliated with Valve or Proton AG.

<img src="docs/divider.svg" width="100%" alt="">

## What it checks

- GPU driver, 64-bit and 32-bit Vulkan
- `vm.max_map_count` and the open-file limit (esync)
- Missing or wrong Proton / compatibility tool
- Broken or incomplete Wine prefixes
- Risky launch options (`DXVK_ASYNC`, `PROTON_USE_WINED3D`, a missing `%command%`, ...)
- Shader cache size, free disk space, known errors in Proton logs
- Steam libraries on external drives, including ones Steam doesn't list

<img src="docs/divider.svg" width="100%" alt="">

## Install

Download from the [latest release](https://github.com/metalmike17/protonmd/releases/latest). Each file has a `.sha256` next to it.

**AppImage** (x86_64, bundles Python and GTK; built on a recent distro, so it needs a similarly recent glibc):

    chmod +x ProtonMD-*-x86_64.AppImage
    ./ProtonMD-*-x86_64.AppImage

**Debian / Ubuntu / Mint** (needs GTK 4 and libadwaita 1, so Debian 12+ or Ubuntu 22.04+):

    sudo apt install ./protonmd_*_all.deb

**Fedora**:

    sudo dnf install ./protonmd-*.noarch.rpm

**Arch / CachyOS**: see `packaging/aur/PKGBUILD`.

**Flatpak** (from source):

    flatpak-builder --user --install --force-clean build-dir io.github.metalmike17.ProtonMD.yml

**From source**: `python -m protonmd` (needs GTK4, libadwaita and PyGObject). Use `--cli` for plain text output.

The .deb and .rpm packages are unsigned and have only been tested by unpacking and running the files, not by installing them on Debian or Fedora. Please open an issue if one fails to install.

<img src="docs/divider.svg" width="100%" alt="">

## Flatpak limitations

The sandbox can't run host commands, so the Vulkan 64-bit check, Proton log scanning and
running-game detection are unavailable, and Flatpak Steam (`com.valvesoftware.Steam`) libraries aren't visible. Use the native package for those. The native package has no such limits.

<img src="docs/divider.svg" width="100%" alt="">

## Contributing

Checks are plain Python in `protonmd/checks/`, and the known-bad launch options and log signatures are
data in `protonmd/checks/rules.py`. New rules are the easiest way to help. Open an issue with the
"New check" template or send a pull request with a test.

<img src="docs/divider.svg" width="100%" alt="">

## Tests

    python -m unittest discover -s tests

<img src="docs/divider.svg" width="100%" alt="">

## License

GPL-3.0-or-later.
