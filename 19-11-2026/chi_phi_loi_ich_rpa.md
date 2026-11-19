# Chi phí và lợi ích của RPA_OHDemo

Ngày lập: 19/11/2026. Phạm vi: chương trình RPA tự động điền danh sách Excel trong ngày vào OH.

Quy ước: **[Cung cấp]** là số do người phụ trách dự án cung cấp, chưa đo lại; **[Giả định]** là giả định của người lập, cần thay bằng số đo thực; **[Tính]** là kết quả tính từ các số trên.

## 1. Số liệu đầu vào

| Số liệu | Giá trị | Nguồn |
|---|---|---|
| Lương lễ tân | 15.000.000 đ/tháng, hiểu là lương tháng | [Cung cấp] |
| Ngày làm việc mỗi năm | 300 ngày | [Cung cấp] |
| Giờ làm mỗi ngày | 8 giờ | [Giả định] |
| Đơn giá nhân sự | 75.000 đ/giờ = 1.250 đ/phút (15.000.000 ÷ 25 ngày ÷ 8 giờ ÷ 60) | [Tính] |
| Số khách mỗi ngày | 80 – 120 | [Cung cấp] |
| Gộp, chuẩn hóa Excel và đưa lên OH (làm tay) | 60 giây/khách, gồm cả hai việc | [Cung cấp] |
| Sau tự động hóa | 10 – 20 giây cho cả danh sách vài trăm người; 2,5 giây/khách khi RPA điền và cập nhật trên OH | [Cung cấp] |
| Nhân viên điền và kiểm tra trên OH tại quầy, trước khi đưa giấy chỉ định | 2 – 3 phút/khách | [Cung cấp] |
| Khách tự điền thông tin cá nhân | 5 – 7 phút/khách | [Cung cấp] |
| Tỷ lệ dòng phải duyệt và nhập tay | khoảng 10% | [Cung cấp, dự tính] |
| Thời gian duyệt lỗi và xem báo cáo | 15 phút/ngày | [Giả định] |

Lưu ý: nếu 15.000.000 đ là đơn giá mỗi giờ thay vì mỗi tháng thì mọi số tiền dưới đây nhân 200.

## 2. Chi phí phát triển và vận hành

| Hạng mục | Kế hoạch | Chi phí thêm |
|---|---|---|
| Windows, Office (Excel, Word) | Đã có bản quyền, dùng máy hiện tại của bệnh viện | 0 |
| Python và thư viện (openpyxl, pywinauto, PyInstaller) | Mã nguồn mở; chương trình đã đóng gói exe nên máy chạy không cần cài Python | 0 |
| SQLite | Chỉ OHDemo dùng; OH thật có cơ sở dữ liệu riêng, RPA không truy cập | 0 |
| Máy chạy RPA | Dùng máy hiện có, chạy sau giờ khám ngày hôm trước | 0 |
| Phát triển ban đầu | Không tính vào ngân sách | 0 (xem lưu ý) |
| Bảo trì | OH là phần mềm đóng, không cập nhật nữa nên rủi ro hỏng do đổi giao diện thấp | gần 0 |
| Vận hành hằng ngày | Người duyệt `ds lỗi.xlsx` và xem báo cáo thay đổi | đã trừ trong mục 3 |

Lưu ý:
- Công sức xây dựng chương trình là chi phí cơ hội; ghi "không tính vào ngân sách" để người đọc không hiểu là không tốn công.
- Chưa xác nhận hợp đồng với nhà cung cấp OH có hạn chế tự động hóa giao diện hay không. Cần hỏi trước khi dùng trên OH thật.
- Vì không có chi phí đầu tư, không có thời gian hoàn vốn; khoản tiết kiệm ròng là lợi ích thuần.

## 3. Lợi ích: thời gian và tiền tiết kiệm

Công thức: `phút ròng mỗi ngày × 1.250 đ × 300 ngày`.

### Kịch bản A (số chính thức): chỉ tính bước 60 giây

Mỗi khách tiết kiệm 60 giây. Trừ 10% dòng phải nhập tay (không tiết kiệm) và 15 phút duyệt lỗi mỗi ngày.

| Khách/ngày | Phút gộp | Sau trừ 10% | Phút ròng (trừ 15 phút duyệt) | Tiền ròng/năm |
|---|---|---|---|---|
| 80 | 80 | 72 | 57 | ≈ 21 triệu đ |
| 100 | 100 | 90 | 75 | ≈ 28 triệu đ |
| 120 | 120 | 108 | 93 | ≈ 35 triệu đ |

