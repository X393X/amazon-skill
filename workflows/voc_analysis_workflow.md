# VOC Analysis Workflow

## Input

Marketplace, ASIN list or competitor matrix, optional review summary, and privacy mode.

## Logic

1. Confirm reviews or review summaries exist.
2. Keep only summary themes and counts; never expose raw review text.
3. Weight high-frequency, low-star, recent, image-attached, repeated, and cross-competitor complaints.
4. Score productization by feasibility, willingness to pay, cost impact, listing visibility, and productization score.
5. Convert pain points into product actions, page expression, validation method, and priority.

## Output

VOC productization score, VOC opportunity matrix, product action plan, VOC trend summary, evidence and missing data.

## Failure Reasons

No reviews, raw review export only, missing ASIN context, or insufficient competitor coverage.

## Degradation

If reviews are insufficient, use title/image/Q&A/category-level evidence as lower-confidence assumptions and require review follow-up.
