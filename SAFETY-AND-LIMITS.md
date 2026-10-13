# Phạm vi bảo mật và hỗ trợ — 0.5.4

Repo public theo chấp thuận của tác giả, chỉ code/docs/tests, không source data/cookies/config. Native root + legacy mirror dùng cùng reviewed runtime; không ghi đè ZIP 0.5.3 hoặc tự thay bản installed. Gói install/probe không tự đọc tài liệu DMS. Đây là bản hoàn chỉnh về native packaging, không chứng nhận đầy đủ nghiệp vụ, security hoặc mọi OS.

## Đã đưa vào gói

- Plan/audit mặc định; deps và copy có cờ consent riêng. Recipe chỉ là dữ liệu để Hermes máy nhận xin quyền và apply bằng supported CLI, không ghi config/allowlist/trust.
- Bộ cài kiểm absolute/non-traversal + toàn ancestors symlink/junction/reparse trước resolve/write; từ chối overwrite. Sửa lỗi installer 0.5.2 ghi qua destination-parent junction. Download task/output/source/continuation thêm cùng path guard; kiểm junction có regression chạy thật trên Windows.
- Exact copy SHA256 read-back; manifest integrity/file-set của bundle; npm package 1.10.1 pinned sha512 và realized-file receipt khi reuse. Không gọi shell=True hoặc nối npm.cmd; npm via Node + npm-cli.js, ignore scripts, prefix/cache và npm config riêng.
- Không mang account/cookies/Chrome profile, .env/config/secrets/trust/plugin-state, raw DMS receipts hoặc tài liệu công ty. Google MCP chỉ 7 UI tools, untrusted, sampling/elicitation/resources/prompts false, no JS/usage statistics/CrUX/sourceMaps.
- Mỗi recipient/profile xác định home, permissions và Chrome login riêng; backend DMS quyết định ACL. Quyền install/LLM/Chrome không gộp thành quyền admin hoặc grant tự động.

## Không được suy rộng

1. PM/plugin/Chrome process không là OS sandbox; plugins là Python thực thi với quyền OS user. Path checks không có cam kết chống mọi TOCTOU/race hoặc malicious local administrator.
2. CRC/SHA256/PDF EOF/npm lock chỉ chứng minh hình dạng/integrity theo nguồn đã chọn, không antivirus, pentest, ký số xác thực tác giả hay audit độc lập toàn dependencies. Receipt nằm cùng payload không chống attacker sửa cả hai; quyền OS/storage và nguồn ZIP vẫn phải tin cậy.
3. Top-level npm pin có integrity; các transitive được npm giải quyết rồi ghi package-lock trong prefix người nhận. Không đóng gói lock transitive chung đã nghiệm thu cho mọi OS. Chưa audit supply chain/transitive toàn bộ hoặc kiểm npm provenance/signature toàn chain. Corporate mirror/security review có thể là cổng bắt buộc riêng.
4. DMS content có thể vào LLM/history/log/state của host. Tắt Google MCP metrics/CrUX không tắt Chrome metrics hoặc host retention và không đảm bảo data residency. Công ty phải phê duyệt.
5. Handshake/tool names, fixture tests, Doctor, copied files hoặc native CLI exit 0 không chứng minh login/role/hooks/attachment/native chat. Bắt buộc live acceptance tại recipient; không chuyển PASS của tác giả sang user khác.
6. Gói không chứng minh toàn DMS/fulltext/current revision/company/legal authority. Không tự nạp Cognee, OCR, tải hàng loạt hoặc sửa/duyệt/xóa/gửi tài liệu.

## Mức hỗ trợ

- Đã kiểm tại máy đóng gói: Windows x64, Hermes Python 3.14.7, PM Node 26.7.0, PM CfT 145.0.7632.6; installer trên temporary homes có Unicode/spaces, tests guards và official npm download/version/reuse/tamper detection. Không phải máy vật lý thứ hai.
- macOS Apple Silicon/Linux native là target hướng dẫn theo docs, chưa đo end-to-end gói. Linux cần shared libraries/X/display; libatomic/Chrome libs do distro/admin, không --no-sandbox. Browser path/version/SDK/OS không đạt thì pending.
- Windows ARM64, WSL/container/remote backend, macOS Intel, Termux/Nix không được gán PASS. Hermes hỗ trợ một nền tảng không tự chứng minh Google Chrome MCP có browser cùng filesystem trên nền tảng đó.
- Python 3.11–3.13 chỉ compatibility updater theo Hermes docs, không runtime support hiện tại. SDK numeric minimum chưa xác minh, nên kiểm actual capabilities/Doctor.
- Gói hỗ trợ thiếu dependencies với internet/consent. Không có internet mà chưa có tools/MCP: chưa đủ để cài; gói không chứa binaries cho mọi OS.

## Lỗi cần stop

Windows cold PM store/đường dẫn archive dài: đã quan sát một native enable bị từ chối và active config/environment giữ nguyên; LongPathsEnabled=0 trên máy đóng gói. Retest dùng shared PM tools hiện có, không sửa registry hoặc Hermes core. Không coi reused-runtime PASS là nghiệm thu cold bootstrap trên Windows; đọc path gate ở START-HERE.

Existing same-name installation; target source/home ancestors có links/reparse; source hash mismatch; npm prefix thiếu receipt/khác bytes; SDK/runtime không phù hợp; ACL/SSO/CA/approval denied; browser session/identity nhiều nguồn; config unrelated changed; unknown transport outcome. Không tự xoá/retry/grant trust hoặc đổi controller để vượt.

## Nguồn chuẩn

Xem URL trong requirements.json và hướng dẫn START-HERE. Nguồn tài liệu official được kiểm khi đóng gói; với máy nhận vẫn phải kiểm installed runtime và đọc lại docs nếu owner/API thay đổi. Release này giữ pilot cho đến khi recipient live acceptance đủ phạm vi.
