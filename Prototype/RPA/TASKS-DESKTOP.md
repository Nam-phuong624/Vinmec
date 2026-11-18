# Chuyển OH sang desktop native

Đã mở rộng tiếp sang RPA hai lần: xem `TASKS-TWO-STAGE.md`. Bảng dưới là kết quả chuyển desktop trước khi bổ sung tạo PID/bung gói.

Yêu cầu: OH là ứng dụng desktop Windows; RPA thao tác control native, không dùng DOM/browser.

| ID | Task | Trạng thái |
|---|---|---|
| D01 | OH native WinForms, build EXE, lưu SQLite | Hoàn thành |
| D02 | Adapter RPA Windows UI Automation | Hoàn thành |
| D03 | Khởi động hai app và đóng sạch tiến trình | Hoàn thành — worker native đã được kiểm thử |
| D04 | Kiểm thử desktop thật: đúng/sai PID, địa chỉ, lưu, dừng | Hoàn thành — 41/41 ca của bộ hiện tại đạt |
| D05 | Ảnh minh chứng và đo thời gian desktop | Hoàn thành — 20/20 lượt dưới 5 giây |
| D06 | Cập nhật hướng dẫn, spec và báo cáo | Hoàn thành |

Bằng chứng: `docs/native-test-results.xml`, `docs/native-timing.json`, `docs/native-evidence/`. Báo cáo: `docs/desktop-report.md`.
