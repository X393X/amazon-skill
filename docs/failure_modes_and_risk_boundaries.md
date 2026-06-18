# Failure Modes And Risk Boundaries

## Failure Modes

| Scenario | Status | Response |
|---|---|---|
| Missing marketplace | `blocked_missing_site` | Ask for US, UK, or CA. |
| Missing product object | `blocked_missing_product_type` | Ask for product type, category, keyword, ASIN, or URL. |
| Invalid input | `blocked_invalid_input` | Return accepted input types and required fields. |
| Fetch failure | `blocked_fetch_failed` | Ask for screenshot, workbook, ASIN list, or retry data source. |
| No data | `blocked_no_data` | Return blocked package and next data tool calls. |
| Missing fields | `blocked_missing_fields` | List missing fields and remediation tools. |
| Provider response unavailable | `blocked_sorftime_unavailable` | Use public-safe fixture only to test workflow, not to make real conclusions. |
| Insufficient competitors | `blocked_insufficient_competitors` | Downgrade to user ASIN analysis or request more competitors. |

## Risk Boundaries

- Do not fabricate reviews, certification, legal clearance, or platform facts.
- Do not show raw review text in reports.
- Do not publish private-internal reports publicly.
- Do not commit raw provider responses.
- Do not use competitor trademarks as Search Terms.
- Do not turn water-resistant into waterproof.
- Do not claim CE, UKCA, ASTM, EN ISO, PPE, or protective footwear without evidence.

## Footwear Visual Handoff Boundaries

- Keep shoe shape unchanged.
- Do not invent logo placement.
- Do not reverse zipper direction.
- Do not invent outsole pattern.
- Do not render children's shoes with adult proportions.
- Do not call PU leather.
- Do not turn splash resistance into waterproof.
