# Luồng Chrome → người dùng đăng nhập → tiếp tục nhiệm vụ

## Cơ chế đã xây
`dms_fast_session` là cửa vào trước các thao tác DMS. Handler dùng public `PluginContext.call_mcp` của Hermes; không thêm browser framework/client hoặc dò API.

1. **prepare**: kiểm input, lưu task không-secret theo profile bằng public `ctx.state`, lấy danh sách tab hiện hành của đúng MCP server.
2. Nếu chưa có tab DMS/login, gọi `new_page` với URL home, `background=false`, không `isolatedContext`. Theo Chrome MCP, browser được khởi chạy khi tool cần browser được gọi; plugin không tự chạy/kill executable hay sửa MCP.
3. Có tab SSO: không snapshot/form-fill trang SSO, không đọc credentials; trả `ok=true,status=awaiting_login`. Đây là trạng thái bình thường, không phải task thất bại. Có thể chờ tối đa 60 giây mỗi call bằng list-pages polling; hết thời gian vẫn giữ task. Không loop nền vô hạn.
4. Người dùng đăng nhập trực tiếp trong Chrome. **resume** dùng lại work ID, liệt kê lại tab; không dùng page ID/UID cũ.
5. DMS canonical + snapshot có tiêu đề, **link Đăng xuất đúng logout route** và không denial: đủ điều kiện chạy executor, không trả `ready` để model bỏ qua workflow. Đây là heuristic UI, không xác minh danh tính/backend ACL.
6. Task `read/open` gọi reader nội bộ và chỉ xoá pending sau thành công. Query-only `search_download_one` chạy search UI → trả candidates, chưa tải. Cancel task tìm kiếm rồi prepare selected task có exact URL/title/code/output_dir. Executor kiểm revision/hiệu lực; reuse file đã kiểm cùng server/source/output hoặc chỉ một click đã duyệt → kiểm tệp/hash/copy/receipt. Chỉ file đã kiểm mới `completed`, vẫn chờ người dùng nghiệm thu.
7. Hết phiên: quay về chờ đăng nhập, giữ task. **cancel** xoá task nhưng không đóng browser, không logout hoặc sửa DMS.

## Nhớ gì và không nhớ gì
- Chrome giữ phiên đăng nhập trong **user data directory riêng của máy**. Gói không mang profile/tài khoản/phiên của máy phát triển sang máy khác.
- Pending state lưu `work_id,server,task,created_at`, TTL 24 giờ; một pending task/profile. Download intent, quota latch, bounded download baseline và ledger tối đa 200 delivery lưu riêng theo profile/server. Giữ intent đã click để resume không click lần hai; cancel/TTL không xoá lịch sử attempt. Runtime state có đường dẫn local và metadata công việc, không đóng gói/chia sẻ. Không raw snapshot, page ID, UID, auth URL, cookie/token/password/OTP.
- Canonical source URL không query/fragment; search query là nội dung công việc, không dùng để nhập secrets.
- Đăng nhập không bao giờ được chứng minh bằng một cờ cached `logged_in=true`. Mỗi lần resume đều kiểm giao diện sống.
- Không thể giữ đăng nhập vĩnh viễn: SSO có thể hết hạn, bị revoke, bắt MFA hoặc người dùng logout.

## Điều kiện vận hành
- MCP Chrome có UI và profile bền vững; không `--isolated` hay `isolatedContext` nếu cần dùng lại login.
- Theo tài liệu Chrome MCP, mặc định user data directory được giữ giữa các lần chạy; có thể chỉ định riêng `--user-data-dir`. Không có quyền tự chỉnh các flags này trên máy người nhận.
- `--autoConnect` đòi người dùng mở Chrome; plugin không hứa tự khởi động Chrome trong chế độ attach. Transport/approval lỗi là lỗi riêng, không giả làm waiting-for-login và không fallback/retry.
- Allowlist đúng server phải do operator cấp riêng; chọn server không tự cấp quyền. Không tự sửa trust, bật network/JS hay restart MCP để ép công việc. Operator có thể duyệt riêng trust full cho server DMS dành riêng và 7 tools UI để bỏ Run; quota recheck vẫn xác nhận mới.
- Các title SSO được hỗ trợ xác định **tab để chờ**, không cấp quyền snapshot/navigate ở origin SSO. Title/format không nhận ra hoặc nhiều tab: trả trạng thái chưa sẵn sàng/ambiguity, không đóng tab hoặc đoán phiên.
- Hai controllers ngoài plugin vẫn có thể đụng nhau: agent phải giữ thao tác tuần tự.

## Quota và môi trường recipient
- UI báo 5 văn bản/ngày → `awaiting_quota`, remaining/reset unknown; giữ login/source/revision/pending. Resume thường không click lại. `resume_after_quota` chỉ sau phê duyệt mới qua host hook; không tự hẹn reset hoặc chuyển tài khoản.
- Operator cấu hình đúng MCP alias và absolute existing download_dir trên host chạy Python. Thiếu directory → configuration_required trước browser call; không đoán Downloads trên từng OS. Selected output_dir phải được duyệt rõ ràng, không overwrite.
- Hỗ trợ page-list title+URL và URL-only; unknown format/ambiguous tabs/schema/denial thì dừng. Tên server không bắt buộc chrome_dms. Máy chạy browser remote/WSL/container nhưng không chung filesystem chưa được hỗ trợ nhận download; xem PORTABILITY.md.

## Mức nghiệm thu
`status` đọc pending/attempt/quota/delivered và phiên bản plugin, không gọi browser, không đổi state. Selected URL không tìm lại. Lần chờ tệp đầu mặc định 2 giây; resume đã click không lặp chờ/click. Không coi timeout tệp là quota nếu chưa có notice sống.
Xem `ACCEPTANCE.md` và `VERIFICATION.json`: phân biệt fixture handler thật, native CLI, live Chrome quan sát và native plugin E2E chưa chạy. Không lấy test cold-start fixture làm bằng chứng đã mở Chrome thật từ trạng thái tắt.

## Nguồn chính thức
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins — public context, durable/profile-scoped plugin state, MCP permissions.
- https://raw.githubusercontent.com/ChromeDevTools/chrome-devtools-mcp/main/README.md — browser khởi chạy khi gọi tool cần browser.
- https://raw.githubusercontent.com/ChromeDevTools/chrome-devtools-mcp/main/docs/advanced-usage.md — profile mặc định bền vững, isolated là tạm, autoConnect yêu cầu Chrome đang mở.
- https://raw.githubusercontent.com/ChromeDevTools/chrome-devtools-mcp/main/docs/configuration.md — user-data-dir/headless/isolated và aliases.
