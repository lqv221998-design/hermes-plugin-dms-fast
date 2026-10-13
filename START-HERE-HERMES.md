# Hướng dẫn cho Hermes trên máy người nhận

**MCP/đã cài nhưng chưa dùng:** đọc MCP-CHROME-SETUP.md hoặc nạp dms-fast:setup (từ 0.5.5). Không chạy bootstrap trong Git/installed tree có .git/host metadata vì strict ZIP manifest reject extras; dùng ZIP sạch đã kiểm cho audit/deps/recipe. Đã cài plugin thì bỏ qua bước 4 copy/install, không overwrite/reinstall. Không tự mở tài liệu DMS trong setup.

**0.5.4:** ưu tiên native Desktop Install plugin → Repository → Review repository theo NATIVE-DESKTOP-INSTALL.md. Repo-root có Agent + Desktop half + bundled skill; legacy dms-fast giữ tương thích ZIP/fragment. Không đọc tài liệu DMS trong lần release này; bước 7 chỉ thực hiện khi recipient chủ động yêu cầu sau này, không tự chạy như bước cài.

## 0. Hợp đồng và thứ tự

Đây là gói cài/pilot, không phải quyền tự thực thi ZIP. Đọc README, requirements.json, SAFETY-AND-LIMITS và VERIFICATION trước khi chạy code. Làm tuần tự; không dùng subagent, không import cấu hình tác giả, không mở mọi tab/cài toàn máy mặc định.

1. Nhận diện đúng OS/architecture, account OS, máy chạy backend/browser và profile Hermes mà người nhận muốn dùng. Xác minh home thực đang tồn tại có config.yaml; không suy từ hostname, ổ C/D hoặc home của tác giả.
2. Giải nén bằng công cụ tin cậy vào thư mục mới, không ghi đè. Kiểm entry ZIP không absolute/traversal/symlink, CRC và SHA256 được gửi kèm từ nguồn tin cậy. Chưa có Python thì người nhận/agent có công cụ giải nén riêng làm bước này; không chạy Python script để 'bootstrap Python trước Python'.
3. Hỏi consent theo nhóm độc lập: cài dependencies; copy plugin/pane; sửa config/connector/allowlist; enable plugin; mở/kết nối Chrome. Trust full không thuộc quyền install; mặc định giữ untrusted. Login/SSO/2FA phải do người nhận thực hiện qua UI/vault của Hermes, không hỏi password/OTP trong chat.
4. Thông báo dữ liệu trang DMS có thể đi vào provider LLM/history/log/state của Hermes. Công ty phải duyệt provider/retention; nếu chưa được phép, chỉ kiểm môi trường, không đọc DMS.

## 1. Hermes/Python thiếu hoặc hỏng

Nếu Hermes hiện hoạt động, ưu tiên môi trường của chính Hermes: kiểm sys.executable, Python 3.14.x, import `hermes_cli.plugins`, `mcp`, `pm`; PluginContext cần call_mcp/get_config/register_tool/register_hook/register_command/register_skill, state/get/set và hook semantics. Doctor + runtime acceptance quyết định, không đoán số phiên bản Hermes tối thiểu.

Nếu terminal `python` là 3.11/3.13, không kết luận Hermes thiếu Python. Dùng launcher/runtime thực mà bản Hermes sở hữu; với source checkout, tài liệu chính thức hỗ trợ `scripts/run-in-hermes-env python <script> ...`. Với Desktop signed payload, dùng interpreter/backend được launcher chọn, không sửa payload, không ghép site-packages của interpreter khác vào agent đang chạy.

Nếu thiếu Hermes/Python thật, xin quyền cài qua https://hermes-agent.nousresearch.com/docs/getting-started/installation : Windows/macOS ưu tiên desktop package chính thức (chứa Python/dependencies); Windows native CLI qua install.ps1 chính thức; POSIX source qua install.sh chính thức. Tải/đọc script trước thực thi theo chính sách công ty; không dùng package PyPI 'hermes-agent' thay thế. Python 3.14 do installer/PM quản lý, không ép cài Python global.

