# Security Policy

This repository is a BYO-MCP framework. It does not include a real Sorftime MCP connector, provider client, credential reader, or network collection script.

Users must connect their own local MCP / Sorftime-compatible provider outside this repository. This repository only processes local provider response JSON files that the user supplies.

## Public Repository Boundary

Public files may include source code, schemas, templates, public-safe fixtures, public-safe examples, provider response contract examples, validators, and docs.

Public files must never include:

- real provider responses
- generated private reports
- user brands, user ASINs, stores, account data, or backend data
- raw review text
- complete real Top100 exports
- private configuration
- credentials or session data
- internal provider locations
- local machine paths

## Ignored Local Directories

Sensitive local files must stay in ignored directories:

- `runtime/`
- `private/`
- `real_data/`
- `tmp/`
- `exports/`
- `secrets/`
- `dist/`

Local private term files and private configuration files must also stay ignored.

## Safe Execution Rules

- `scripts/run_public_safe_demo.py` uses only public-safe fixtures.
- `scripts/run_from_provider_response.py` does not connect to MCP, does not read credentials, and does not access the network.
- `scripts/privacy_scan.py` scans the repository public surface and skips ignored output directories by default.
- private reports must remain local or in approved internal systems.

## Required Checks

Before publishing, run:

```bash
python scripts/quick_validate.py
python scripts/privacy_scan.py .
```

Expected result:

- quick validation returns `ok=true`
- privacy scan returns `findings_count=0`

If a public file contains private data, remove the data, rotate any affected credentials outside this repository, and regenerate only public-safe outputs.
