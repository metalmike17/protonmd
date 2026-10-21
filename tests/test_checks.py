import os
import tempfile
import unittest
from pathlib import Path

from protonmd import steam, vdf
from protonmd.checks import game as gc
from protonmd.model import Game, Status


def make_steam(tmp, launch="", tool="GE-Proton9-1", installed=("GE-Proton10-1",), prefix=True, complete=True):
    root = Path(tmp)
    (root / "steamapps/common").mkdir(parents=True)
    (root / "steamapps/libraryfolders.vdf").write_text(
        f'"libraryfolders"\n{{\n"0"\n{{\n"path" "{root}"\n}}\n}}\n')
    (root / "steamapps/appmanifest_42.acf").write_text(
        '"AppState"\n{\n"appid" "42"\n"name" "Test Game"\n"installdir" "TestGame"\n"StateFlags" "4"\n"SizeOnDisk" "1000"\n}\n')
    (root / "config").mkdir()
    (root / "config/config.vdf").write_text(
        '"InstallConfigStore"\n{"Software"{"Valve"{"Steam"{"CompatToolMapping"{"42"{"name" "%s"}}}}}}\n' % tool)
    (root / "userdata/1/config").mkdir(parents=True)
    (root / "userdata/1/config/localconfig.vdf").write_text(
        '"UserLocalConfigStore"{"Software"{"Valve"{"Steam"{"apps"{"42"{"LaunchOptions" "%s"}}}}}}\n' % launch)
    (root / "compatibilitytools.d").mkdir()
    for t in installed:
        (root / "compatibilitytools.d" / t).mkdir()
    if prefix:
        pfx = root / "steamapps/compatdata/42/pfx"
        pfx.mkdir(parents=True)
        if complete:
            (pfx / "system.reg").write_text("x")
    return root


class Tests(unittest.TestCase):
    def run_checks(self, **kw):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_steam(tmp, **kw)
            g = steam.scan_games(root)[0]
            return {r.id: r for r in gc.run_all(root, g)}

    def test_vdf(self):
        d = vdf.loads('"a" { "b" "c\\"d" "e" { "f" "g" } }')
        self.assertEqual(d["a"]["b"], 'c"d')
        self.assertEqual(vdf.get(d, "A", "E", "f"), "g")

    def test_missing_proton(self):
        self.assertEqual(self.run_checks()["proton"].status, Status.FAIL)

    def test_present_proton(self):
        self.assertEqual(self.run_checks(tool="GE-Proton10-1")["proton"].status, Status.OK)

    def test_builtin_proton_name(self):
        self.assertEqual(self.run_checks(tool="proton_experimental")["proton"].status, Status.OK)

    def test_broken_prefix_has_fix(self):
        r = self.run_checks(complete=False)["prefix"]
        self.assertEqual(r.status, Status.FAIL)
        self.assertIsNotNone(r.fix)

    def test_launch_options_flag_bad_vars(self):
        r = self.run_checks(launch="PROTON_USE_WINED3D=1 DXVK_ASYNC=1 %command%")["launch"]
        self.assertEqual(r.status, Status.WARN)
        self.assertIn("WINED3D", r.detail)

    def test_missing_command(self):
        self.assertEqual(self.run_checks(launch="MANGOHUD=1")["launch"].status, Status.FAIL)

    def test_clean_launch(self):
        self.assertEqual(self.run_checks(launch="gamemoderun %command%")["launch"].status, Status.OK)

    def test_empty_prefix_is_not_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_steam(tmp, prefix=False)
            os.makedirs(root / "steamapps/compatdata/42")
            g = steam.scan_games(root)[0]
            r = {x.id: x for x in gc.run_all(root, g)}["prefix"]
            self.assertEqual(r.status, Status.INFO)

    def test_reset_prefix_moves_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_steam(tmp, complete=False)
            g = steam.scan_games(root)[0]
            r = {x.id: x for x in gc.run_all(root, g)}["prefix"]
            msg = r.fix.run()
            self.assertIn("Moved prefix", msg)
            self.assertFalse(os.path.exists(g.prefix))


if __name__ == "__main__":
    unittest.main()
