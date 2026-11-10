# bundeswahlleiter-mcp 🗳️

mcp-name: io.github.mohammad-abbasi-sh/bundeswahlleiter-mcp

Unofficial **read-only** MCP server for **[bundeswahlleiterin.de](https://www.bundeswahlleiterin.de)** — Official Bundestag election results from bundeswahlleiterin.de (free open data, no key, no login): national results, party results, constituencies and turnout for 2017, 2021 and 2025. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory". Not affiliated with bundeswahlleiterin.de.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "bundeswahlleiter": {
      "command": "uvx",
      "args": ["bundeswahlleiter-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m bundeswahlleiter_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `bwl_national_results` | National results of a Bundestag election: turnout, valid votes, per-party second votes with previous-election comparison — `year` (2017, 2021 or 2025) |
| `bwl_party_results` | Results of one party in a Bundestag election, nationally and by Land — `year`, `party` (e.g. CDU, SPD, AfD, GRÜNE, FDP, Die Linke, BSW) |
| `bwl_constituency_results` | Results of one constituency: winner, turnout, per-party first/second votes — `year`, `constituency` (number 1–299 or name, e.g. 1, Flensburg) |
| `bwl_constituencies` | List all 299 constituencies with winner and turnout — `year`, `land` (optional Land name or number), `limit` 1..299 |
| `bwl_turnout` | Voter turnout by Land and nationally — `year` |
| `bwl_health` | Reachability probe (ok / blocked / error) — one polite request |

## Notes

- All data comes from **the Bundeswahlleiterin's open data** (free, no key, no login; Datenlizenz Deutschland – Namensnennung – Version 2.0).
- Each call discovers the election's `*_kerg2.csv` link from its results page and parses the long-format file (semicolon-separated, German decimal commas).
- Supported years: **2017, 2021, 2025** — kerg2 exists only for these (2013 has only the wide kerg.csv; 2009 has no English results page).
- 2017/2021 files have 18 columns (no Gewählt) and call voters "Wähler" (2021/2025: "Wählende"); party names are the short names from kerg2 (CDU, CSU, AfD, GRÜNE, SPD, FDP, DIE LINKE/Die Linke, BSW …).
- Constituency winner: 2025 reads the official Gewählt column — it names a party for 276 constituencies and shows "–" for the 23 whose direct winner was not allocated a seat under the 2025 second-vote coverage rule (there the winner is derived from the most first votes and labeled as such); 2017/2021 winners are always derived that way.

Tests: 24/24 green (19 offline + 5 live, 2026-11-10).

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
