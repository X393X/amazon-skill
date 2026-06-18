# Team Review Notes

## Skill Solves

`amazon-sorftime-product-selection-research` turns Amazon category, keyword, ASIN, URL, or product idea inputs into a traceable product-selection decision report.

It is designed for Sorftime-backed Amazon market entry validation, with a fixed 100-point scoring model, blocked states, evidence tables, missing-data notes, risk checks, and downstream Listing / image / A+ handoff briefs.

## Best Fit

- Amazon category or Best Sellers product-selection screening
- keyword opportunity and entry-point validation
- competitor structure and review moat analysis
- VOC pain point productization checks
- trend, price band, and profit-space analysis
- team-readable HTML / Markdown / JSON delivery packages

## Not Fit

- automatic ads, inventory, or purchasing actions
- final legal, certification, patent, or compliance clearance
- public publishing of private market reports
- using public-safe fixtures as live market conclusions
- storing raw review text or complete real Top100 exports in the repository

## Input Contract

Required inputs are documented in `contracts/input.schema.json`.

Core fields:

- `marketplace`: `US`, `UK`, or `CA`
- `input_type`: `asin`, `url`, `keyword`, `category`, `best_sellers`, or `natural_language`
- one primary object: `product_type`, `category_name`, `keyword`, `asin`, or `url`
- `task_type`: `product_selection`, `competitor_analysis`, `keyword_research`, `voc_analysis`, or `listing_handoff_brief`

## Output Deliverables

Each completed run should produce:

- `product_selection_report.html`
- `product_selection_report.md`
- `product_selection_data.json`
- `source_manifest.json`
- `validation_result.json`
- `product_selection_delivery_package.zip`

Local preview URLs are only for validation. Share the ZIP package or publish through an approved internal or public-safe channel.

## Privacy Modes

`public_safe_real_world` is the default GitHub demo mode. It allows public category names and generic keywords, but competitors, ASINs, brands, profit details, and samples must be anonymized or template-level.

`strict_anonymized` is for stronger anonymized examples where all market identifiers should be generalized.

`private_internal` is for local team analysis with real provider data. These outputs must remain outside GitHub and should stay in local or approved internal channels.

## Public-safe Demo

Run from `<skill_dir>`:

```bash
python scripts/normalize_market_data_response.py fixtures/best_sellers_on_ear_headphones_us_public_safe.json --out dist/product_selection_data.json
python scripts/render_product_selection_report.py dist/product_selection_data.json --out dist/product_selection_report.html
python scripts/export_markdown_report.py dist/product_selection_data.json --out dist/product_selection_report.md
python scripts/package_report.py --input-dir dist --out dist/product_selection_delivery_package.zip
python scripts/validate_product_selection_package.py dist
python scripts/privacy_scan.py .
```

The On-Ear Headphones fixture is a public-safe template sample. It is not live market data, not a complete real Top100, not a raw Sorftime export, and not a real product-selection conclusion.

## Private Internal Analysis

Private runs should use the Sorftime MCP contract documented in `adapters/sorftime_mcp_contract.example.json`.

Rules:

- keep raw provider responses in local runtime-only folders
- do not commit private reports or provider raw output
- do not publish real ASIN, brand, or complete Top100 reports publicly
- return blocked states when data is unavailable or required fields are missing

## Opening Reports

For local review, open `product_selection_report.html` directly from the generated output folder.

For team handoff, send `product_selection_delivery_package.zip` through an approved internal channel. Do not send localhost, loopback, or local file URLs as share links.

## Validation Commands

Run these before release:

```bash
python scripts/validate_product_selection_package.py dist
python scripts/privacy_scan.py .
python <skill_creator_dir>/scripts/quick_validate.py <skill_dir>
```

Expected result:

- package validator returns `ok=true`
- privacy scan returns `findings_count=0`
- quick validate prints `Skill is valid!`

## GitHub Exclusions

GitHub should include source code, schemas, contracts, workflows, scoring rules, templates, anonymized fixtures, examples, adapters, docs, and release notes.

GitHub must not include:

- generated `dist` outputs
- `runtime` or `tmp` folders
- private local configuration
- real provider raw responses
- real business reports
- complete real Top100 exports
- user brands, user ASINs, store data, backend data, account data, or credentials

## Next Steps

- create a team repository or confirm the target repository URL
- push this skill on `release/amazon-product-selection-skill-v0.2`
- open a review PR
- ask reviewers to run the public-safe demo and validation commands
- keep private_internal test reports outside the repository
