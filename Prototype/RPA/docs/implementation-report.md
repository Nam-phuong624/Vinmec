# Báo cáo triển khai prototype

**Báo cáo lịch sử bản web:** đường chạy hiện tại đã được thay bằng OH desktop native. Kết quả kiểm thử và hướng dẫn mới tại `desktop-report.md` và `../README.md`; số đo bên dưới thuộc bản web trước khi chuyển đổi.

Ngày bàn giao: 17/11/2026. Phạm vi: OH mô phỏng và RPA tiếp đón chạy cục bộ trên Windows.

## 1. Kết quả

Đã hoàn thành T01–T08 trong `TASKS.md` cho phạm vi prototype. Chạy được luồng: mở hồ sơ bằng PID → nhận CCCD → đối chiếu Excel và OH → lễ tân xác nhận địa chỉ → RPA điền qua giao diện → lễ tân lưu → tải lại hồ sơ để xác minh.

Đã khởi động thử bằng đúng điểm vào `python scripts/start.py`, mở cửa sổ Tkinter và OH trong Edge; trang OH, CSS và JavaScript trả HTTP 200. Đóng cửa sổ RPA để kết thúc demo.

## 2. Thành phần bàn giao

| Thành phần | Vị trí | Hành vi |
|---|---|---|
| OH mô phỏng | `oh_mock/` | Tra PID; Patient Profile; bổ sung CCCD; sửa địa chỉ; lưu/hủy; kiểm tra phiên bản tránh ghi đè dữ liệu cũ |
| Công cụ RPA | `rpa_tool/` | Cửa sổ Tkinter, worker Playwright/Edge, xem trước, xác nhận, điền/đọc lại và xác minh lưu |
| Xử lý dữ liệu | `shared/` | Nhập Excel, chuẩn hóa định danh/ngày sinh/tên và quy tắc đối chiếu |
| Ánh xạ cột | `config/column-mapping.json` | Cho đổi nhãn cột qua nút Ánh xạ cột, chọn hàng tiêu đề và sheet |
| Dữ liệu giả | `demo/` | 20 người, 2 công ty, Excel A/B, file thiếu/sai CCCD, file trùng ID, chuỗi CCCD và thẻ demo |
| Khởi động/reset | `scripts/start.py`, `scripts/reset.py` | Chạy một lệnh; reset seed và SQLite demo, giữ nguyên file tham chiếu |
| Hướng dẫn | `README.md`, `docs/demo-script.md` | Cài, chạy, trình diễn và phục hồi khi lỗi |

Flask được dùng thay FastAPI vì đã có sẵn trên máy. Tkinter, SQLite, openpyxl và Playwright giữ theo hướng kiến trúc đã chọn. Thư viện bổ sung trên máy hiện tại nằm trong `.deps`; có script tạo môi trường ảo cho máy mới.

## 3. Quy tắc CCCD đã cập nhật theo yêu cầu

- Mọi dòng người khám trong Excel phải có `National ID` hợp lệ, dạng chuỗi 12 chữ số.
- Một dòng thiếu/sai CCCD làm **chặn nạp toàn bộ danh sách**; thông báo chỉ rõ số dòng cần sửa.
- Giữ nguyên số 0 đầu; không tự đoán CCCD từ ô số hoặc từ tên gần giống.
- CCCD đã có trên OH khác số quét thì chặn. Nếu OH trống, chỉ bổ sung sau khi CCCD quét và Excel khớp, đồng thời tên/ngày sinh/PID khớp.
- Trùng CCCD/PID bị chặn cho lượt liên quan, kể cả CCCD trùng nằm ở một dòng khác bị lỗi PID.

## 4. Kiểm chứng

Lệnh chạy cuối:

```powershell
$env:PYTHONPATH = '.deps;.'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest tests -q --tb=short --junitxml=docs/test-results.xml
```

**Kết quả: 44 passed, không có ca thất bại hoặc bỏ qua.** Nhật ký máy đọc được: `docs/test-results.xml`. Kiểm thử không dùng SQLite vận hành demo; mỗi ca dùng cơ sở dữ liệu tạm.

Các nhóm đã kiểm tra:

- Excel thiếu/sai CCCD, mất số 0 do kiểu số, sai sheet/hàng tiêu đề, đổi ánh xạ cột, `.xlsm`, công thức thiếu giá trị đã tính và ID trùng.
- CCCD quét lỗi, người không có trong đoàn, trùng tên và mâu thuẫn PID/tên/ngày sinh/CCCD/công ty/đợt.
- Điền đúng, chưa xác nhận địa chỉ, sửa sau xem trước, đổi hồ sơ giữa chừng, dừng trước/giữa lúc điền, timeout, đóng trang, lỗi lưu, hủy và chạy lặp.
- Lưu xong tải lại để kiểm tra dữ liệu thực sự còn; khóa các nút đổi hồ sơ/lưu trong nhóm điền.
- Trạng thái nút trên Tkinter, thay đổi địa chỉ làm mất xác nhận, bỏ kết quả worker đến muộn sau lệnh dừng, khởi chạy worker với Edge có giao diện và đóng sạch worker.
- OH tại 1440×1000, 820×1000 và 390×844; không tràn ngang; Enter/Tab/Escape, focus, modal và các trạng thái loading/empty/error/partial/success.

