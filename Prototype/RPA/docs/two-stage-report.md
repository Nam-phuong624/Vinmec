# Báo cáo RPA hai giai đoạn

**Cập nhật giao diện 18/11/2026:** đường khởi động hiện dùng OHDesktop-v3.exe, Patient Profile bám ảnh nguồn. Chức năng hai giai đoạn bên dưới giữ nguyên; xem `oh-reference-layout.md` và `reference-test-results.xml` cho bản mới.

Ngày cập nhật: 17/11/2026. Spec: phiên bản 0.3. Tasks: `../TASKS-TWO-STAGE.md`.

## Hành vi đã thay đổi

**Lần 1, trước ngày khám:** nạp Excel khách mới có CCCD nhưng chưa PID, chọn khách, RPA mở form tạo mới trên OH Desktop và điền hồ sơ/gói. Nhân viên kiểm tra rồi bấm Lưu và cấp PID. OH cấp PID trong giao dịch lưu; RPA đọc lại qua UI Automation và tải lại hồ sơ để xác minh. Chỉ sau đó xuất dòng thành công vào Excel riêng.

**Lần 2, khi khách đến:** dùng danh sách có PID từ lần 1, mở đúng hồ sơ bằng PID, quét CCCD để đối chiếu đúng người, xác nhận địa chỉ và cập nhật. Giữ nguyên PID và thông tin gói đã chuẩn bị.

Lần 1 điền: họ tên, CCCD, ngày sinh, giới tính, điện thoại từ Excel, quốc tịch, địa chỉ nguồn, công ty/đợt, mã/tên policy, mã/tên gói, ngày/giờ khám. Không suy ra địa chỉ sau sáp nhập; địa chỉ có cấu trúc hiện tại để trống ở hồ sơ mới, chờ xác nhận trong lần 2.

OH native bản này là `runtime/OHDesktop-v2.exe`; bản EXE trước được giữ để không ghi đè chương trình đang chạy trong lúc triển khai. `scripts/start.py` luôn mở bản v2 và kết nối RPA đúng PID tiến trình của bản đó.

Đã đặt DPI awareness trước khi Tk tạo cửa sổ để việc worker UI Automation khởi động không làm đổi tỷ lệ giao diện sau bố trí. Công cụ chụp ảnh cửa sổ cũng dùng tọa độ DPI-aware để tránh ảnh bị cắt ở màn hình có scaling.

## Tính đúng đắn và phục hồi

- PID trống/chưa có cột PID được chấp nhận ở lần 1; lần 2 cần PID đã lưu.
- CCCD bắt buộc ở mọi dòng trong cả hai lần; thiếu/sai làm chặn nạp toàn bộ file.
- Trùng CCCD/PID trong file bị chặn ở các dòng liên quan. Dòng đã có PID không được dùng tạo mới.
- Tra CCCD trên OH trước tạo và kiểm tra lại trong giao dịch SQLite `BEGIN IMMEDIATE`; hai yêu cầu đồng thời không sinh hai PID cho cùng CCCD.
- Nhân viên phải lưu; RPA không tự bấm Lưu và cấp PID. Hủy/dừng trước lưu không tạo hồ sơ.
- Các giá trị đã lưu khác Excel sẽ bị báo cần kiểm tra, không xuất kết quả hoàn tất.
- File bàn giao riêng nằm ở `runtime/prepared/<mã công ty-đợt>.xlsx`; một file cho từng ngữ cảnh công ty/đợt. Ghi bằng file tạm rồi thay thế, giữ nguyên workbook nguồn. Lần chạy tiếp nối đọc các kết quả trước để không làm mất các dòng đã xác minh.
- Nếu OH đã lưu nhưng xuất Excel thất bại, thông báo giữ PID để người dùng ghi nhận; không tự tạo lại. Các file kết quả chứa dữ liệu nghiệp vụ, tách khỏi nhật ký kỹ thuật chỉ có sự kiện/thời gian.
- Reset dữ liệu demo đặt lại bộ đếm PID và xóa đúng các file kết quả có tên mã tự động trong thư mục runtime/prepared; không xóa workbook nguồn hoặc thư mục tham chiếu.

## Kiểm thử

Lệnh chạy cuối:

```powershell
$env:PYTHONPATH = '.deps;.'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest tests -q --tb=short --junitxml=docs/two-stage-test-results.xml
```

**51/51 ca đạt**, không có ca bỏ qua/thất bại trong bộ hiện tại. JUnit tại `two-stage-test-results.xml`. Kiểm thử web cũ vẫn được loại khỏi lượt mặc định; không cộng gộp kết quả lịch sử.

Đã kiểm tra thêm: Excel chưa PID hoặc thiếu hẳn cột PID; yêu cầu CCCD/gói; bảo toàn ngày/giờ khám; OH tự cấp PID; chặn trùng trong hai yêu cầu đồng thời; form tạo mới native; hủy/dừng giữa lúc nhập; không xuất nếu gói lưu khác nguồn; xuất và đọc lại Excel; trạng thái giao diện và nút chuyển lần 2; chạy xuyên suốt trên cùng PID từ khách mới đến cập nhật địa chỉ sau tiếp đón. Các kiểm thử tiếp đón native và dữ liệu trước đó vẫn đạt.

Ảnh đã xem tại `two-stage-evidence/stage1-create.png` và `stage1-pid-created.png`. Form tạo mới chứa cả hồ sơ và gói; sau lưu thấy PID do OH cấp trên Patient Profile. Mỗi test native dùng tiến trình và SQLite riêng, không tạo khách mới trong cơ sở dữ liệu demo người dùng đang mở.

## Giới hạn cần biết khi trình diễn

- “Bung gói” ở mức mô phỏng mã/tên gói, policy và ngày/giờ trên hồ sơ; chưa triển khai danh mục gói, sinh từng dịch vụ/chỉ định hoặc thanh toán.
- Làm từng khách, nhân viên duyệt và lưu; chưa tự lưu cả danh sách hàng loạt.
- Chưa hỗ trợ gán thêm gói/đợt cho PID cũ hoặc nhiều lượt khám trên cùng PID. Khi phát hiện CCCD đã có, chặn tạo mới và hiển thị PID cho nhân viên kiểm tra.
- Chưa tự in hồ sơ hay mã vạch vật lý; Excel bàn giao cung cấp PID đã xác minh để chuẩn bị hồ sơ.
- Chưa nối OH hoặc đầu đọc thật; adapter UI Automation mới được kiểm chứng với OH WinForms mô phỏng.
- Nếu sửa nội dung ngay trên OH khác dữ liệu nguồn, công cụ yêu cầu xử lý lại nguồn/đối chiếu thủ công trước khi bàn giao; không tự ghi ngược dữ liệu người dùng sửa vào Excel đầu vào.

Hướng dẫn thao tác đầy đủ và cách tự test nằm tại `../README.md` và `two-stage-demo.md`.
