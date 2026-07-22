#!/usr/bin/env python3
"""Static site build for The Exhibit Cost Record.

Same content-fragment + YAML front matter -> Jinja2 base -> static output
pattern used by sitara-website and the Experiential Design Index. This
site has its own visual identity — a neutral public-data resource, not
Sitara's own brand chrome.

Content model
-------------
content/pages/<slug>.html, each:

    ---
    title: Page Title | The Exhibit Cost Record
    description: meta description
    url: /slug/            # output path; "/" for the home page
    ---
    <main>...</main>

Data: scripts/export_data.py normalizes data/*.csv (one level up, in the
dataset repo root) into assets/data/records.json + stats.json, which the
/browse/ page's client-side JS reads directly. Run automatically as part
of build().

Usage: python build.py [--out DIR]
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
import export_data  # noqa: E402

ROOT = Path(__file__).resolve().parent

# Deployed as a sibling section to the Experiential Design Index, both under
# sitara.systems -- NOT folded into the index itself (that would blur its
# credits-neutral editorial surface against this dataset's
# price-descriptive one).
# SITE_URL is the single knob, same pattern as the index's build_site.py:
# change it at deploy time (or override via the SITE_URL env var) and every
# internal link/asset reference derives from it, so the site works
# regardless of whether it's served at the domain root or a subdirectory.
SITE_URL = os.environ.get("SITE_URL", "https://sitara.systems/exhibit-cost-record")
BASE = urllib.parse.urlsplit(SITE_URL).path.rstrip("/")

PAGES_DIR = ROOT / "content" / "pages"
TEMPLATES_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"
DEFAULT_OUT = ROOT / "_site"


def parse_page(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path.name}: missing front matter")
    _, fm, body = text.split("---", 2)
    meta = yaml.safe_load(fm)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    meta["content"] = body.strip("\n")
    meta.setdefault("url", f"/{path.stem}/")
    for key in ("title", "description"):
        if not meta.get(key):
            raise ValueError(f"{path.name}: front matter missing '{key}'")
    return meta


def out_path(out_dir: Path, url: str) -> Path:
    if url == "/":
        return out_dir / "index.html"
    if url == "/404/":
        return out_dir / "404.html"
    return out_dir / url.strip("/") / "index.html"


def build(out_dir: Path) -> list[dict]:
    # regenerate the browse dataset from the source CSVs every build so the
    # site never drifts from data/*.csv
    records = export_data.normalize()
    export_data.OUT_DIR.mkdir(parents=True, exist_ok=True)
    import json
    (export_data.OUT_DIR / "records.json").write_text(
        json.dumps(records, separators=(",", ":")), encoding="utf-8")
    stats = export_data.stats(records)
    (export_data.OUT_DIR / "stats.json").write_text(
        json.dumps(stats, indent=1), encoding="utf-8")

    # browse.html is server-rendered with every record as a table row (same
    # technique as the Experiential Design Index's browse pages) so crawlers
    # and no-JS visitors see the complete dataset, not an empty shell.
    substitutions = {
        "[[ROWS]]": export_data.render_rows(records),
        "[[CLASS_OPTIONS]]": export_data.render_class_options(records),
        "[[TOTAL]]": f"{len(records):,}",
    }

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False,
                      keep_trailing_newline=True)
    base = env.get_template("base.html.j2")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    pages = [parse_page(p) for p in sorted(PAGES_DIR.glob("*.html"))]
    for page in pages:
        for marker, value in substitutions.items():
            if marker in page["content"]:
                page["content"] = page["content"].replace(marker, value)

    urls = [p["url"] for p in pages]
    dupes = {u for u in urls if urls.count(u) > 1}
    if dupes:
        raise ValueError(f"duplicate page urls: {dupes}")

    # every internal href/src in both the base template and each content
    # fragment is authored root-absolute ("/browse/", "/assets/css/site.css")
    # for simplicity; prefix with BASE here so the site still resolves
    # correctly when served at a subdirectory. Protocol-relative ("//...")
    # and full external URLs are untouched since they don't start with a
    # single "/".
    base_prefix_re = re.compile(r'(href|src)="/(?!/)')

    for page in pages:
        html = base.render(page=page, content=page["content"], site_url=SITE_URL,
                           stats=stats)
        if BASE:
            html = base_prefix_re.sub(f'\\1="{BASE}/', html)
        dest = out_path(out_dir, page["url"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")

    shutil.copytree(ASSETS_DIR, out_dir / "assets",
                    ignore=shutil.ignore_patterns("_*"))

    entries = "\n".join(
        f"  <url><loc>{SITE_URL}{p['url']}</loc></url>"
        for p in pages if p["url"] != "/404/"
    )
    (out_dir / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n", encoding="utf-8")

    root_dir = ROOT / "content" / "root"
    if root_dir.exists():
        for extra in root_dir.glob("*"):
            shutil.copy2(extra, out_dir / extra.name)

    return pages


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    pages = build(args.out)
    print(f"built {len(pages)} pages -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