Ảnh đã render nằm trong `docs/evidence/`. Bản ghi `docs/ui-evidence.json` đã qua checker của skill `frontend-design-direction`; đã xem trực tiếp ảnh OH, modal và cửa sổ RPA. Đây là kiểm tra giao diện cơ bản, chưa phải đánh giá khả năng tiếp cận toàn diện.

Các script PowerShell đã qua kiểm tra cú pháp. Reset đã được chạy và so sánh SHA-256 trước/sau của workbook tham chiếu và ảnh OH: không thay đổi. Máy mới và quy trình cài venv từ đầu chưa được thử trên máy thứ hai.

## 5. Số đo thời gian

Nguồn: `docs/timing.json`, 20 người giả, Edge headless 157.0.4341.60, server và SQLite cục bộ trên máy hiện tại.

| Chỉ số đối chiếu + điền + đọc lại | Kết quả |
|---|---|
| Số lượt | 20 |
| Trung bình | 147,5 ms |
| Nhỏ nhất / lớn nhất | 127,3 / 170,4 ms |
| Lượt dưới 5 giây | 20/20 |

Số đo không tính thao tác hỏi/xác nhận địa chỉ, nhấn lưu hoặc thời gian quét thiết bị; chưa bao gồm thời gian tìm hồ sơ giấy. Chỉ kết luận đạt mục tiêu kỹ thuật trên môi trường kiểm thử này, chưa kết luận tiết kiệm thời gian tiếp đón thực tế. Cửa sổ RPA hiển thị thời gian thực đo của lượt chạy demo có giao diện.

## 6. Đối chiếu nghiệm thu spec

| Tiêu chí | Kết quả trong môi trường prototype |
|---|---|
| AC-01 | Đạt — đúng PID và xử lý không tìm thấy |
| AC-02 | Đạt — Excel tiêu đề hàng 2, giữ chuỗi định danh |
| AC-03 | Đạt — tìm đúng CCCD theo công ty/đợt |
| AC-04 | Đạt — chặn lệch danh tính và trùng ID |
| AC-05 | Đạt — địa chỉ phải được xác nhận; không tự chuyển đổi hành chính |
| AC-06 | Đạt — Playwright thao tác giao diện và đọc lại |
| AC-07 | Đạt — chỉ xác nhận hoàn tất sau lưu và reload |
| AC-08 | Đạt — chạy lặp không thêm địa chỉ; kiểm tra đổi hồ sơ/dừng |
| AC-09 | Đạt ở mức kiểm thử giả lập — gồm timeout, mất trang và response lỗi lưu; các ca thường gặp có dữ liệu để diễn tập |
| AC-10 | Đạt — reset dữ liệu giả, không sửa file tham chiếu |
| AC-11 | Đạt trong lần đo headless hiện tại — 20/20 lượt dưới 5 giây |

## 7. Giới hạn và việc tiếp nối

- Chưa kết nối OH thật. Patient Profile chỉ tái hiện các nhóm và trường cần cho demo; chưa sao chép toàn bộ chức năng trong ảnh OH.
- Đầu đọc thật chưa được thử. Chế độ JSON giả dùng ngay; adapter QR pipe phải được xác minh định dạng với thiết bị/thẻ thực tế. Chưa có OCR/NFC.
- Thẻ demo chứa PID và chuỗi CCCD giả để sao chép/nhập; chưa tạo thẻ mã vạch vật lý để kiểm thử đầu đọc PID.
- Mỗi lần nạp gán một công ty/đợt cho danh sách; file trộn nhiều công ty cần tách trước. Chưa có bộ chuyển đổi mọi quy ước tên ngoài mẫu đã định nghĩa.
- Địa chỉ dùng dữ liệu giả và nhập xác nhận, chưa tích hợp danh mục đơn vị hành chính hoặc tự ánh xạ sau sáp nhập.
- Dừng là cơ chế hợp tác trước thao tác tiếp theo; thao tác đang chờ có thể mất tới timeout 5 giây. Khi đã điền một phần, lễ tân kiểm tra/hủy trên OH; không tự hoàn tác hoặc tự lưu.
- RPA quản lý riêng phiên Edge do công cụ mở; chưa gắn với cửa sổ OH người dùng đã mở sẵn.
- Chưa có buổi xác nhận với lễ tân hoặc đo tại quầy thật. Cần xác nhận PID/Hospital Number, bộ trường được cập nhật và quy trình xử lý dữ liệu mâu thuẫn trước giai đoạn tích hợp.
