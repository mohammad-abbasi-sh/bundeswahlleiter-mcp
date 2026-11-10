"""MCP server: unofficial read-only access to the Bundeswahlleiterin's
official Bundestag election results (open data). No key, no login.
NOTE: each election's results page links a `*_kerg2.csv` file
("Ergebnisse nach Wahlkreisen", long format, semicolon-separated);
the server discovers that link per call, then parses the CSV.
Supported years: 2017, 2021, 2025 (kerg2 exists only for these —
2013 has only the wide kerg.csv, 2009 has no English results page).
2025 carries an official Gewählt (winner) column; for 2017/2021 the
constituency winner is derived as the party with the most first
votes and labeled as such. Party names are the short names used in
kerg2 (CDU, CSU, AfD, GRÜNE, SPD, FDP, DIE LINKE/Die Linke, BSW …)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for the Bundeswahlleiterin's official \
Bundestag election results (open data, no key, no login): national \
results, one party's results nationally and by Land, one \
constituency's results, the full list of 299 constituencies with \
winner and turnout, and turnout by Land — for the 2017, 2021 and \
2025 Bundestag elections. NOTE: each call discovers the election's \
kerg2 CSV link from its results page and parses the file; 2025 \
carries an official winner column, while 2017/2021 winners are \
derived as the party with the most first votes and labeled as such. \
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir \
· https://mabbasi.ir — Germany MCP factory.\
"""

_SOURCE = "bundeswahlleiterin.de"
_DISCLAIMER = ("Unofficial read-only data from the Bundeswahlleiterin's "
               "open data (Datenlizenz Deutschland – Namensnennung – "
               "Version 2.0); verify on the site before acting on it.")


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


mcp = FastMCP("bundeswahlleiter-mcp", instructions=INSTRUCTIONS)


def _load_rows(year: int) -> tuple[list[dict], str]:
    """Fetch the year's results page, discover the kerg2 CSV, fetch
    and parse it. Returns (rows, csv_url)."""
    y = _dom.validate_year(year)
    page = _http.fetch_text(_dom.results_page_url(y))
    csv_url = _dom.find_kerg2_url(page, y)
    rows = _dom.parse_kerg2(_http.fetch_text(csv_url))
    return rows, csv_url


@mcp.tool()
def bwl_national_results(year: int = 2025) -> str:
    """National results of a Bundestag election: election date,
    eligible voters, turnout, valid votes, and per-party second
    votes (with previous-election comparison), ranked by votes.
    year: 2017, 2021 or 2025 (default 2025)."""
    try:
        rows, csv_url = _load_rows(year)
        out = _dom.national_results(rows)
    except (_http.BundeswahlleiterMcpError, ValueError) as e:
        return _err(e)
    return _ok({"year": _dom.validate_year(year), "csv_url": csv_url, **out})


@mcp.tool()
def bwl_party_results(year: int, party: str) -> str:
    """Results of one party in a Bundestag election: national second
    votes (with previous-election comparison) and second-vote share
    by Land.
    year: 2017, 2021 or 2025. party: e.g. CDU, SPD, AfD, GRÜNE, FDP,
    Die Linke, BSW."""
    try:
        rows, csv_url = _load_rows(year)
        out = _dom.party_results(rows, party)
    except (_http.BundeswahlleiterMcpError, ValueError) as e:
        return _err(e)
    return _ok({"year": _dom.validate_year(year), "csv_url": csv_url, **out})


@mcp.tool()
def bwl_constituency_results(year: int, constituency: str) -> str:
    """Results of one constituency: winner, turnout, eligible voters,
    and per-party first/second votes ranked by first votes.
    year: 2017, 2021 or 2025. constituency: number 1–299 or (part of)
    the name, e.g. 1, Flensburg, München-Süd."""
    try:
        rows, csv_url = _load_rows(year)
        out = _dom.constituency_results(rows, constituency)
    except (_http.BundeswahlleiterMcpError, ValueError) as e:
        return _err(e)
    return _ok({"year": _dom.validate_year(year), "csv_url": csv_url, **out})


@mcp.tool()
def bwl_constituencies(year: int, land: str | None = None,
                       limit: int = 50) -> str:
    """List constituencies with winner and turnout.
    year: 2017, 2021 or 2025. land: optional Land name or number
    (e.g. Bayern, 2) to filter. limit: 1..299 (default 50)."""
    try:
        lim = _dom.validate_limit(limit)
        rows, csv_url = _load_rows(year)
        items = _dom.constituencies(rows, land)
    except (_http.BundeswahlleiterMcpError, ValueError) as e:
        return _err(e)
    return _ok({"year": _dom.validate_year(year), "csv_url": csv_url,
                "land": land, "total_results": len(items),
                "count": min(lim, len(items)), "items": items[:lim]})


@mcp.tool()
def bwl_turnout(year: int = 2025) -> str:
    """Voter turnout by Land and nationally for a Bundestag election.
    year: 2017, 2021 or 2025 (default 2025)."""
    try:
        rows, csv_url = _load_rows(year)
        out = _dom.turnout(rows)
    except (_http.BundeswahlleiterMcpError, ValueError) as e:
        return _err(e)
    return _ok({"year": _dom.validate_year(year), "csv_url": csv_url, **out})


@mcp.tool()
def bwl_health() -> str:
    """Check whether bundeswahlleiterin.de is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
