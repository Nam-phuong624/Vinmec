# Tách hai chế độ thao tác RPA

Vấn đề: bộ chọn đã chuyển phần tạo PID/tiếp đón, nhưng khu vực nạp Excel dùng chung luôn hiện, gây hiểu nhầm rằng phải thực hiện cả hai thao tác ở mỗi lượt.

Đã thay đổi:

- Lần 1 hiển thị thiết lập Excel và phần chọn khách/tạo hồ sơ-gói.
- Lần 2 chỉ hiển thị đoàn, số khách đã nạp, quét CCCD và xác nhận địa chỉ. Thiết lập Excel chỉ mở qua Đổi đoàn / chọn danh sách, và tự đóng sau nạp thành công.
- Tự nạp file PID đã xác minh khi chuyển sang lần 2 nếu đúng ngữ cảnh và chưa có danh sách tiếp đón đã nạp. Không âm thầm dùng dữ liệu mẫu khi chưa nạp.
- Giữ file, ánh xạ, danh sách và lựa chọn riêng cho mỗi chế độ; chuyển qua lại không mất danh sách. Lượt mới giữ dữ liệu đoàn cho khách tiếp theo.
- Tiêu đề đổi theo chế độ; mỗi màn chỉ có các thao tác tương ứng và không lặp nút dừng.

Các kiểm tra GUI mới xác nhận trực tiếp frame nào được hiển thị, frame nào bị ẩn; kiểm tra nạp đầu buổi, giữ danh sách khi đổi khách/chế độ và tự dùng file bàn giao. Kết quả lượt đầy đủ tại `workflow-view-test-results.xml`.

Kết quả: **57/57 ca đạt**, gồm cả hai lần RPA qua OH native. Chưa có thay đổi adapter OH hoặc quy tắc cấp PID trong đợt sửa giao diện này.
