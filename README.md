# Amazon Product Selection Research

BYO-MCP Skill Framework for Amazon product-selection research.

This repository does **not** include a live Sorftime MCP connector, credentials, network client, or provider runtime. Users bring their own local MCP / Sorftime-compatible provider, save a provider response JSON locally, and use this repository to normalize, render, package, validate, and privacy-scan the result.

## What This Repository Provides

- provider response contract examples
- public-safe fixtures and examples
- normalizer
- HTML renderer
- Markdown exporter
- ZIP package builder
- package validator
- privacy scanner
- one-command public-safe demo runner

## What This Repository Does Not Provide

- no live Sorftime MCP connector
- no MCP auth flow
- no provider credentials
- no network collection script
- no real provider response
- no private ASIN, brand, account, store, backend, or raw review data

Real provider responses must stay local in ignored directories such as `runtime/`, `private/`, or `real_data/`. Do not commit generated reports, private outputs, provider responses, credentials, account data, raw reviews, or complete real Top100 exports.

## Use Modes

### 1. Public-safe Demo Mode

Use the anonymized public-safe fixture to verify the full pipeline:

```bash
python scripts/run_public_safe_demo.py
```

Default output goes to `dist/`, which is ignored by Git.

The On-Ear Headphones fixture is a public-safe template sample. It is not live market data, not a complete real Top100, not a raw provider export, and not a real product-selection conclusion.

### 2. BYO MCP Provider Response Mode

Use your own local MCP / Sorftime-compatible provider outside this repository, save the response JSON in an ignored local folder, then run:

```bash
python scripts/run_from_provider_response.py runtime/provider_response.json --out-dir dist
```

This script does not connect to MCP, does not read credentials, and does not access the network. It only processes the local JSON you provide.

Expected response shape is documented in:

- `adapters/provider_response_contract.example.json`
- `adapters/sorftime_mcp_contract.example.json`

### 3. Private Internal Local Mode

Use `privacy_mode=private_internal` only for local or approved internal analysis. The generated report may contain real market identifiers from your provider response, so keep it outside GitHub unless your team has explicitly anonymized and approved it.

Private output rules:

- write provider responses to `runtime/`, `private/`, or `real_data/`
- write generated private reports to ignored local output folders
- do not commit real responses, reports, manifests, ZIP packages, or screenshots
- do not publish private reports to public static sites

## Output Deliverables

Each run produces:

- `product_selection_report.html`
- `product_selection_report.md`
- `product_selection_data.json`
- `source_manifest.json`
- `validation_result.json`
- `product_selection_delivery_package.zip`

Local preview URLs are validation-only. Share the ZIP package only through an approved public-safe or internal channel.

## Validation

Run the repository-level validation:

```bash
python scripts/quick_validate.py
```

This runs the public-safe demo, blocked fixture package checks, package validator, and privacy scanner.

Individual commands:

```bash
python scripts/validate_product_selection_package.py dist
python scripts/privacy_scan.py .
```

Expected result:

- package validator returns `ok=true`
- privacy scan returns `findings_count=0`
- quick validate returns `ok=true`

## GitHub Boundary

Publishable:

- source code
- schemas and contracts
- workflows and scoring rules
- templates
- anonymized fixtures and examples
- adapter contract examples
- release notes and team docs

Do not publish:

- `dist/`
- `runtime/`
- `tmp/`
- `private/`
- `real_data/`
- `exports/`
- private local configuration
- real provider responses
- private reports
- credentials or account data
- raw review text
- complete real Top100 exports
