# Contributing

Keep contributions public-safe by default.

Required checks:

```bash
python scripts/normalize_market_data_response.py fixtures/best_sellers_on_ear_headphones_us_public_safe.json --out dist/product_selection_data.json
python scripts/render_product_selection_report.py dist/product_selection_data.json --out dist/product_selection_report.html
python scripts/validate_product_selection_package.py dist
python scripts/privacy_scan.py .
```

Rules:

- Use `public_safe_real_world` for GitHub fixtures.
- Do not commit `dist/*.html` or `dist/*.json`.
- Do not commit private terms, real exports, credentials, internal endpoints, raw review text, or complete real Top 100 data.
- Keep competitor identifiers anonymized as `example_competitor_001`, `example_asin_001`, and `example_brand_a`.
- Keep Sorftime integration details in adapter contracts, not in public fixtures.