PM không là application updater. Source update, MSIX/App Installer/Store, macOS signed app và container giữ owner riêng. Nếu SDK/API thiếu, kiểm owner và xin quyền update đúng owner; `hermes pm repair` chỉ sửa dependency generation. Không raw pip/uv vào runtime, không bare PM install như bước 'sửa mọi thứ' mặc định. Docker/Nix/Termux/remote backend cần kế hoạch riêng, không chạy desktop bootstrap mù.

## 2. Kiểm trước, lập kế hoạch không thay đổi

Trong thư mục gói, chọn đúng interpreter; placeholder dưới đây không phải lệnh literal:

```text
<HERMES_PYTHON> bootstrap.py audit --home <RECIPIENT_HOME>
```

`audit` kiểm manifest từng file, SDK/runtime, Node/npm CLI, Chrome/CfT và MCP đã cài dưới scope gói. Không ghi config/cài software/khởi chạy browser; probe Node --version và import SDK/PM local. Bytecode Python trong thư mục nguồn có thể được interpreter tạo; không phải thay profile. PM lookup local không bootstrap downloader. Rà `facts`/`plan`: đường dẫn là của người nhận, không đưa ra ngoài chat công ty.

- Python hỗ trợ: 3.14.x; bản máy đóng gói 3.14.7 không phải bắt mọi máy đúng patch đó.
- MCP 1.10.1 npm engines: ^20.19.0 || ^22.12.0 || >=23. Gói chọn chặt hơn: 22 >=22.12, 24 hoặc 26; loại 20/25. Khuyên 24 LTS; PM của bản Hermes hiện đóng gói là Node 26.7.0 và đã được kiểm engine-compatible, không coi 26 là khuyến nghị LTS từ Google.
- Browser: Google Chrome/CfT có UI. PM package tên chromium ở máy đóng gói cung cấp CfT 145.0.7632.6; không suy từ tên 'chromium' rằng mọi browser tương thích. Browser system được tìm thấy mới chứng minh path, chưa chứng minh version/attach. Operator kiểm version/Google support và handshake. AutoConnect tùy chọn yêu cầu Chrome >=144 và chấp thuận riêng, không là mặc định gói này.
- npm CLI phải khả dụng. Helper gọi Node + npm-cli.js, không shell=True hoặc npm.cmd nối chuỗi; không cài npm global.
- Kiểm dung lượng/quyền ghi theo kích thước artifact thật, mạng/proxy/CA theo chính sách công ty. Không tắt TLS để chữa certificate errors.

Có plugin/pane/connector cùng tên đang chạy: giữ nguyên và dừng để thống nhất migration. Chỉ có ZIP không cần Git/GitHub; nguồn installer Hermes kiểu source vẫn có prerequisites riêng (POSIX Git/curl/tar/SHA utilities; Windows source có thể bootstrap Git).

## 3. Cài thành phần thiếu sau consent

**Windows path gate:** kiểm LongPathsEnabled và đường dẫn PM store/staging thực. Lần kiểm isolated cold store trên máy đóng gói gặp FileNotFoundError khi tạo archive download path dài, với LongPathsEnabled=0. Không tự sửa registry/core. Nếu gặp: giữ config/active environment, dùng tool store đã cài của chính installation qua cơ chế public được owner hỗ trợ hoặc chọn root ngắn sau consent; nếu công ty chọn bật Win32 long paths thì cần grant administrator/GPO riêng và ứng dụng longPathAware, có thể phải restart/reboot. Không tự coi registry=1 là mọi ứng dụng đã hỗ trợ. Nguồn Microsoft: https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation . Cold PM bootstrap là cổng pending, không giả làm enable PASS.

```text
<HERMES_PYTHON> bootstrap.py deps --home <RECIPIENT_HOME> --approve-dependencies
```

Helper tái dùng Node/Chrome đủ điều kiện. Thiếu hoặc không phù hợp → explicit public `python -m pm.cli install node`/`chromium` theo lock của bản Hermes, không sửa lock/facts/global PATH/source. PM tool store có thể chia sẻ giữa profile cùng installation; nêu scope này trước grant. Không gọi PM update/change pins. Nếu hệ thống không có PM/API phù hợp, dừng về bước 1.

