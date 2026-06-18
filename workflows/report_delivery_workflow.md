# Report Delivery Workflow

## Input

Generated report directory containing HTML, Markdown, JSON data, source manifest, and validation result.

## Logic

1. Render offline HTML and Markdown.
2. Add delivery metadata to data package and manifest.
3. Mark local preview URL as local validation only.
4. Generate `product_selection_delivery_package.zip` with `README_OPEN_REPORT.txt`.
5. Keep `shareable_url` null unless an approved publishing target sets it.
6. For public-safe publishing, use only public-safe data and run validator plus privacy scan.
7. For internal publishing, require explicit user-provided internal target.

## Output

ZIP package, updated delivery metadata, validation result, and optional publish URL metadata.

## Failure Reasons

Missing report file, invalid package directory, unsafe shareable URL, private report marked public, missing README.

## Degradation

If publishing is not configured, set `publish_status=local_only` and return the ZIP path.
