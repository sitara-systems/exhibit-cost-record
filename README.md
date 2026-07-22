# The Exhibit Cost Record

*Public contract awards for museum exhibits and interactive media — a
neutral, citable cost baseline assembled entirely from public records.*

> **Status: pre-publication working dataset.** Rows are collected from
> public sources and classified; a stratified classification QA pass has
> been completed on the federal awards file (see `docs/methodology.md`).
> Do not cite individual rows without checking them against the linked
> source.

## What this is

Every row is a real, publicly recorded transaction: a federal contract
award, a federal or state grant, a state government contract, a UK public
tender, or a nonprofit museum's IRS Form 990 contractor disclosure. The
record of what exhibits and interactive media actually cost already exists
in public — it has just never been assembled in one place. No firm's
internal finances appear here; every row carries a source URL that traces
to the public record.

See `docs/methodology.md` for full sourcing, classification, and QA detail,
and `docs/benchmarks.md` for published industry cost benchmarks that
contextualize (but are not part of) the row-level dataset.

## Data

| File | Rows | Source |
|---|---|---|
| `data/awards_federal.csv` | 1,237 | USAspending.gov API (award types A–D, 2015–present; keyword + recipient + agency passes, extended via an Experiential Design Index cross-reference) |
| `data/awards_grants.csv` | 218 | NSF (AISL) + IMLS awarded-grants databases |
| `data/contractors_990.csv` | 58 | IRS Form 990 Part VII Section B, via the IRS's own bulk e-file XML index (156 museums swept, 58 exhibit/AV/design-relevant rows kept) |
| `data/awards_state.csv` | 107 | State open-checkbook / contract-transparency portals — TX (63), CA (21), NY (16), WA (7); FL investigated twice (a real bulk source exists but yields nothing usable) |
| `data/awards_uk.csv` | 9 | UK Find a Tender / Contracts Finder — non-US comparables, flagged with a `currency` column |

## Schema and classification

Columns: `award_id, recipient, awarding_agency, sub_agency, start_year,
obligated_amount, total_award_value, award_description, project_class,
fabrication_inclusive, scope_confidence, source_url, notes`
(grants add `grant_program`; state awards add `state`; UK tenders add
`currency`; the 990 contractor file uses its own shape: `museum, ein,
tax_year, contractor_name, compensation, services_description,
source_url`).

`project_class` is one of: `kiosk` · `single_interactive` ·
`multi_station` · `building_wide` · `maintenance` · `other`.
Classification is derived from the award description only; rows that
can't be confidently classified keep `scope_confidence: low` rather than
being forced into a class.

**Scope normalization standard.** The canonical unit of comparison is the
*full interactive scope, hardware and software combined* — design,
software, content, hardware, and integration — excluding exhibit
fabrication and base-building infrastructure. Awards that deviate are
flagged (`fabrication_inclusive: y` for bundled fabrication scope) rather
than silently mixed: published figures vary mostly by scope bundling, and
this dataset's job is to make that visible, not to average it away.

## Known caveats

- **Obligations ≠ final cost.** USAspending amounts are obligations to
  date; `total_award_value` is recorded where the API exposes it (empty
  for federal rows — see `docs/methodology.md`).
- Award modifications and IDV/task-order structures can represent the same
  project more than once; deduplication is by USAspending's stable award
  id. A dataset-wide check for base-award/task-order double-counting found
  zero cases where both a parent IDV and one of its own task orders appear
  as separate rows.
- Sparse classes are published sparse, with their n — no padding. See
  `docs/methodology.md` for the classification QA results per class.
- UK tender rows are non-US comparables, flagged with a `currency` column
  and never mixed into US-market figures.
- This is a descriptive record, not price advice, and it makes no
  commentary on any firm's pricing.

## License

Dataset and documentation released under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution:
"The Exhibit Cost Record." Underlying government records are public
domain; the compilation, classification, and documentation are what this
license covers.
