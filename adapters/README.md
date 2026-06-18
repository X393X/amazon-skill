# Adapters

Adapters document how a local BYO-MCP / Sorftime-compatible provider response should be mapped into this skill without exposing private implementation details.

This repository does not include a live connector, auth flow, credential reader, or network collection script. Users are responsible for connecting their own provider outside the repository and saving a local response JSON in an ignored folder.

Public files in this directory must not contain:

- Real user brands, ASINs, shops, account data, or backend data.
- Real provider responses.
- Internal provider locations.
- Credentials or session data.
- Raw review text.

Use `provider_response_contract.example.json` as the primary public-safe contract shape.

Use `sorftime_mcp_contract.example.json` as a Sorftime-compatible mapping example only.

`private_config.example.json` does not contain connection fields. It only documents where a local provider response may be stored. Real local configuration files must remain ignored by source control.

If a provider response is unavailable or incomplete, the skill must generate a blocked package. It must not use public web scraping, old files, fixtures, or hard-coded rows as a substitute for provider data.
