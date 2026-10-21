"""Locate Steam and read its libraries, games, Proton installs and per-game settings."""
import glob
import os
from pathlib import Path

from . import vdf
from .model import Game

HOME = Path.home()
STEAM_CANDIDATES = [
    HOME / ".local/share/Steam",
    HOME / ".steam/steam",
    HOME / ".var/app/com.valvesoftware.Steam/.local/share/Steam",
]

TOOL_HINTS = ("proton", "steam linux runtime", "steamworks common", "steam linux runtime")


def find_steam_root():
    for c in STEAM_CANDIDATES:
        if (c / "steamapps").is_dir():
            return c.resolve()
    return None


def _registered_libraries(root):
    paths = [str(root)]
    lf = root / "steamapps/libraryfolders.vdf"
    if lf.exists():
        data = vdf.get(vdf.load(lf), "libraryfolders", default={})
        for entry in data.values():
            p = entry.get("path") if isinstance(entry, dict) else None
            if p and p not in paths:
                paths.append(p)
    return paths


def _mount_bases():
    user = HOME.name
    bases = []
    for pattern in (f"/run/media/{user}/*", f"/media/{user}/*", "/mnt/*"):
        bases.extend(glob.glob(pattern))
    return bases


def _discover_unregistered():
    """Steam libraries sitting on mounted drives that Steam doesn't list (e.g. a copied SteamLibrary)."""
    found = []
    for base in _mount_bases():
        for cand in (base, f"{base}/SteamLibrary", f"{base}/Steam", f"{base}/steam"):
            if os.path.isdir(f"{cand}/steamapps"):
                found.append(cand)
    return found


def missing_libraries(root):
    """Registered libraries whose folder isn't reachable, usually an unmounted drive."""
    return [p for p in _registered_libraries(root) if not os.path.isdir(f"{p}/steamapps")]


def library_paths(root):
    paths, seen = [], set()
    for p in _registered_libraries(root) + _discover_unregistered():
        if not os.path.isdir(f"{p}/steamapps"):
            continue
        real = os.path.realpath(p)
        if real not in seen:
            seen.add(real)
            paths.append(p)
    return paths


def scan_games(root):
    games = []
    for lib in library_paths(root):
        for acf in sorted(glob.glob(f"{lib}/steamapps/appmanifest_*.acf")):
            try:
                st = vdf.get(vdf.load(acf), "AppState", default={})
            except OSError:
                continue
            name = st.get("name", "")
            games.append(Game(
                appid=st.get("appid", ""),
                name=name,
                library=lib,
                installdir=st.get("installdir", ""),
                size_on_disk=int(st.get("SizeOnDisk", 0) or 0),
                state_flags=int(st.get("StateFlags", 0) or 0),
                is_tool=any(h in name.lower() for h in TOOL_HINTS),
            ))
    return games


def installed_proton_tools(root):
    """Return {tool_dir_name: path} for custom (compatibilitytools.d) and Valve Protons."""
    tools = {}
    for d in (root / "compatibilitytools.d", HOME / ".steam/root/compatibilitytools.d"):
        if d.is_dir():
            for p in d.iterdir():
                if p.is_dir() or p.is_symlink():
                    tools.setdefault(p.name, str(p))
    for lib in library_paths(root):
        for p in glob.glob(f"{lib}/steamapps/common/Proton*"):
            tools.setdefault(os.path.basename(p), p)
    return tools


def _config_files(root):
    return sorted(glob.glob(f"{root}/userdata/*/config/localconfig.vdf"))


def compat_tool_mapping(root):
    """appid -> compat tool name chosen in Steam ('0' is the global default)."""
    cfg = root / "config/config.vdf"
    if not cfg.exists():
        return {}
    m = vdf.get(vdf.load(cfg), "InstallConfigStore", "Software", "Valve", "Steam",
                "CompatToolMapping", default={})
    return {k: v.get("name", "") for k, v in m.items() if isinstance(v, dict)}


def launch_options(root, appid):
    for lc in _config_files(root):
        apps = vdf.get(vdf.load(lc), "UserLocalConfigStore", "Software", "Valve", "Steam",
                       "apps", default={})
        opts = vdf.get(apps, appid, "LaunchOptions")
        if opts:
            return opts
    return ""


def dir_size(path):
    total = 0
    for dp, _, files in os.walk(path, onerror=lambda e: None):
        for f in files:
            try:
                total += os.lstat(os.path.join(dp, f)).st_size
            except OSError:
                pass
    return total


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
