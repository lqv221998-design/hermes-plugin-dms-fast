# Sources and evidenced routes

Read-only navigation allowlist (not an authorization sandbox):
- `https://dms.newtecons.vn/`: home.
- `https://dms.newtecons.vn/document/list`: document grid, observed research snapshot; StaticText names do not guarantee clickable links.
- `https://dms.newtecons.vn/document/dept`: link observed in document grid; route allowed, not a claim all department workflows passed.
- `https://dms.newtecons.vn/document/site`: live menu route read-back observed with 0.5.1; not a full inventory or project-content acceptance.
- `https://dms.newtecons.vn/schedule/booking`: live read-view route observed with 0.5.1; no meeting/vehicle reservation created or tested.
- Exact menu labels are recipes, not generic click authorization. Home, departments, sites, charts, grid and booking have live route observations in the recipient report; guides and two catalogue/handbook controls remain unverified targets. Do not turn a catalogue link into a download action.
- `/document/detail/<lowercase UUID>`: canonical document source. Reject query, fragment, userinfo, explicit port, percent-encoding and host lookalikes.

Verified example, not universal default or automatic test target:
https://dms.newtecons.vn/document/detail/cab9eb52-bb54-4e32-ba4a-766717c488ac
QT-KT-07 — Quy trình lập hồ sơ quản lý chất lượng công trình; lần ban hành 1, hiệu lực 21/12/2022, Còn hiệu lực as observed 2026-10-08. Reverify for every substantive answer.

## Engineering sources
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins — register_tool, register_command, register_skill, native call_mcp grant and host client.
- https://hermes-agent.nousresearch.com/docs/developer-guide/desktop-plugin-sdk — standalone ESM, host.composer, palette/routes/nav and UI imports.
- https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference — trust, native tool include names and lifecycle.
- https://github.com/ChromeDevTools/chrome-devtools-mcp/tree/v1.10.1 — installed MCP pin; this package does not replace or restart it.

Implementation checked against installed PluginContext.call_mcp and register_skill source; no private MCP handler import in plugin code. Data observations are not a guarantee of business-content completeness.
