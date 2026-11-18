# Kịch bản trình diễn 5–7 phút

**Luồng hiện tại gồm hai lần RPA:** dùng `two-stage-demo.md` để thử từ Excel chưa PID đến tiếp đón. Kịch bản bên dưới chỉ dành cho thử riêng bước tiếp đón với hồ sơ có sẵn.

## Chuẩn bị

Đóng demo cũ, chạy `python scripts/reset.py` rồi `python scripts/start.py`. Đặt hai cửa sổ cạnh nhau. Dùng `company_A.xlsx`, Công ty Demo A, DEMO-2026, sheet DS_bung_DEMO, hàng 2.

## Ca 1 — Đúng người, địa chỉ mới

Nạp danh sách, mở DEMO0001 trên OH. Bấm CCCD demo theo PID → Đối chiếu. Đây là chuỗi CCCD giả; chưa kiểm chứng với đầu đọc thật.

Nhập Thành phố Demo / Phường Mới / 12 Đường Demo. Đánh dấu xác nhận, bấm Điền vào OH. Quan sát CCCD còn trống được bổ sung và hộp địa chỉ được điền. Lễ tân kiểm tra, lưu. Công cụ tải lại rồi mới báo hoàn tất.

## Ca 2 — Mở nhầm PID

Bấm Lượt mới. Mở DEMO0002 trên OH nhưng đưa chuỗi CCCD của DEMO0001 từ `demo/scans.json` vào ô quét. Bấm Đối chiếu: phải báo sai PID và giữ nguyên OH. Không dùng nút CCCD demo theo PID ở ca này vì nút đó lấy số tương ứng đúng hồ sơ đang mở.

## Ca 3 — Người trùng tên

Mở DEMO0010, lấy CCCD demo theo PID và đối chiếu. Đây cũng là Nguyễn Văn An nhưng có CCCD/ngày sinh khác DEMO0001. Công cụ dùng CCCD chính xác và kiểm tra danh tính, không tự chọn theo tên.

## Ca 4 — CCCD bắt buộc trong Excel

Chọn `demo/errors.xlsx`, chọn sheet và gán lại Công ty Demo A/DEMO-2026. Bấm Nạp danh sách: toàn bộ file bị chặn do CCCD sai tại một dòng. Với `demo/duplicates.xlsx`, file có CCCD đầy đủ nhưng trùng CCCD/PID; có cảnh báo số dòng và lượt liên quan không được chạy.

## Ca 5 — Thay đổi sau xem trước

Nạp lại company_A.xlsx, mở đúng hồ sơ và đối chiếu. Sửa trực tiếp CCCD trên OH sau khi RPA lập bản xem trước. Bấm Điền: công cụ yêu cầu đối chiếu lại. Dùng Hủy thay đổi trên OH để phục hồi.

## Giải thích kết quả

Mở `docs/native-timing.json` và `docs/desktop-report.md` để xem số đo desktop thực tế. OH là WinForms native, RPA thao tác qua Windows UI Automation. Đây là thời gian phần mềm xử lý trên dữ liệu giả, chưa tính hỏi địa chỉ, kiểm tra và lưu; không dùng làm kết luận thời gian tiết kiệm tại quầy thật.

Bước tiếp theo với phòng khám: xác minh PID/Hospital Number, form địa chỉ thật, đầu ra đầu đọc và quy tắc tên trong Excel; sau đó lập kế hoạch nối OH thật.
