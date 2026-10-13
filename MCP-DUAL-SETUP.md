# Cài cả DMS MCP và Web MCP trên Hermes máy khác

## Hai connector, một package chính thức
Cả `chrome_dms_setup` và `chrome_web` dùng **Google chrome-devtools-mcp@1.10.1**, không phải hai sản phẩm/npm khác nhau. Repo này có helper, hai guide và template cấu hình; không vendor binary/node_modules/account/profile/trust của tác giả. Link MCP: https://github.com/ChromeDevTools/chrome-devtools-mcp .

| Thành phần | DMS connector | Web tổng quát |
|---|---|---|
| Native key mẫu | chrome_dms_setup | chrome_web |
| Tools policy | 7 tools UI tối thiểu | 16 tools UI cho website được phép |
| Default Chrome profile | browser-profiles/dms-fast-setup | browser-profiles/chrome-web-setup |
| Default filesystem cache | cache/dms-fast-setup | cache/chrome-web-setup |
| Plugin binding | dms-fast chỉ gọi server DMS này | Không cấp cho dms-fast |
| Website flow | dms_fast_session/skill DMS hiện hành | Native chrome_web, per-action scope/ACL |
| Package/executable MCP | Một pinned npm prefix của recipient, có receipt | Reuse cùng entry point, không cài npm lần nữa |

Tên server có thể khác mẫu nhưng distinct và setting/allowlist phải khớp. Không ghi đè connector hiện có hoặc dùng web bypass DMS/QAQC denial/pending/quota. No domain filter ở web không là quyền đọc mọi tab hoặc bảo đảm mọi site.

## Bước 1 — Kiểm trước, chưa thay đổi
Xác định profile/home/backend và host Chrome của người nhận; remote/container/WSL khác host cần plan riêng. Đọc requirements/START-HERE và hai guide:
- MCP-CHROME-SETUP.md hoặc skill dms-fast:setup.
- MCP-WEB-SETUP.md hoặc skill dms-fast:web-setup (từ 0.5.6).

Python/runtime Hermes do owner launcher quản lý; không raw pip/uv. Kiểm Node/npm/Chrome thật, không lấy path máy tác giả. Máy cài plugin thành công **không cài lại/copy-overwrite** để chữa thiếu MCP. Cần grant riêng cho dependencies, connector/config/allowlist, plugin enable và Chrome/website; không auto trust/full hay auto-login.

## Bước 2 — Cài dependency một lần, sinh recipe cho cả hai
Dùng ZIP release 0.5.6 sạch, kiểm SHA256, giải nén thư mục mới. Strict ZIP helper không hỗ trợ extra .git/host metadata; không chạy trong Git-installed tree hoặc xóa metadata/bỏ integrity để lách. <> là placeholder, phải resolve actual path/scope recipient:
```text
<HERMES_PYTHON> <CLEAN_ZIP>/bootstrap.py audit --home <RECIPIENT_HOME>
<HERMES_PYTHON> <CLEAN_ZIP>/bootstrap.py deps --home <RECIPIENT_HOME> --approve-dependencies
<HERMES_PYTHON> <CLEAN_ZIP>/bootstrap.py recipe-both --home <RECIPIENT_HOME> --server chrome_dms_setup --web-server chrome_web
```
Audit không cài software/config/browser; xin grant dependency rồi mới deps. Deps lấy package pin/SRI, no lifecycle scripts, prefix/cache riêng của recipient, realized-file receipt/tamper rejection. Reuse nếu đủ; incomplete/tamper thì dừng. Recipe-both là **DATA chưa apply**, không tạo Chrome/config/grant và ready_to_use=false.

Output có `connectors` gồm hai entry path đã audit, `create_after_consent` gồm 4 thư mục riêng, `dms_plugin_settings` chỉ chứa DMS server, `shared_mcp_package`. JSON MCP-CONNECTORS.template.json trên repo chỉ là mẫu với placeholders, không chạy/apply literal.

## Bước 3 — Apply riêng đúng scope, không phá các flow cũ
Sau grant connector/config, private snapshot config của recipient; không xuất backup/secrets. Kiểm key collision, chủ sở hữu profile/cache; tạo đúng thư mục mới sau consent. Scope native Hermes CLI/UI phải đúng profile/backend; helper --home không tự đổi scope CLI.

