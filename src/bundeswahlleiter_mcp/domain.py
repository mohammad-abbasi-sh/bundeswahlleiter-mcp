"""Domain logic: shape the Bundeswahlleiterin's kerg2 CSVs (official
Bundestag election results) into compact dicts (stdlib only).

Data source: bundeswahlleiterin.de open data — the per-election
results page (https://www.bundeswahlleiterin.de/en/bundestagswahlen/
{year}/ergebnisse.html) links the `*_kerg2.csv` file ("Ergebnisse
nach Wahlkreisen"), free, no key, no login.

kerg2 format (verified 2026-11-10 for 2017, 2021, 2025):
- long format, semicolon-separated, UTF-8 with BOM. Columns:
  Wahlart, Wahltag, Gebietsart (Bund/Land/Wahlkreis), Gebietsnummer,
  Gebietsname, UegGebietsart, UegGebietsnummer, Gruppenart
  (System-Gruppe/Partei/Einzelbewerber…), Gruppenname, Gruppen-
  reihenfolge, Stimme (''/1 Erststimme/2 Zweitstimme), Anzahl,
  Prozent, VorpAnzahl, VorpProzent, DiffProzent, DiffProzentPkt,
  Bemerkung, Gewählt (2025 only).
- 2017/2021 have 18 columns (no Gewählt) and call voters 'Wähler'
  (2021/2025: 'Wählende'). Party names are short names (CDU, CSU,
  AfD, GRÜNE, SPD, FDP, DIE LINKE/Die Linke, BSW …).
- Numbers use German decimal commas (82,5122); counts have no
  thousands separators.
- Constituency winner: 2025 reads the official Gewählt column;
  it names a party for 276 constituencies and shows '–' for the 23
  whose direct winner was not allocated a seat under the 2025
  second-vote coverage rule — there (and for all of 2017/2021, which
  have no Gewählt column) the winner is derived as the party with
  the most first votes and labeled as such.
- Supported years: 2017, 2021, 2025 (kerg2 exists only for these;
  2013 has only the wide kerg.csv, 2009 has no English results page).
"""
from __future__ import annotations

import csv
import io
import re
from urllib.parse import urljoin

BASE = "https://www.bundeswahlleiterin.de"
SUPPORTED_YEARS = (2017, 2021, 2025)
TURNOUT_NAMES = ("Wählende", "Wähler")

# common spellings -> the short name used in kerg2 (case-insensitive;
# the matcher also tries exact + substring on the year's party list)
PARTY_ALIASES = {
    "gruene": "GRÜNE",
    "grüne": "GRÜNE",
    "die grünen": "GRÜNE",
    "linke": "DIE LINKE",
    "die linke": "DIE LINKE",
    "freie wähler": "FREIE WÄHLER",
    "freie waehler": "FREIE WÄHLER",
    "die partei": "Die PARTEI",
    "tierschutzpartei": "Tierschutzpartei",
    "piraten": "PIRATEN",
    "volt": "Volt",
    "ssw": "SSW",
    "bsw": "BSW",
    "afd": "AfD",
    "cdu": "CDU",
    "csu": "CSU",
    "spd": "SPD",
    "fdp": "FDP",
}


def validate_year(year: int) -> int:
    try:
        y = int(year)
    except (TypeError, ValueError):
        raise ValueError(f"year must be one of {list(SUPPORTED_YEARS)}") from None
    if y not in SUPPORTED_YEARS:
        raise ValueError(
            f"unsupported year: {year} "
            f"(kerg2 open data exists for {list(SUPPORTED_YEARS)} only)")
    return y


def validate_limit(limit: int, maximum: int = 299) -> int:
    if not 1 <= limit <= maximum:
        raise ValueError(
            f"limit out of range: {limit} (expected 1..{maximum})")
    return limit


def results_page_url(year: int) -> str:
    return (f"{BASE}/en/bundestagswahlen/{year}/ergebnisse.html")


def find_kerg2_url(page_html: str, year: int) -> str:
    """The *_kerg2.csv link on the year's results page (relative)."""
    m = re.search(r'href="([^"]*kerg2\.csv[^"]*)"', page_html, re.I)
    if not m:
        raise ValueError(
            f"no kerg2 CSV found on the {year} results page "
            "(the open-data link may have moved)")
    # DAM links are root-relative in effect (../../dam/...); resolve
    # against the site root for the canonical URL (both /dam/... and
    # /en/dam/... answer 200, the former is canonical).
    return urljoin(BASE + "/", m.group(1))


