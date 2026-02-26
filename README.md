# Administrations (StegBiography Module)

Administrations is an evidence-first, append-only repository documenting **federal executive behavior by presidential term**.

This repo reuses the same ingest + archival + FREE-DOM involvement engine as Trumpality, but the scope is institutional:

- President / Vice President
- Executive departments and agencies (DOJ, DHS, CMS, etc.)
- Funding actions, enforcement actions, directives, and litigation

## Structure

`administrations/` contains one folder per presidential term:

- `2017-2021_Trump/`
- `2021-2025_Biden/`
- `2025-2029_Trump/`

Each term folder has its own:
- `records/` (statements, actions, links)
- `seeds/` (source URL lists, court dockets)
- `freedom/` (FREE-DOM graph CSVs)

## Standards

- Verbatim quotes only for statements
- Primary sources required (transcripts, official docs, court filings)
- Secondary allowed only if it cites primary
- Append-only: corrections are new entries

## Quick Start (no laptop needed)

1) Upload the ZIP contents to the repo root.
2) Add administration term folders under `/administrations/`.
3) Run **weekly-ingest** from Actions to populate the database.
4) Add records under each administration’s `/records/`.

## Related Repos

- Trumpality — Trump-only, across his entire public life
- Executive_Rhetoric_Ledger — cross-administration comparison and scoring
