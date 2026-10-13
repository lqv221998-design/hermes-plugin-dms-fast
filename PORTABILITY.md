# DMS Fast 0.5.2 — hợp đồng cài đặt và nghiệm thu đa máy

## 1. Một gói chung, không sao chép một máy đã đăng nhập

Gói chứa code Python, manifest, bundled skill, pane tùy chọn, tests và tài liệu. Cùng các file này được cài trên máy người nhận; không sửa code theo tên người dùng, ổ đĩa, hostname hoặc vị trí repo.

| Dùng chung | Người nhận tự cấu hình/nghiệm thu |
|---|---|
| Workflow/session, policy nguồn DMS Newtecons | Hermes build/public API, profile-home |
| Hook routing, schema tool, quota policy | Native MCP server và quyền/approval riêng |
| Search/one-file/file-check code | Chrome, persistent user-data-dir của chính người nhận |
| Skill hướng dẫn và pane user-click single-submit | Tài khoản DMS/ACL/mạng công ty, human login |
| Tests và hướng dẫn | Chrome download_dir, project output_dir trên host thực thi |

Không đóng gói config.yaml, .env, secrets, browser profile, cookie/token/storage, plugin state, session chat, inventory hay tài liệu công ty. Runtime state/receipt bàn giao có dữ liệu công việc và đường dẫn local: giữ tại profile/dự án của người nhận, không đưa vào ZIP chung.

Domain/route DMS là policy ứng dụng công ty dùng chung, không địa chỉ máy phát triển. Khả chuyển giữa máy không có nghĩa tự hoạt động trên mọi website.

## 2. Các môi trường và điều kiện

- Windows, macOS, Linux là các nền tảng mục tiêu. Bản này đã chạy local trên Windows; chưa chạy native trên macOS/Linux hoặc máy vật lý thứ hai. Không được gắn nhãn các môi trường chưa đo là PASS.
- Backend Python chỉ dùng stdlib; dùng interpreter của Hermes để chạy kiểm và bảo đảm public API tương thích. Không đoán một minimum Hermes version từ trí nhớ: chạy Doctor/validator và kiểm host hooks thật.
- Hermes cần get_config/call_mcp/register_tool/register_hook/register_command/register_skill, state get/set theo profile, pre_tool_call block/approve semantics. Tool registrations hoặc manifest không chứng minh middleware thực sự chặn runtime.
- Pane cần Hermes Desktop SDK/React/composer. CLI không dùng Desktop được cài backend+skill qua --without-panel; Chrome có UI vẫn cần để người dùng đăng nhập.
- Máy chạy browser và Python cần có cùng filesystem tải xuống nhìn thấy được. Browser remote, WSL hoặc container không có shared path đã xác minh: chưa hỗ trợ nhận file tự động. Không dùng port/path máy phát triển hoặc tự mount/copy browser profile để vá.
- Chrome DevTools MCP chính thức hỗ trợ Google Chrome/Chrome for Testing; không bảo đảm các browser Chromium khác. Node.js LTS/npm là prerequisites chính thức, không cần Docker/Cognee/Supabase/Firecrawl/Playwright/gateway.

## 3. MCP — cấu hình riêng, hợp đồng chung

Nếu profile đã có Chrome MCP hoạt động: tái dùng sau khi kiểm schema/permission, không cài bản khác, restart hoặc thay trust để ép chạy.

Nếu là máy mới: operator setup qua native Hermes MCP, sau khi duyệt thực thi và phạm vi browser. Một entry là mcp_servers.<tên-do-người-nhận-chọn>, không dùng cấu trúc mcpServers của client khác trong config Hermes. Khóa tên có 1–64 ký tự chữ/số/`.`/`_`/`-`. Cho stdio, operator chọn command npx hoặc npx.cmd đúng hệ điều hành/PATH. Chốt phiên bản chrome-devtools-mcp đã được duyệt và kiểm schema; không coi @latest là version đã nghiệm thu.

- Visible launched Chrome với persistent --user-data-dir riêng cho từng recipient/profile là phương án tách phiên. Operator chọn absolute local directory, không thư mục tạm dễ bị dọn, không sao chép từ người khác. Không --isolated/isolatedContext/headless cho luồng nhớ human login.
- --autoConnect là lựa chọn riêng khi người dùng muốn Chrome đang mở; theo docs yêu cầu Chrome 144+ và user phê duyệt kết nối. MCP không tự khởi chạy Chrome ở chế độ này và có thể nhìn toàn bộ tab của profile đã kết nối; không coi đó là giới hạn chỉ DMS.
- Giữ pageId routing bật; không --no-page-id-routing hoặc --slim khi thiếu bộ tools/schema dưới đây. Không tự sửa flags trên server đang làm việc.
- Dành server đã cấu hình cho DMS: hook chặn model-facing tools của toàn server đó, không chỉ một URL. Các browser nghiệp vụ khác dùng server riêng sau phê duyệt, không trá hình thành đường bypass DMS.
- Chính sách telemetry do operator quyết định. Google mặc định thu usage statistics; --no-usage-statistics và --no-performance-crux là opt-out chính thức. Plugin không tự thay cấu hình.
- Server-native allowlist tối thiểu cho workflow: list_pages, new_page, take_snapshot, navigate_page, fill, press_key, click. Không cần evaluate_script, network/console, upload, delete hoặc hidden API. Client filtering không phải ACL backend.