def _num(text: str) -> float | None:
    """German number ('82,5122' / '60510631' / '') -> float or None."""
    t = (text or "").strip()
    if not t:
        return None
    try:
        return float(t.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _int(text: str) -> int | None:
    v = _num(text)
    return int(v) if v is not None else None


def parse_kerg2(csv_text: str) -> list[dict]:
    """Rows as dicts with normalized fields. Header row is found by
    the 'Wahlart;' prefix; column positions come from the header, so
    the 18-column (2017/2021) and 19-column (2025) variants both
    parse (Gewählt is '' when the column is absent)."""
    text = csv_text.lstrip("\ufeff")
    lines = text.splitlines()
    hi = next((i for i, ln in enumerate(lines)
               if ln.startswith("Wahlart;")), None)
    if hi is None:
        raise ValueError("not a kerg2 file: no Wahlart header row found")
    reader = csv.reader(io.StringIO("\n".join(lines[hi:])),
                        delimiter=";")
    header = next(reader)
    idx = {name: i for i, name in enumerate(header)}
    out = []
    for r in reader:
        if not r or not any(c.strip() for c in r):
            continue

        def col(name: str) -> str:
            i = idx.get(name)
            return r[i] if i is not None and i < len(r) else ""

        out.append({
            "wahlart": col("Wahlart"),
            "wahltag": col("Wahltag"),
            "gebietsart": col("Gebietsart"),
            "gebietsnummer": col("Gebietsnummer"),
            "gebietsname": col("Gebietsname"),
            "ueg_gebietsnummer": col("UegGebietsnummer"),
            "gruppenart": col("Gruppenart"),
            "gruppenname": col("Gruppenname"),
            "stimme": col("Stimme"),
            "anzahl": _int(col("Anzahl")),
            "prozent": _num(col("Prozent")),
            "vorp_anzahl": _int(col("VorpAnzahl")),
            "vorp_prozent": _num(col("VorpProzent")),
            "diff_prozentpkt": _num(col("DiffProzentPkt")),
            "gewaehlt": col("Gewählt"),
        })
    if not out:
        raise ValueError("kerg2 file has no data rows")
    return out


def _bund(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["gebietsart"] == "Bund"]


def _system(rows: list[dict], name: str) -> dict | None:
    for r in rows:
        if r["gruppenart"] == "System-Gruppe" and r["gruppenname"] == name:
            return r
    return None


def _turnout_row(rows: list[dict]) -> dict | None:
    for name in TURNOUT_NAMES:
        r = _system(rows, name)
        if r is not None:
            return r
    return None


def party_names(rows: list[dict]) -> list[str]:
    """Short party names present in these rows (Gruppenart=Partei),
    in first-seen order."""
    out: list[str] = []
    for r in rows:
        if r["gruppenart"] == "Partei" and r["gruppenname"] not in out:
            out.append(r["gruppenname"])
    return out


def match_party(rows: list[dict], query: str) -> str:
    """Resolve a party query to the year's canonical short name.
    Exact (case-insensitive) first, then alias map, then a unique
    substring match; ambiguous or unknown -> ValueError listing the
    year's parties."""
    q = (query or "").strip()
    if not q:
        raise ValueError("party must not be empty")
    parties = party_names(rows)
    qf = q.casefold()
    for p in parties:
        if p.casefold() == qf:
            return p
    if qf in PARTY_ALIASES:
        cand = PARTY_ALIASES[qf]
        for p in parties:
            if p.casefold() == cand.casefold():
                return p
    hits = [p for p in parties if qf in p.casefold()]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        raise ValueError(
            f"ambiguous party {query!r}: matches {hits} — be more specific")
    raise ValueError(
        f"unknown party {query!r} for this election "
        f"(parties: {', '.join(parties)})")


def _party_votes(rows: list[dict], party: str, stimme: str) -> dict | None:
    for r in rows:
        if (r["gruppenart"] == "Partei" and r["gruppenname"] == party
                and r["stimme"] == stimme):
            return r
    return None


def national_results(rows: list[dict]) -> dict:
    """{election_date, eligible_voters, voters, turnout_percent,
    valid_first, valid_second, parties: [{party, second_votes,
    second_percent, prev_percent, diff_pp, first_votes}]}."""
    bund = _bund(rows)
    date = bund[0]["wahltag"] if bund else ""
    elig = _system(bund, "Wahlberechtigte")
    turnout = _turnout_row(bund)
    valid1 = _system(bund, "Gültige")
    valid_first = valid1["anzahl"] if valid1 and valid1["stimme"] == "1" else None
    valid_second = None
    for r in bund:
        if (r["gruppenart"] == "System-Gruppe"
                and r["gruppenname"] == "Gültige" and r["stimme"] == "2"):
            valid_second = r["anzahl"]
    parties = []
    for p in party_names(bund):
        second = _party_votes(bund, p, "2")
        first = _party_votes(bund, p, "1")
        parties.append({
            "party": p,
            "second_votes": second["anzahl"] if second else None,
            "second_percent": second["prozent"] if second else None,
            "prev_percent": second["vorp_prozent"] if second else None,
            "diff_pp": second["diff_prozentpkt"] if second else None,
            "first_votes": first["anzahl"] if first else None,
        })
    parties.sort(key=lambda x: (x["second_votes"] is None,
                                -(x["second_votes"] or 0)))
    return {
        "election_date": date,
        "eligible_voters": elig["anzahl"] if elig else None,
        "voters": turnout["anzahl"] if turnout else None,
        "turnout_percent": turnout["prozent"] if turnout else None,
        "valid_first_votes": valid_first,
        "valid_second_votes": valid_second,
        "parties": parties,
    }


def party_results(rows: list[dict], party: str) -> dict:
    """{party, national: {second_votes, second_percent, prev_percent,
    diff_pp, first_votes}, by_land: [{land, land_number,
    second_votes, second_percent}]}."""
    canonical = match_party(rows, party)
    bund = _bund(rows)
    second = _party_votes(bund, canonical, "2")
    first = _party_votes(bund, canonical, "1")
    by_land = []
    lands = {}
    for r in rows:
        if r["gebietsart"] == "Land" and r["gebietsnummer"] not in lands:
            lands[r["gebietsnummer"]] = r["gebietsname"]
    for num in sorted(lands):
        land_rows = [r for r in rows
                     if r["gebietsart"] == "Land"
                     and r["gebietsnummer"] == num]
        s = _party_votes(land_rows, canonical, "2")
        by_land.append({
            "land": lands[num],
            "land_number": num,
            "second_votes": s["anzahl"] if s else None,
            "second_percent": s["prozent"] if s else None,
        })
    return {
        "party": canonical,
        "national": {
            "second_votes": second["anzahl"] if second else None,
            "second_percent": second["prozent"] if second else None,
            "prev_percent": second["vorp_prozent"] if second else None,
            "diff_pp": second["diff_prozentpkt"] if second else None,
            "first_votes": first["anzahl"] if first else None,
        },
        "by_land": by_land,
    }


def _winner(rows: list[dict]) -> tuple[str, str]:
    """(winner, how) — the official Gewählt column when it names a
    party (2025). In 2025 the column shows '–' for 23 constituencies
    whose direct winner was NOT allocated a seat under the
    second-vote coverage rule — there the winner is the party with
    the most first votes, labeled as such. 2017/2021 have no Gewählt
    column at all, so the winner is always derived that way."""
    official = sorted(set(r["gewaehlt"] for r in rows
                          if r["gewaehlt"] and r["gewaehlt"] != "–"))
    if official:
        return official[0], "official (Gewählt column)"
    best: dict | None = None
    for r in rows:
        if r["gruppenart"] == "Partei" and r["stimme"] == "1":
            if best is None or (r["anzahl"] or 0) > (best["anzahl"] or 0):
                best = r
    if best is None:
        return "", "unknown (no first-vote rows)"
    if any(r["gewaehlt"] == "–" for r in rows):
        return (best["gruppenname"],
                "derived (most first votes; official Gewählt column "
                "shows '–' — the direct winner was not allocated a "
                "seat under the 2025 second-vote coverage rule)")
    return best["gruppenname"], "derived (most first votes)"


def constituency_results(rows: list[dict],
                         constituency: str) -> dict:
    """{number, name, land, land_number, winner, winner_how, voters,
    turnout_percent, eligible_voters, parties: [{party, first_votes,
    first_percent, second_votes, second_percent}]}."""
    q = (constituency or "").strip()
    if not q:
        raise ValueError("constituency must not be empty")
    wks = {}
    for r in rows:
        if r["gebietsart"] == "Wahlkreis":
            wks.setdefault(r["gebietsnummer"], r["gebietsname"])
    number = None
    if q.isdigit():
        number = f"{int(q):03d}"
        if number not in wks:
            raise ValueError(
                f"no constituency number {q} (1–299) in this election")
    else:
        qf = q.casefold()
        hits = [(n, name) for n, name in wks.items()
                if qf in name.casefold()]
        if len(hits) == 1:
            number = hits[0][0]
        elif len(hits) > 1:
            raise ValueError(
                f"ambiguous constituency {constituency!r}: matches "
                f"{[f'{n} {name}' for n, name in hits]} — be more specific")
        else:
            raise ValueError(
                f"unknown constituency {constituency!r} "
                "(try a number 1–299 or a fuller name)")
    wk_rows = [r for r in rows
               if r["gebietsart"] == "Wahlkreis"
               and r["gebietsnummer"] == number]
    winner, how = _winner(wk_rows)
    turnout = _turnout_row(wk_rows)
    elig = _system(wk_rows, "Wahlberechtigte")
    lands = {r["gebietsnummer"]: r["gebietsname"] for r in rows
             if r["gebietsart"] == "Land"}
    land_num = wk_rows[0]["ueg_gebietsnummer"] if wk_rows else ""
    parties = []
    for p in party_names(wk_rows):
        first = _party_votes(wk_rows, p, "1")
        second = _party_votes(wk_rows, p, "2")
        parties.append({
            "party": p,
            "first_votes": first["anzahl"] if first else None,
            "first_percent": first["prozent"] if first else None,
            "second_votes": second["anzahl"] if second else None,
            "second_percent": second["prozent"] if second else None,
        })
    parties.sort(key=lambda x: (x["first_votes"] is None,
                                -(x["first_votes"] or 0)))
    return {
        "number": number,
        "name": wks[number],
        "land": lands.get(land_num, ""),
        "land_number": land_num,
        "winner": winner,
        "winner_how": how,
        "eligible_voters": elig["anzahl"] if elig else None,
        "voters": turnout["anzahl"] if turnout else None,
        "turnout_percent": turnout["prozent"] if turnout else None,
        "parties": parties,
    }


def constituencies(rows: list[dict], land: str | None = None) -> list[dict]:
    """[{number, name, land, land_number, winner, winner_how,
    turnout_percent}] — all 299, optionally filtered by Land name
    or number."""
    lands = {r["gebietsnummer"]: r["gebietsname"] for r in rows
             if r["gebietsart"] == "Land"}
    land_num = None
    if land:
        q = land.strip()
        if q.isdigit():
            land_num = f"{int(q):02d}"
            if land_num not in lands:
                raise ValueError(f"unknown Land number {q} (1–16)")
        else:
            qf = q.casefold()
            hits = [(n, name) for n, name in lands.items()
                    if qf in name.casefold()]
            if len(hits) == 1:
                land_num = hits[0][0]
            elif len(hits) > 1:
                raise ValueError(
                    f"ambiguous Land {land!r}: matches "
                    f"{[name for _n, name in hits]}")
            else:
                raise ValueError(f"unknown Land {land!r}")
    wks: dict[str, dict] = {}
    for r in rows:
        if r["gebietsart"] != "Wahlkreis":
            continue
        num = r["gebietsnummer"]
        if land_num and r["ueg_gebietsnummer"] != land_num:
            continue
        wks.setdefault(num, {"rows": [], "name": r["gebietsname"],
                             "land_number": r["ueg_gebietsnummer"]})
        wks[num]["rows"].append(r)
    out = []
    for num in sorted(wks):
        info = wks[num]
        winner, how = _winner(info["rows"])
        turnout = _turnout_row(info["rows"])
        out.append({
            "number": num,
            "name": info["name"],
            "land": lands.get(info["land_number"], ""),
            "land_number": info["land_number"],
            "winner": winner,
            "winner_how": how,
            "turnout_percent": turnout["prozent"] if turnout else None,
        })
    return out


def turnout(rows: list[dict]) -> dict:
    """{national: {voters, turnout_percent, eligible_voters},
    by_land: [{land, land_number, voters, turnout_percent,
    eligible_voters}]}."""
    bund = _bund(rows)
    t = _turnout_row(bund)
    elig = _system(bund, "Wahlberechtigte")
    lands = {r["gebietsnummer"]: r["gebietsname"] for r in rows
             if r["gebietsart"] == "Land"}
    by_land = []
    for num in sorted(lands):
        land_rows = [r for r in rows
                     if r["gebietsart"] == "Land"
                     and r["gebietsnummer"] == num]
        lt = _turnout_row(land_rows)
        le = _system(land_rows, "Wahlberechtigte")
        by_land.append({
            "land": lands[num],
            "land_number": num,
            "voters": lt["anzahl"] if lt else None,
            "turnout_percent": lt["prozent"] if lt else None,
            "eligible_voters": le["anzahl"] if le else None,
        })
    return {
        "national": {
            "voters": t["anzahl"] if t else None,
            "turnout_percent": t["prozent"] if t else None,
            "eligible_voters": elig["anzahl"] if elig else None,
        },
        "by_land": by_land,
    }
