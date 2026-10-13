# DMS Fast 0.5.5 — Chrome MCP onboarding cho máy nhận

**Đã cài plugin nhưng chưa dùng được:** nạp **dms-fast:setup**, đọc [MCP-CHROME-SETUP.md](MCP-CHROME-SETUP.md). MCP Google chính thức ở [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp); helper tải npm **chrome-devtools-mcp@1.10.1** có consent, không vendor binary/node_modules hay profile tác giả. Native install plugin không tự cài Node/Chrome/MCP/config/allowlist. Skill setup mới được register cùng reading; runtime mới cần cập nhật/nạp đúng profile theo consent, bản cũ vẫn đọc guide và dùng helper từ ZIP sạch.

**Cách cài chính:** mở Install plugin trong Hermes Desktop, nhập `https://github.com/lqv221998-design/hermes-plugin-dms-fast`, chọn **Review repository** rồi kiểm Agent `dms-fast`, Desktop half và profile/commit trước khi cài. Xem [NATIVE-DESKTOP-INSTALL.md](NATIVE-DESKTOP-INSTALL.md). Repo-root có manifest, entry Python, `skills/reading` và `desktop/plugin.js`; không cần fragment cho cách cài mới. Native review/consent do Hermes sở hữu, không có auto-installer tự grant quyền.

Phiên bản này hoàn thiện **đóng gói/phân phối native**, không tuyên bố hoàn thiện mọi chức năng DMS. Không đọc tài liệu trên DMS trong lần phát hành này. Toàn văn/OCR, pagination và advanced filter vẫn chưa triển khai/nghiệm thu. Login/ACL/Chrome/MCP/LLM policy của người nhận là cổng riêng.

**Bắt đầu bằng [START-HERE-HERMES.md](START-HERE-HERMES.md), [requirements.json](requirements.json), [SAFETY-AND-LIMITS.md](SAFETY-AND-LIMITS.md).** ZIP này không cần GitHub/Git để cài plugin. Có kiểm môi trường, cài dependencies thiếu sau consent, backend/skill/routes và pane tùy chọn. Không mang tài khoản, config, trust hoặc Chrome profile tác giả.

`bootstrap.py audit --home <HOME>` mặc định chỉ kiểm; `deps --approve-dependencies` mới cài thiếu; `install --approve-install` mới copy; `recipe` chỉ xuất dữ liệu cấu hình cho agent xin quyền/apply qua native CLI và read-back. Interpreter phải là runtime Hermes Python 3.14.x, không đoán từ system Python. MCP pin 1.10.1; Node/CfT theo PM bản Hermes hoặc thành phần phù hợp đã kiểm. Có manifest SHA256, tests và acceptance riêng.

**Không phải bộ cài hoàn toàn offline:** thiếu binaries/MCP cần internet và quyền tải nguồn chính thức. Chưa có/hỏng Hermes/Python thì dùng installer/package chính thức của Hermes; không chạy Python để bootstrap chính Python hoặc raw pip/uv vào runtime. Cài xong chưa chứng minh dùng DMS được: phải qua consent, native-chat/Chrome/login/ACL/LLM policy tại máy nhận.

Gói giữ nhãn pilot: Windows x64 được kiểm, chưa nghiệm thu máy vật lý thứ hai/macOS/Linux. `VERIFICATION.json`/`ACCEPTANCE.md` là bằng chứng của phiên bản này.

Plugin và bundled skill cho DMS Newtecons. Mỗi người dùng dùng Chrome, tài khoản DMS và quyền backend của chính họ. Không có thông tin đăng nhập, cấu hình máy phát triển hoặc phiên Chrome trong repository.

## Git-native hoặc ZIP

Release v0.5.4 cung cấp gói ZIP riêng. Chọn native Desktop để cài từ URL, hoặc gửi ZIP và theo START-HERE-HERMES cho máy không muốn dùng Git/GitHub. Subdirectory `dms-fast` được giữ tương thích lệnh cũ và đồng nhất bytes với runtime ở root.

Repository được phân phối public theo quyền của tác giả: tải source không cần GitHub sign-in. Native Desktop vẫn cần Git khả dụng. Nếu dùng fork private, người nhận phải tự có quyền Git; Chrome login không xác thực Git CLI. Không dán token vào chat/URL.

Chọn đúng profile Hermes trước khi chạy (dùng `hermes -p <profile-name>` nếu không phải Default).

