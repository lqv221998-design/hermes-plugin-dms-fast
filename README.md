# Hermes Plugin — DMS Fast 0.5.2

Plugin và bundled skill cho DMS Newtecons. Mỗi người dùng dùng Chrome, tài khoản DMS và quyền backend của chính họ. Không có thông tin đăng nhập, cấu hình máy phát triển hoặc phiên Chrome trong repository.

## Cài từ GitHub

Repository private: người nhận phải được cấp quyền đọc GitHub và Git HTTPS/SSH trên máy đó đã xác thực. Phiên đăng nhập GitHub trong Chrome không tự xác thực Git CLI. Không dán token vào chat hoặc URL Git.

Chọn đúng profile Hermes trước khi chạy (dùng `hermes -p <profile-name>` nếu không phải Default).

```bash
hermes plugins install 'https://github.com/lqv221998-design/hermes-plugin-dms-fast.git#dms-fast' --no-enable
hermes plugins doctor dms-fast --ci
hermes plugins enable dms-fast --no-allow-tool-override
```

Để triển khai bất biến, thêm `--ref <COMMIT_SHA_40_KY_TU>` vào lệnh install. Lấy SHA đầy đủ từ commit đã duyệt; không thay bằng tên nhánh/tag hoặc SHA rút gọn. Không dùng `--force` để ghi đè bản đang hoạt động.

Plugin nằm trong thư mục `dms-fast`, vì vậy fragment `#dms-fast` là bắt buộc với bố cục repository này. Lệnh install plugin không tự cài pane Desktop, Chrome/Node hoặc MCP, không tự cấp quyền hay sao chép cấu hình người phát triển.

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

87 Python contract tests đã đạt trên Windows tại máy phát triển; fixtures không chứng minh chạy được mọi máy/role. Chưa nghiệm thu máy vật lý thứ hai/macOS/Linux hay toàn DMS. Đọc [ACCEPTANCE.md](ACCEPTANCE.md).

Pane Desktop là tùy chọn. Bộ cài offline `install.py` dùng profile-home explicit, từ chối ghi đè và không enable/grant. Không chạy bộ cài này để cài lại backend sau khi đã cài bằng Git. Xem [BUNDLE-GUIDE.md](BUNDLE-GUIDE.md), [PORTABILITY.md](PORTABILITY.md) và [SESSION-WORKFLOW.md](SESSION-WORKFLOW.md).

## Nguồn

- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins#bundle-skills
- https://hermes-agent.nousresearch.com/docs/user-guide/features/plugin-catalog
- https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference
- https://github.com/ChromeDevTools/chrome-devtools-mcp

License: MIT.
