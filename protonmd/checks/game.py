"""Per-game checks for Steam titles."""
import glob
import os
import re
import shutil
import subprocess
import time

from .. import steam
from ..model import Fix, Game, Result, Status
from . import rules


IN_FLATPAK = os.path.exists("/.flatpak-info")


def _steam_running():
    try:
        return subprocess.run(["pgrep", "-x", "steam"], capture_output=True).returncode == 0
    except OSError:
        return False


def _game_running(game):
    if IN_FLATPAK:  # the sandbox can't see host processes
        return False
    try:
        out = subprocess.run(["pgrep", "-af", f"AppId={game.appid}"], capture_output=True, text=True).stdout
        return bool(out.strip())
    except OSError:
        return False


def check_installed(root, game):
    if game.state_flags & 4 and not game.state_flags & 2:  # fully installed, no update pending
        return Result("installed", "Installation", Status.OK, steam.human(game.size_on_disk))
    return Result("installed", "Installation", Status.WARN,
                  f"Steam reports the game is not fully installed or has a pending update (state {game.state_flags}).",
                  hint="Let Steam finish updating, or verify integrity of game files.")


def check_disk(root, game):
    try:
        free = shutil.disk_usage(game.library).free
    except OSError:
        return None
    if free < 5 * 1024**3:
        return Result("disk", "Free disk space", Status.WARN,
                      f"Only {steam.human(free)} free on the library drive. Shader caches and updates can fail.")
    return Result("disk", "Free disk space", Status.OK, f"{steam.human(free)} free")


def check_compat_tool(root, game):
    mapping = steam.compat_tool_mapping(root)
    tools = steam.installed_proton_tools(root)
    chosen = mapping.get(game.appid) or mapping.get("0") or ""
    if not chosen:
        return Result("proton", "Compatibility tool", Status.INFO,
                      "Using Steam's default. Windows-only games need Proton enabled in Properties > Compatibility.")
    # Steam internal names like proton_experimental / proton_9 map to Valve installs.
    internal_ok = chosen.startswith("proton_") or chosen.startswith("steamlinuxruntime")
    if chosen in tools or internal_ok:
        return Result("proton", "Compatibility tool", Status.OK, chosen)
    return Result("proton", "Compatibility tool", Status.FAIL,
                  f"Steam is set to use '{chosen}' but it isn't installed. The game will fail to launch or silently fall back.",
                  hint=f"Install it, or choose another tool. Installed: {', '.join(sorted(tools)) or 'none'}")


def check_prefix(root, game):
    if game.is_tool:
        return None
    if not os.path.isdir(game.prefix):
        return Result("prefix", "Wine prefix", Status.INFO,
                      "No prefix yet. It is created on first launch with Proton.")
    if not os.listdir(game.prefix):
        return Result("prefix", "Wine prefix", Status.INFO,
                      "Empty prefix folder. Normal for native Linux games, or a Windows game that hasn't launched via Proton yet.")
    reg = os.path.join(game.prefix, "pfx/system.reg")
    if not os.path.exists(reg):
        return Result("prefix", "Wine prefix", Status.FAIL,
                      "The prefix exists but is incomplete (no system.reg). This is a typical sign of an interrupted first launch.",
                      fix=_reset_prefix_fix(game))
    size = steam.dir_size(game.prefix)
    return Result("prefix", "Wine prefix", Status.OK, f"Healthy, {steam.human(size)}")


def _write_failed(err):
    why = f" ({err.strerror})" if err is not None and getattr(err, "strerror", None) else ""
    return ("Couldn't change this folder" + why + ". It is read-only for ProtonMD, which is the case for "
            "Flatpak Steam libraries inside the Flatpak build. Use the native package or do it by hand.")


def _reset_prefix_fix(game):
    def run():
        if _steam_running() and _game_running(game):
            return "Close the game first."
        dest = f"{game.prefix}.protonmd-bak-{int(time.time())}"
        try:
            os.rename(game.prefix, dest)
        except OSError as e:
            return _write_failed(e)
        return f"Moved prefix to {dest}. Steam will create a fresh one on next launch."
    return Fix("Back up and reset prefix", run, command=f"mv compatdata/{game.appid} compatdata/{game.appid}.protonmd-bak-<time>")


def check_launch_options(root, game):
    opts = steam.launch_options(root, game.appid)
    if not opts:
        return Result("launch", "Launch options", Status.OK, "None set.")
    found = []
    worst = Status.OK
    for pat, st, msg, hint in rules.LAUNCH_OPTION_RULES:
        if st is None:
            continue
        if re.search(pat, opts):
            found.append(msg + (f" {hint}" if hint else ""))
            worst = max(worst, Status[st])
    if "%command%" not in opts and re.search(r"\b\w+=", opts) and not opts.strip().startswith("-"):
        found.append("Environment variables are set but '%command%' is missing, so they won't be applied.")
        worst = max(worst, Status.FAIL)
    if not found:
        return Result("launch", "Launch options", Status.OK, opts)
    return Result("launch", "Launch options", worst, f"{opts}\n" + "\n".join(found))


def check_shader_cache(root, game):
    path = f"{game.library}/steamapps/shadercache/{game.appid}"
    if not os.path.isdir(path):
        return None
    size = steam.dir_size(path)

    def run():
        if _game_running(game):
            return "Close the game first."
        if not os.access(os.path.dirname(path), os.W_OK):
            return _write_failed(None)
        shutil.rmtree(path, ignore_errors=True)
        return "Shader cache cleared. The first launch will recompile shaders."
    fix = Fix("Clear shader cache", run, command=f"rm -r steamapps/shadercache/{game.appid}")
    st = Status.WARN if size > 2 * 1024**3 else Status.OK
    return Result("shadercache", "Shader cache", st, steam.human(size) +
                  (" is large; clearing it can fix stutter or corrupted rendering." if st else ""), fix=fix)


def check_proton_log(root, game):
    if IN_FLATPAK:
        return Result("log", "Proton log", Status.INFO,
                      "Log scanning isn't available inside the Flatpak sandbox (logs are written to your home folder).")
    candidates = [os.path.expanduser(f"~/steam-{game.appid}.log")]
    log = next((c for c in candidates if os.path.exists(c)), None)
    if not log:
        return Result("log", "Proton log", Status.INFO,
                      f"No log found. Add PROTON_LOG=1 %command% to launch options, run the game, then re-scan.")
    with open(log, errors="replace") as f:
        text = f.read()
    hits = []
    for pat, title, hint in rules.LOG_SIGNATURES:
        m = re.search(pat, text)
        if m:
            hits.append(f"{title.format(*m.groups())}: {hint}")
    if not hits:
        return Result("log", "Proton log", Status.OK, f"No known errors in {log}")
    return Result("log", "Proton log", Status.FAIL, "\n".join(hits))


ALL = [check_installed, check_compat_tool, check_prefix, check_launch_options,
       check_shader_cache, check_disk, check_proton_log]


def run_all(root, game):
    out = []
    for fn in ALL:
        try:
            r = fn(root, game)
            if r:
                out.append(r)
        except Exception as e:
            out.append(Result(fn.__name__, fn.__name__, Status.INFO, f"Check crashed: {e}"))
    return out