### Kịch bản B (tiềm năng, chưa xác nhận): bước 2–3 phút tại quầy cũng giảm hoặc bỏ

Nếu hồ sơ đã có sẵn trên OH từ hôm trước nên nhân viên không còn phải điền và kiểm tra lại. Cộng thêm 2–3 phút/khách trên 90% số khách.

| Khách/ngày | Phút thêm so với A | Phút ròng | Tiền ròng/năm |
|---|---|---|---|
| 80 (2 phút) | 144 | 201 | ≈ 75 triệu đ |
| 100 (2,5 phút) | 225 | 300 | ≈ 113 triệu đ |
| 120 (3 phút) | 324 | 417 | ≈ 156 triệu đ |

Chỉ đưa kịch bản B vào quyết định sau khi chạy thử và đo thực tế số phút nhân viên tiết kiệm ở quầy.

### Lợi ích không quy ra tiền công lễ tân
- Nếu quét CCCD thay cho việc khách tự điền, mỗi khách bớt tối đa 5–7 phút chờ (tổng 400–840 phút khách mỗi ngày). Đây là trải nghiệm của khách, không phải chi phí nhân sự; chưa đo thời gian quét và xử lý CCCD đọc lỗi nên 5–7 phút là mức trần.
- Tiền tiết kiệm chỉ thành tiền thật khi quy được ra giảm nhân sự hoặc giờ làm thêm. Nếu giữ nguyên số người, đây là năng lực được giải phóng.

## 4. Chạy RPA sau giờ khám ngày hôm trước

Ưu điểm:
- Không có người thao tác trên OH trong lúc RPA chạy; thời gian chạy (khoảng 200–300 giây mỗi ngày) không chiếm quầy.
- Có thời gian xem `ds lỗi.xlsx`, bấm "Đối soát (chỉ đọc)" và nếu cần "Khôi phục lượt chạy…" trước khi khách đến.

Cần chú ý:
1. Phiên Windows phải mở và không khóa màn hình; không để máy ngủ, tắt màn hình hoặc thu nhỏ kết nối từ xa, vì RPA điều khiển giao diện.
2. Dữ liệu chuẩn bị từ hôm trước có thể lỗi thời: khách đăng ký thêm hoặc hủy trong ngày cần quy trình xử lý tay.
3. Số 10–20 giây và 2,5 giây/khách chưa được người lập đo lại; cần chạy thử 3–5 dòng trên OH thật.

## 5. Độ tin cậy và giới hạn

- Kiểm thử (522 ca, 0 vi phạm, trên OHDemo) chứng minh phần RPA điền vào OH. Xem `Prototype/RPA/KIEM_THU_RPA.md` và `Prototype/RPA/bieu_do/an_toan_rpa.png`.
- Bước gộp Excel thành file tổng và tạo Excel/VBA chưa được kiểm thử, nhưng tạo phần lớn khoản tiết kiệm. File tổng sai thì RPA vẫn nhập đúng theo dữ liệu sai. Đề xuất so một mẫu danh sách làm tay với kết quả tự động trước khi dùng thật.
- RPA chưa được thử trên OH thật; OH thật có thể chậm hơn hoặc có trường, hộp thoại mà bản mô phỏng không có.
- Hoàn tác có giới hạn: chỉ khôi phục hồ sơ đã cập nhật; hồ sơ tạo mới và địa chỉ đã thêm cần người có quyền xử lý.
- Tỷ lệ 10% dòng phải duyệt tay là dự tính, chưa đo trên dữ liệu thật.
- Ước tính cũ "4,8–12 phút/ngày" không có căn cứ trong repo; bảng trên dựa trên số liệu mới ở mục 1.

## 6. Việc cần làm tiếp

1. Chạy thử 3–5 dòng trên OH thật, đo thời gian mỗi khách và tỷ lệ dòng phải duyệt.
2. Đo số phút nhân viên thực sự tiết kiệm ở quầy để quyết định có dùng kịch bản B không.
3. Hỏi nhà cung cấp OH về việc tự động hóa giao diện.
4. Kiểm thử bước gộp Excel bằng một mẫu so sánh với làm tay.
5. Tắt khóa màn hình và chế độ ngủ trên máy chạy RPA ban đêm.
