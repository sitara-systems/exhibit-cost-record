#!/usr/bin/env python3
"""Normalize the five source CSVs into one browsable/searchable JSON array
plus a small stats summary, written into assets/data/ at build time.

Run standalone (python scripts/export_data.py) or imported by build.py.
Never edits the source CSVs in ../data/ — read-only.
"""
from __future__ import annotations

import csv
import html
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT.parent / "data"
OUT_DIR = ROOT / "assets" / "data"


def read_csv(name: str) -> list[dict]:
    path = DATA_DIR / name
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_amount(v: str | None) -> float | None:
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def normalize() -> list[dict]:
    records = []

    for r in read_csv("awards_federal.csv"):
        records.append({
            "source": "federal", "source_label": "Federal contract (USAspending)",
            "recipient": r["recipient"], "client": r["awarding_agency"],
            "sub_client": r.get("sub_agency") or None,
            "year": r.get("start_year") or None,
            "amount": to_amount(r.get("obligated_amount")),
            "amount_ceiling": to_amount(r.get("total_award_value")),
            "currency": "USD",
            "description": r.get("award_description") or "",
            "project_class": r.get("project_class") or None,
            "fabrication_inclusive": r.get("fabrication_inclusive") or None,
            "scope_confidence": r.get("scope_confidence") or None,
            "source_url": r.get("source_url") or None,
            "notes": r.get("notes") or None,
        })

    for r in read_csv("awards_grants.csv"):
        records.append({
            "source": "grant", "source_label": "Federal grant (NSF/IMLS)",
            "recipient": r["recipient"], "client": r["awarding_agency"],
            "sub_client": r.get("grant_program") or None,
            "year": r.get("start_year") or None,
            "amount": to_amount(r.get("obligated_amount")),
            "amount_ceiling": to_amount(r.get("total_award_value")),
            "currency": "USD",
            "description": r.get("award_description") or "",
            "project_class": r.get("project_class") or None,
            "fabrication_inclusive": r.get("fabrication_inclusive") or None,
            "scope_confidence": r.get("scope_confidence") or None,
            "source_url": r.get("source_url") or None,
            "notes": r.get("notes") or None,
        })

    for r in read_csv("awards_state.csv"):
        records.append({
            "source": "state", "source_label": f"State contract ({r.get('state', '?')})",
            "recipient": r["recipient"], "client": r["awarding_agency"],
            "sub_client": r.get("sub_agency") or None,
            "year": r.get("start_year") or None,
            "amount": to_amount(r.get("obligated_amount")),
            "amount_ceiling": to_amount(r.get("total_award_value")),
            "currency": "USD",
            "description": r.get("award_description") or "",
            "project_class": r.get("project_class") or None,
            "fabrication_inclusive": r.get("fabrication_inclusive") or None,
            "scope_confidence": r.get("scope_confidence") or None,
            "source_url": r.get("source_url") or None,
            "notes": r.get("notes") or None,
            "state": r.get("state") or None,
        })

    for r in read_csv("awards_uk.csv"):
        records.append({
            "source": "uk", "source_label": "UK tender (non-US comparable)",
            "recipient": r["recipient"], "client": r["awarding_agency"],
            "sub_client": r.get("sub_agency") or None,
            "year": r.get("start_year") or None,
            "amount": to_amount(r.get("obligated_amount")),
            "amount_ceiling": to_amount(r.get("total_award_value")),
            "currency": r.get("currency") or "GBP",
            "description": r.get("award_description") or "",
            "project_class": r.get("project_class") or None,
            "fabrication_inclusive": r.get("fabrication_inclusive") or None,
            "scope_confidence": r.get("scope_confidence") or None,
            "source_url": r.get("source_url") or None,
            "notes": r.get("notes") or None,
        })

    for r in read_csv("contractors_990.csv"):
        records.append({
            "source": "990", "source_label": "IRS Form 990 contractor disclosure",
            "recipient": r["contractor_name"], "client": r["museum"],
            "sub_client": None,
            "year": r.get("tax_year") or None,
            "amount": to_amount(r.get("compensation")),
            "amount_ceiling": None,
            "currency": "USD",
            "description": r.get("services_description") or "",
            "project_class": None,
            "fabrication_inclusive": None,
            "scope_confidence": None,
            "source_url": r.get("source_url") or None,
            "notes": None,
            "ein": r.get("ein") or None,
        })

    for i, r in enumerate(records):
        r["id"] = i

    return records


