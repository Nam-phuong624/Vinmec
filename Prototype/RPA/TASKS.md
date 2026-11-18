# Theo dõi triển khai

**Cập nhật:** theo yêu cầu OH phải là desktop, đường chạy hiện tại đã chuyển sang WinForms + Windows UI Automation. Xem `TASKS-DESKTOP.md` và `docs/desktop-report.md`. Bảng bên dưới là lịch sử bản prototype đầu tiên.

Các task prototype theo `PLAN.md` đã được triển khai ngày 17/11/2026. Kết quả chi tiết và giới hạn tại `docs/implementation-report.md`. “Hoàn thành” ở đây là phạm vi demo cục bộ, chưa bao gồm OH/đầu đọc thật.

| ID | Task | Trạng thái |
|---|---|---|
| T01 | Môi trường, cấu trúc và dữ liệu giả | Hoàn thành — 20 hồ sơ giả, 2 công ty, bộ file lỗi |
| T02 | OH mô phỏng, tra PID, sửa/lưu/hủy | Hoàn thành — Flask, giao diện web và SQLite |
| T03 | Đọc Excel và adapter CCCD | Hoàn thành — CCCD bắt buộc mọi dòng; JSON giả + QR pipe |
| T04 | Đối chiếu danh tính, bản xem trước | Hoàn thành — CCCD, tên, ngày sinh, PID, công ty/đợt |
| T05 | Giao diện RPA và worker trình duyệt | Hoàn thành — Tkinter và Playwright/Edge |
| T06 | Điền, đọc lại, xác minh lưu, dừng/lỗi | Hoàn thành — thao tác UI, không dùng API ghi từ RPA |
| T07 | Kiểm thử tự động và kiểm tra giao diện | Hoàn thành — 44/44 ca đạt, ảnh bằng chứng và đo 20 lượt |
| T08 | Script chạy/reset, tài liệu và báo cáo | Hoàn thành — README, script khởi động/reset/test và kịch bản demo |

Các việc tiếp nối cần điều kiện thực tế: xác minh đầu đọc CCCD; khảo sát PID, form địa chỉ và công nghệ OH thật; diễn tập với lễ tân; đo quy trình tại quầy. Các việc này chưa được đánh dấu hoàn thành.
