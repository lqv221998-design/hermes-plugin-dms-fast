# DMS Fast 0.6.0 — một tệp, hai pha độc lập

## Trên máy người nhận

Plugin cung cấp executor đọc `dms_fast_session`, hook/schema và bundled skill `dms-fast:reading` 0.6.2. Công cụ `computer_use` thuộc Hermes host, **không được vendored hoặc tự cài/enable bởi plugin**. Nạp skill computer-use đã có và kiểm actual schema/capture/approval tại máy nhận. Không mang driver, account, Chrome profile, local paths, config hoặc history của tác giả.

Pane “Tải một tệp — Computer Use” gửi một yêu cầu tới chat đang mở sau thao tác user. Điền đúng canonical document URL, filename và thư mục absolute được duyệt. Nút không tự chọn tệp, chạy nền, bấm browser hay bypass host approval. Session busy thì không enqueue thêm. Đường dẫn/filename là dữ liệu lựa chọn cần kiểm lại, không phải chỉ dẫn thực thi.

## Workflow bắt buộc

1. **Chọn** đúng một nguồn/tệp theo phạm vi được phép. Inventory chỉ giúp chọn; không cấp quyền tải toàn thư viện. Kiểm bản local/receipt/hash hiện có để tránh tải lại.
2. **Đọc/kiểm nguồn** bằng `dms_fast_session prepare`, task `read/open` với canonical URL và expected code/title nguyên văn khi biết. Chỉ task đọc completed đúng source mới đủ điều kiện handoff; metadata/title không là toàn văn. Số hiệu và Mã hiệu là hai trường khác nhau; token kỳ vọng phải khớp literal một trường, không substring hoặc sửa token. Revision/hiệu lực thiếu phải giữ gap/pending theo skill; biểu mẫu tham khảo có ngày trống không trở thành chuẩn hiện hành.
3. **Kiểm work cũ** nếu chưa rõ bằng status (zero-browser). Legacy attempt/quota/uncertain/refusal không được xóa, replay hay chuyển sang CUA. Không cancel việc lạ; cancel work quen thuộc cần operator duyệt đúng ID, giữ lịch sử và chỉ bỏ qua nguồn cũ, không replay. Không đổi controller sau refusal/access/approval/transport failure.
4. **Handoff**: kết thúc controller plugin trên page; chọn đúng Chrome/window/profile hiện có bằng computer_use, fresh capture đối chiếu canonical source/title/code và đúng hàng filename có Download. Không dùng tên tệp/preview, Save Link As/hidden API/Ctrl+S thay quyền export. Attachment có identity riêng, tải attachment không chứng minh đã tải/đọc tài liệu mẹ.
5. **Chuẩn bị local**: resolve download_dir thực và output_dir được duyệt, cùng filesystem, tồn tại, không link/reparse, không trùng đích. Ghi ledger versioned: source/revision/effective-date/gaps, selected filename, baseline file/size/mtime, timestamp, controller/mode/evidence; không secrets/raw auth data.
6. **Một transfer**: ghi attempt_uncertain **trước** inner click. Một inner click tối đa; không dùng live download làm phép thử background rồi foreground. Chỉ foreground khi operator chọn trước lượt mới và host approval cho phép. Input delivered/unverifiable/timeout không chứng minh request chưa tới server: fresh capture/disk reconciliation trước mọi quyết định, không retry.
7. **Xác minh tệp**: bounded wait, file mới so baseline, size ổn định, không partial/empty/HTML; signature và parser/listing/CRC phù hợp. Thiếu validator thì pending. Không mở macro, execute hoặc extract tự động. SHA256/copy nguyên bản không overwrite; nguồn và bản dự án phải cùng bytes/hash, ghi receipt local riêng và đọc lại.
8. **Bàn giao**: completed local file không là fulltext/current-effectivity/company publication/Cognee ingestion. Giữ full_document_read=false, inventory_complete=false, acceptance=pending_user và gaps. Không viết receipt CUA giả vào state plugin.

## Tương thích và điều gì thực sự thay đổi

- Model-facing schema chỉ expose task mới read/search, không continue_download/resume_after_quota. Hook chặn các lời gọi cũ trực tiếp hoặc trong tool_call, và chặn resume legacy chưa có attempt; status/resume attempt đã lưu chỉ đối soát. Cancel có approval riêng theo work.
- Helpers/validation legacy giữ nguyên để nhận state cũ và regression fixtures. Đây **không** là quyền gọi helper/registry/CLI trực tiếp để bỏ agent-loop approval. Python plugin/hook không là OS sandbox.
- Root native package, legacy mirror và standalone/unified pane phải byte-identical ở các half tương ứng. Setup hai MCP connector của 0.5.6 giữ nguyên; generic web không là đường vượt DMS/QAQC.
- Cập nhật source trên đĩa không thay tool catalog hoặc prefix của phiên đang chạy. Kiểm bản cài và mở phiên mới/idle reload theo native host, không kill/restart MCP/Chrome để ép hiệu lực.

## Mức kiểm chứng

VERIFICATION.json mô tả tests/native contract của gói, không chứng minh người nhận đã đăng nhập, có ACL, capture đúng Chrome hay tải DMS được. Receipt/tệp CUA thật của tác giả được đối soát **local**, không đóng gói/công khai. Không tải thêm DMS để thử release, không reset quota. Máy vật lý thứ hai/macOS/Linux/cold setup còn pending và release giữ Pre-release.

Hướng dẫn chi tiết: bundled `skills/reading/references/computer-use-download.md`. Cài native: [NATIVE-DESKTOP-INSTALL.md](NATIVE-DESKTOP-INSTALL.md); prerequisites: [MCP-DUAL-SETUP.md](MCP-DUAL-SETUP.md). Hermes docs: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/ và https://hermes-agent.nousresearch.com/docs/developer-guide/desktop-plugin-sdk/.