MCP lấy đúng `chrome-devtools-mcp@1.10.1` tại registry.npmjs.org trong `<RECIPIENT_HOME>/plugin-tools/dms-fast-setup`, không global; ignore lifecycle scripts, tắt audit/fund, cache riêng, không dùng npmrc/credential của tác giả. Kiểm package-lock version + pinned sha512 integrity, ghi hashes realized files để reuse phát hiện thay đổi; CLI --version phải đúng. Lockfile/hash tự nó không là OS sandbox hoặc ký xác thực toàn chain.

Nếu prefix đã có nhưng incomplete/hash khác/ownership receipt thiếu: giữ file và dừng, không tự xóa/retry. Cần quyết định cleanup đúng prefix riêng, không xóa cache/profile/node_modules của flow khác. Thiếu system libraries Linux (libatomic/Chrome shared libs), administrator supplies đúng distro package từ nguồn chính thức sau UAC/sudo consent; không tự thêm --no-sandbox. ARM64/WSL/remote không có Google-supported browser cùng host thì pending kế hoạch riêng.

## 4. Copy plugin, giữ disabled

```text
<HERMES_PYTHON> bootstrap.py install --home <RECIPIENT_HOME> --approve-install
```

Thêm `--include-panel` chỉ khi có Desktop SDK và người nhận muốn pane. Backend + skill là đủ cho CLI. Bộ cài kiểm ancestors symlink/junction/reparse, không overwrite, đối chiếu bytes sau copy. Không auto enable/config/trust/browser. `install.py --home <HOME>` riêng là plan; `--apply` mới copy (mặc định kèm pane, `--without-panel` bỏ pane).

Trong cùng scope CLI, chạy `hermes plugins doctor dms-fast --ci`; validator `hermes plugins validate <INSTALLED_PLUGIN_DIR> --json` dùng installed directory path và tests từ gói. Bất kỳ failure phải xử lý trước enable. Không bỏ qua Doctor bằng đổi API/controller khác.

## 5. Tạo recipe, cấp quyền/config có kiểm read-back

```text
<HERMES_PYTHON> bootstrap.py recipe --home <RECIPIENT_HOME> --server chrome_dms_setup
```

Recipe là DATA, chưa ghi. Nếu đã có native Chrome MCP riêng DMS phù hợp: kiểm schema/settings/permissions rồi tái dùng; không ghi đè/restart connector đang chạy để ép tên trên. Nếu mới, chọn server key chưa dùng; dedicated profile của người nhận, visible/persistent, không clone Chrome profile có sẵn. Mặc định không dùng cổng debug cố định hoặc endpoint tác giả. Không autoConnect toàn Chrome thường của người nhận.

Sau grant config/connector/allowlist, tạo đúng 2 thư mục trong `create_after_consent` nếu chưa có; nếu đã có dữ liệu/profile chưa biết chủ thì dừng/hỏi, không tự tiếp quản. Snapshot config nguyên bản PRIVATE tại home người nhận, không đưa backup/secret vào ZIP/chat. Các CLI phải có process-local HERMES_HOME đúng target hoặc chọn profile qua `hermes -p <NAME>`; --home của helper không đổi scope CLI.

Dùng native supported config CLI/UI, KHÔNG tự rewrite YAML:

```text
hermes config set mcp_servers.<SERVER> <JSON_OBJECT_FROM_RECIPE.connector>
hermes config get mcp_servers.<SERVER> --json
hermes config set plugins.entries.dms-fast.settings.mcp_server <SERVER_LITERAL>
hermes config get plugins.entries.dms-fast.settings.mcp_server --json
hermes config set plugins.entries.dms-fast.mcp_allowlist <JSON_ARRAY_WITH_EXACT_SERVER>
hermes config get plugins.entries.dms-fast.mcp_allowlist --json
```

