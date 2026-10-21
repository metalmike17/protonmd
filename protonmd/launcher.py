import sys


def main():
    if "--cli" in sys.argv:
        from .cli import main as cli_main
        return cli_main([a for a in sys.argv[1:] if a != "--cli"])
    from .app import main as app_main
    return app_main()
