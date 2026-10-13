# Thiết lập Chrome DevTools MCP cho DMS Fast

## Dành cho Hermes máy nhận
Dùng khi plugin đã cài nhưng chưa dùng được, thiếu Chrome/Node/MCP, sai server binding hoặc chưa được cấp allowlist. Đây là hướng dẫn thiết lập có consent, không tự chạy lúc import/cài plugin. MCP chính thức của Google đã có tại https://github.com/ChromeDevTools/chrome-devtools-mcp ; repo DMS Fast không vendor node_modules, binary Chrome, tài khoản, cookie hoặc trust của tác giả. Gói dùng npm `chrome-devtools-mcp@1.10.1`, không thay bằng @latest trong luồng đã kiểm.

**Cài code ≠ cấu hình MCP ≠ được phép kết nối Chrome ≠ dùng DMS thành công.** Chỉ cấu hình hệ thống trong bước setup; không đọc tài liệu DMS để thử. Không kết luận máy thiếu dependency từ Python/PATH của máy khác, không cài lại plugin đã cài thành công, không reset pending/attempt/quota.

## 1. Xác định đúng máy và profile — chỉ kiểm
- Xác nhận OS/architecture, Hermes backend chạy ở đâu, Chrome chạy ở đâu, profile/home của recipient. Remote/SSH/WSL/container khác browser host không được giả như có cùng Chrome/filesystem.
- Dùng launcher/interpreter do installation Hermes sở hữu; kiểm PluginContext.call_mcp/get_config/register_tool/register_hook/register_command/register_skill, import mcp/pm và Doctor. Python 3.14.x là policy gói; không ép cài Python global, không raw pip/uv vào managed runtime.
- Node policy: 22 từ 22.12.0, 24 hoặc 26; khuyến nghị 24 LTS; npm phải có. npm engine của Google rộng hơn policy này. Kiểm version thực, không bắt máy khác đúng patch máy đóng gói.
- Google Chrome/CfT có UI; không bảo đảm mọi Chromium browser. Kiểm executable/version thực. AutoConnect chỉ là nhánh tùy chọn cho Chrome >=144 đã bật remote debugging và được user chấp thuận.
- Kiểm Agent enable đúng profile, tools `dms_fast_session` có trong chat và skill reading/setup có thể nạp. Desktop pane hiện không chứng minh Agent backend đã enable.
- Kiểm native MCP hiện có bằng supported CLI/UI; không in raw config, secrets hoặc credentials. Nếu có server phù hợp, ưu tiên tái dùng sau kiểm thay vì tạo trùng.

## 2. Chọn luồng cài — không trộn hai cách
### A. Helper có audit/integrity — ưu tiên khi chưa có MCP
Lấy ZIP sạch của release đã xác minh, giải nén vào thư mục mới của recipient; đọc START-HERE-HERMES và requirements trước. **Không chạy bootstrap CLI trong Git checkout/installed tree có .git hoặc host metadata:** bộ kiểm manifest ZIP hiện từ chối extra files. Không xóa .git/metadata hay bỏ kiểm hash để lách. ZIP v0.5.4 Native-LF vẫn có helper dùng được cho audit/deps/recipe; code/skill mới không bắt buộc cài lại bản cũ để dùng helper.

Các dấu ngoặc dưới đây là placeholder, recipient phải resolve đường dẫn thực, không chạy literal:
```text
<HERMES_PYTHON> <CLEAN_ZIP>/bootstrap.py audit --home <RECIPIENT_HOME>
```
`audit` không sửa config/cài phần mềm/mở Chrome. Xem facts/plan, báo thiếu gì và xin riêng quyền cài dependency trước khi chạy:
```text
<HERMES_PYTHON> <CLEAN_ZIP>/bootstrap.py deps --home <RECIPIENT_HOME> --approve-dependencies
<HERMES_PYTHON> <CLEAN_ZIP>/bootstrap.py recipe --home <RECIPIENT_HOME> --server chrome_dms_setup
```
Helper dùng public PM của installation cho Node/CfT khi thiếu; npm prefix `plugin-tools/dms-fast-setup` theo recipient home, version/SRI pin, ignore lifecycle scripts, kiểm realized-file receipts. `deps` không ghi connector/config và không chứng minh browser attachment. `recipe` chỉ trả DATA, chưa apply. Prefix đã có nhưng thiếu receipt/tamper thì dừng, không tự xóa. **Plugin đã cài: bỏ qua phase install/copy**, không overwrite nó.

### B. Native MCP UI + npm launcher — khi recipient chủ động chọn
Sau kiểm Node/npm/Chrome và grant cài package, resolve executable npx/npx.cmd bằng resolver của máy đó. Thêm **stdio/command server** qua Hermes MCP UI (không phải ô Repository để install plugin), tên mới chưa bị dùng. Command là path npx/npx.cmd thật; args là mảng token riêng, không shell-concatenate. Tham khảo args:
```json
["-y","chrome-devtools-mcp@1.10.1","--no-usage-statistics","--no-performance-crux","--no-javascript-evaluation","--no-source-maps","--categoryInput=true","--categoryDebugging=true","--categoryEmulation=false","--categoryPerformance=false","--categoryNetwork=false","--categoryMemory=false"]
```
Nhánh này tải theo npm/cache của recipient, không có realized-file receipt của helper A; không quảng cáo mức integrity tương đương A. Kiểm CLI version thật và schema. Nếu npx.cmd không launch được trong host, quay về helper A/Node + npm-cli.js của recipient sau consent, không raw shell bridge hay global install.

