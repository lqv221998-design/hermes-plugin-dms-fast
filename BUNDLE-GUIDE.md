# DMS Fast 0.5.2 — vào đúng từ prepare, chẩn đoán pending rõ ràng

Plugin và skill đọc/điều hướng DMS dựa trên **native Hermes → Chrome DevTools MCP hiện có**, không tạo kết nối hoặc browser thứ hai. Bản này KHÔNG tuyên bố đã điều khiển/nghiệm thu toàn bộ DMS. `capabilities` tách chức năng có handler và phần chưa triển khai; bản tải thực tế trên máy kiểm còn bị chặn ở inner click, không coi là PASS.

## Thành phần
- `dms-fast/`: plugin Python stdlib, tools `dms_fast_session` và `dms_fast_read`, slash `/dms`, skill `dms-fast:reading`.
- `desktop-plugins/dms-fast-panel/plugin.js`: pane tùy chọn; một lần nhấn thao tác gửi yêu cầu `dms_fast_session` vào đúng phiên chat hiện hành qua SDK. Không gọi browser trực tiếp hoặc tự chạy sau cài đặt.
- `install.py`: copy theo profile, kiểm hash từng file, từ chối ghi đè; không copy credentials/config/browser profile.
- `tests/`: policy/parser, session, routing hook, search/quota/file executor, cấu hình recipient/relocation và Desktop SDK fixture.
- `PORTABILITY.md`: hợp đồng đa máy, cấu hình MCP của người nhận, cổng kiểm và giới hạn hỗ trợ.

## Hợp đồng đa máy
- Cùng một code/skill/pane cho mọi máy đáp ứng prerequisites; không fork theo tên người dùng, ổ đĩa hoặc vị trí repo.
- Cài theo `HERMES_HOME` hoặc `--home` rõ ràng. Settings được đọc lại qua `ctx.get_config` mỗi lần gọi, không cache profile/server/tài khoản ở module.
- Mỗi máy/profile chọn native MCP server riêng tại `plugins.entries.dms-fast.settings.mcp_server`; mặc định `chrome_dms` chỉ là tên gợi ý, không là server/phiên dùng chung.
- Page ID là ID hiện hành của server đó, UID được resolve tại thao tác; không chia sẻ ID từ máy nghiên cứu.
- Mỗi người tự đăng nhập Chrome và giữ ACL tài khoản DMS của họ. Plugin không có key admin, không đọc cookie/token/storage, không tự cấp hoặc xác minh vai trò admin/user.
- Domain `https://dms.newtecons.vn` và read routes là policy của ứng dụng chung, không phải địa chỉ máy cá nhân. Đổi site/route cần đối chiếu và nghiệm thu policy, không tự cho phép URL bất kỳ.
- Python backend là stdlib, pane dùng SDK/React do Hermes Desktop cung cấp; không cần Docker, Cognee, local REST server hoặc remote-debugging port cố định.
- Portability local không chứng minh chạy trên tất cả phần cứng/OS/Hermes cũ. Xem `ACCEPTANCE.md` và `VERIFICATION.json` để biết chính xác phần đã chạy và còn thiếu.

## Cài tại profile của người nhận
Yêu cầu Hermes có `PluginContext.call_mcp/get_config/register_tool/register_hook/register_skill`, `ctx.state` (`get/set` bền vững theo profile). Pane Desktop cần `host.composer.submit/insertText` và `host.state.focusedSessionId/busyBySession`; SDK thiếu thì dừng rõ ràng, không gửi sang phiên khác. Node/Chrome/MCP được setup trên chính máy người nhận theo `PORTABILITY.md`; Python plugin chỉ dùng stdlib. Chỉ Windows đã chạy phép kiểm local; chưa nghiệm thu macOS/Linux.

Dùng tool `terminal` chạy `python <bundle>/install.py --home <profile-home>` với đúng profile hiện tại. Script không đoán home, không ghi đè và không enable. Tên/đường dẫn được người nhận xác định trên máy của họ; không sao chép home/config của máy phát triển.
Không dùng Desktop: thêm `--without-panel`, chỉ cài backend và bundled skill; vẫn cần Chrome có UI trên host thực thi để người dùng đăng nhập.
Nếu profile đã có `dms-fast` hoặc pane, installer từ chối toàn bộ trước ghi. Bản này chưa tự nâng cấp: giữ bản cũ, snapshot và thống nhất migration riêng; không dùng force/xoá bản cũ để bỏ cổng này.
Mọi CLI tiếp theo phải chọn cùng profile qua `hermes -p <profile-name> ...` hoặc `HERMES_HOME` đúng. `--home` của installer không tự đổi scope của CLI. Sau kiểm tra/đồng ý, enable bằng `hermes plugins enable dms-fast --no-allow-tool-override` trong scope đó.