Scalar tên server là literal (không thêm JSON dấu quote); object/list mới serialize JSON. Chỉ thêm entry mới, không set lại toàn mcp_servers. Read-back exact target sau từng write, so sánh parsed config toàn bộ với private before: chỉ các key được cấp phép thay đổi. Không in raw config/secrets. CLI exit 0 chưa là read-back; config race/mismatch thì stop/investigate, không rollback toàn profile mù.

Giữ untrusted, sampling/elicitation/resource/prompts false, chỉ 7 tools UI. Không --slim/--no-page-id-routing; tắt JS evaluation/telemetry/CrUX/sourceMaps. Trust full phải là grant riêng của người nhận, không theo trust của tác giả. Filtering không thay backend ACL. Không tự bật/tắt connector UI hoặc /reload-mcp toàn bộ nếu sẽ restart flow khác.

## 6. Enable và kiểm native metadata

Sau grant enable: `hermes plugins enable dms-fast --no-allow-tool-override` cùng scope; read-back enabled list (`hermes config get plugins.enabled --json`), Doctor/list và xác minh unrelated configuration. `hermes mcp test <SERVER>` kiểm handshake/schema, không chứng minh browser đã attach. Kiểm 7 tools/fields đúng bảng PORTABILITY; nếu host/API không khớp, dừng.

Nạp skill bằng `skill_view(name='dms-fast:reading')`; file/reference tự đi cùng plugin, không copy kho skills cá nhân. Nếu chat chưa có native tool/schema mới, mở lại đúng chat/backend theo cơ chế của host sau grant; không tự restart mọi MCP/Chrome. Có quyền connector chưa đồng nghĩa UI Chrome đã được phép; recipient tự approve host UI/Chrome khi xuất hiện.

## 7. Nghiệm thu DMS thật — mới được báo dùng được

Xin quyền mở Chrome/đọc DMS + xác nhận LLM policy. Dùng duy nhất native `dms_fast_session`, không thêm Python MCP/browser transport để vượt approval/guard:

```json
{"action":"prepare","work_id":"recipient_setup_read","task":{"kind":"read","action":"open","url":"https://dms.newtecons.vn/","expected_title":"Tài liệu Phòng/Ban - Newtecons"}}
```

Human login/SSO/2FA → resume cùng work ID → read-back đúng DMS URL/title/metadata và ACL của recipient. Cần thêm lượt inspect/resume hợp lệ để chứng minh phiên được tái dùng, không chỉ tab opened/handshake/click. Direct model reader/MCP của DMS phải bị hook chặn; kiểm negative gate qua native host, không dựng fake approval. Unknown title/login/denial/quota/uncertain để pending/stop; không hủy việc khác, reset attempts/quota hoặc đổi tài khoản.

Nếu chỉ cần đọc/search: không đặt download_dir giả. Nếu cần một file: xác minh Chrome download path thật, cấu hình `plugins.entries.dms-fast.settings.download_dir` qua CLI sau grant; output_dir absolute/existing được user chọn. Same filesystem/browser host; WSL/remote mismatch pending. Chọn exact source/code/title/revision, một download được phép; verify file/hash/receipt/read-back bytes đúng output. Nhánh tải nhiều biến thể chưa qua live ở máy đóng gói nên cổng này phải nghiệm thu riêng; không coi PDF EOF/ZIP CRC là quét virus/fulltext.

## 8. Báo cáo và rollback

Báo OS/runtime/versions, profile đã kiểm, nguồn + integrity, permissions được grant, Doctor/tests, schema/handshake, native-chat reload, URL/title/session/ACL thật, download nếu có và những pending. Chỉ `ready_to_use` khi tất cả cổng trong phạm vi cần dùng đã đo. Không gửi cookies/password/token/OTP/private config/raw SSO sang chat hay report.

Rollback sau grant: disable đúng dms-fast/pane và connector mới của gói nếu cần; revoke riêng allowlist/settings đã thêm qua supported CLI. Không logout, close Chrome khác, xoá data/profile hoặc restore toàn config đè thay đổi mới của người khác. Gói không tự uninstaller; giữ receipt/files để điều tra, xóa chỉ khi người nhận quyết định đúng scope.
