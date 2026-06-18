---
name: amazon-sorftime-product-selection-research
description: Use when the user asks for Sorftime-backed Amazon product selection, category research, product opportunity validation, market-entry decisions, competitor/VOC/keyword opportunity analysis, or HTML/Markdown product selection delivery packages.
---

# Amazon Product Selection Research

## 1. Purpose

Use this skill to turn Amazon category, keyword, ASIN, URL, or product idea inputs into a traceable product selection decision. The report combines Sorftime MCP live data or public-safe fixtures with market capacity, competitor structure, keyword opportunity, VOC pain points, trend signals, profit scenarios, risk checks, and a next validation plan.

Default evidence source is Sorftime MCP / Sorftime-compatible full market data. Public-safe fixtures are allowed only for template tests and GitHub-safe examples.

## 2. Scope

Use this skill for Amazon US, UK, and CA product selection work:

- keyword, ASIN, URL, category, Best Sellers page, or natural-language product idea input
- product selection screening and category opportunity decisions
- competitor structure and review moat analysis
- VOC pain point productization checks
- trending product signals
- downstream Listing / image / A+ handoff brief

## 3. Out of Scope

Do not use this skill to automate ads, inventory, purchasing, legal conclusions, certification claims, review creation, or final Listing publication. Do not publish `private_internal` reports publicly. Do not use public-safe fixtures to represent live market conclusions.

## 4. Core Goal

Produce a reproducible, verifiable, evidence-backed Amazon product selection decision report with clear blocked states, missing fields, scoring, risks, and next validation actions.

## 5. Final Deliverables

Generate these deliverables in the selected output directory:

- `product_selection_report.html`
- `product_selection_report.md`
- `product_selection_data.json`
- `source_manifest.json`
- `validation_result.json`
- `product_selection_delivery_package.zip`
- optional charts manifest when chart assets exist

Do not treat any local preview URL as an external delivery link. Use the HTML file path, ZIP package, or an explicitly configured public-safe/internal publishing target.

## 6. Success Criteria

A run is successful only when:

- data sources and tool calls are clear
- each key conclusion is traceable to evidence, assumptions, and missing data
- the 100-point scoring model is complete
- raw review text is not shown
- no token, secret, cookie, account, private endpoint, or private user data is leaked
- public-safe and private-internal boundaries are explicit
- `validate_product_selection_package.py` passes
- `privacy_scan.py .` passes for the public repository surface
- the run can be repeated from the same input and fixture/runtime data
- localhost or loopback URLs are not used as shareable delivery links

## 7. Input Contract

Read `contracts/input.schema.json` for the formal contract. Required fields are:

- `marketplace`: `US`, `UK`, or `CA`
- `input_type`: `asin`, `url`, `keyword`, `category`, `best_sellers`, or `natural_language`
- one primary object: `product_type`, `category_name`, `keyword`, `asin`, or `url`
- `task_type`: `product_selection`, `competitor_analysis`, `keyword_research`, `voc_analysis`, or `listing_handoff_brief`

Optional fields include brand, target price, target user, material, color, size range, existing images, competitor ASINs, keyword pool, category node ID, privacy mode, and report language.

Blocked states include `blocked_missing_site`, `blocked_missing_product_type`, `blocked_invalid_input`, `blocked_no_data`, `blocked_missing_fields`, `blocked_sorftime_unavailable`, `blocked_insufficient_competitors`, and `blocked_fetch_failed`.

When input is insufficient, output a TaskPlan or a blocked package with missing fields and remediation. Do not invent market conclusions.

## 8. Decision Router

Read `workflows/router_workflow.md` before running ambiguous inputs.

- URL or ASIN input routes to product dataset, competitor analysis, Listing handoff, or image planning brief.
- Keyword input routes to search dataset, keyword opportunity, competitor pool, VOC, and market opportunity.
- Best Sellers category input routes to category dataset and Top100 category opportunity report.
- Natural language input routes to intent parsing, missing-field check, TaskPlan, then user confirmation before execution.

Skill runs should plan before execution. If required input or evidence is missing, return a TaskPlan or blocked state.

## 9. Workflows

Workflow references live in `workflows/`:

- `category_selection_workflow.md`
- `keyword_research_workflow.md`
- `asin_competitor_workflow.md`
- `voc_analysis_workflow.md`
- `trending_products_workflow.md`
- `report_delivery_workflow.md`
- `validation_workflow.md`

Standard stages are input recognition, data check, dataset creation, competitor screening, keyword extraction, VOC analysis, trend signal judgment, profit scenarios and risk checks, report output, quality validation, and delivery packaging.

