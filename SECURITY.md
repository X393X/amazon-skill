# Security Policy

This skill supports public-safe template tests and local `private_internal` Sorftime MCP analysis. Public files must never include user private data, raw Sorftime exports, raw review text, credentials, accounts, endpoint secrets, or internal endpoints.

Sensitive files must stay local and ignored by source control:

- `private_config.local.json`
- `*.local.json`
- `private_terms.txt`
- `dist/*.html`
- `dist/*.json`
- `runtime/`
- `real_data/`
- `exports/`
- `private/`
- `secrets/`
- `.env`
- `.env.*`

Real MCP tokens must be read from environment variables such as `SORFTIME_MCP_TOKEN`. Do not write tokens, cookies, passwords, API keys, account identifiers, endpoint secrets, raw Sorftime responses, raw review text, or real business reports into public files.

Before publishing, run:

```bash
python scripts/privacy_scan.py .
```

If a public file contains private data, remove the data, rotate any affected credential outside this repository, and regenerate only the public-safe fixture package.
