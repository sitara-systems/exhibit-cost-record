#!/usr/bin/env python3
"""Generate one page per recipient (firm) from the normalized records.

D5 decision (2026-08-27, made in-session): firm-centric, not
institution-centric. The `client` field in the source data is dominated
by large federal awarding agencies -- Department of the Interior (482
records), Smithsonian Institution (257), Institute of Museum and Library
Services (203), Department of Defense (200) -- only 89 unique clients
total, most of them department-level buckets rather than individual
museums. That doesn't match a real "[museum] exhibit cost" query.
`recipient` (559 unique firms -- Capitol Exhibit Services, Color-Ad,
Electrosonic, ExPlus, Ideum, and so on) is the dataset's real facet axis:
named, specific businesses a real buyer, journalist, or competitor would
search for by name, mirroring the Experiential Design Index's own
firm-page pattern. See PLAN.md T7 / D5 and the dated addendum in
Public_Cost_Baseline_Plan.md for the full reasoning and the Search
Console evidence that motivated this task.

Imported by build.py. Also runnable standalone for a dry-run page/URL
count without touching _site/.
"""
from __future__ import annotations

import html
import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_data  # noqa: E402


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[,.]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "firm"


def choose_display_name(variant_counts: dict[str, int]) -> str:
    """Pick one display name for a group of same-firm name variants (the
    source CSVs are not casing/punctuation-normalized -- e.g. "Cinnabar
    California, Inc." / "CINNABAR CALIFORNIA INC." / "CINNABAR CALIFORNIA,
    INC." all slugify to cinnabar-california-inc and must merge into one
    page, or that firm's award history gets split across 2-3 thin pages,
    undercutting the whole point of a firm-level page). Prefer the variant
    used on the most records; tie-break toward not-ALL-CAPS, then longer
    (more likely to carry a suffix like ", Inc."), then alphabetical for
    stability."""
    def key(name: str):
        return (-variant_counts[name], name.isupper(), -len(name), name)
    return sorted(variant_counts, key=key)[0]


def _esc(v) -> str:
    return html.escape(str(v)) if v not in (None, "") else export_data.DASH


def _record_key(r: dict):
    return (r.get("year") or "", r.get("client") or "")


def build_pages(records: list[dict]) -> list[dict]:
    # Group by slug, not by raw recipient string -- the source CSVs carry
    # inconsistent casing/punctuation for the same firm (see
    # choose_display_name's docstring), and grouping by raw string would
    # split one firm's history across multiple thin pages.
    by_slug: dict[str, list[dict]] = defaultdict(list)
    variant_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in records:
        slug = slugify(r["recipient"])
        by_slug[slug].append(r)
        variant_counts[slug][r["recipient"]] += 1

    display_names = {slug: choose_display_name(vc) for slug, vc in variant_counts.items()}
    pages: list[dict] = []

    for slug, recs in by_slug.items():
        name = display_names[slug]
        n = len(recs)
        usd_amounts = [r["amount"] for r in recs if r["amount"] and r["currency"] == "USD"]
        total_usd = sum(usd_amounts) if usd_amounts else None
        clients = sorted({r["client"] for r in recs if r.get("client")})
        years = sorted({r["year"] for r in recs if r.get("year")})
        year_span = f"{years[0]}\u2013{years[-1]}" if len(years) > 1 else (years[0] if years else None)

        subtotal_line = f"${round(total_usd):,}" if total_usd else None

        desc_bits = [f"{n} public award record{'s' if n != 1 else ''}"]
        if subtotal_line:
            desc_bits.append(f"{subtotal_line} total")
        if year_span:
            desc_bits.append(str(year_span))
        description = html.escape(
            f"{name}: " + ", ".join(desc_bits) +
            ". Exhibit contract and grant data, each row linked to its public source."
        )[:300]

        rows_html = export_data.render_rows(sorted(recs, key=_record_key))

        client_items = "".join(f"<li>{_esc(c)}</li>" for c in clients[:12])
        if len(clients) > 12:
            client_items += f"<li>&hellip; and {len(clients) - 12} more</li>"

        subtitle_parts = [f"{n} record{'s' if n != 1 else ''}"]
        if subtotal_line:
            subtitle_parts.append(f"{subtotal_line} across USD-denominated rows")
        if year_span:
            subtitle_parts.append(str(year_span))
        subtitle = " &middot; ".join(subtitle_parts)

        browse_query = urllib.parse.quote(name)
        esc_name = _esc(name)

        content = f"""<div class="breadcrumbs"><a href="/">Home</a> &gt; <a href="/firms/">Firms</a> &gt; {esc_name}</div>
<h1>{esc_name}</h1>
<p class="subtitle">{subtitle}</p>
<p class="note">Every row below traces to a public source &mdash; a federal
contract, federal or state grant, state procurement record, UK tender, or
IRS Form 990 disclosure. This page is descriptive, not price advice: it
reports what was awarded, not what any project should cost. Column
definitions are on the <a href="/methodology/">methodology page</a>.</p>
<h2>Clients / awarding agencies</h2>
<ul>{client_items}</ul>
<h2>Records ({n})</h2>
<table class="list">
  <thead>
    <tr><th>Source</th><th>Recipient</th><th>Client / agency</th><th>Year</th><th>Class</th><th>Competition</th><th>Description</th><th>Amount</th><th>Source</th></tr>
  </thead>
  <tbody>
{rows_html}
  </tbody>
</table>
<p class="note"><a href="/browse/?q={browse_query}">See these rows highlighted in the full browse table &rarr;</a></p>
"""
        pages.append({
            "title": html.escape(f"{name} \u2014 The Exhibit Cost Record"),
            "description": description,
            "url": f"/firms/{slug}/",
            "content": content,
        })

    index_items = "\n".join(
        f'<li><a href="/firms/{slug}/">{_esc(display_names[slug])}</a> '
        f'<span class="note">({len(recs)} record{"s" if len(recs) != 1 else ""})</span></li>'
        for slug, recs in sorted(by_slug.items(), key=lambda kv: display_names[kv[0]])
    )
    pages.append({
        "title": "Firms \u2014 The Exhibit Cost Record",
        "description": html.escape(
            f"All {len(by_slug)} firms named in The Exhibit Cost Record's "
            f"{len(records)} records, alphabetically, with each firm's record count."
        ),
        "url": "/firms/",
        "content": f"""<div class="breadcrumbs"><a href="/">Home</a> &gt; Firms</div>
<h1>Firms</h1>
<p class="subtitle">{len(by_slug)} firms &middot; {len(records)} total records.</p>
<p class="note">Every firm named anywhere in the dataset &mdash; as the
recipient of a federal contract or grant, a state contract, a UK tender,
or an IRS Form 990 contractor disclosure. Not every firm here works in
museum exhibits exclusively; see each firm's page for its actual record
set.</p>
<ul class="firm-index">
{index_items}
</ul>
""",
    })
    return pages


def main() -> None:
    records = export_data.normalize()
    pages = build_pages(records)
    firm_pages = [p for p in pages if p["url"] != "/firms/"]
    n_recipients = len({r["recipient"] for r in records})
    print(f"{len(firm_pages)} firm pages + 1 index page from {len(records)} records "
          f"({n_recipients} unique recipients)")


if __name__ == "__main__":
    main()