```bash
hermes plugins install 'https://github.com/lqv221998-design/hermes-plugin-dms-fast.git' --no-enable
hermes plugins doctor dms-fast --ci
hermes plugins enable dms-fast --no-allow-tool-override
```

Để triển khai bất biến, thêm `--ref <COMMIT_SHA_40_KY_TU>` vào lệnh install. Lấy SHA đầy đủ từ commit đã duyệt; không thay bằng tên nhánh/tag hoặc SHA rút gọn. Không dùng `--force` để ghi đè bản đang hoạt động.

Plugin native ở repo root gồm Agent, skill và Desktop half. Fragment `#dms-fast` chỉ là đường tương thích cũ. Native Desktop có thể cài cả hai half theo lựa chọn của người nhận; CLI và ZIP cần kiểm half theo host riêng. Không coi native install là tự cài Chrome/Node/MCP hoặc tự cấp quyền; dùng setup có consent trong START-HERE.

## Skill đi kèm

Sau khi bật plugin, Hermes nạp bằng `skill_view(name='dms-fast:reading')`. Skill cùng `references/routes.md` được đăng ký từ chính thư mục plugin; không cần copy vào kho skills cá nhân. Cập nhật code và skill đi cùng nhau.

## Điều kiện tại máy người nhận

1. Hermes có public Plugin SDK và native MCP tương thích; dùng Doctor rồi kiểm runtime tại máy đó.
2. Google Chrome/Node và Chrome DevTools MCP chính thức của chính người nhận đã hoạt động. Người dùng tự chấp thuận kết nối và tự đăng nhập.
3. Chọn đúng MCP server dành riêng DMS, không trỏ DMS vào connector Chrome dùng chung: hook DMS chặn model gọi trực tiếp toàn server được chọn. Xem [PORTABILITY.md](PORTABILITY.md).
4. Operator tự đặt setting `mcp_server`, cấp `mcp_allowlist` riêng sau consent, giữ approval/trust phù hợp. Installer không tự làm các bước này.
5. Tải tài liệu cần `download_dir` Chrome thật và `output_dir` được duyệt, trên cùng filesystem. Luồng đọc metadata không cần thư mục tải.

Ví dụ dùng server người nhận đã tạo tên `team_dms`:

```bash
hermes config set plugins.entries.dms-fast.settings.mcp_server team_dms
hermes config get plugins.entries.dms-fast.settings.mcp_server
```

Chỉ sau operator chấp thuận quyền gọi server:

```bash
hermes config set plugins.entries.dms-fast.mcp_allowlist '["team_dms"]'
hermes config get plugins.entries.dms-fast.mcp_allowlist
```

## Sử dụng

Nạp `dms-fast:reading`, gọi `dms_fast_session` với `prepare` và task đọc/search đúng yêu cầu. Khảo sát cấu trúc bắt đầu read/open `https://dms.newtecons.vn/`; `inspect` chỉ quan sát, không bootstrap Chrome. Login/quota/denial/refusal phải chờ hoặc dừng; không đổi tài khoản/công cụ để vượt.

Plugin chưa hỗ trợ generic mọi website, sửa/duyệt/gửi tài liệu, bulk crawling, pagination đầy đủ hoặc fulltext OCR. Chrome connector dùng chung là thành phần độc lập, không được dùng để né guard DMS/QAQC.

## Kiểm thử và pane tùy chọn

```bash
python -m unittest discover -s tests -v
node tests/test_panel.mjs
hermes plugins doctor ./dms-fast --ci
```

Kết quả tests 0.5.3 và kiểm cài online được ghi trong VERIFICATION.json; fixtures không chứng minh chạy được mọi máy/role. Chưa nghiệm thu máy vật lý thứ hai/macOS/Linux hay toàn DMS. Đọc [ACCEPTANCE.md](ACCEPTANCE.md).

Pane Desktop là tùy chọn. Bộ cài offline `install.py` dùng profile-home explicit, từ chối ghi đè và không enable/grant. Không chạy bộ cài này để cài lại backend sau khi đã cài bằng Git. Xem [BUNDLE-GUIDE.md](BUNDLE-GUIDE.md), [PORTABILITY.md](PORTABILITY.md) và [SESSION-WORKFLOW.md](SESSION-WORKFLOW.md).

## Nguồn

- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins#bundle-skills
- https://hermes-agent.nousresearch.com/docs/user-guide/features/plugin-catalog
- https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference
- https://github.com/ChromeDevTools/chrome-devtools-mcp

License: MIT.