Kiểm schema discovered của recipient:

| Tool | Trường được workflow dùng |
|---|---|
| list_pages | không arguments; trả ## Pages, các ID/title+URL hoặc ID/URL-only |
| new_page | url, background, timeout |
| take_snapshot | pageId; semantic a11y snapshot có RootWebArea URL/uid |
| navigate_page | pageId, type, url, timeout, handleBeforeUnload |
| fill | pageId, uid, value |
| press_key | pageId, key |
| click | pageId, uid |

Plugin chỉ dùng public ctx.call_mcp; host trả envelope ok/result/truncated tương thích. MCP khác schema/format/ACL thì dừng, không thử API/controller khác. call_mcp và mcp_allowlist dùng nguyên server key; tên tool model-facing được Hermes sanitize ký tự không thuộc chữ/số/_ thành _, hook tính đúng quy tắc đó.

## 4. Cài và cấu hình recipient

1. Chọn đúng profile-home hiện có, kiểm checksum gói. Chạy tests/Doctor/validator tại máy đó trước enable. Launcher Hermes có thể hoàn tất update đã pending trước một CLI command; kiểm trạng thái host và không coi đây là hành vi của DMS installer.
2. Chạy python <bundle>/install.py --home <profile-home>, thêm --without-panel nếu không dùng Desktop. Installer không đoán home, đọc secrets, sửa config, enable, cấp quyền hoặc restart. Có bản cũ thì từ chối overwrite trước ghi; backup/migration cần quyết định riêng.
3. Các supported CLI sau đó phải dùng cùng HERMES_HOME hoặc hermes -p <profile-name>. --home của installer không tự chuyển scope CLI. Enable với --no-allow-tool-override sau phê duyệt.
4. Đặt plugins.entries.dms-fast.settings.mcp_server là nguyên tên server recipient; mcp_allowlist chỉ cấp riêng sau operator consent và giữ trust/approval.
5. Đặt plugins.entries.dms-fast.settings.download_dir là absolute existing directory Chrome thật trên host chạy Python. Không có default Downloads; thiếu trả configuration_required trước browser call. download_wait_seconds là integer 0–60, mặc định 2; resume attempt đã click kiểm tệp ngay, không lặp thời gian chờ.
6. Selected task truyền output_dir absolute/existing của dự án được duyệt; không có default repo/user-home/ổ đĩa. Không overwrite bản có sẵn. Cấu hình chỉ qua supported Hermes CLI/UI và read-back đúng scalar, không dump config chứa secrets.
7. Mở phiên chat được host hỗ trợ để thấy tool và nạp bundled dms-fast:reading. Không copy toàn thư mục skills/memory/profile máy phát triển. Skill có procedure độc lập với tên alias/path/ID của người phát triển, không tự grant.

## 5. Checklist nghiệm thu tại mỗi môi trường
No-Run là lựa chọn operator: cần phê duyệt riêng trust full cho đúng server DMS, chỉ giữ 7 tools UI đã liệt kê và tắt resource/prompt wrappers. Không grant khi cài; không chuyển cấu hình này từ máy khác. Trust áp dụng cả server, filtering không phải ACL. Quota recheck vẫn cần xác nhận mới. Pane chỉ gửi do một lần nhấn của user qua SDK; SDK thiếu/phiên bận thì fail closed. Không chạy timer browser nền.

- [ ] Ghi OS/interpreter/Hermes/MCP version và profile đang kiểm; không công khai secrets.
- [ ] Python full suite, Node pane fixture nếu dùng Desktop, Plugin Doctor/validator PASS.
- [ ] Đúng MCP schema/envelope và đường dẫn download/output thật; không phụ thuộc máy phát triển.
- [ ] Runtime direct reader/MCP bị hook block, internal session vẫn gọi MCP được; quota recheck cần approval mới. Không chỉ kiểm callback registration.
- [ ] Cold/open nếu được phép → human login → fresh resume; phiên được giữ trên chính Chrome recipient. Không clone phiên từ máy khác.
- [ ] Query-only tìm đúng source; selected exact URL/title/code/revision/hiệu lực → tối đa một file đã duyệt.
- [ ] Completed bytes/format/hash/source receipt tại đúng project output; reuse không click lại; mismatch/partial/ambiguity không được báo hoàn tất.
- [ ] Quota UI 5/ngày là awaiting_quota, giữ việc/login, không retry; không đoán quota còn lại hoặc reset time.
- [ ] Người dùng nghiệm thu riêng; download không đồng nghĩa đọc toàn văn. Benchmark tốc độ cần baseline và completeness, không dùng thời gian fixture.

Chỉ đánh dấu từng ô bằng evidence thực tế của môi trường đó. Gói chung không mang kết quả live của một máy thành chứng nhận cho tất cả máy.

## 6. Nguồn chính thức

- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- https://hermes-agent.nousresearch.com/docs/developer-guide/middleware
- https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference
- https://raw.githubusercontent.com/ChromeDevTools/chrome-devtools-mcp/main/README.md
- https://raw.githubusercontent.com/ChromeDevTools/chrome-devtools-mcp/main/docs/configuration.md
- https://raw.githubusercontent.com/ChromeDevTools/chrome-devtools-mcp/main/docs/advanced-usage.md
- https://raw.githubusercontent.com/ChromeDevTools/chrome-devtools-mcp/main/docs/tool-reference.md