Chọn đúng native MCP server đã hoạt động của profile (ví dụ tên `team_chrome`): `hermes config set plugins.entries.dms-fast.settings.mcp_server team_chrome`. Đọc lại chính scalar: `hermes config get plugins.entries.dms-fast.settings.mcp_server`; không dump toàn config.
**Cổng quyền riêng:** chỉ sau người dùng chủ động cho phép, grant đúng tên tương ứng bằng supported CLI: `hermes config set plugins.entries.dms-fast.mcp_allowlist '["team_chrome"]'` rồi đọc lại riêng allowlist. Installer/plugin không tự chạy lệnh này. Tên server nhận 1–64 ký tự chữ/số/`.`/`_`/`-`; `call_mcp` dùng nguyên khóa, hook dùng tên tool đã sanitize theo Hermes.
Download bắt buộc operator cấu hình `plugins.entries.dms-fast.settings.download_dir` là thư mục Chrome thật, absolute và đang tồn tại trên host chạy Python. Không đoán `Downloads`. Thư mục bàn giao absolute đang tồn tại phải được duyệt trong mỗi selected task; không tự dùng repo hay home của người phát triển.
Mặc định giữ trust/approval. Để bỏ nút Run lặp lại, **operator phải duyệt riêng** `trust: full` cho server dành riêng DMS; đây là quyền cả server, không chỉ plugin. Giới hạn tools UI về list_pages/new_page/take_snapshot/navigate_page/fill/press_key/click; tắt resource/prompt wrappers. Không tắt bảo vệ toàn Hermes. Installer không đổi trust. Hook vẫn chặn model gọi reader/MCP trực tiếp và yêu cầu xác nhận riêng cho `resume_after_quota`. Filtering/hook không thay backend ACL hoặc sandbox.

Không sửa/reload cấu hình MCP của người nhận, không restart Chrome hoặc clone profile. Tools trong chat có thể cần phiên mới; không restart browser để ép activation. Standalone panel không cần Python backend REST.

## Dùng
**Vào DMS ngay bằng prepare, không bootstrap bằng inspect.** Nguồn đã biết dùng read/open/canonical URL; nghiên cứu cấu trúc dùng read/open/https://dms.newtecons.vn/; tìm kiếm dùng kind=search. prepare mở một tab home nếu chưa có và tái dùng phiên của người nhận. inspect chỉ quan sát tab đang có. Không kiểm framework/config/Cognee trước bước mở website nếu chưa có lỗi thực sự.
pending_work_conflict/status bổ sung pending_work_expired, work_ttl_seconds và next_action/next_work_id. Việc đọc/search đã hết TTL cùng server có hướng dẫn prepare mới qua TTL hiện có, không phải hủy. Việc còn sống/luồng tải/server khác không được tự thay; attempts/quota không bị xóa. browser_not_ready của inspect có reason no_dms_or_login_tab và hướng dẫn prepare/resume thích hợp, không bị đánh đồng MCP hỏng.
Luôn nạp `dms-fast:reading`, dùng `dms_fast_session` theo schema thật: prepare → human login nếu cần → resume → tìm nguồn/đối chiếu → tối đa một download đã duyệt → kiểm tệp/hash/bàn giao. Không truyền page ID/UID; handler lấy mới qua cùng MCP. Xem `SESSION-WORKFLOW.md`.
- Task `read/open/url` mở nguồn canonical; `expected_code`/`expected_title` đối chiếu khi có, không có thì identity chưa pin.
- Task `search_download_one/query` chỉ trả candidates quan sát được, `inventory_complete=false`, chưa download. Khi chọn nguồn, cancel task tìm kiếm rồi prepare selected task có query/url/expected_title/expected_code/output_dir; không tự thay task pending.
- Selected task kiểm source/revision/ngày hiệu lực, tái dùng file đã kiểm cùng server/source/revision/output nếu có. Nút Tải về có thể chỉ mở danh sách; `download_selection_required` trả filename đã quan sát. Chọn đúng tên và duyệt riêng `continue_download`; chỉ inner link mới là transfer intent, ghi bền trước click. Kiểm ZIP/PDF, SHA256, copy không overwrite, receipt nguồn. Tệp chưa xác minh thì không completion.
- `inspect` đọc UI hiện tại không đổi pending/attempt/quota; `section=info|original` chỉ mở tab đọc đúng nguồn. Original không chứng minh đã đọc/render/fulltext. `status` thêm file_transfer_attempted/download_phase; error trả failed_mcp_tool chứ không upstream message bí mật.
- `inspect,menu=internal|departments|sites|charts|grid|booking|guides` chỉ dùng khi không có pending: resolve link sống đúng nhãn và URL đã chứng minh, click rồi đọc lại đích. Booking chỉ xem, không tạo lịch; guides dừng nếu đích chưa được xác minh. `menu_targets` là chẩn đoán quan sát, không tự cấp quyền vào URL. Metadata của grid không được hiểu thành metadata tài liệu.
- Chưa triển khai upload/edit/delete/sign/approve/send, booking họp/xe, advanced filter/pagination/fulltext OCR. Không tự gọi các control chỉ vì inspect thấy nhãn.
- Quota giao diện 5 văn bản/ngày là `awaiting_quota`, giữ việc và phiên. `resume` không click lại; `resume_after_quota` cần một phê duyệt mới qua host hook, không tự suy reset time.
- `dms_fast_read`, slash reader và model calls trực tiếp tới MCP dành riêng bị chặn. Pane gửi session task ngay khi người dùng nhấn thao tác, chặn gửi trùng khi phiên bận, không tự chọn nguồn tải. Nút nạp skill chỉ soạn nháp.
- Hook chặn model-facing calls trên server đã cấu hình, kể cả nested wrapper; **không phải sandbox**, không kiểm soát mọi browser/terminal/transport ngoài workflow. Nghiệm thu hook enforcement trên host người nhận là cổng riêng, không suy từ manifest.

