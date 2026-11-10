# bundeswahlleiter-mcp 🗳️

mcp-name: io.github.mohammad-abbasi-sh/bundeswahlleiter-mcp

Inoffizieller **nur lesender** MCP-Server für **[bundeswahlleiterin.de](https://www.bundeswahlleiterin.de)** — Amtliche Bundestagswahlergebnisse von bundeswahlleiterin.de (freie offene Daten, kein Schlüssel, kein Login): Bundesergebnisse, Parteiergebnisse, Wahlkreise und Wahlbeteiligung für 2017, 2021 und 2025. Kein Schlüssel, keine Anmeldung.

> Gebaut von Mohammad Abbasi als Teil der "Germany MCP factory". Nicht mit bundeswahlleiterin.de verbunden.

## Für KI-Agenten

Zur MCP-Client-Konfiguration hinzufügen (stdio):

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

Oder lokal starten: `python -m bundeswahlleiter_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|-------------|
| `bwl_national_results` | Bundesergebnis einer Bundestagswahl |
| `bwl_party_results` | Ergebnis einer Partei, bundesweit und nach Ländern |
| `bwl_constituency_results` | Ergebnis eines Wahlkreises |
| `bwl_constituencies` | Wahlkreise mit Gewinner und Wahlbeteiligung auflisten |
| `bwl_turnout` | Wahlbeteiligung nach Ländern und bundesweit |
| `bwl_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## Lizenz

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