## 10. Evidence Layer

Keep facts, model inference, visible conclusions, and risk warnings separate. Expected files are:

- `product_selection_data.json` or `dataset.json`
- `evidence.json`
- `raw_summary.json`
- `scoring_result.json` or `scoring_result.xlsx`
- `product_selection_report.html`
- `product_selection_report.md`
- `validation_result.json`
- `source_manifest.json`

`source_manifest.json` must record data source, tools, generation time, sanitized parameter summary, missing fields, confidence, privacy mode, public-safe status, private-internal status, and delivery metadata.

`evidence.json` should contain `claims`, `sources`, `assumptions`, `missing_data`, and `confidence`.

## 11. Scoring

Do not change the main 100-point scoring model:

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

If a disqualifier has `status=active` and `severity=critical`, the decision label must not be `enter`; cap it at `cautious` or lower. Read `scoring/` for competitor, keyword, VOC, evidence, ramp, and data coverage rules.

## 12. Output Contract

HTML and Markdown reports must contain:

1. 执行摘要
2. 输入信息
3. 数据源状态
4. 类目容量判断
5. 关键词机会判断
6. 竞品结构判断
7. 价格带与利润判断
8. 评论 VOC 痛点判断
9. 差异化机会判断
10. 风险判断
11. 评分表
12. 选品结论
13. 证据表
14. 假设与缺失数据
15. 下一步验证动作
16. 下游 Listing / 图片 / A+ 交接 Brief
17. 交付说明 Delivery Notes

Fixed output fields include `data_coverage_score`, `profit_scenarios`, `ramp_path`, `voc_opportunity_matrix`, `validation_plan`, `trending_product_signals`, `voc_trend_summary`, `product_action_plan`, `optional_charts_manifest`, `report_delivery_package`, and `delivery`.

Delivery metadata must distinguish `local_preview_url`, `report_file_path`, `package_zip_path`, `public_safe_publish_url`, `internal_publish_url`, `publish_status`, `shareable_url`, and `shareable_url_scope` when applicable. Local preview URLs are for validation only.

## 13. Validation

Run validation from the skill directory:

```bash
python scripts/normalize_market_data_response.py fixtures/best_sellers_on_ear_headphones_us_public_safe.json --out dist/product_selection_data.json
python scripts/render_product_selection_report.py dist/product_selection_data.json --out dist/product_selection_report.html
python scripts/export_markdown_report.py dist/product_selection_data.json --out dist/product_selection_report.md
python scripts/package_report.py --input-dir dist --out dist/product_selection_delivery_package.zip
python scripts/validate_product_selection_package.py dist
python scripts/privacy_scan.py .
```

The validator checks required files, UTF-8 readability, missing sections, unresolved placeholders, decision legality, blocked status legality, extended model fields, public-safe boundaries, delivery URL safety, and ZIP package contents.

`privacy_scan.py .` scans the public repository surface and skips generated/private output directories by default. Use `--include-private-output` only for an explicit local private audit.

## 14. Failure Modes

Use blocked packages instead of fabricated conclusions:

- fetch failure: `blocked_fetch_failed`, ask for screenshot, workbook, or ASIN list
- missing fields: `blocked_missing_fields`, list required fields and tools
- insufficient competitors: `blocked_insufficient_competitors`, downgrade to user ASIN analysis
- insufficient reviews: downgrade to title, image, Q&A, or category evidence
- unconfirmed material: mark as `user_claimed_material`, not platform fact
- MCP unavailable: `blocked_sorftime_unavailable`, public-safe fixture may test the workflow but cannot produce a real conclusion

## 15. Risk Boundaries

Never fabricate reviews, certifications, legal clearance, platform facts, or raw data. Do not turn water-resistant into waterproof. Do not use competitor trademarks in Search Terms. Do not create infringement-prone brand terms. Do not claim PPE, protective footwear, CE, UKCA, ASTM, EN ISO, or similar compliance without evidence. Do not publish `private_internal` reports publicly. Do not commit real Sorftime raw responses.

For footwear visual or Listing handoff briefs: do not change shoe shape, invent logo placement, reverse zipper direction, invent outsole patterns, render children's shoes with adult proportions, call PU leather, or turn splash resistance into waterproof.

## Support Files

- Contracts: `contracts/`
- Workflows: `workflows/`
- Scoring rules: `scoring/`
- Examples: `examples/`
- Public-safe publishing notes: `adapters/publish_static.example.md`
