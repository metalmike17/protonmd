"""Plain-text mode: `python -m protonmd --cli [appid]`. Also used for testing the checks."""
import sys

from . import checks, steam
from .model import Status

ICON = {Status.OK: "[ ok ]", Status.INFO: "[info]", Status.WARN: "[warn]", Status.FAIL: "[FAIL]"}


def _print(results):
    for r in results:
        print(f"{ICON[r.status]} {r.title}: {r.detail}")
        if r.hint:
            print(f"        -> {r.hint}")
        if r.fix:
            print(f"        -> fix available: {r.fix.label} ({r.fix.command})")


def main(argv):
    root = steam.find_steam_root()
    print("== System ==")
    _print(checks.run_system_checks())
    if not root:
        print("\nSteam not found.")
        return 1
    games = [g for g in steam.scan_games(root) if not g.is_tool]
    target = argv[0] if argv else None
    for g in games:
        if target and g.appid != target:
            continue
        print(f"\n== {g.name} ({g.appid}) ==")
        _print(checks.run_game_checks(root, g))
    if not games:
        print("\nNo games installed in Steam (tools like Proton are hidden).")
    return 0