## 3. Chọn Chrome của chính recipient
Mặc định ưu tiên Chrome riêng có UI và profile persistent mới, không copy browser profile cũ. Với A, recipe sinh path Chrome/profile/cache thật từ audit. Với B, thêm `--executable-path=<CHROME_ACTUAL_PATH>`, `--user-data-dir=<RECIPIENT_PERSISTENT_PROFILE>` và `--filesystem-root=<RECIPIENT_APPROVED_CACHE>` bằng giá trị thực đã xác minh; tạo đúng thư mục mới sau consent. Không thêm --headless/--isolated/--slim/--no-page-id-routing/--allow-unrestricted-paths/--no-sandbox hoặc bỏ TLS.

Nếu user yêu cầu dùng Chrome đang mở: nhánh AutoConnect dùng `--autoConnect`, channel đúng (default stable), user tự bật chrome://inspect/#remote-debugging và bấm Allow. AutoConnect có thể vào default profile do Chrome chọn và thấy mọi cửa sổ của profile đó; phải xác minh/được user chọn, không hứa origin sandbox. Không ghép nhánh autoConnect với recipe launched-profile hoặc endpoint/debug port của tác giả. Không restart/đóng Chrome/MCP đang có để ép kết nối. Manual port/remote host cần kế hoạch riêng; không đoán port cố định.

## 4. Config và quyền — grant riêng, đọc lại exact target
MCP entry phải ở `mcp_servers.<SERVER>` của đúng profile Hermes, **không dùng root mcpServers** trong ví dụ generic Google. Giữ enabled theo quyết định recipient, trust=untrusted, parallel=false, sampling/elicitation=false; tools.include là 7 tên nguyên gốc:
`list_pages`, `new_page`, `take_snapshot`, `navigate_page`, `fill`, `press_key`, `click`; resources/prompts=false. JavaScript/telemetry/CrUX/sourceMaps tắt như args trên. Không đặt include bằng tên đã sanitize mcp__... . Server filtering và trust không thay website ACL.

Nếu dùng A: sau grant config/connector, private snapshot config, tạo đúng create_after_consent và apply riêng recipe.connector bằng supported config CLI/UI. Nếu dùng B: đặt các policy trên trong UI/CLI, kiểm lại entry đã lưu. Không sửa YAML tay, không set toàn bộ mcp_servers, không sao chép credentials.

Trong scope profile/backend đã resolve (helper --home không tự đổi scope CLI), xin quyền plugin gọi MCP rồi apply/read-back:
```text
hermes config set plugins.entries.dms-fast.settings.mcp_server <SERVER_LITERAL>
hermes config get plugins.entries.dms-fast.settings.mcp_server --json
hermes config set plugins.entries.dms-fast.mcp_allowlist <JSON_ARRAY_OF_EXACT_SERVER_KEY>
hermes config get plugins.entries.dms-fast.mcp_allowlist --json
```
Scalar server name không bọc thêm JSON quote; array mới serialize JSON. Ví dụ server chrome_dms_setup thì allowlist chỉ ["chrome_dms_setup"]. Tên không bắt buộc giống máy tác giả nhưng setting/entry/allowlist phải nhất quán. Không tự nâng trust full. User tự approve MCP/Chrome; từ chối/hết hạn approval là pending, không bypass.

## 5. Enable, handshake, schema — chưa đọc DMS
Sau grant enable: `hermes plugins enable dms-fast --no-allow-tool-override` đúng scope. Đọc lại plugins.enabled. Doctor: `hermes plugins doctor dms-fast --ci`. Validator dùng **installed directory path**: `hermes plugins validate <INSTALLED_PLUGIN_DIR> --json`, không lấy cú pháp ID của Doctor thay thế. `hermes mcp test <SERVER>` là handshake/schema, không browser login hoặc full site acceptance. Kiểm 7 tools và pageId routing theo plugin contract.

Chỉ làm reload/new chat đúng cơ chế host sau consent. /reload-mcp có thể ảnh hưởng các server khác; không restart tất cả flow đang chạy. Backend mới/skill mới có thể cần session mới, không coi file edited là active runtime đã đổi. Thiếu quyền hoặc tools/schema không tương thích thì giữ pending và báo đúng gate.

## 6. Tiêu chí sẵn sàng và chẩn đoán
- Package launch/version: PASS không đồng nghĩa MCP handshake PASS.
- Handshake/tools: PASS không đồng nghĩa Chrome đã attach/đăng nhập.
- Các key setting/allowlist/enable có read-back và đúng recipient/profile.
- Khi user riêng cho phép website và LLM policy: nạp dms-fast:reading, **chỉ dms_fast_session prepare** với canonical home hoặc bounded search. inspect không bootstrap Chrome. Login/SSO/2FA và quota là pending bình thường; không hủy việc lạ/reset/retry tải. Không dùng raw MCP/CDP/browser khác để thử DMS hoặc vượt guard.
- Chỉ báo ready khi scope user muốn dùng đã đo bằng executor và read-back. Setup guide không chứng nhận physical recipient/OS/ACL hoặc sửa mọi lỗi. WinError 5 publication/rename, long-path cold PM, DLL/system library/proxy/CA, schema drift: báo exact sanitized error, không ép fix core/registry/force.
- Log bàn giao không có password/cookie/token/OTP/raw config; nội dung browser có thể tới LLM/history/log của recipient, không hứa zero egress.

## Nguồn chính thức
- https://github.com/ChromeDevTools/chrome-devtools-mcp
- https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/chrome-devtools-mcp-v1.10.1/README.md
- https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/chrome-devtools-mcp-v1.10.1/docs/configuration.md
- https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/chrome-devtools-mcp-v1.10.1/docs/advanced-usage.md
- https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins#bundle-skills
- https://hermes-agent.nousresearch.com/docs/getting-started/installation
