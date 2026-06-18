# Validation Workflow

## Input

Generated package directory and optional privacy scan scope.

## Logic

1. Check required files.
2. Confirm HTML, Markdown, and JSON are UTF-8 readable.
3. Reject unresolved placeholders and corrupt question marks.
4. Validate decision label, blocked status, extended model fields, and source manifest.
5. Reject public-safe packages that contain private markers or real identifiers.
6. Reject private-internal packages that expose public shareable URLs.
7. Reject localhost or loopback as `shareable_url`.
8. Validate ZIP package contents when ZIP exists.
9. Run privacy scan on public repository scope.

## Output

`validation_result.json` and privacy scan result.

## Failure Reasons

Missing files, invalid JSON, missing sections, unsafe delivery URL, privacy leak, raw review text, raw export, or invalid package ZIP.

## Degradation

Do not mark the package successful. Return errors and remediation steps.
