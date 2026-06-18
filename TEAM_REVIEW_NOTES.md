# Team Review Notes

## Repository Positioning

`amazon-sorftime-product-selection-research` is now a BYO-MCP Skill Framework. It does not include a real Sorftime MCP connector, provider client, auth flow, credential reader, or network collection script.

Teams bring their own local MCP / Sorftime-compatible provider, save a provider response JSON locally, then use this repository to normalize, render, package, validate, and privacy-scan the result.

## What It Solves

- Amazon category and product-selection decision reports
- competitor, keyword, VOC, trend, price, and risk synthesis
- fixed 100-point decision scoring
- blocked package generation when data is unavailable or incomplete
- HTML / Markdown / JSON / ZIP delivery packages

## Use Modes

### Public-safe demo mode

Run the anonymized fixture:

```bash
python scripts/run_public_safe_demo.py
```

This proves the pipeline, but it is not live market data and not a real selection conclusion.

### BYO MCP provider response mode

Run your own local provider outside this repository, save the response JSON in an ignored local directory, then run:

```bash
python scripts/run_from_provider_response.py runtime/provider_response.json --out-dir dist
```

The script does not connect to MCP, does not read credentials, and does not access the network.

### Private internal local mode

Use `privacy_mode=private_internal` only for local or approved internal analysis. Keep real provider responses and private reports outside GitHub.

## Input Contract

Provider response shape is documented in:

- `adapters/provider_response_contract.example.json`
- `adapters/sorftime_mcp_contract.example.json`

The response should provide market capacity, keywords, competitors, price/profit summary, VOC summary, differentiation notes, risks, scoring inputs, and source metadata. If required data is missing, the package should use a blocked status instead of fabricating conclusions.

## Output Deliverables

- `product_selection_report.html`
- `product_selection_report.md`
- `product_selection_data.json`
- `source_manifest.json`
- `validation_result.json`
- `product_selection_delivery_package.zip`

Do not send localhost, loopback, or local file URLs as team share links. Share ZIP packages only through approved internal or public-safe channels.

## GitHub Boundary

GitHub should include source code, schemas, contracts, workflows, scoring rules, templates, anonymized fixtures, examples, adapters, docs, and release notes.

GitHub must not include:

- generated `dist` outputs
- `runtime`, `tmp`, `private`, `real_data`, or `exports`
- private local configuration
- real provider responses
- real business reports
- real ASIN lists
- raw review text
- complete real Top100 exports
- credentials, account data, or internal provider locations

## Validation

Run before review:

```bash
python scripts/quick_validate.py
```

Expected result:

- public-safe demo passes
- blocked fixtures pass package validation
- package validator returns `ok=true`
- privacy scan returns `findings_count=0`

## Next Steps

- reviewers run `python scripts/quick_validate.py`
- reviewers inspect `dist/product_selection_report.html` from the public-safe demo
- private internal tests use ignored local directories only
- keep live provider collection outside this repository
