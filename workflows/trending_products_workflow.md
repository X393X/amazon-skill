# Trending Products Workflow

## Input

Marketplace, category or keyword dataset, competitor matrix, trend data, and privacy mode.

## Logic

1. Detect low-review high-sales products, new product share, rising keywords, seasonality, and demand changes.
2. Separate seasonal spikes from sustained growth.
3. Mark market stage as growth, mature, price war, seasonal, declining, or unknown.
4. Connect trend signals to entry strategy and ramp path.

## Output

Market stage, trending product signals, ramp path, entry strategy, and validation plan.

## Failure Reasons

Missing trend data, missing product age/review/sales fields, no keyword trend, or unreliable data.

## Degradation

If trend data is missing, set market stage to `unknown` or use category proxy with lower confidence.
