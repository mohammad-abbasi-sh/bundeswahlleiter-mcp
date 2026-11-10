"""Offline tests — parse trimmed real kerg2 CSVs + real results pages,
no network."""
import json
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from bundeswahlleiter_mcp import domain as dom
from bundeswahlleiter_mcp import server as srv

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _read(name):
    return (FIX / name).read_text(encoding="utf-8")


def _rows(year):
    return dom.parse_kerg2(_read(f"kerg2-{year}.csv"))


class TestValidation(unittest.TestCase):
    def test_year(self):
        self.assertEqual(dom.validate_year(2025), 2025)
        self.assertEqual(dom.validate_year("2021"), 2021)
        for bad in (2013, 2009, 2026, 0, "abc"):
            with self.assertRaises(ValueError, msg=str(bad)):
                dom.validate_year(bad)

    def test_kerg2_url_discovery(self):
        self.assertEqual(
            dom.find_kerg2_url(_read("results-page-2025.html"), 2025),
            "https://www.bundeswahlleiterin.de/dam/jcr/"
            "f49a47a1-735b-4e9b-b4e1-4c73cad2292e/btw25_kerg2.csv")
        self.assertEqual(
            dom.find_kerg2_url(_read("results-page-2021.html"), 2021),
            "https://www.bundeswahlleiterin.de/dam/jcr/"
            "860495c9-83fb-4068-8a99-c1c985ffffd2/w-btw21_kerg2.csv")


class TestNational(unittest.TestCase):
    def test_2025(self):
        out = dom.national_results(_rows(2025))
        self.assertEqual(out["election_date"], "23.02.2025")
        self.assertEqual(out["eligible_voters"], 60510631)
        self.assertEqual(out["voters"], 49928653)
        self.assertAlmostEqual(out["turnout_percent"], 82.5122)
        self.assertEqual(len(out["parties"]), 29)
        top = out["parties"][0]
        self.assertEqual(top["party"], "CDU")
        self.assertEqual(top["second_votes"], 11196374)
        self.assertAlmostEqual(top["second_percent"], 22.550824)
        self.assertAlmostEqual(top["prev_percent"], 18.952971)
        self.assertAlmostEqual(top["diff_pp"], 3.597853)
        self.assertEqual(out["parties"][1]["party"], "AfD")
        self.assertEqual(out["parties"][2]["party"], "SPD")

    def test_2021(self):
        out = dom.national_results(_rows(2021))
        self.assertEqual(out["election_date"], "26.09.2021")
        self.assertAlmostEqual(out["turnout_percent"], 76.353159)
        self.assertEqual(out["parties"][0]["party"], "SPD")
        self.assertEqual(out["parties"][0]["second_votes"], 11901558)
        self.assertEqual(len(out["parties"]), 47)

    def test_2017_turnout_name(self):
        # 2017 calls voters 'Wähler', not 'Wählende'
        out = dom.national_results(_rows(2017))
        self.assertEqual(out["election_date"], "24.09.2017")
        self.assertAlmostEqual(out["turnout_percent"], 76.150907)
        self.assertEqual(out["parties"][0]["party"], "CDU")
        self.assertEqual(out["parties"][0]["second_votes"], 12447656)


class TestParty(unittest.TestCase):
    def test_cdu_2025(self):
        out = dom.party_results(_rows(2025), "CDU")
        self.assertEqual(out["party"], "CDU")
        self.assertEqual(out["national"]["second_votes"], 11196374)
        self.assertAlmostEqual(out["national"]["diff_pp"], 3.597853)
        self.assertEqual(len(out["by_land"]), 2)  # trimmed fixture

    def test_alias_gruene(self):
        out = dom.party_results(_rows(2025), "gruene")
        self.assertEqual(out["party"], "GRÜNE")
        self.assertEqual(out["national"]["second_votes"], 5762380)

    def test_ambiguous(self):
        with self.assertRaises(ValueError) as ctx:
            dom.party_results(_rows(2025), "Bündnis")
        self.assertIn("ambiguous", str(ctx.exception))

    def test_unknown(self):
        with self.assertRaises(ValueError) as ctx:
            dom.party_results(_rows(2025), "Piratenpartei Deutschland")
        self.assertIn("unknown party", str(ctx.exception))