def stats(records: list[dict]) -> dict:
    by_source = Counter(r["source"] for r in records)
    by_class = Counter(r["project_class"] for r in records if r["project_class"])
    amounts_by_class = defaultdict(list)
    for r in records:
        if r["project_class"] and r["amount"] and r["currency"] == "USD":
            amounts_by_class[r["project_class"]].append(r["amount"])

    def median(vals):
        s = sorted(vals)
        n = len(s)
        if n == 0:
            return None
        mid = n // 2
        return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2

    class_stats = {
        cls: {"n": len(vals), "median": median(vals), "min": min(vals), "max": max(vals)}
        for cls, vals in amounts_by_class.items()
    }

    fab_y = [r["amount"] for r in records
             if r.get("fabrication_inclusive") == "y" and r["amount"] and r["currency"] == "USD"
             and r["project_class"] not in (None, "other")]
    fab_n = [r["amount"] for r in records
             if r.get("fabrication_inclusive") == "n" and r["amount"] and r["currency"] == "USD"
             and r["project_class"] not in (None, "other")]

    return {
        "total_records": len(records),
        "by_source": dict(by_source),
        "by_class": dict(by_class),
        "class_stats": class_stats,
        "fabrication_inclusive_median": median(fab_y),
        "fabrication_excluded_median": median(fab_n),
    }


SOURCE_LABELS = {"federal": "Federal", "grant": "Grant", "state": "State", "uk": "UK", "990": "990"}


DASH = "—"  # em dash, used as a literal display character (not an
                 # HTML entity) so it can safely pass through html.escape()
                 # without double-escaping.


def _esc(v) -> str:
    return html.escape(str(v)) if v not in (None, "") else DASH


def fmt_amount(amount, currency) -> str:
    if amount is None:
        return DASH
    symbol = "£" if currency == "GBP" else "$"
    return f"{symbol}{round(amount):,}"


def render_rows(records: list[dict]) -> str:
    """Server-render every record as a <tr> for table.list, with data-*
    attributes for filter.js's progressive-enhancement filtering. All rows
    ship in the HTML (not fetched via JS) so crawlers and no-JS visitors see
    the complete table, same as the Experiential Design Index's browse
    pages."""
    rows = []
    for r in records:
        search_blob = html.escape(
            f"{r['recipient']} {r['client']} {r['description']} {r.get('sub_client') or ''}"
        ).lower()
        cls = r.get("project_class") or ""
        rows.append(
            "    <tr data-source=\"{source}\" data-class=\"{cls}\" data-search=\"{search}\">"
            "<td><span class=\"src-tag\">{source_label}</span></td>"
            "<td>{recipient}</td>"
            "<td>{client}</td>"
            "<td>{year}</td>"
            "<td>{cls_label}</td>"
            "<td class=\"desc\">{description}</td>"
            "<td class=\"amount\">{amount}</td>"
            "<td>{source_link}</td>"
            "</tr>".format(
                source=html.escape(r["source"]),
                cls=html.escape(cls),
                search=search_blob,
                source_label=html.escape(SOURCE_LABELS.get(r["source"], r["source"])),
                recipient=_esc(r["recipient"]),
                client=_esc(r["client"]),
                year=_esc(r["year"]),
                cls_label=_esc(cls.replace("_", " ")) if cls else DASH,
                description=_esc(r["description"]),
                amount=fmt_amount(r["amount"], r["currency"]),
                source_link=(f'<a href="{html.escape(r["source_url"])}" target="_blank" rel="noopener">source</a>'
                             if r.get("source_url") else DASH),
            )
        )
    return "\n".join(rows)


def render_class_options(records: list[dict]) -> str:
    classes = sorted({r["project_class"] for r in records if r["project_class"]})
    return "\n".join(
        f'      <option value="{_esc(c)}">{_esc(c.replace("_", " "))}</option>' for c in classes
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = normalize()
    (OUT_DIR / "records.json").write_text(
        json.dumps(records, separators=(",", ":")), encoding="utf-8")
    s = stats(records)
    (OUT_DIR / "stats.json").write_text(
        json.dumps(s, indent=1), encoding="utf-8")
    print(f"exported {len(records)} records -> {OUT_DIR / 'records.json'}")
    print(f"stats -> {OUT_DIR / 'stats.json'}")
    print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
