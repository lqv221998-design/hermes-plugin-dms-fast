# Cài DMS Fast trực tiếp trong Hermes Desktop

## Repo native

Dán nguyên URL sau vào ô **Repository** của **Install plugin**:

https://github.com/lqv221998-design/hermes-plugin-dms-fast

Chọn **Review repository**. Repo-root từ 0.5.4 có `plugin.yaml`/`__init__.py`, `skills/reading/SKILL.md` và `desktop/plugin.js`, nên native reviewer nhận cả Agent `dms-fast` và Desktop half. Không cần `#dms-fast` cho cách cài chính; đường fragment cũ vẫn được giữ.

## Trình tự an toàn

1. Chọn đúng connection/backend/profile của người nhận trong review dialog. Đối chiếu Agent name, thành phần Desktop, warnings và commit với release đã duyệt.
2. Nếu cần pin, nhập đúng SHA đầy đủ từ release vào **Pin to commit**. Không dùng SHA bịa/rút gọn hoặc suy tag luôn đồng nhất branch tip.
3. Chọn Agent và Desktop half theo nhu cầu. Skill đi cùng Agent; không phải copy kho skill cá nhân. **Enable agent plugin after install** có thể mặc định bật: tắt nếu chưa xong kiểm/config/consent. Không bật Force reinstall để đè bản đang chạy nếu chưa có quyết định migration/backup.
4. Người nhận xác nhận cài qua UI native. Hermes quản lý clone/scan/admission và component install; gói không tự cấp quyền, không tự đăng nhập, không chạy code cài global sau khi import.
5. Doctor/validator và kiểm installed version/provenance. Nạp `dms-fast:reading` để kiểm skill. Pane chỉ thực hiện yêu cầu khi user nhấn, không mở DMS/ngầm đọc tài liệu lúc cài.
6. Kiểm Python 3.14.x, Node/npm, Google Chrome/CfT và native MCP của chính recipient. Cài từ repo không tự giải quyết mọi software thiếu hoặc approve Chrome. Dùng START-HERE-HERMES/requirements và setup có consent; dùng launcher thật của installation, không PATH venv cũ hoặc `-m hermes_cli.main` từ generated workspace.
7. Cấp riêng settings/allowlist/Chrome/LLM policy theo nguồn và scope của người nhận. Giữ untrusted, không kế thừa tài khoản/cookie/trust từ người phát triển. Trong lần release này không đọc tài liệu DMS để nghiệm thu; phần business live acceptance để recipient chủ động thực hiện sau.

## Public repo và quyền

Tác giả cho phép public phần code plugin. Clone repo public không cần GitHub sign-in/token, nhưng Native Desktop cần Git hoạt động và mạng tới GitHub. Công khai code không công khai tài khoản/quyền DMS hoặc data công ty; repository không chứa chúng. Nếu fork private, quyền Git riêng vẫn bắt buộc, Chrome login không thay thế Git auth.

## Giới hạn minh bạch

Bản 0.5.4 hoàn thiện native packaging/distribution, giữ nghiệp vụ có handler đã kiểm. Không tuyên bố hỗ trợ toàn văn/OCR, pagination, advanced filters hoặc mọi menu/biến thể download đã live pass. Không đọc trực tiếp tài liệu DMS trong task release. Native probe/Doctor/install fixtures chứng minh packaging và loader, không chứng minh ACL hoặc mọi máy vật lý/OS. Không gọi custom Git URL là đã được catalog maintainer review.

## Máy không dùng repo

Gửi `DMS-Fast_0.5.4_Native.zip` trực tiếp, đọc START-HERE-HERMES rồi dùng helper plan/consent. Không cần Git/GitHub để copy từ ZIP; thiếu prerequisites vẫn cần nguồn tải chính thức. Hai kênh dùng cùng runtime/skill; legacy `dms-fast` directory đồng nhất bytes với native root và được kiểm tự động.

Nguồn: official Hermes plugin/catalog docs và installed Electron resolvePluginGitUrl/detectPluginComponents/probePluginRepo + PluginInstallModal. Direct repo review dùng cơ chế native, không patch Hermes core hoặc adapter trình duyệt riêng.
