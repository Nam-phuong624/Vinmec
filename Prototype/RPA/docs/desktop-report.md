# Báo cáo chuyển OH sang desktop native

**Bản hiện tại đã bổ sung RPA hai lần:** xem `two-stage-report.md` và `../README.md`. Báo cáo này ghi lại mốc chuyển sang native trước khi có tạo PID/bung gói.

Ngày: 17/11/2026. Yêu cầu: OH mô phỏng phải là ứng dụng desktop để demo sát thao tác tại quầy.

## Kiến trúc đã triển khai

- **OH:** C#/WinForms, build thành `runtime/OHDesktop.exe`. Các ô PID, tên, CCCD, ngày sinh, công ty và địa chỉ là control Windows native. Hộp sửa địa chỉ là cửa sổ modal WinForms.
- **RPA:** Python/Tkinter với pywinauto/Windows UI Automation. Kết nối đúng tiến trình OH và HWND, tìm control bằng AutomationId, đọc ValuePattern, nhập và nhấn nút native. Riêng mở hộp modal dùng BM_CLICK trên HWND của nút để không chặn worker trong InvokePattern đồng bộ.
- **Lưu trữ:** SQLite cục bộ. Helper Python được chính OH gọi để đọc/lưu; dữ liệu trao đổi qua stdin/stdout UTF-8. RPA không gọi helper, không đọc SQLite và không có luồng cập nhật API.
- **Khởi động:** `python scripts/start.py` mở OH Desktop và RPA. Không chạy web server, Edge, Playwright hoặc DOM trong đường chạy hiện tại.

OHDesktop.exe vẫn cần Python cho phần lưu trữ; đây chưa phải bộ cài EXE tự chứa tất cả phụ thuộc. Bản web cũ và bằng chứng kiểm thử cũ được giữ làm tài liệu lịch sử, không dùng trong đường khởi động hiện tại.

## Hành vi giữ lại

Mở hồ sơ bằng PID → quét CCCD → đối chiếu Excel/OH → xác nhận địa chỉ → tự điền → lễ tân lưu → RPA tải lại hồ sơ để xác minh. CCCD bắt buộc trong mọi dòng Excel; thiếu/sai ở một dòng thì chặn nạp toàn bộ file.

Trong lúc điền, khóa các nút mở/tải hồ sơ/lưu/hủy. Trước từng nhóm ghi kiểm tra lại hồ sơ, phiên bản và lượt tiếp nhận. Thay đổi sau xem trước, sai danh tính hoặc đổi hồ sơ đều yêu cầu đối chiếu lại. Dừng không tự lưu; phần đã điền có thể hủy trên OH.

## Kiểm chứng bản desktop

Lệnh chạy:

```powershell
$env:PYTHONPATH = '.deps;.'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest tests -q --tb=short --junitxml=docs/native-test-results.xml
```

**41/41 ca đạt, không có ca bỏ qua trong bộ desktop hiện tại.** `pytest.ini` loại hai file kiểm thử web cũ khỏi lượt mặc định; con số này thay thế 44 ca của bản web trước, không phải cộng gộp hai bộ.

Đã kiểm tra: toàn bộ quy tắc nhập Excel/CCCD; native đúng/sai PID; sửa sau xem trước; thiếu xác nhận; dừng trước/giữa lúc điền; lưu xung đột phiên bản; chạy lặp; hủy modal; PID không tồn tại; đóng OH; worker RPA kết nối/đóng; lưu và tải lại để xác minh.

Mỗi test OH dùng tiến trình mới, SQLite tạm và thư mục APPDATA/LOCALAPPDATA/TEMP riêng. Chỉ chụp cửa sổ ứng dụng demo. Bằng chứng:

- `native-test-results.xml`: kết quả JUnit.
- `native-evidence/oh-native.png`: màn hình hồ sơ WinForms.
- `native-evidence/oh-native-address.png`: hộp địa chỉ WinForms.
- `native-timing.json`: 20 lượt trên cửa sổ native có hiển thị, không phải số đo browser/headless.

20/20 lượt đối chiếu + điền + đọc lại dưới 5 giây trong lần chạy cuối. Giá trị từng lượt được lưu trong JSON. Thời gian hỏi/xác nhận địa chỉ, lễ tân lưu và tìm hồ sơ giấy không được tính; chưa dùng số đo này để suy ra hiệu quả vận hành tại phòng khám.

Các vấn đề phát hiện và đã sửa: dò UIA toàn desktop có thể treo; InvokePattern đồng bộ bị chặn bởi modal; COM không còn hợp lệ sau khi dialog bị hủy; dò control lặp làm chậm. Adapter hiện nhắm HWND trực tiếp, mở modal bất đồng bộ, chờ HWND biến mất khi đóng và cache control theo từng cửa sổ.

## Giới hạn còn lại

- Chưa kết nối OH thật hoặc đầu đọc CCCD/PID thật. Cần khảo sát khả năng UI Automation của OH thực tế; app mô phỏng không chứng minh mọi control trên OH thật đều truy cập được.
- Ngôn ngữ giao diện, nhóm trường và hành vi tiếp đón được mô phỏng; chưa tái tạo toàn bộ nghiệp vụ OH.
- Chạy trên phiên Windows đã đăng nhập; OH và RPA cần cùng mức quyền. Chưa kiểm chứng trên máy thứ hai, nhiều mức DPI hoặc desktop bị khóa.
- Địa chỉ vẫn cần lễ tân xác nhận; chưa có danh mục chuyển đổi đơn vị hành chính.
- Các bài kiểm thử lỗi lưu native hiện dùng xung đột phiên bản; lỗi đóng cửa sổ được kiểm tra riêng. Chưa giả lập đủ mọi trường hợp mất điện, lỗi ổ đĩa hoặc provider UIA bị treo của phần mềm bên ngoài.

Hướng dẫn vận hành hiện tại nằm ở `../README.md`; danh sách task ở `../TASKS-DESKTOP.md`.