```text
hermes config set mcp_servers.chrome_dms_setup <JSON_FROM_RECIPE.connectors.chrome_dms_setup>
hermes config get mcp_servers.chrome_dms_setup --json
hermes config set mcp_servers.chrome_web <JSON_FROM_RECIPE.connectors.chrome_web>
hermes config get mcp_servers.chrome_web --json
hermes config set plugins.entries.dms-fast.settings.mcp_server chrome_dms_setup
hermes config get plugins.entries.dms-fast.settings.mcp_server --json
hermes config set plugins.entries.dms-fast.mcp_allowlist '["chrome_dms_setup"]'
hermes config get plugins.entries.dms-fast.mcp_allowlist --json
```
Đây là ví dụ với keys mặc định; dùng exact keys đã chọn. Serialize object/list như JSON; scalar server literal không bọc thêm JSON quotes. Trên PowerShell/cmd/bash kiểm quoting theo shell thật, không copy shell syntax sai môi trường. Không set lại toàn mcp_servers, không manual YAML. Đọc lại từng entry và so sánh toàn unrelated config với private before. Hai entry giữ untrusted, no parallel/sampling/elicitation/resources/prompts, JS/telemetry/CrUX/sourceMaps off. Các write site phải user cho phép riêng.

## Bước 4 — Enable/handshake và actual runtime, chưa suy là dùng được
Grant enable plugin riêng, `hermes plugins enable dms-fast --no-allow-tool-override` đúng scope; đọc lại plugins.enabled. Doctor theo ID, validator theo installed directory path. Test handshake cả hai:
```text
hermes mcp test chrome_dms_setup
hermes mcp test chrome_web
```
Kiểm runtime filter/schema/actual chat tools. Handshake không mở Chrome theo default lazy browser của Google và không chứng minh login. Reload/new chat theo host sau consent, không restart mọi server hoặc đóng Chrome flow khác. Tool thiếu/mismatch/approval timeout thì pending.

Default hai browser persistent có UI riêng; mỗi người tự login/ACL. Nếu chủ động muốn web dùng Chrome đang mở, xem AutoConnect >=144 + user bật remote debugging/Allow trong MCP-WEB-SETUP. Không ghép mù launched profile và autoConnect hoặc dùng port/endpoint tác giả.

## Bước 5 — Nghiệm thu riêng từng scope khi được yêu cầu
Web: dùng đúng native chrome_web với website public/user chọn và action được phép, read-back kết quả, không tự inspect tab nhạy cảm. DMS đọc/search/metadata: dms-fast:reading và chỉ dms_fast_session prepare với canonical home/bounded search; inspect không bootstrap. Download/handoff tuân theo skill/standing policy DMS hiện hành; web không là fallback. QAQC giữ qaqc_fast_session/exact project. Login/SSO/2FA/quota/denial là pending, không reset/replay/cancel việc lạ.

Chỉ báo cả hai ready khi các gate của cả hai đã đo. Cài cả hai không sửa ACL, mọi lỗi Windows/PM/long paths/proxy/schema hay tự cấp quyền. Không mở/tải tài liệu DMS lúc setup. Chưa có physical recipient/cross-OS certification, không quảng cáo zero egress hoặc sandbox. Cần company-approved LLM/history/retention.

## Prompt đưa cho Hermes máy nhận
“Đọc MCP-DUAL-SETUP.md và hai guide DMS/Web trong gói. Kiểm đúng profile/backend/host và prerequisites; báo thiếu gì rồi xin quyền. Cài pinned package một lần và lập recipe cho hai connector riêng; giữ server cũ, DMS binding chỉ DMS, không tự trust/login/reinstall hoặc đọc tài liệu DMS. Apply từng key bằng native CLI/UI sau grant, đọc lại exact config; test handshake/schema từng connector và báo pending/verified riêng.”

Nguồn: Google chrome-devtools-mcp tag chrome-devtools-mcp-v1.10.1 README/configuration/advanced-usage; https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference .
