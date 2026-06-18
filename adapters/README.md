# Adapters

Adapters document how a real Sorftime MCP / Sorftime-compatible MCP response should be mapped into this skill without exposing private implementation details.

Public files in this directory must not contain:

- Real user brands, ASINs, shops, account data, or backend data.
- Raw Sorftime exports.
- Internal MCP endpoints.
- Credentials or session data.
- Raw review text.

Use `sorftime_mcp_contract.example.json` as a public-safe contract shape only.

Use `private_config.example.json` as a template for local private configuration. A real file should be named `private_config.local.json`, must stay ignored by source control, and must not contain a token. Real tokens are read from environment variables such as `SORFTIME_MCP_TOKEN`.

If a provider adapter cannot return live data, the skill must generate `blocked_sorftime_unavailable`; it must not use public web scraping, old files, fixtures, or hard-coded rows as a substitute for Sorftime data.
