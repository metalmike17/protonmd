from . import game, system


def run_system_checks():
    return system.run_all()


def run_game_checks(root, game_obj):
    return game.run_all(root, game_obj)
