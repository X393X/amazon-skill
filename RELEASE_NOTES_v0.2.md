# Release Notes v0.2

## Scope

`amazon-sorftime-product-selection-research` v0.2 is a release-freeze version for a public-safe, reproducible skill package. It keeps the core positioning unchanged: Sorftime-backed Amazon product selection and category research with HTML as the primary decision report.

This release does not modify Amazon Ops APP entrypoints, workflows, SOP files, Excel templates, UI, APIs, or quality gates.

## New Capabilities

- Public-safe release governance with `public_safe_real_world`, `strict_anonymized`, and `private_internal` modes.
- Full dist package generation: HTML report, normalized data JSON, source manifest, validation result, and optional Markdown report.
- Blocked package support for `blocked_no_data`, `blocked_missing_fields`, and `blocked_sorftime_unavailable`.
- Active critical disqualifier rule: a package with an active critical disqualifier cannot output `decision.label=enter`.
- Public-safe fixture support for `Best Sellers in On-Ear Headphones`, `Amazon US`, and generic on-ear headphone keywords.

## BSC Framework Fusion

v0.2 studied the BSC Amazon VOC trending product framework and adopted only portable workflow ideas:

- `product_selection_data.json -> optional visuals -> product_selection_report.html -> source_manifest.json -> validation_result.json`
- data coverage scoring
- VOC opportunity matrix
- trending product signals
- product action planning
- optional charts manifest
- optional external delivery adapter boundary

The release does not copy the external repository implementation, does not import its runtime client, and does not add real Feishu publishing.

## HTML Report Optimizations

- Keeps the fixed 16 report sections.
- Adds data coverage, trend signals, keyword Top20, competitor Top20, competitor clusters, profit scenarios, VOC trend summary, VOC opportunity matrix, product action plan, validation plan, delivery package, and optional charts manifest inside existing sections.
- Preserves offline HTML with inline CSS and no CDN dependency.
- Shows the public-safe fixture notice and private-internal GitHub warning in the report.
- Keeps the profit detail warning: public-safe profit details are template-level only and not live margin estimates.

## Added Fields

The normalized data package now includes:

- `data_coverage_score`
- `profit_scenarios`
- `ramp_path`
- `voc_opportunity_matrix`
- `validation_plan`
- `trending_product_signals`
- `voc_trend_summary`
- `product_action_plan`
- `report_delivery_package`
- `optional_charts_manifest`

Existing v0.1 model fields remain:

- `market_stage`
- `new_product_ramp_difficulty`
- `entry_strategy`
- `voc_productization_score`
- `disqualifiers`
- `evidence_level`
- `competitor_clusters`
- `profit_space_detail`

The 100-point scoring model and `decision.label + decision.blocked_status` structure are unchanged.

## Markdown Export

v0.2 adds `scripts/export_markdown_report.py`.

Markdown is an auxiliary export for review and handoff. It does not replace `product_selection_report.html` as the primary report.

## Validator Enhancements

`scripts/validate_product_selection_package.py` now checks:

- required dist files
- fixed 16 HTML sections
- no unresolved template placeholders
- no `???` marker
- required model fields
- VOC productization score range
- required VOC `painpoint`
- disqualifier status and severity enums
- active critical disqualifier cap
- public-safe profit detail restrictions
- competitor cluster required fields
- new v0.2 extended fields
- optional Markdown report when present
- source manifest consistency

## Privacy Scan Enhancements

`scripts/privacy_scan.py` remains separate from the package validator and scans the whole skill or repository. It supports:

- generic privacy-risk patterns
- local `private_terms.txt` as an optional private-term extension
- repository-safe `private_terms.example.txt`
- skips for local output directories such as `dist`, `runtime`, `tmp`, private data, exports, and secrets directories

## Test Results

Last validated release-freeze checks:

- `quick_validate.py`: passed.
- public-safe On-Ear Headphones clean-run: passed.
- `valid_product_selection_public_safe`: passed.
- blocked package fixtures: passed for `blocked_no_data`, `blocked_missing_fields`, and `blocked_sorftime_unavailable`.
- active critical disqualifier downgrade: passed.
- final package validator: passed.
- privacy scan: passed.
- negative validator probes: failed as expected for missing file, unresolved marker, sensitive output term, invalid public-safe profit value, invalid VOC score, missing VOC painpoint, invalid disqualifier status, and missing competitor-cluster field.
- private-term privacy scan probe: failed as expected.

## Known Limitations

- The standalone provider path is contract-only and does not perform live Sorftime MCP calls by itself.
- Real Sorftime MCP calls must be executed in the local Codex/MCP environment and normalized from saved local runtime responses.
- Public-safe fixtures are template samples, not live market data.
- Public-safe fixtures are not complete real Top100 exports.
- Public-safe fixtures are not raw Sorftime exports.
- Public-safe fixture scores are not real product-selection conclusions.
- Optional charts manifest is supported, but chart rendering is not required for v0.2.
- Feishu delivery is only documented as an optional adapter boundary; no real publishing is included.

## Files That Must Not Be Submitted

- `dist/`
- `runtime/`
- `tmp/`
- `real_data/`
- `exports/`
- `private/`
- `secrets/`
- `private_config.local.json`
- `.env`
- `.env.*`
- `*.local.json`
- Sorftime raw responses
- `private_internal` HTML, JSON, Markdown, or manifest outputs
- complete real Top100 exports
- real business reports
- credential, session, account, or key material
