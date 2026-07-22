# Methodology

*How this dataset was built, what's included, what's excluded, and where
it's thin. Updated as the dataset grows — see the file table below for
current row counts.*

## What counts as a row

Every row is a real, individually identifiable public-record transaction —
a federal contract award, a federal or state grant, a state government
contract, a UK public tender, or an IRS Form 990 contractor disclosure. No
row is estimated, interpolated, or reconstructed; every row carries a
`source_url` that traces to the specific public record.

## Sources

| File | Source | Sweep window |
|---|---|---|
| `data/awards_federal.csv` | USAspending.gov API (contract award types A–D) | 2015–present, swept 2026-07-21; extended 2026-07-22 via Experiential Design Index cross-reference |
| `data/awards_grants.csv` | NSF AISL program + IMLS awarded-grants database (Museums for America, National Leadership Grants – Museums, Inspire! Grants for Small Museums) | FY1996–2025 (no floor applied), swept 2026-07-21 |
| `data/contractors_990.csv` | IRS Form 990 Part VII Section B (five highest-paid independent contractors over $100K), via the IRS's own bulk e-file XML index | FY2022–2025 filings, swept 2026-07-21 |
| `data/awards_state.csv` | State open-checkbook / contract-transparency portals (TX, CA, NY, WA — FL investigated twice, no usable rows found despite a real bulk source) | swept 2026-07-21, FL re-investigated 2026-07-22 |
| `data/awards_uk.csv` | UK Find a Tender / Contracts Finder (non-US comparables) | swept 2026-07-21 |

### USAspending federal sweep

Three passes, unioned and deduplicated by USAspending's stable award ID:
a keyword pass (8 phrases: exhibit design, exhibit fabrication, interactive
exhibit, museum interactive, interpretive media, audiovisual production,
visitor center exhibit, immersive experience), a recipient pass (27 named
exhibit/media/AV firms), and an agency pass (7 federal agencies crossed with
3 narrowing keywords each). A bare "exhibit" keyword was found to be too
generic during the sweep — it collides with legal-contract "Exhibit A/B/C"
attachments — so the relevance filter requires multi-word phrases plus an
exclusion list for boilerplate matches.

**Known truncation**: six query tags hit their per-query page cap during
the sweep and almost certainly have more results beyond what's captured —
treat counts from those tags as a sample, not a census, until a follow-up
pass raises the page cap.

**Two named recipient firms produced zero usable data** because their
exact names collide with unrelated companies in USAspending's full-text
search (a Florida exhibit-fabrication firm and an entertainment-technology
firm, both with common-word names). Re-attempting these requires the exact
registered legal name or a DUNS/UEI-based search rather than name text.

### Grants sweep

NSF's free-text keyword search proved unreliable for topical queries (even
distinctive single words returned mostly unrelated STEM-research grants), so
NSF rows were built by identifying named AISL-funded exhibit projects via
web search and individually verifying each through NSF's single-award
lookup endpoint — a smaller n than a systematic sweep, but every row is
independently verified. IMLS has no working bulk API for current data; rows
were pulled from its live awarded-grants search page, filtered to three
museum-relevant programs crossed with two keyword phrases narrow enough to
return a workable result count.

### IRS Form 990 contractor sweep

The most direct path — ProPublica Nonprofit Explorer's structured API and
its filing-download endpoints — does not expose Part VII Section B and
returns a bot-detection block on direct filing downloads. This dataset
instead uses the **IRS's own official bulk e-file XML index**
(`apps.irs.gov/pub/epostcard/990/xml/`), which publishes a monthly index CSV
(EIN, taxpayer name, object ID, batch ID) alongside batched ZIP archives of
the underlying e-file XML, unauthenticated and with no bot-detection layer.
Individual filings were pulled via ranged HTTP reads against the relevant
batch archive (avoiding a full download of each ~100MB batch) and parsed
for `ContractorCompensationGrp` entries.

