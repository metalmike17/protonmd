import unittest

from protonmd import demo
from protonmd.model import Status


class DemoTests(unittest.TestCase):
    def test_every_demo_game_has_results(self):
        for appid, name, _ in demo.GAMES:
            res = demo._game_results(appid)
            self.assertTrue(res, name)
            self.assertTrue(all(isinstance(r.status, Status) for r in res))

    def test_demo_fixes_change_nothing(self):
        fixes = [r.fix for a, _, _ in demo.GAMES for r in demo._game_results(a) if r.fix]
        self.assertTrue(fixes)
        for f in fixes:
            self.assertIn("nothing was changed", f.run())

    def test_system_page_says_it_is_sample_data(self):
        self.assertIn("not your system", demo._system_results()[0].detail)


if __name__ == "__main__":
    unittest.main()
