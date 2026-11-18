# Giao diện OH desktop theo ảnh tham chiếu

Tham chiếu: `OH_UI/OH.jpg`; màn hình Patient Profile, các nhóm Identification, Contact, Personal/Employment. Các hộp địa chỉ và nút lưu được mô phỏng theo spec.

Người dùng là lễ tân; hành động chính là mở đúng PID, xác nhận địa chỉ rồi lưu. Bố cục desktop hiện tại dùng nhãn trái/ô phải, màu trắng/xám nhẹ, font Segoe UI, hàng nhập liệu dày như OH trong ảnh. Không dùng bố cục thẻ hai cột hoặc tiêu đề thương hiệu lớn. PID và tên nằm ở Hospital Number; các nhóm đúng thứ tự; nhãn mô phỏng đặt gọn trên thanh tra cứu.

Kiểm tra cửa sổ WinForms mặc định (tối đa 1280 theo chiều rộng logical, chiều cao theo vùng làm việc) và cửa sổ 1120×680. Vùng thông tin cuộn riêng; lưu/hủy nằm ngoài vùng cuộn. Kiểm tra đọc tên, Enter tra PID, UI Automation, modal và hai lần RPA. Các viewport web trong bằng chứng cũ là lịch sử bản web.

Trạng thái: loading khi mở/lưu; empty khi chưa chọn PID; error khi không tìm thấy/lưu lỗi; partial là dữ liệu đã điền nhưng chưa lưu; success sau lưu. Không có luồng cấp quyền trong sản phẩm cục bộ; quyền cài đặt và đầu đọc là cấu hình ngoài ứng dụng.
