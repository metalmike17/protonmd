"""`protonmd --demo`: sample games and results so you can try the app (and take screenshots)
without Steam. Nothing here reads or changes your system."""
from . import checks, config, steam
from .model import Fix, Game, Result, Status

OK, INFO, WARN, FAIL = Status.OK, Status.INFO, Status.WARN, Status.FAIL
GB = 1024**3
LIB = "/mnt/games/SteamLibrary"

GAMES = [  # appid, name, size in GB
    ("1091500", "Cyberpunk 2077", 70), ("3764200", "Resident Evil Requiem", 62),
    ("2406770", "Bodycam", 41), ("1643320", "S.T.A.L.K.E.R. 2: Heart of Chornobyl", 160),
    ("1245620", "ELDEN RING", 60), ("1086940", "Baldur's Gate 3", 150),
    ("553850", "HELLDIVERS 2", 100), ("2358720", "Black Myth: Wukong", 130),
    ("730", "Counter-Strike 2", 35),
]


def _fix(label, cmd):
    return Fix(label, lambda: "Demo mode: nothing was changed.", command=cmd)


def _cache(appid, size_gb):
    st = WARN if size_gb > 2 else OK
    return Result("shadercache", "Shader cache", st, f"{size_gb:.1f} GB" +
                  (" is large; clearing it can fix stutter or corrupted rendering." if st else ""),
                  fix=_fix("Clear shader cache", f"rm -r steamapps/shadercache/{appid}"))


def _base(appid, size_gb, tool="proton_experimental", prefix="Healthy", free=836.5):
    return [Result("installed", "Installation", OK, f"{size_gb:.1f} GB"),
            Result("proton", "Compatibility tool", OK, tool),
            Result("prefix", "Wine prefix", OK, f"{prefix}, 412.0 MB"),
            Result("disk", "Free disk space", OK, f"{free:.1f} GB free")]


def _game_results(appid):
    size = {g[0]: g[2] for g in GAMES}[appid]
    r = _base(appid, size)
    opts_ok = Result("launch", "Launch options", OK, "None set.")
    log_ok = Result("log", "Proton log", OK, f"No known errors in ~/steam-{appid}.log")
    if appid == "1091500":  # Cyberpunk: big shader cache
        return r + [opts_ok, log_ok, _cache(appid, 4.2)]
    if appid == "3764200":  # RE Requiem: stale launch options
        return r + [Result("launch", "Launch options", WARN,
                           "DXVK_ASYNC=1 PROTON_USE_WINED3D=1 %command%\n"
                           "DXVK_ASYNC only works in patched DXVK builds. Mainline DXVK ignores it, and it can trigger "
                           "anti-cheat bans in some online games. Remove it. Use shader pre-caching instead.\n"
                           "PROTON_USE_WINED3D=1 replaces DXVK/VKD3D with OpenGL translation. It is much slower and "
                           "rarely needed on modern GPUs. Remove it unless this game specifically needs it."),
                    log_ok, _cache(appid, 1.1)]
    if appid == "2406770":  # Bodycam: missing runtime
        return r + [opts_ok, Result("log", "Proton log", FAIL,
                                    "Missing DLL: vcruntime140_1.dll\nA runtime is missing from the prefix. Install it "
                                    "with protontricks (for example vcrun2022, d3dcompiler_47, dotnet)."),
                    _cache(appid, 0.8)]
    if appid == "1643320":  # STALKER 2: no proton chosen
        return [r[0], Result("proton", "Compatibility tool", INFO,
                             "Using Steam's default. Windows-only games need Proton enabled in Properties > Compatibility."),
                r[2], r[3], opts_ok, log_ok, _cache(appid, 3.6)]
    if appid == "1245620":
        return r + [Result("launch", "Launch options", OK, "gamemoderun %command%"), log_ok, _cache(appid, 1.4)]
    if appid == "553850":  # Helldivers: broken prefix
        r[2] = Result("prefix", "Wine prefix", FAIL,
                      "The prefix exists but is incomplete (no system.reg). This is a typical sign of an interrupted first launch.",
                      fix=_fix("Back up and reset prefix", "mv compatdata/553850 compatdata/553850.protonmd-bak-<time>"))
        return r + [opts_ok, log_ok]
    return r + [opts_ok, log_ok, _cache(appid, 0.6)]


def _system_results():
    return [Result("demo", "Demo mode", INFO, "Sample data for screenshots and trying the app. This is not your system."),
            Result("gpu", "GPU driver", OK, "NVIDIA kernel module 580.95.05"),
            Result("vulkan", "Vulkan 64-bit", OK, "NVIDIA GeForce RTX 4070"),
            Result("vulkan32", "32-bit Vulkan", OK, "32-bit loader present."),
            Result("maxmap", "vm.max_map_count", OK, "2147483642"),
            Result("nofile", "Open file limit", OK, "1048576")]


def install():
    steam.find_steam_root = lambda: "/demo/steam"
    steam.scan_games = lambda root, hidden=(): [
        Game(appid=a, name=n, library=LIB, installdir=n, size_on_disk=int(s * GB), state_flags=4) for a, n, s in GAMES]
    steam.missing_libraries = lambda root: []
    steam.all_libraries = lambda root: [(LIB, True)]
    config.hidden_libraries = lambda: set()
    checks.run_system_checks = _system_results
    checks.run_game_checks = lambda root, g: _game_results(g.appid)
