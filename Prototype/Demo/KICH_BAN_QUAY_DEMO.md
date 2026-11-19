# Kịch bản quay demo 3 phút: OHDemo → RPA_OHDemo → In_Phieu

Toàn bộ dữ liệu trong demo là dữ liệu giả (tạo bởi `chuan_bi_demo.py`).

## 1. Chuẩn bị (làm trước khi bấm quay, không quay phần này)

1. Chạy `python Prototype\Demo\chuan_bi_demo.py` (môi trường conda `vinmec`). Lệnh này:
   - cất file/thư mục cũ của hôm nay (ds lỗi, phieu_in, file Excel khác) sang thư mục sao lưu ngoài repo, không xóa;
   - ghi `ds bung\<hôm nay>\DS_bung_<ngày>_demo.xlsx` gồm 7 dòng (bảng ở mục 2).
   - Chạy lại lệnh này trước **mỗi lần quay lại** để về trạng thái ban đầu. Đóng `OHDemo.exe` thì dữ liệu OH tự về 5 hồ sơ mẫu.
2. Đóng hết cửa sổ Word, Excel và các chương trình khác. Tắt thông báo Windows (Focus assist). Ẩn các thư mục cá nhân trên Desktop.
3. Bố trí màn hình 1920×1080, độ phóng đại 100–125%. Xếp sẵn: OHDemo ở nửa trái, RPA_OHDemo ở nửa phải (chưa mở cũng được).
4. Mở sẵn trong File Explorer thư mục `ds bung\<hôm nay>` để cuối video chỉ ra `ds lỗi.xlsx` và `phieu_in`.
5. Công cụ quay: **Xbox Game Bar** (Win + G, rồi Win + Alt + R) hoặc OBS. Quay cả màn hình, có tiếng thuyết minh qua micro. Quay thử 10 giây để kiểm tra tiếng.
6. In phiếu: **không bấm "In phiếu này"** trong demo (tránh in thật). Chỉ cho Word tự mở để xem phiếu đã điền.

## 2. Dữ liệu demo (7 dòng) và kết quả mong đợi

Kết quả này đã được chạy thử trên OHDemo thật trước khi giao.

| Dòng Excel | Người | Tình huống | RPA sẽ báo |
|---|---|---|---|
| 3 | Nguyễn Văn Mẫu, 15/02/1980 | Trùng hồ sơ DEMO0001 (cùng tên, cùng năm sinh), Excel có địa chỉ mới | Đã cập nhật · DEMO0001 · Địa chỉ |
| 4 | Lê Hoàng Long, 08/07/1988 (Nam, gói cơ bản) | Người mới | Đã tạo |
| 5 | Phạm Thu Hà, 14/11/1992 (Nữ, gói tiêu chuẩn) | Người mới | Đã tạo |
| 6 | Đỗ Minh Quân, 30/03/1979 (Nam, gói tiêu chuẩn) | Người mới | Đã tạo |
| 7 | Vũ Thị Lan, 02/09/1985 | Địa chỉ chỉ có "Hà Nội" | Cần điền tay |
| 8 | Hoàng Văn Bình, 19/12/1983 | SĐT mất số 0 đầu (912000106) | Lỗi → `ds lỗi.xlsx` |
| 9 | Bùi Thị Mai2, 05/05/1991 | Tên có chữ số | Lỗi → `ds lỗi.xlsx` |

Ý chính để nói: dòng đúng thì tự xử lý, dòng nghi ngờ thì **không tự nhập** mà chuyển người duyệt tay.

## 3. Kịch bản quay (tổng ~3 phút)

