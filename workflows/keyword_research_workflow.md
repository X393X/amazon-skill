# Keyword Research Workflow

## Input

Marketplace, keyword, optional category node ID, optional keyword pool, and privacy mode.

## Logic

1. Validate keyword and marketplace.
2. Pull keyword detail, keyword extensions, keyword search results, and trend data when available.
3. Classify keywords into core terms, product terms, attributes, audience, scenario, material, seasonal, problem, long-tail conversion, and competitor-title terms.
4. Score keyword entry by volume, competition proxy, CPC, search result density, seasonality, and relevance.
5. Build competitor pool and VOC bridge when keyword search results provide products.

## Output

Keyword metrics, keyword opportunity table, search result competitor pool, trend signal summary, validation plan.

## Failure Reasons

Missing keyword, no keyword metrics, unsupported tool, empty search result set, unavailable Sorftime.

## Degradation

If trend data is missing, keep keyword opportunity but lower confidence and list `keyword_trend` as required validation.
