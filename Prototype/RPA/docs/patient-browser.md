# Danh sách hồ sơ trên OH demo

Mục tiêu: xem toàn bộ người khám đã lưu và chọn mở hồ sơ mà không phải ghi nhớ PID.

Truy cập bằng nút Danh sách hồ sơ trên thanh công cụ hoặc mục cùng tên dưới Registration. Bảng có PID, tên, ngày sinh, CCCD, công ty/đợt, mã gói và ngày/giờ khám. Khách mới lưu xếp trên. Tìm tên không dấu, CCCD, PID hoặc công ty; chọn dòng rồi Mở, Enter hoặc nhấp đúp. Mỗi trang 50 dòng, có nút trang trước/sau và làm mới.

Danh sách được chính OH đọc qua helper SQLite nội bộ; RPA không truy cập trực tiếp cơ sở dữ liệu. Không có thao tác sửa/xóa trên bảng. Nút bị khóa khi RPA đang điền; đang có thay đổi chưa lưu thì yêu cầu lưu/hủy trước khi đổi hồ sơ.

Kiểm thử mới gồm tìm tên/CCCD/công ty và tên không dấu, phân trang, mở dòng tìm được mà không nhập PID, thấy khách mới tạo, trạng thái không có kết quả, giữ hồ sơ khi đóng danh sách, bảo vệ thay đổi chưa lưu và ảnh cửa sổ native. Bộ kết quả đầy đủ được lưu tại `patient-browser-test-results.xml`; ảnh tại `patient-browser-evidence/patient-list.png`.

Kết quả lượt đầy đủ: **62/62 ca đạt**. Kiểm tra phân trang đã chạy với 75 hồ sơ giả; các bài kiểm thử tạo PID/bung gói và tiếp đón trước đó vẫn đạt.

Đây là danh sách hồ sơ tiếp đón/gói khám trong prototype, chưa có bệnh án lâm sàng. Đường khởi động vẫn là `python scripts/start.py`, dùng OHDesktop-v5.exe và giữ nguyên cơ sở dữ liệu đã lưu.