class TestConstituency(unittest.TestCase):
    def test_wk001_2025_uncovered(self):
        # Flensburg 2025: CDU won the most first votes, but the
        # official Gewählt column shows '–' (winner not seated)
        out = dom.constituency_results(_rows(2025), "1")
        self.assertEqual(out["name"], "Flensburg – Schleswig")
        self.assertEqual(out["winner"], "CDU")
        self.assertIn("not allocated a seat", out["winner_how"])
        self.assertAlmostEqual(out["turnout_percent"], 83.091875)
        self.assertEqual(out["parties"][0]["party"], "CDU")
        self.assertEqual(out["parties"][0]["first_votes"], 50838)

    def test_wk001_2021_derived(self):
        out = dom.constituency_results(_rows(2021), "Flensburg")
        self.assertEqual(out["number"], "001")
        self.assertEqual(out["winner"], "GRÜNE")
        self.assertEqual(out["winner_how"], "derived (most first votes)")

    def test_wk001_2017_derived(self):
        out = dom.constituency_results(_rows(2017), "1")
        self.assertEqual(out["winner"], "CDU")

    def test_unknown_constituency(self):
        with self.assertRaises(ValueError):
            dom.constituency_results(_rows(2025), "999")
        with self.assertRaises(ValueError):
            dom.constituency_results(_rows(2025), "Xyzqwe")


class TestTurnoutAndList(unittest.TestCase):
    def test_turnout_2025(self):
        out = dom.turnout(_rows(2025))
        self.assertAlmostEqual(out["national"]["turnout_percent"], 82.5122)
        self.assertEqual(len(out["by_land"]), 2)  # trimmed fixture
        self.assertEqual(out["by_land"][0]["land"], "Schleswig-Holstein")

    def test_constituencies_trimmed(self):
        items = dom.constituencies(_rows(2025))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["number"], "001")
        self.assertEqual(items[0]["winner"], "CDU")
        self.assertEqual(items[1]["number"], "002")
        self.assertEqual(items[1]["winner"], "CDU")
        self.assertEqual(items[1]["winner_how"], "official (Gewählt column)")

    def test_constituencies_land_filter(self):
        items = dom.constituencies(_rows(2025), land="Schleswig-Holstein")
        self.assertEqual(len(items), 2)
        with self.assertRaises(ValueError):
            dom.constituencies(_rows(2025), land="Xyzqwe")


class TestServerWiring(unittest.TestCase):
    def _mock_load(self, year):
        page = _read(f"results-page-{year}.html")
        csv_text = _read(f"kerg2-{year}.csv")

        def fake_fetch(url):
            if "ergebnisse.html" in url:
                return page
            if "kerg2.csv" in url:
                return csv_text
            raise AssertionError("unexpected url: " + url)

        return mock.patch("bundeswahlleiter_mcp.server._http.fetch_text",
                          side_effect=fake_fetch)

    def test_national_uses_fixture(self):
        with self._mock_load(2025):
            out = json.loads(srv.bwl_national_results(2025))
        self.assertEqual(out["source"], "bundeswahlleiterin.de")
        self.assertAlmostEqual(out["turnout_percent"], 82.5122)
        self.assertEqual(out["parties"][0]["party"], "CDU")

    def test_constituency_uses_fixture(self):
        with self._mock_load(2025):
            out = json.loads(srv.bwl_constituency_results(2025, "1"))
        self.assertEqual(out["winner"], "CDU")
        self.assertIn("not allocated a seat", out["winner_how"])

    def test_bad_year(self):
        out = json.loads(srv.bwl_national_results(2013))
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
