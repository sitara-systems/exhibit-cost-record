# The Exhibit Cost Record — site

Static site framing the dataset one level up (`../data/*.csv`): home page,
a searchable/filterable browse table over all records, an enumerated
findings page, and rendered methodology/benchmarks docs.

Same content-fragment + YAML front matter → Jinja2 → static-output pattern
as `sitara-website/site/`. Visual design and page conventions closely
follow **The Experiential Design Index**
(`ExperientialIndex/experiential-design-index/`) — same CSS token
structure (`--bg`/`--fg`/`--muted`/`--border`/`--accent`/`--accent-bg`/
`--link`, light+dark+`data-theme` support), same plain 900px-wide
Wikipedia/IMDb-style layout (system fonts, no hero sections), same
`table.facts`/`table.list` conventions, and the same server-rendered +
progressive-enhancement filter pattern (`assets/js/filter.js`, adapted
from the index's `assets/filter.js` with an added free-text search mode).
Deliberately not Sitara's own brand chrome — both are neutral public-data
resources published by Sitara Systems and share a visual family for that
reason.

`/browse/` renders **every record as a real `<tr>` at build time** — the
full dataset ships in the HTML, not fetched via a JS call after load — so
crawlers, AI answer engines, and no-JS visitors all see the complete table.
`filter.js` only hides/shows rows client-side; nothing about the data
depends on JavaScript running.

## Build

```
pip install -r requirements.txt
python build.py            # -> _site/
```

`build.py` always regenerates `assets/data/records.json` and `stats.json`
from `../data/*.csv` first, so the site can never drift from the source
CSVs. Nothing under `assets/data/*.json` is committed — it's a build
artifact.

## Local preview

```
python -m http.server 8096 -d _site
```

(or use the `exhibit-cost-record` entry in the workspace's
`.claude/launch.json`.)

## Content model

`content/pages/<slug>.html`: YAML front matter (`title`, `description`,
`url`) + an HTML body fragment. `methodology.html` and `benchmarks.html`
were generated once from `../docs/*.md` via `markdown` (tables + smarty
extensions) — if the source docs change, regenerate and re-paste rather
than hand-editing both copies out of sync.

## Deployment target

This site lives as a sibling section to the Experiential Design Index,
both under `sitara.systems` — `sitara.systems/exhibit-cost-record/`,
alongside `sitara.systems/experiential-design-index/` — not folded into
the index itself (that would blur the index's credits-neutral editorial
surface against this dataset's price-descriptive one).

`SITE_URL` in `build.py` defaults to `https://sitara.systems/exhibit-cost-record`
(override via the `SITE_URL` env var for a preview/interim deploy, same
knob the index's `build_site.py` uses). Every internal `href`/`src` is
authored root-absolute in the source (`/browse/`, `/assets/css/site.css`)
and prefixed with the URL's path component at build time via a regex pass
over the rendered HTML — verified working by mirroring `_site/` into an
`exhibit-cost-record/` subfolder and serving it locally.

At actual deploy time, `sitara-website`'s own root `robots.txt`/`llms.txt`
need a line added pointing at this site's sitemap — the same thing already
done for the index. This repo's own `content/root/robots.txt`/`llms.txt`
are the fallback if it's ever served from its own origin instead.

## Status

Built, not deployed. This is scaffolding: build now, launch decision
later.
