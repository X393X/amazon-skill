# Category Selection Workflow

## Input

Marketplace, category name or category node ID, category scope, privacy mode, and report language.

## Logic

1. Recognize category or Best Sellers input.
2. Verify Sorftime availability or fixture mode.
3. Build category dataset from category metrics, Top products, price bands, competitor fields, trend signals, and risk flags.
4. Screen competitors by relevance, category fit, price band, review count, rating, and product positioning.
5. Extract category keywords and keyword trend signals when available.
6. Summarize VOC from review summaries without raw review text.
7. Build profit scenarios, ramp difficulty, disqualifiers, and validation plan.
8. Render report and package delivery ZIP.

## Output

`product_selection_data.json`, HTML report, Markdown report, manifest, validation result, delivery ZIP, evidence summary.

## Failure Reasons

Sorftime unavailable, no category data, missing Top product fields, insufficient competitor count, missing trend or keyword fields.

## Degradation

If competitor count is insufficient, return `blocked_insufficient_competitors`. If only category summary exists, output partial analysis with missing fields and require follow-up tools.
