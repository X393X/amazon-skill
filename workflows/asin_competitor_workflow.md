# ASIN Competitor Workflow

## Input

Marketplace, one ASIN or ASIN list, optional keyword/category context, and privacy mode.

## Logic

1. Validate ASIN-like input and marketplace.
2. Pull product detail, traffic terms, product trend, reviews summary, and competitor keyword data when available.
3. Build competitor matrix using relevance, category consistency, price band fit, review quality, rating stability, and audience/material match.
4. Identify review moat, brand concentration, organic ranking barrier, and new product ramp difficulty.
5. Create downstream Listing / image / A+ handoff brief only as planning input.

## Output

Competitor matrix, evidence table, VOC summary, ramp difficulty, risks, and handoff brief.

## Failure Reasons

Invalid ASIN, no product data, missing competitor fields, too few competitors, missing review summary.

## Degradation

If ASIN detail exists but reviews are missing, downgrade VOC to title/image/Q&A/category-level hypotheses and mark missing data.