**Museum list**: compiled from public rankings (Wikipedia's most-visited/
science-center/children's-museum/natural-history-museum/aquarium/zoo lists,
Smithsonian Affiliations) weighted toward institution types most likely to
contract exhibit/AV/design work — science centers, natural history and
history museums, children's museums, major art museums, aquariums, and
zoos. 173 candidate museums were compiled; 136 were matched to a specific
Form 990 filer by legal/DBA name (many nonprofit museums file under a
holding entity or foundation name distinct from their public name — e.g.
LACMA files as "Museum Associates," The Henry Ford as "The Edison
Institute"). Matching required the filer's legal name to exactly equal or
extend (with a suffix like "Inc"/"Foundation") the target name — a
deliberately conservative rule, chosen after a looser substring rule
produced false matches between similarly-named but unrelated organizations
(e.g. "Southern California Academy of Sciences" matching a search for
"California Academy of Sciences," or Boston's "Museum of Science" matching
a search for Chicago's "Museum of Science and Industry"). This trades
recall for precision — 37 candidate museums were not matched to a filer in
this first pass.

**Follow-up pass (2026-07-22)** individually researched all 37: 26 turned
out to be private nonprofits filing under a different legal/DBA name than
their public one (now matched directly by EIN rather than name — e.g.
COSI files as "Center of Science and Industry," the Mob Museum as "300
Stewart Avenue Corporation," the High Museum of Art as a division of
"Robert W. Woodruff Arts Center, Inc."); 2 are genuinely government-run
and don't file a 990 at all (North Carolina Museum of Natural Sciences,
History Colorado — both state-agency museums); 4 are for-profit
commercial operations outside 990 scope entirely (Newport Aquarium and
Adventure Aquarium, both Herschend Family Entertainment; Ripley's
Aquarium, Ripley Entertainment; Kennedy Space Center Visitor Complex,
operated commercially by Delaware North under a NASA concession). 5 of
the 26 EINs found, once looked up directly, returned zero contractors
over the $100K disclosure threshold for the year checked (Great Lakes
Science Center, Fleet Science Center, Mob Museum, Old Sturbridge Village,
Glazer Children's Museum, Louisiana Children's Museum, Alaska SeaLife
Center) — a legitimate finding (no vendor crossed the threshold that
year), not a sweep failure.

**Two filers were excluded entirely despite a successful EIN match**,
same reasoning as the AMNH-vs-Harvard-credit-union and Sam Noble/OU
Foundation exclusions above: Carnegie Science Center files under
"Carnegie Institute," the umbrella entity for four distinct Carnegie
museums (Science Center, Natural History, Art, and the Warhol), and none
of its contractor rows named a specific museum — unattributable, so
excluded. The High Museum of Art files under "Robert W. Woodruff Arts
Center, Inc.," which also covers the Alliance Theatre and Atlanta
Symphony Orchestra — confirmed cross-institution mixing directly (one
disclosed contractor payment was to the symphony's own music director),
so excluded for the same reason.

Two 990-PF (private foundation) filers were processed with the
equivalent Part VIII schema element (`CompensationOfHghstPdCntrctGrp`
instead of `ContractorCompensationGrp`) — the J. Paul Getty Trust and the
Kimbell Art Foundation. Neither disclosed any exhibit/design-relevant
contractor (Getty's five are advertising, web services, legal,
accounting, and investment management; Kimbell's are construction
management, investment management, and structural engineering) — both
processed cleanly, zero rows kept, a real finding not a gap.

**Keep/skip rule**: across both passes (~537 contractor rows extracted
across 156 museums), 58 rows were kept as plausibly exhibit/interactive/
AV/design-related. Skipped categories: food service and catering, general
construction contractors, security, janitorial/custodial, legal,
audit/accounting, investment management, generic architecture and
engineering firms, generic marketing/advertising, fine-art shipping and
storage, and inter-museum exhibition loan fees. Four museums were
excluded entirely after their matched 990 filer turned out to be the
wrong entity or too broad in scope to attribute specifically to the
museum (a same-named but unrelated credit union; a university-wide
foundation; and two multi-institution umbrella filers, Carnegie Institute
and the Robert W. Woodruff Arts Center — see the follow-up pass above).
Several kept rows are included on the strength of the vendor's name being
a recognized exhibit/experience-design firm even where the IRS's own
"services description" field used a generic label like "construction" —
these are flagged individually where that judgment call was made.

**Known limitation**: the IRS e-file schema caps the `ServicesDesc` field at
roughly 40 characters, so some kept descriptions are visibly truncated
mid-word. This is a source-data limitation, not a transcription error.

### State portal sweep

Five states were attempted (CA, NY, TX, WA, FL); four yielded usable data.

- **Texas — the richest state source (63 rows).** The Legislative Budget
  Board's Contracts Database is a client-side app whose data layer exposes
  the state's full contracts dataset (all state contracts since ~2013) as
  structured JSON, keyword-filterable directly with no scraping required.
  Strong signal came from the Texas Historical Commission, Parks &
  Wildlife, and the State Preservation Board (Bullock Texas State History
  Museum).
- **California (21 rows).** `data.ca.gov`'s CKAN purchase-order dataset is
  SQL-queryable but only covers FY2012–2015 — no current bulk dataset was
  found. Signal concentrated in California State Parks contracts.
- **New York (16 rows).** `data.ny.gov` publishes several Socrata
  "Procurement Report for [State/Local/IDA] Authorities" datasets with
  vendor/description/amount fields; real signal concentrated in the New
  York Power Authority's Niagara Power Vista visitor center after filtering
  out substantial noise (trade-show sponsorships, memberships, unrelated
  facility repairs).
- **Washington (7 rows).** `data.wa.gov` publishes per-fiscal-year "Agency
  Contracts" Socrata datasets (2014–2025, with inconsistent field names
  across years); Washington State Parks and the Washington State Historical
  Society yielded the usable hits.
- **Florida — a real bulk source exists, but yields nothing usable.**
  FACTS and MyFloridaMarketPlace remain unusable (see above), but a
  follow-up pass (2026-07-22) found the Florida Comptroller's
  **Vendor Payments** transparency tool
  (`myfloridacfo.com/transparency/vendorpayments`) publishes genuinely
  bulk, unauthenticated, CORS-open ZIP downloads of every state vendor
  disbursement, one file per fiscal year back to FY2009 (confirmed
  working: downloaded and parsed the full FY2025 file, ~1.2GB of
  pipe-delimited text across four parts). It's a real, reusable source —
  and still didn't produce a single row for this dataset, for two
  independent reasons: (1) the `object_description` field is a fixed,
  generic accounting-category enum (e.g. "SUPPLIES - GENERAL", "FEES -
  GENERAL - COMMODITIES," "CONTRACTED SERVICES - OTHER") — a direct
  search of the entire file for the literal word "EXHIBIT" in this field
  returned **zero** results, confirming the category list never
  itemizes by project type the way a museum-specific line item would;
  (2) cross-referencing every known exhibit-industry firm name already
  in this dataset (363 recipients across the federal/state/990 files)
  against the file's vendor-name field surfaced real hits, but every one
  that looked promising on the vendor name alone turned out on inspection
  to be out of scope: Ace Exhibits' Department of Health payments are
  categorized "ADVERTISING - GENERAL" / "PRINTING/REPRODUCTION - GENERAL"
  (health-fair print materials, not museum exhibits); Gallagher &
  Associates' and Explus's Department of Environmental Protection
  payments are $590–$13,688 line items coded "SUPPLIES - GENERAL" or
  "FEES - GENERAL" (too small and too generically categorized to
  represent a real exhibit design/fabrication engagement, more likely a
  minor licensing or add-on charge); Electrosonic's one hit is coded
  "REFUNDS - GENERAL" (not a purchase at all); Gulf Exhibition Corp's
  six-figure Fish and Wildlife Conservation Commission payments are coded
  "STATE FINANCIAL ASSISTANCE - GENERAL," a grant/subgrant passthrough
  category, not a services contract, and the company's actual line of
  business couldn't be confirmed as exhibit-related. Every other
  EXHIBIT-named vendor found (Exhibit Arts, Exhibitor Media, Marquis
  Exhibits, HT International Exhibitions, and several more) is paid
  exclusively by the **Department of Commerce** — Florida's
  economic-development trade-show/pavilion program, the same
  out-of-scope category (booths, not museum exhibits) already excluded
  everywhere else in this dataset. Recorded in full so a future session
  doesn't re-download and re-discover the same dead end — though the
  source itself (the ZIP files, by fiscal year) is worth keeping in mind
  if a different research angle (e.g. reading the raw agency-payment
  detail, not just the category code) is ever attempted.

**Data-quality caveats specific to this file**:
- Several Texas Historical Commission awards to a single large exhibit firm
  carry `scope_confidence: low` — they read as IDIQ ceiling values rather
  than true single-project spend.
- A number of Texas and Washington rows are one of a batch of identical
  same-day, same-amount awards to multiple vendors on an on-call/IDIQ
  roster — flagged in `notes` as pool awards, not a single discrete
  project.
- Some New York rows only expose "amount expended this fiscal year" on a
  standing purchase order rather than a true contract ceiling — flagged in
  `notes`.
- Several rows are traveling-exhibit *leases* rather than fabrication
  contracts (e.g. a state-authority-routed lease of a touring exhibition) —
  tagged `fabrication_inclusive: n` and noted as a lease, a different scope
  than this dataset's core comparison unit.

### UK tender sweep

These rows are **non-US comparables** and are never mixed into US-market
figures without that flag — different market, different procurement
culture, different currency.

Neither UK public-procurement portal's documented API supported keyword
search in practice at sweep time: Contracts Finder's OCDS search endpoint
accepts only date/stage/limit parameters (its `searchTerm` parameter is
silently ignored per the portal's own API documentation), and Find a
Tender has no public keyword-search endpoint. The sweep pivoted to
targeted web search to identify specific museum-sector notices by name
(Science Museum Group, V&A, Natural History Museum, National Museums
Liverpool, Imperial War Museum, Royal Institution of Cornwall, London
Museum), then read each notice's structured GOV.UK page directly.

Of the 9 rows collected: 3 carry a confirmed final awarded value distinct
from (or matching) the pre-award estimate; 1 has a matching estimate and
award; 5 are pre-award estimates or preliminary market-engagement figures
only (no award notice was reached in the sweep's timebox), and are marked
`scope_confidence: low` or `med` accordingly with `total_award_value` left
blank rather than guessed. One row's actual award notice is known to exist
(referenced from its tender page) but wasn't reached — the source domain
began rate-limiting the sweep near the end of the session.

### SAM.gov opportunity side (investigated, not pursued)

The original plan named SAM.gov's contract-opportunity archive as an
optional extension — the "asking" side of the market (stated NTE budgets
in RFPs) as a comparison to the "awarded" side already in this dataset.
Investigated 2026-07-22 and found not viable, for two independent reasons:

1. **No working keyword search.** SAM.gov's public Opportunities API v2
   does not support free-text search via its documented GET parameters —
   `q`, `keyword`, and `keywords` were all tested against clearly
   unrelated terms (e.g. "museum" vs. a nonsense string) and returned an
   identical result count in every case, confirming the parameter is
   silently ignored rather than filtering. NAICS-code filtering (`ncode`)
   does work (verified: different codes return different counts), but
   browsing by plausible codes (541420 Industrial Design Services, 337215
   Showcase/Partition/Shelving Manufacturing) surfaces almost no volume
   (4 opportunities for all of 2024 under 541420) and what comes back is
   generic GSA Multiple Award Schedule vehicle notices, not project-level
   museum RFPs.
2. **No structured budget field on pre-award records.** The one sampled
   record that did carry a dollar figure was already an *award* notice
   (duplicating what USAspending already captures, just less completely
   structured) — true solicitation/presolicitation records expose no
   comparable `estimatedValue`-type field; a stated NTE budget, where one
   exists at all, lives only in an attached, unstructured solicitation
   document, one per record, not scalable to sweep.

Conclusion: this source doesn't deliver what the plan hoped for and isn't
included. Recorded here so a future session doesn't re-attempt the same
investigation from scratch.

### Cross-reference with the Experiential Design Index (2026-07-22)

Sitara Systems also publishes [The Experiential Design
Index](https://sitara.systems/experiential-design-index/) — a separate,
neutral public record of "who built what" in experiential design (firms,
projects, venues, credits), sourced independently of this dataset. The
two datasets don't share an editorial process, but they describe
overlapping subject matter, so a firm credited in the Index on a project
this dataset hasn't captured is a genuinely useful, targeted research
lead — far more efficient than a broad keyword sweep, since the lead
already names a specific firm, venue, and year to search for.

**Method**: matched the Index's ~237 firms against this dataset's ~530
distinct recipients by normalized name (237 Index firms checked; 42 had
a name-match). For every Index project credited to one of those 42
firms, checked whether this dataset already had a plausibly-corresponding
row (same recipient, and the credited venue's name substantially present
in the award's description or client field). Result: **395 Index credits
were already corroborated** by an existing row in this dataset (useful
confirmation that the two records agree, not itself a reason to add
anything); **990 credits had no obviously-corresponding row** — leads.

**Follow-up on the leads**: narrowed to venue types most likely to have a
public-record trail (visitor centers, history/natural-history/science
museums, aquariums/zoos, art and children's museums, academic and
cultural institutions — 532 unique firm+venue leads after deduping),
then re-ran a broad, un-keyworded USAspending recipient-name search for
the firms with the most concentrated lead counts. Because these firms
were already confirmed exhibit-industry players (that's why they matched
in the first place), a pure recipient search — no exhibit keyword
required — was safe to run and surfaced substantially more of their real
federal award history than the original keyword/agency/recipient sweep
had captured.

**Result: 144 new federal rows kept after classification and QA**, out
of several hundred candidate rows surfaced by the firm-recheck searches
(the excluded majority were $0 IDIQ "minimum guarantee" administrative
entries, generic purchase-card line items, or descriptions too
vague/cryptic to classify confidently — excluded rather than guessed,
per this dataset's standing rule). Two firms account for most of the
yield:
**HealyKohler Design** and **The Design Minds** — both National Park
Service exhibit-planning-and-design specialists whose IDIQ task-order
history (dozens of small design-only contracts across individual NPS
units) had been almost entirely missed by the original sweep, since
"exhibit planning and design" for e.g. "Little Bighorn Battlefield" or
"Lake Mead National Recreation Area" doesn't match a generic exhibit
keyword search unless you already know to look for that firm. Smaller
genuine finds: Ralph Appelbaum Associates ($3.04M, NMAAHC exhibition
design), Trivium Interactive ($950,534 + $25,380, the Lockkeeper's House
exhibits), Taylor Studios (18 rows, mostly "life cast figures" for museum
dioramas), Southern Custom Exhibits of Alabama (a vendor already heavily
represented in this dataset, but with real additional awards the
original sweep missed), Exhibit Concepts, Building Four Fabrication,
Steve Feldman Design, and Tessellate.

**Firms rejected for name-collision false positives** (same discipline as
the SEARCH LLC/TAIT exclusions in the original federal sweep): a plain
recipient-name search for **"Roto"** returns Norotos Inc. (night-vision
equipment) and City of Groton; **"West Office"** returns Midwest Office
Furniture; **"Ideum"** returns Trideum Corporation (defense simulation
contractor) and Nemean Trideum Joint Venture; **"Gallagher & Associates"**
returns G&A Strategy and Design LLC (an unrelated firm); **"TAIT"**
returns R.E. Staite Engineering (harbor dredging) exactly as documented
before; **"Tessellate"** returns both the real firm (Tessellate, LLC) and
an unrelated aerospace materials company (Tessellated Inc) — only exact
recipient-name matches to the real firm were kept. **"SmithGroup"**
returned 100 real awards, but all generic hospital/laboratory
architecture — a real firm, wrong scope, correctly excluded rather than
force-fit.

This cross-reference is a repeatable technique — as either dataset grows,
re-running it will likely surface more leads. It was not applied to the
Index's own data (no changes were made to that repo); the corroboration
count above is a one-way benefit noted here, not yet written back as
cross-reference notes on individual rows.

## Scope-normalization standard

The canonical unit of comparison across this dataset is the **full
interactive scope, hardware and software combined** — design, software,
content, hardware, and integration — excluding exhibit fabrication and
base-building infrastructure. Awards that deviate from this (bundling in
fabrication, or covering hardware/media only) are flagged rather than
silently averaged in: published exhibit-cost figures vary mostly by what's
bundled into the scope, and this dataset's job is to make that visible.

- `fabrication_inclusive`: `y` when the award description indicates exhibit
  fabrication is bundled into the scope, `n` when it's excluded, `unknown`
  when the description doesn't say.
- `scope_confidence`: `high` / `med` / `low`, reflecting how confidently the
  award description supports the assigned `project_class`.

## Obligations vs. total award value

USAspending's award-search endpoint exposes obligated-to-date amounts
(`obligated_amount`); it does not expose the base-and-all-options ceiling
value at the same endpoint (`total_award_value` is present in the schema
but empty for federal rows in this dataset — getting it would require a
per-award detail-page fetch for all ~1,231 federal rows, not yet done). For
sources that expose both an estimated and a final awarded figure (UK
tenders), both are recorded with a note distinguishing them.

## Dedupe policy

Rows are deduplicated by their source system's own stable identifier
(USAspending's `generated_internal_id` for federal awards) — an award
appearing in more than one sweep pass collapses to a single row, with all
matching passes recorded in `notes`. **Base-award vs. task-order
double-counting was specifically checked** (a possible source of double
counting flagged as an open question by an earlier pass of this dataset):
every federal row's award ID was parsed for its IDV/parent-award reference
and checked against every other row's own award ID. Zero cases were found
where both a base IDV and one of its own task orders appear as separate
rows in this dataset — the parent IDVs themselves generally weren't
independently swept up by the keyword/agency/recipient passes, so this
concern does not currently materialize in the data. Per the dataset's
"never delete a public record row" rule, if a genuine duplicate project is
later found across sources (e.g., the same project appearing in both a 990
and a state portal), both rows are kept and cross-referenced in `notes`
rather than one being removed.

**Cross-source vendor overlap was also checked**: several exhibit firms
appear across multiple files (e.g. Design and Production Inc. appears in
`awards_federal.csv` against several different federal agencies *and* in
`contractors_990.csv` against two different museums; Pacific Studio,
Roto Group, and Space Haus each appear in both a federal row and a 990
row). In every case checked, these are different clients and different
projects for the same vendor — not the same transaction recorded twice —
so no rows were merged or flagged as duplicates. This is expected: a small
number of national exhibit-fabrication firms do recurring work across many
institutions, which is itself a legitimate finding of the dataset rather
than a data-quality problem.

## Classification QA

A stratified sample (15 rows per `project_class`, or the full class where
smaller) was independently re-verified against each award's full detail
record via the USAspending award API — not just the truncated description
already in the CSV. Findings, and the rows fixed as a result:

| Class | Sampled | Reclassified | Notes |
|---|---|---|---|
| `kiosk` | 15 | 1 | One vague, larger-scope award moved to `other` |
| `maintenance` | 15 | 2 (+1 confidence-lowered) | Two rows were base-building repairs (a fence installation, a facade repoint) outside the scope-normalization standard, moved to `other` |
| `multi_station` | 15 | 0 | Three IDIQ "minimum guarantee" line items don't describe a specific project scope — flagged as a methodology caveat, not reclassified |
| `single_interactive` | 15 | 3 | A personnel-staffing contract and a general architecture design-services contract were not exhibit-specific; one AV "refurbishment" was moved to `maintenance` |
| `other` | 15 | 3 (moved *into* other classes) | Three rows had enough signal to classify confidently (an explicit "exhibit remodeling," gallery lighting, and exhibit-case rehab) and were promoted out of `other` |
| `building_wide` | 0 → 6 (2026-07-22) | 6 | See below — a follow-up pass found six federal rows that had been sitting misclassified as `multi_station` or `other` |

No class exceeded a 20% error rate on its sampled subset (the threshold
this project's build plan set for flagging a class loudly rather than
silently re-labeling everything), though `single_interactive` and `other`
both sat right at that boundary and would benefit from a closer read if
this dataset is extended.

### `building_wide` follow-up pass (2026-07-22)

The federal file's zero-row `building_wide` class turned out to be a
classification gap, not a real absence of whole-museum federal exhibit
contracts. A targeted USAspending search for unqualified "entire
museum"/"all exhibits"-scoped language found six rows already present in
`awards_federal.csv`, previously misclassified:

- **National Museum of African American History and Culture, inaugural
  exhibits** (Design and Production Inc., Smithsonian, $7.07M obligated /
  **$48.6M ceiling** — `total_award_value` filled in from the USAspending
  award-detail endpoint, one of the few rows in this dataset where that
  field isn't empty) — moved from `multi_station`.
- **National Museum of the United States Army, exhibit
  fabrication/installation** (Design and Production Inc., Dept. of the
  Army, $45.2M obligated / **$69.6M ceiling**, also filled in) — the sole
  fabrication contract found for this entire museum; moved from
  `multi_station`. A companion Eisterhold Associates row for the same
  museum ("exhibit and fabrication support services," $3.2M) was
  deliberately left as `multi_station` — its description reads as an
  ancillary support contract, not the primary whole-museum scope.
- **Goddard Space Flight Center Visitor Center** (RGI International,
  NASA, $1.4M, high confidence) — description explicitly covers "design,
  fabrication, and installation of museum-quality exhibits" for the whole
  (small) visitor center; moved from `multi_station`.
- **Three National Park Service/Fish & Wildlife visitor-center exhibit
  contracts** — Crab Orchard NWR ($784,520), American Camp NHP
  ($636,582), Capitol Reef NP ($395,820) — each titled simply "[site]
  visitor center exhibits" with no gallery specified; moved from `other`
  to `building_wide` at **low** confidence, since the title alone doesn't
  explicitly confirm full-facility scope the way the three rows above do.

## Known gaps

- `total_award_value` is empty for every federal row except the two
  `building_wide` rows filled in during the 2026-07-22 follow-up pass
  (see "Obligations vs. total award value" above) — filling the rest
  would need a per-award detail-page fetch for all ~1,231 remaining rows.
- Federal award truncation on six high-volume query tags (see USAspending
  sweep section above).
- One UK award notice (Royal Institution of Cornwall) is known to exist but
  wasn't reached before the source domain began rate-limiting the sweep;
  5 of 9 UK rows are pre-award estimates rather than confirmed final values.
- Florida remains uncovered in `awards_state.csv` (TX, CA, NY, and WA
  only) — not for lack of a bulk source (the Comptroller's Vendor
  Payments ZIPs are real and were fully pulled and searched), but because
  nothing in that source cleared the bar for inclusion — see the state
  portal sweep section above for the full negative finding.
- California's open purchase-order dataset only covers FY2012–2015; no
  current bulk source was found for more recent CA state contracts.
- Two named recipient firms in the federal sweep produced zero usable data
  due to name collisions.
- This is a descriptive record of what was awarded, not a statement about
  final project cost or any firm's pricing — obligations recorded here can
  differ from a project's eventual total cost, and scope bundling
  (fabrication-inclusive vs. not) means figures are not directly comparable
  across rows without checking the `fabrication_inclusive` flag.
