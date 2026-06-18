# Amazon Product Selection Research

Public-safe, Sorftime-backed Amazon product selection skill template.

## What It Produces

- `product_selection_report.html`
- `product_selection_report.md`
- `product_selection_data.json`
- `source_manifest.json`
- `validation_result.json`
- `product_selection_delivery_package.zip`

Local preview URLs are validation-only. Do not send a localhost or loopback URL as a final delivery link. Send the ZIP package or publish through an explicitly configured public-safe/internal channel.

## Public-safe Clean Run

Run from `<skill_dir>`:

```bash
python scripts/normalize_market_data_response.py fixtures/best_sellers_on_ear_headphones_us_public_safe.json --out dist/product_selection_data.json
python scripts/render_product_selection_report.py dist/product_selection_data.json --out dist/product_selection_report.html
python scripts/export_markdown_report.py dist/product_selection_data.json --out dist/product_selection_report.md
python scripts/package_report.py --input-dir dist --out dist/product_selection_delivery_package.zip
python scripts/validate_product_selection_package.py dist
python scripts/privacy_scan.py .
```

Compatibility entry:

```bash
python scripts/normalize_sorftime_response.py fixtures/best_sellers_on_ear_headphones_us_public_safe.json --out dist/product_selection_data.json
```

## Delivery Metadata

Generated packages distinguish:

- `local_preview_url`: local validation only
- `report_file_path`: local HTML file in the package
- `package_zip_path`: portable ZIP package
- `publish_status`: `not_published`, `local_only`, `public_safe_published`, or `internal_published`
- `shareable_url`: null unless an allowed publishing workflow sets it
- `shareable_url_scope`: `none`, `public_safe`, or `internal_only`

`private_internal` reports must not have public shareable URLs.

## Private MCP Input

This repository only documents the private Sorftime MCP contract. Real private configuration must stay local and must not be committed.

Private runs should write runtime/raw outputs outside public-safe fixtures and examples. If the standalone provider cannot call Sorftime, it must return `blocked_sorftime_unavailable` and must not fabricate a live result from public fixtures.

## On-Ear Headphones Fixture

The On-Ear Headphones fixture is a public-safe template sample:

- not live market data
- not a complete real Top 100
- not a raw Sorftime export
- not a real product selection conclusion
- profit detail is template-level only and not a live margin estimate

## GitHub Boundary

Publishable: source code, contracts, templates, anonymized fixtures, examples, adapters, workflows, scoring docs, and collaboration docs.

Do not publish generated `dist` outputs, `runtime`, `tmp`, private configuration, real data, raw Sorftime responses, credentials, account data, user private brands, user ASINs, store data, raw review text, or complete real Top 100 exports.
