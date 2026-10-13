# Chrome Web MCP — cài riêng bên cạnh DMS

## MCP web là gì
`chrome_web` là connector web tổng quát của **Google chrome-devtools-mcp@1.10.1**, không phải package npm khác hoặc browser SDK tự viết. Hai connector DMS/web dùng cùng một package đã pin; khác tên server, tools và Chrome profile/cache. Không đóng gói binary, node_modules, endpoint hay credentials tác giả vào GitHub. DMS Fast plugin không cần quyền gọi connector web.

## Prerequisites và consent
Đọc MCP-DUAL-SETUP.md ở root hoặc dms-fast:setup trước. Xác định đúng backend/browser host, active Hermes home/profile, launcher Python của Hermes, Node/npm và Google Chrome/CfT có UI. Khuyên Node 24 LTS; policy gói nhận 22 từ 22.12 hoặc 24/26, Python 3.14.x. Máy đã cài plugin bỏ phase copy/install. Giữ servers đang có và xin consent riêng cho deps, config, Chrome/website scope; trust full không tự đi theo install.

## Tạo recipe web hoặc cả hai
Dùng ZIP sạch đã kiểm SHA, không chạy helper trong Git-installed tree có .git/host metadata. Dấu <> là placeholder cần resolve, không chạy literal. Audit trước; deps chỉ sau grant:
```text
<HERMES_PYTHON> <CLEAN_ZIP>/bootstrap.py audit --home <RECIPIENT_HOME>
<HERMES_PYTHON> <CLEAN_ZIP>/bootstrap.py deps --home <RECIPIENT_HOME> --approve-dependencies
<HERMES_PYTHON> <CLEAN_ZIP>/bootstrap.py recipe --home <RECIPIENT_HOME> --mode web --server chrome_web
<HERMES_PYTHON> <CLEAN_ZIP>/bootstrap.py recipe-both --home <RECIPIENT_HOME> --server chrome_dms_setup --web-server chrome_web
```
Deps cài **một** pinned package trong recipient prefix; recipe chỉ DATA, không tự apply/create/grant. Không chạy deps lần thứ hai để tạo connector thứ hai. Nếu đủ package/receipt thì reuse; prefix tamper/incomplete thì dừng, không tự xóa. Server keys phải khác nhau và chưa thuộc flow khác; đang có server phù hợp thì xác minh/tái dùng sau grant, không ghi đè. Trong both output: `dms_plugin_settings` chỉ trỏ DMS, không chứa chrome_web.

## Web connector policy
- command/args là Node và entry point cùng package đã audit, path Chrome thật trên recipient; default profile persistent **browser-profiles/chrome-web-setup**, cache **cache/chrome-web-setup**, tách DMS. Tạo mới sau consent, không takeover profile chưa biết chủ. Browser visible, không headless/isolated/slim.
- **Không URL/domain allowlist/blocklist** trong recipe web; dùng được cho các website được user cho phép, không bảo đảm mọi site và không vượt ACL/CAPTCHA/SSO. Không hứa behavioral scope là origin sandbox. Không có quyền tự đọc mọi tab/account.
- 16 native tool names trong tools.include: list_pages, new_page, take_snapshot, navigate_page, fill, press_key, click, select_page, fill_form, type_text, hover, drag, upload_file, wait_for, take_screenshot, handle_dialog. Không evaluate_script/JS, network inspection/cookie/storage export. Args tắt JS/telemetry/CrUX/sourceMaps. Giữ untrusted, sampling/elicitation/resources/prompts false, parallel false. Upload/send/edit/delete cần yêu cầu rõ và read-back; bộ tools không là grant cho mọi write.
- Phải cấu hình root **mcp_servers.chrome_web** qua native Hermes UI/CLI; không dùng mcpServers generic Google như root Hermes. Apply đúng recipe.connector (hoặc both.connectors.chrome_web), không set lại cả map hoặc copy tài khoản tác giả. Private snapshot và đọc lại exact entry + so sánh unrelated config; không in raw config/secrets.
- **Không thêm chrome_web vào DMS plugin mcp_allowlist, không đổi DMS mcp_server sang web** để chữa lỗi DMS. DMS reading/search/metadata chỉ dms_fast_session. Download/handoff theo skill DMS hiện hành và quyền từng tác vụ; generic web không là fallback. QAQC giữ executor riêng và exact project.

## Kết nối Chrome đang mở — nhánh tùy chọn
Nếu user muốn session Chrome cá nhân đang mở thay default dedicated mới, đọc official advanced-usage và chọn AutoConnect riêng: Chrome >=144, channel đúng, user bật chrome://inspect/#remote-debugging, tự bấm Allow. Thay launched profile/executable args bằng --autoConnect theo docs, không ghép mù hai mode. Profile default do Chrome chọn, có thể thấy mọi cửa sổ của profile đó; cần user chọn/xác minh, không clone cookies/profile. Không tự đóng/restart Chrome/MCP hoặc đoán port/debug endpoint để thử lại. Manual remote host/WSL/browserUrl cần kế hoạch riêng.

## Verify từng connector
`hermes mcp test chrome_web` đúng profile là handshake, chưa Chrome attachment/website acceptance. Xác minh tool schema/filter và actual chat exposure; reload/new chat sau consent, không restart toàn bộ server để ép cập nhật. Với website public do user chọn, chỉ một controller, snapshot đúng page/account, thao tác đã được phép và đọc lại exact result. Đăng nhập do recipient UI/vault, không password/OTP trong chat. Denial/timeout/uncertain write: stop, kiểm trạng thái trước retry; không đổi controller để bypass. DMS/QAQC live không thuộc smoke test web tổng quát.

Chỉ báo cả hai ready khi từng gate thực sự đã kiểm; không suy DMS ready từ web PASS hoặc ngược lại. Không tự mở/tải tài liệu công ty lúc cài. Browser data có thể tới LLM/history/log của recipient, cần policy công ty; không hứa zero egress.

## Nguồn
https://github.com/ChromeDevTools/chrome-devtools-mcp
https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/chrome-devtools-mcp-v1.10.1/docs/configuration.md
https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/chrome-devtools-mcp-v1.10.1/docs/advanced-usage.md
https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference
