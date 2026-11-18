# RPA hai lần: bung gói trước ngày khám và tiếp đón

Patient Profile đã được chỉnh tiếp theo ảnh OH: xem `TASKS-REFERENCE.md`. Chức năng hai giai đoạn trong bảng dưới được giữ lại.

| ID | Công việc | Trạng thái |
|---|---|---|
| P01 | Excel khách mới: CCCD bắt buộc, PID trống, gói/ngày khám | Hoàn thành |
| P02 | OH tạo hồ sơ, cấp PID, lưu gói khám và chặn trùng CCCD | Hoàn thành |
| P03 | RPA lần 1 điền, xác minh PID và xuất danh sách bàn giao | Hoàn thành |
| P04 | Giao diện chọn hai lần RPA, đọc danh sách PID cho lần 2 | Hoàn thành |
| P05 | Kiểm thử xuyên suốt từ Excel chưa PID đến tiếp đón | Hoàn thành — 51/51 ca của bộ hiện tại đạt |
| P06 | Cập nhật spec, hướng dẫn test và báo cáo | Hoàn thành |

Bằng chứng: `docs/two-stage-test-results.xml`, `docs/two-stage-evidence/`. Báo cáo: `docs/two-stage-report.md`. Các task trên chỉ thuộc prototype với dữ liệu giả; chưa tích hợp OH thật/đầu đọc thật hoặc tự sinh chỉ định bên trong gói.
