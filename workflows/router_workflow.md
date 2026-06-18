# Decision Router Workflow

## Input

Accept `asin`, `url`, `keyword`, `category`, `best_sellers`, or `natural_language` inputs that satisfy `contracts/input.schema.json`.

## Logic

1. Identify input type and marketplace.
2. Check required fields.
3. Build a TaskPlan when natural language or incomplete input needs user confirmation.
4. Route URL or ASIN to product dataset and competitor workflow.
5. Route keyword to keyword research and competitor pool workflow.
6. Route Best Sellers category to category dataset and Top100 opportunity workflow.
7. Route VOC-specific requests to VOC workflow.
8. Route delivery-only requests to report delivery workflow.

## Output

TaskPlan, selected workflow name, required data blocks, expected files, and blocked status when applicable.

## Failure Reasons

Missing marketplace, missing product type/object, invalid input, unavailable Sorftime, no data, missing fields, or insufficient competitors.

## Degradation

Return a blocked package with missing fields and next tool calls. Do not run a live analysis from public-safe fixtures.
