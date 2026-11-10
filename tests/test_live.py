"""Live tests — hit the real bundeswahlleiterin.de results pages +
kerg2 CSVs. Cautious: each tool call downloads a ~2MB CSV.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set BWL_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from bundeswahlleiter_mcp import server as srv

pytestmark = pytest.mark.live
SKIP = os.environ.get("BWL_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="BWL_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_national_live(self):
        out = json.loads(srv.bwl_national_results(2025))
        self.assertNotIn("error", out)
        self.assertEqual(out["election_date"], "23.02.2025")
        self.assertAlmostEqual(out["turnout_percent"], 82.5122, places=3)
        self.assertEqual(out["parties"][0]["party"], "CDU")
        self.assertAlmostEqual(out["parties"][0]["second_percent"],
                               22.550824, places=3)
        print(f"\nLIVE national 2025: turnout {out['turnout_percent']}% — "
              f"CDU {out['parties'][0]['second_percent']}%")

    def test_party_live(self):
        out = json.loads(srv.bwl_party_results(2025, "AfD"))
        self.assertNotIn("error", out)
        self.assertEqual(out["party"], "AfD")
        self.assertAlmostEqual(out["national"]["second_percent"],
                               20.803387, places=3)
        self.assertEqual(len(out["by_land"]), 16)

    def test_constituency_live(self):
        out = json.loads(srv.bwl_constituency_results(2025, "1"))
        self.assertNotIn("error", out)
        self.assertEqual(out["winner"], "CDU")
        self.assertIn("not allocated a seat", out["winner_how"])

    def test_constituencies_live(self):
        out = json.loads(srv.bwl_constituencies(2025, limit=3))
        self.assertNotIn("error", out)
        self.assertEqual(out["total_results"], 299)
        self.assertEqual(len(out["items"]), 3)

    def test_turnout_2021_live(self):
        out = json.loads(srv.bwl_turnout(2021))
        self.assertNotIn("error", out)
        self.assertAlmostEqual(out["national"]["turnout_percent"],
                               76.353159, places=3)
        self.assertEqual(len(out["by_land"]), 16)
