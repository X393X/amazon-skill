# Optional Feishu Delivery Adapter

This document is an example contract only. It does not perform authentication,
does not publish documents, and does not include real private configuration.

## Boundary

- HTML remains the primary report.
- Markdown is an auxiliary export for external handoff.
- Feishu delivery is optional and must be enabled by a separate local adapter.
- Local adapters must read credentials from the operator environment and must
  not write private configuration into the skill package.

## Expected Inputs

- `dist/product_selection_report.html`
- `dist/product_selection_report.md`
- `dist/product_selection_data.json`
- `dist/source_manifest.json`
- `dist/validation_result.json`
- Optional `dist/optional_charts_manifest.json`

## Delivery Rules

- Do not upload raw Sorftime responses.
- Do not upload raw review text.
- Do not upload runtime files.
- Do not upload private configuration files.
- Preserve the `privacy_mode` warning in the delivered document.
- For `private_internal`, label the document as local internal analysis and not
  suitable for public repository use.

## Suggested Local Adapter Contract

```json
{
  "input_markdown": "dist/product_selection_report.md",
  "input_html": "dist/product_selection_report.html",
  "source_manifest": "dist/source_manifest.json",
  "validation_result": "dist/validation_result.json",
  "privacy_mode": "private_internal",
  "publish": false
}
```
