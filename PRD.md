# BYO-MCP Amazon Product Selection Research PRD

## 1. Positioning

This repository is a BYO-MCP Skill Framework for Amazon product-selection research. It does not include a live Sorftime MCP connector, provider runtime, credential reader, auth flow, or network collection client.

Users must connect their own local MCP / Sorftime-compatible provider outside this repository, export or save a provider response JSON locally, then use this repository to normalize, render, package, validate, and privacy-scan the result.

## 2. Goals

- Provide a reusable Amazon product-selection decision framework.
- Normalize provider responses into a stable `product_selection_data.json` contract.
- Render Chinese/English-capable HTML and Markdown reports.
- Package reports into a portable ZIP.
- Validate package structure, scoring legality, blocked states, and privacy boundaries.
- Provide public-safe fixtures for GitHub-visible tests.

## 3. Non-goals

- Do not connect to Sorftime MCP directly.
- Do not ship provider credentials, account settings, or connection configuration.
- Do not fetch live market data from the network.
- Do not commit real provider responses or private generated reports.
- Do not automate ads, inventory, purchasing, legal conclusions, certification clearance, review creation, or final Listing publication.

## 4. Provided Components

- `adapters/provider_response_contract.example.json`: BYO-MCP provider response contract.
- `adapters/sorftime_mcp_contract.example.json`: Sorftime-compatible response mapping example.
- `fixtures/`: public-safe fixtures only.
- `examples/`: public-safe input/output examples only.
- `scripts/normalize_market_data_response.py`: normalizes a local provider response or fixture.
- `scripts/run_public_safe_demo.py`: one-command public-safe pipeline.
- `scripts/run_from_provider_response.py`: one-command local provider response pipeline.
- `scripts/render_product_selection_report.py`: renders HTML.
- `scripts/export_markdown_report.py`: exports Markdown.
- `scripts/package_report.py`: creates ZIP delivery package.
- `scripts/validate_product_selection_package.py`: validates generated package directory.
- `scripts/privacy_scan.py`: scans the repository surface.
- `scripts/quick_validate.py`: runs the release validation suite.

## 5. Use Modes

| Mode | Purpose | Data Rule |
|---|---|---|
| Public-safe demo mode | GitHub-visible demo and CI-style testing | Uses anonymized fixtures only. Not live market data. |
| BYO MCP provider response mode | User supplies a local provider response JSON | No network call. No credential read. Processes only the provided file. |
| Private internal local mode | Local team analysis with real provider data | Keep response and generated reports in ignored local folders. Do not commit. |

## 6. Privacy Modes

| `privacy_mode` | Use | Rule |
|---|---|---|
| `public_safe_real_world` | GitHub demo | Public category names and generic keywords may be present; competitors, ASINs, brands, and profit details are anonymized or template-level. |
| `strict_anonymized` | Strict sample | All market identifiers are generalized. |
| `private_internal` | Local internal analysis | Real provider data may appear in local reports; outputs must not be committed or publicly shared. |

## 7. Private Data Boundary

Public files must not include:

- user brands, user ASINs, user stores, account data, backend data
- real provider responses
- generated private reports
- raw review text
- complete real Top100 exports
- local machine paths
- private configuration files
- credentials, session data, or account identifiers
- internal provider locations

Real provider responses and generated private reports may only be saved in ignored local directories such as:

- `runtime/`
- `private/`
- `real_data/`
- `tmp/`
- `exports/`

## 8. Core Workflow

1. User runs their own local MCP / provider outside this repository.
2. User saves a provider response JSON in an ignored local folder.
3. `run_from_provider_response.py` normalizes the response.
4. Renderer generates HTML.
5. Markdown exporter generates Markdown.
6. Package builder creates ZIP.
7. Package validator verifies output structure and decision legality.
8. Privacy scanner verifies repository public-surface safety.

Public-safe demo mode uses the same pipeline with an anonymized fixture.

## 9. Scoring Model

The main 100-point scoring model stays fixed:

| Dimension | Points |
|---|---:|
| Demand capacity | 20 |
| Competition entry | 20 |
| Profit space | 20 |
| Differentiation opportunity | 15 |
| VOC painpoint opportunity | 10 |
| Keyword entry | 10 |
| Compliance and supply risk | 5 |

Decision thresholds:

- `80-100`: `enter`
- `65-79`: `cautious`
- `50-64`: `weak`
- `<50`: `no-enter`

Blocked packages do not use the score threshold as a market-entry decision.

## 10. Extended Judgment Fields

The model also supports:

- `market_stage`
- `new_product_ramp_difficulty`
- `entry_strategy`
- `voc_productization_score`
- `disqualifiers`
- `evidence_level`
- `competitor_clusters`
- `profit_space_detail`

If any disqualifier has `status=active` and `severity=critical`, `decision.label` must not be `enter`.

## 11. Required Outputs

Generated output directory must include:

- `product_selection_report.html`
- `product_selection_report.md`
- `product_selection_data.json`
- `source_manifest.json`
- `validation_result.json`
- `product_selection_delivery_package.zip`

`source_manifest.json` must indicate privacy mode, generation time, query summary, data blocks, confidence, blocked status, privacy flags, data freshness, delivery metadata, and sources.

## 12. Blocked States

Supported blocked states:

- `blocked_sorftime_unavailable`
- `blocked_no_data`
- `blocked_missing_fields`
- `blocked_fetch_failed`
- `blocked_invalid_input`
- `blocked_missing_site`
- `blocked_missing_product_type`
- `blocked_insufficient_competitors`

Blocked packages must still produce a complete package and pass the package validator.

## 13. Public-safe Requirements

The public-safe On-Ear Headphones fixture is a template sample:

- not live market data
- not a complete real Top100
- not a raw provider export
- not a real product-selection conclusion
- profit detail is template-level only and not a live margin estimate

## 14. Validation Requirements

Release validation must pass:

```bash
python scripts/run_public_safe_demo.py
python scripts/quick_validate.py
python scripts/privacy_scan.py .
```

`scripts/quick_validate.py` must run public-safe demo, blocked fixture package validation, package validator, and privacy scanner.

## 15. GitHub Release Boundary

GitHub may contain source code, contracts, schemas, templates, public-safe fixtures, public-safe examples, validation scripts, and release docs.

GitHub must not contain live provider responses, generated private reports, real ASIN lists, raw reviews, credentials, internal provider locations, account data, or complete real Top100 exports.