| Thời gian | Màn hình | Thao tác | Lời thuyết minh gợi ý |
|---|---|---|---|
| 0:00–0:20 | File Explorer: thư mục `ds bung\<hôm nay>`; mở Excel xem nhanh 7 dòng | Cuộn nhanh qua các dòng, chỉ vào dòng 7, 8, 9 | "Mỗi sáng công ty gửi danh sách bung gói. Đây là danh sách hôm nay, có 7 người, trong đó có 3 dòng cố ý để sai hoặc thiếu." Đóng Excel. |
| 0:20–0:45 | Mở `OH_Demo\OHDemo.exe` | Tìm "Nguyễn Văn Mẫu" để cho thấy 3 hồ sơ cùng tên (DEMO0001/4/5), mở DEMO0001 (chưa có địa chỉ) | "Đây là OH mô phỏng, hiện có 5 hồ sơ mẫu. Hồ sơ DEMO0001 chưa có địa chỉ." Quay lại màn hình tìm kiếm. |
| 0:45–1:45 | Mở `RPA\dist\RPA_OHDemo.exe` (đặt cạnh OHDemo) | RPA tự nạp 7 dòng và tự chạy; để nguyên, không thao tác | "RPA đọc danh sách và tự điền vào OH, không cần người ngồi nhập. Mỗi dòng khoảng 2–3 giây." Chỉ vào cột Trạng thái khi từng dòng đổi: Đã cập nhật, Đã tạo ×3, Cần điền tay, Lỗi ×2. |
| 1:45–2:05 | Vẫn RPA, chỉ vào dòng Cần điền tay và 2 dòng Lỗi; mở `ds lỗi.xlsx` | Cho thấy file có số dòng gốc và lý do | "Dòng nghi ngờ không bị nhập bừa: RPA ghi vào `ds lỗi.xlsx` kèm lý do để người duyệt tay." |
| 2:05–2:20 | OHDemo | Tìm lại DEMO0001: giờ đã có địa chỉ; tìm "Lê Hoàng Long" để thấy PID mới | "Hồ sơ cũ được cập nhật, người mới được cấp PID." |
| 2:20–3:00 | Mở `In_Phieu\dist\In_Phieu.exe` | Bấm **Mô phỏng quét QR (khách mẫu)…**, chọn "Phạm Thu Hà" → **Quét QR này**; Word tự mở phiếu; cuộn qua trang 1 (PID) và trang 4 (thông tin hành chính) | "Tại quầy, nhân viên quét mã QR trên CCCD. Chương trình đối chiếu CCCD với danh sách, chọn đúng form theo giới tính và gói khám, điền sẵn PID và thông tin, rồi mở Word để kiểm tra trước khi in." |

Nếu còn dư thời gian, mô phỏng thêm "Đỗ Minh Quân" (Nam, tiêu chuẩn) để thấy form khác. Nếu muốn nhắc quét bằng điện thoại, chỉ cần nói một câu: nút **Ghép điện thoại quét CCCD…** dùng cùng luồng này. Không nên quay trực tiếp phần ghép đôi vì phải thao tác trên điện thoại và Windows Firewall.

## 4. Lưu ý khi quay

- Mở **OHDemo trước, RPA sau**. RPA chờ cửa sổ OHDemo rồi mới chạy; nếu mở ngược lại, RPA vẫn chờ.
- Trong lúc RPA chạy, **không bấm vào OHDemo** và không đóng nó; đây là điều dễ làm hỏng nhất khi quay.
- Nếu quay hỏng: đóng OHDemo, RPA và In_Phieu, chạy lại `chuan_bi_demo.py`, quay lại từ đầu.
- Nếu Word chưa mở xong khi bấm Quét: chờ vài giây, không bấm lại. Nếu file phiếu đang bị khóa, chương trình sẽ lưu thêm bản có hậu tố thời gian.
- Nên quay thành 2–3 đoạn ngắn (Excel+OH, RPA, In_Phieu) rồi ghép; dễ quay lại từng đoạn hơn là quay liền 3 phút.
- Thuyết minh đọc thong thả. Nếu vượt 3 phút, cắt phần mở Excel và phần tìm lại hồ sơ ở 2:05–2:20.
