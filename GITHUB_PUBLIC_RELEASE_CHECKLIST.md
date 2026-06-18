# GitHub Public Release Checklist

## Release Mode

- Target version: `v0.2`
- Default test mode: `public_safe_real_world`
- Primary report: `dist/product_selection_report.html`
- Auxiliary report: `dist/product_selection_report.md`
- GitHub release package must include source, templates, schemas, fixtures, examples, and docs only.

## Allowed To Submit

- `SKILL.md`
- `README.md`
- `PRD.md`
- `LICENSE`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `.gitignore`
- `schemas/`
- `scripts/`
- `templates/`
- `fixtures/`
- `examples/`
- `adapters/`
- `private_terms.example.txt`
- `RELEASE_NOTES_v0.2.md`
- `GITHUB_PUBLIC_RELEASE_CHECKLIST.md`

## Must Not Submit

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
- real provider response files
- `private_internal` real HTML reports
- `private_internal` real JSON packages
- `private_internal` real Markdown reports
- real source manifests from private analysis
- real complete Top100 details
- real business reports
- credential, session, account, or key material
- user private brand, ASIN, store, backend data, or account identifiers
- raw review text

## Required Checks Before Publishing

Run from the skill root:

```bash
python scripts/run_public_safe_demo.py
python scripts/quick_validate.py
python scripts/privacy_scan.py .
```

## Public-Safe Output Requirements

- `privacy_mode` must be `public_safe_real_world`.
- Report and Markdown must state that the On-Ear Headphones fixture is a public-safe template sample.
- Output must not contain private-internal runtime data.
- Output must not contain raw provider responses.
- Output must not contain complete real Top100 exports.
- Output must not contain raw review text.
- Output must not contain credential, session, account, or key material.
- Output must not contain user private brand, ASIN, store, backend data, or account identifiers.
- Output must not contain unresolved placeholders or `???`.
- Validator must pass.
- Privacy scan must pass.
- Quick validate must pass.

## GitHub Submit Decision

Submit only after all checks pass and after confirming that generated `dist/`, `runtime/`, and `tmp/` outputs are ignored by source control.
