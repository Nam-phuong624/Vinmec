# Tự test hai lần RPA trên cùng một khách

1. Chạy `python scripts/start.py`. Chọn chế độ **1. Chuẩn bị — tạo PID / bung gói**.
2. Giữ `demo/new_customers_A.xlsx`, sheet `DS_bung_DEMO`, hàng 2, Công ty Demo A, đợt DEMO-2026. Bấm Nạp danh sách.
3. Chọn khách đầu **Nguyễn Minh Anh**, bấm **Điền hồ sơ & gói khám vào OH**.
4. Trên OH xem CCCD, tên, ngày sinh, địa chỉ nguồn và gói `KSK-A01`; bấm **Lưu và cấp PID**.
5. Đợi RPA báo HOÀN TẤT LẦN 1. Ghi nhận PID thực tế được cấp, ví dụ `NEW000001`. Không lấy PID cố định từ tài liệu nếu máy đã tạo khách khác trước đó.
6. Bấm **Dùng danh sách đã có PID cho lần 2**, hoặc chọn chế độ lần 2 để tự nạp file bàn giao đúng công ty/đợt nếu chưa nạp danh sách khác. Màn hình chỉ hiện tóm tắt đoàn, quét CCCD và địa chỉ; Excel không hiện như một thao tác mỗi khách. Muốn đổi danh sách, bấm **Đổi đoàn / chọn danh sách**.
7. Trên OH nhập PID vừa ghi nhận và mở hồ sơ, mô phỏng bước quét PID hôm sau.
8. Trên RPA bấm **CCCD demo theo PID** rồi **Đối chiếu**. Phải hiện KHỚP đúng Nguyễn Minh Anh.
9. Nhập Thành phố Demo / Phường Mới / 12 Đường Demo, xác nhận đã hỏi khách, bấm **Điền vào OH**.
10. Trên OH kiểm tra rồi **Lưu hồ sơ**. Đợi RPA tải lại và báo HOÀN TẤT. PID vẫn là PID ở bước 5; gói KSK-A01 vẫn còn.

Ca lỗi nên thử: hủy form trước lưu (không cấp PID); chọn khách đã tạo để thử lại (không tạo trùng); sửa mã gói ngay trên form OH trước lưu (công cụ không xuất kết quả khớp Excel); mở sai PID trước đối chiếu lần 2 (bị chặn).

Nếu chạy lại bài từ dữ liệu sạch, đóng toàn bộ demo rồi chạy `python scripts/reset.py`. Lệnh này xóa hồ sơ mới và kết quả bàn giao demo đã tạo. Không cần reset nếu muốn giữ những khách đã tạo để tiếp tục thử lần 2.