## Kiểm tra local
Qua `terminal`:
- `python -m unittest discover -s <bundle>/tests -v`
- `node <bundle>/tests/test_panel.mjs`
- `hermes plugins doctor <bundle>/dms-fast --ci`
- `hermes plugins validate <bundle>/dms-fast --json`
- Chạy từ một working directory khác repo và đường dẫn có dấu/khoảng trắng; `test_portability` kiểm relocation cùng hai home thử riêng trên máy đang chạy. Đây không phải hai máy vật lý.

Tests mock **chỉ biên MCP**, chạy parser/policy/handler thật. JS test mô phỏng SDK, không chứng minh pane render thực tế. Xem `ACCEPTANCE.md` để phân biệt local, live, những cổng chưa đạt.

## Phạm vi và tốc độ
Kế thừa 0.4.2: bỏ tìm lại khi selected task đã có URL chính xác; vẫn đọc lại mã/tên/revision/hiệu lực. Lần đầu chờ tệp mặc định 2 giây; resume kiểm ngay, không click lại. 0.5.0 phân biệt list opener và transfer, chưa có benchmark tốc độ end-to-end.
Session inspect bình thường dùng list_pages + take_snapshot (2 MCP calls); info/original thêm click + read-back (4). status/capabilities không gọi browser. Đây là call budget, không phải benchmark tăng tốc. Bounded login wait tối đa 60 giây/call; không loop nền vô hạn.

Có bounded UI search và one-file executor; không OCR/PDF full-text, bulk crawling hay full inventory. Chỉ ZIP/PDF được kiểm cấu trúc, không thực thi hoặc giải nén; file không bind mã nguồn thì dừng. Grid StaticText không link không được biến thành URL đoán. Metadata/render trang đầu/file đã tải không đồng nghĩa đọc toàn văn. MCP/host vẫn có quyền của user; policy không phải sandbox OS.

## Rollback
`hermes plugins disable dms-fast`; tắt **DMS Fast — thao tác đọc** ở Settings → Plugins. Không đóng Chrome/MCP, không reset cấu hình khác. Giữ folder để kiểm tra; chỉ xoá sau khi người dùng yêu cầu. Nếu từng grant allowlist, thu hồi riêng key đó bằng supported CLI sau quyết định operator.

## Nguồn
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- https://hermes-agent.nousresearch.com/docs/developer-guide/desktop-plugin-sdk
- https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference
- https://raw.githubusercontent.com/ChromeDevTools/chrome-devtools-mcp/main/docs/tool-reference.md
- https://raw.githubusercontent.com/ChromeDevTools/chrome-devtools-mcp/main/docs/advanced-usage.md

Repository chỉ chứa code/docs/tests; không config máy nghiên cứu, không cookie/token/session, không transcript/raw DMS logs, không inventory nội bộ hay receipt của tài khoản nghiên cứu. Xem `README.md` để cài từ GitHub; chưa cài/nghiệm thu máy vật lý khác.
