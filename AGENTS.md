# Hướng dẫn làm việc với repo Vinmec

## Phạm vi

- Hướng dẫn này áp dụng cho toàn bộ repo, trừ khi thư mục con có `AGENTS.md` riêng.
- Repo hiện lưu tài liệu Markdown theo ngày; chưa có ứng dụng hoặc bộ kiểm thử tự động.
- Giao tiếp và viết tài liệu bằng tiếng Việt, trừ khi người dùng yêu cầu khác.

## Cấu trúc và nội dung

- Lưu nội dung theo ngày trong thư mục có định dạng `DD-MM-YYYY`, ví dụ `30-10-2026/`.
- Giữ cách đặt tên file hiện có trong từng thư mục; không tự ý đổi tên hoặc di chuyển tài liệu.
- Giữ `.gitkeep` trong các thư mục trống cần được Git theo dõi.
- Dùng Markdown rõ ràng và mã hóa UTF-8 để giữ đúng dấu tiếng Việt.
- Không tự bổ sung thông tin chưa được cung cấp hoặc xác minh vào tài liệu.

## Quy tắc chỉnh sửa

- Đọc nội dung liên quan trước khi sửa và chỉ thay đổi trong phạm vi yêu cầu.
- Giữ nguyên thay đổi đang có của người dùng; không ghi đè hoặc xóa nội dung ngoài phạm vi.
- `spec.md` là tài liệu cục bộ được `.gitignore` bỏ qua; không ép thêm file này vào Git.
- Không đưa mật khẩu, khóa API hoặc dữ liệu cá nhân nhạy cảm vào repo.
- Chỉ commit hoặc push khi người dùng yêu cầu.

## Kiểm tra trước khi hoàn tất

- Kiểm tra đường dẫn, định dạng Markdown và dấu tiếng Việt của nội dung vừa sửa.
- Kiểm tra `git diff --check` và `git status --short` để phát hiện lỗi khoảng trắng và thay đổi ngoài dự kiến.
- Với file mới chưa được Git theo dõi, đọc lại nội dung vì `git diff` mặc định chưa hiển thị file đó.
- Khi sửa `.gitignore`, dùng `git check-ignore -v <đường-dẫn>` để xác nhận quy tắc.
- Báo ngắn gọn các file đã thay đổi và kết quả kiểm tra; không khẳng định đã chạy kiểm tra nếu chưa thực hiện.
