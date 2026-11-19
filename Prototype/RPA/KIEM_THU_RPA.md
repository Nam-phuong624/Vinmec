# Kiểm thử RPA_OHDemo: các trường hợp có thể gây lỗi

*Báo cáo sinh tự động từ lần chạy thật ngày 2026/11/19 (19:07 – 19:38). Toàn bộ số liệu bên dưới lấy từ file `kiem_thu/ket_qua.json`, không nhập tay.*

## 1. Mục đích và phạm vi

Kiểm tra RPA_OHDemo (đọc danh sách Excel và tự điền vào OHDemo) trong các tình huống có thể sinh lỗi, và ghi nhận kết quả thực tế của từng ca. Mục tiêu không phải chứng minh "không bao giờ lỗi", mà là: (1) tìm ra những chỗ RPA nhập sai hoặc nhập thầm lặng, (2) xác nhận dữ liệu sai/thiếu bị chặn và báo rõ, (3) có số liệu cụ thể để trình bày.

Phạm vi: chương trình `RPA_OHDemo` (bộ điều khiển `rpa_tool/ohdemo_engine.py` và đọc file `shared/excel.py`) làm việc với `OHDemo.exe` (OH mô phỏng). **Không** gồm OH thật, việc in phiếu và chương trình In_Phieu.

## 2. Môi trường và dữ liệu

| Mục | Giá trị |
|---|---|
| Thời điểm chạy | 2026-11-19 19:07:00 → 2026-11-19 19:38:05 |
| Hệ điều hành | Windows-10-10.0.19045-SP0 |
| Python | 3.11.18 |
| Bộ điều khiển (ohdemo_engine.py) | SHA-256 `53230222d75a…` |
| OHDemo.exe | SHA-256 `11c0202eb34b…` |
| Hạt giống sinh dữ liệu | 20261119 |
| Tổng số ca | 522 |

**Dữ liệu:** sinh tự động bằng `kiem_thu/chay_kiem_thu.py` (cùng hạt giống thì ra cùng dữ liệu), lưu ở `kiem_thu/du_lieu_kiem_thu.xlsx` (đúng định dạng file ds bung). Tên người ghép từ danh sách họ, đệm, tên tiếng Việt có dấu; ngày sinh nhiều định dạng (chuỗi dd/mm/yyyy, yyyy-mm-dd, ddmmyyyy, ô ngày của Excel); địa chỉ 2 đến 3 phần; mỗi người duy nhất theo (họ tên, năm sinh) và SĐT. Ngoài dữ liệu hợp lệ còn có các ca sai, lỗi, thiếu đặt tay (nhóm D, E, F, G).

## 3. Phương pháp

1. **Mong đợi viết trước.** Mỗi ca có kết quả mong đợi (Tạo mới / Cập nhật / Không đổi / Lỗi / Cần điền tay) và, nếu là lỗi, từ khóa phải có trong thông báo.
2. **Chạy thật.** Đưa từng dòng qua đúng hàm xử lý của RPA (`process`) trên OHDemo thật, cửa sổ OH hiện bình thường.
3. **Đối soát độc lập.** Sau khi chạy, mở lại từng hồ sơ trong OH, đọc các trường và so với **dữ liệu gốc do người viết ca nêu** (không so với kết quả mà RPA tự tính), để bắt lỗi nhập sai thầm lặng.
4. **Kiểm tra tác động phụ.** Với ca mong đợi "Lỗi", đếm số hồ sơ cùng tên trong OH trước và sau: phải không đổi (không được tạo hoặc sửa gì).
5. **Chạy lại lần 2 (nhóm B).** Chạy lại toàn bộ nhóm A và H: phải ra "Không đổi", không tạo trùng, PID không đổi.
6. **Tiêu chí ĐẠT:** thực tế đúng mong đợi **và** đối soát khớp **và** không có tác động phụ. Chỉ cần sai một điều kiện là KHÔNG ĐẠT.
7. **Lưu ý về tiêu chí:** một số mong đợi (đánh dấu "mong đợi tiêu chí thực tế" trong ghi chú) là yêu cầu hợp lý của người dùng nhưng RPA hiện chưa làm; các ca này KHÔNG ĐẠT là có chủ ý để lộ ra điểm cần cải thiện.

8. **Nhóm I và J (can thiệp và ngắt giữa chừng).** Mỗi ca chèn đúng một thao tác vào giữa hai bước của RPA (người dùng tìm hồ sơ khác, gõ vào ô, bấm nút, thu nhỏ cửa sổ...) hoặc tắt OH / tắt tiến trình RPA / bấm Dừng ở đúng bước đó, rồi đọc lại **toàn bộ** hồ sơ trong OH. ĐẠT khi giữ đủ các bất biến: S1 không đổi hồ sơ khác (không ghi nhầm người); S2 báo thành công thì dữ liệu phải khớp Excel, OH đã tắt thì không được báo thành công; S3 không tạo trùng hay hồ sơ ngoài ý định; S4 hồ sơ nửa vời phải được nêu trong thông báo; S5 (tắt RPA) dòng dở phải để lại dấu vết và dòng lỗi trước đó phải còn trong ds lỗi.xlsx; C1 chạy lại khi không còn can thiệp thì hội tụ đúng. Thao tác "người dùng" được chèn đồng bộ giữa hai bước (tái lập được), không chạy song song ngẫu nhiên.
9. **Nhóm K (phát hiện và hoàn tác sau khi ghi).** Kiểm tra vết trước/sau khớp với hồ sơ thật trong OH, khôi phục hồ sơ cập nhật về giá trị trước (và từ chối khi hồ sơ đã bị người khác sửa), đối soát chỉ đọc không ghi gì vào OH, đối soát phát hiện lệch, trùng, hồ sơ mất, và khôi phục sau khi RPA bị tắt giữa lượt chạy.
## 4. Tổng hợp kết quả

**Tổng: 522 ca, ĐẠT 522, KHÔNG ĐẠT 0 (100.0% đạt trong số ca đã chạy).**

| Nhóm | Số ca | Đạt | Không đạt | Tỷ lệ đạt |
|---|---:|---:|---:|---:|
| A. Người mới hợp lệ (sinh tự động) | 80 | 80 | 0 | 100% |
| B. Chạy lại lần 2 (không được tạo trùng) | 180 | 180 | 0 | 100% |
| C. Cập nhật người đã có | 15 | 15 | 0 | 100% |
| C. Cập nhật (bước chuẩn bị: tạo người gốc) | 15 | 15 | 0 | 100% |
| D. Trùng lặp và nhập nhằng | 10 | 10 | 0 | 100% |
| E. Dữ liệu sai, lỗi, thiếu | 46 | 46 | 0 | 100% |
| F. Lỗi ở file Excel / thư mục | 14 | 14 | 0 | 100% |
| G. Tình huống môi trường | 8 | 8 | 0 | 100% |
| H. Khối lượng (sinh tự động) | 100 | 100 | 0 | 100% |
| I. Người dùng can thiệp khi RPA đang chạy | 22 | 22 | 0 | 100% |
| J. OH hoặc RPA bị ngắt/dừng giữa chừng | 25 | 25 | 0 | 100% |
| K. Phát hiện và hoàn tác sau khi RPA đã ghi | 7 | 7 | 0 | 100% |

**Hiệu năng (nhóm A và H, 180 dòng tạo mới):** trung bình 3.88 giây/dòng, nhanh nhất 3.70, chậm nhất 4.71 giây.

**Luồng chính ổn định:** 360 lần chạy (tạo mới và chạy lại) đều đạt, đối soát khớp. Theo "quy tắc ba", 0 lỗi trong 360 lần chỉ cho phép kết luận tỷ lệ lỗi thật dưới khoảng 0.8% (độ tin cậy 95%), không phải bằng 0.

## 5. Các phát hiện (ca không đạt)

Không có ca nào không đạt.

### Nhóm I và J: so sánh trước và sau khi sửa mã

Cùng bộ 47 ca được chạy trên mã **trước khi sửa** (23 đạt, 24 không đạt) rồi trên mã **sau khi sửa** (47 đạt, 0 không đạt).

| Mã | Tình huống | Trước khi sửa | Sau khi sửa |
|---|---|---|---|
| I01 | Người dùng tìm hồ sơ khác ngay sau khi RPA tìm xong | S2 RPA báo thành công nhưng DEMO0001 lệch Excel: Điện thoại: OH="0900000001" ≠ gốc="0900000009"; Địa chỉ: không thấy "Số 10 Đường Láng, Phường Láng Hạ, Hà Nội" trong [];… | ĐẠT: RPA báo ERROR: ReviewRequired: Kết quả tìm kiếm không phải của dòng này (trang đang mở: list; có thao tác khác trên OH trong lúc RPA chạy?); dừng để … |
| I02 | Người dùng mở hồ sơ khác khi RPA vừa mở DEMO0001 | S1 DEMO0002 bị đổi ngoài ý muốn (trường: title, first, middle, last, sex, dob, phone, addresses; SĐT OH="0900000009", gốc="0900000002"); S2 RPA báo thành công nhưng DEMO… | ĐẠT: RPA báo ERROR: ReviewRequired: Trang Edit đang mở là hồ sơ DEMO0002, không phải DEMO0001 (có thao tác khác trên OH?); dừng để không ghi nhầm người. |
| I05 | Người dùng gõ SĐT khác vào form trước khi RPA bấm Lưu | S1 DEMO0001 bị đổi ngoài ý muốn (trường: phone, addresses; SĐT OH="0111111111", gốc="0900000001"); S2 RPA báo thành công nhưng DEMO0001 lệch Excel: Điện thoại: OH="01111… | ĐẠT: RPA báo ERROR: ReviewRequired: Sau khi lưu, hồ sơ DEMO0001 không khớp dữ liệu Excel (SĐT: OH="0111111111" ≠ Excel="0900000009"); cần kiểm tra tay. |
| I06 | Người dùng đổi họ trên form trước khi RPA bấm Lưu | S1 DEMO0001 bị đổi ngoài ý muốn (trường: first, phone, addresses; SĐT OH="0900000009", gốc="0900000001"); S2 RPA báo thành công nhưng DEMO0001 lệch Excel: Họ: OH="Sai" ≠… | ĐẠT: RPA báo ERROR: ReviewRequired: Sau khi lưu, hồ sơ DEMO0001 không khớp dữ liệu Excel (Họ: OH="Sai" ≠ Excel="Nguyễn"); cần kiểm tra tay. |
| I09 | Người dùng đổi nội dung ô tìm kiếm thành PID | S2 RPA báo thành công nhưng DEMO0001 lệch Excel: Điện thoại: OH="0900000001" ≠ gốc="0900000009"; Địa chỉ: không thấy "Số 10 Đường Láng, Phường Láng Hạ, Hà Nội" trong [];… | ĐẠT: RPA báo ERROR: ReviewRequired: Kết quả tìm kiếm không phải của dòng này (trang đang mở: view; có thao tác khác trên OH trong lúc RPA chạy?); dừng để … |
| I24 | Người dùng tìm hồ sơ khác ngay sau khi hồ sơ mới được tạo | S4 hồ sơ nửa vời NEW000001 không được nêu trong thông báo của RPA | ĐẠT: RPA báo ERROR: ReviewRequired: Hết thời gian chờ: cấp PID mới [trang đang mở: view; dòng trạng thái OH: "Đã mở hồ sơ DEMO0002. Bấm Edit để chỉnh sửa.… |
| I26 | Người dùng mở New Patient ngay sau khi hồ sơ mới được tạo | S4 hồ sơ nửa vời NEW000001 không được nêu trong thông báo của RPA | ĐẠT: RPA báo ERROR: ReviewRequired: Hết thời gian chờ: cấp PID mới [trang đang mở: new; dòng trạng thái OH: "Nhập tên, năm sinh, số điện thoại rồi Save để… |
| I27 | Người dùng tự bấm Save trong khung New Patient trước RPA | S4 hồ sơ nửa vời NEW000001 không được nêu trong thông báo của RPA | ĐẠT: RPA báo ERROR: ReviewRequired: Lỗi khi điều khiển OH (error: (1400, 'PostMessage', 'Invalid window handle.')). [trang đang mở: view; dòng trạng thái … |
| I28 | Người dùng thu nhỏ cửa sổ OH khi RPA đang điền khung New Patient | S4 hồ sơ nửa vời NEW000001 không được nêu trong thông báo của RPA | ĐẠT: RPA báo ERROR: ReviewRequired: Hết thời gian chờ: cấp PID mới [cửa sổ OH đang THU NHỎ (RPA không điều khiển được cửa sổ thu nhỏ); trang đang mở: blan… |
| J11 | RPA bị tắt đột ngột: cập nhật, after search | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J12 | RPA bị tắt đột ngột: cập nhật, after click:edit-toggle | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J13 | RPA bị tắt đột ngột: cập nhật, after read_edit | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J14 | RPA bị tắt đột ngột: cập nhật, after set_text:edit-phone | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J15 | RPA bị tắt đột ngột: cập nhật, before click:edit-save | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J16 | RPA bị tắt đột ngột: cập nhật, after click:edit-save | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J17 | RPA bị tắt đột ngột: tạo mới, after click:new-patient | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J18 | RPA bị tắt đột ngột: tạo mới, after set_text:new-last | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J19 | RPA bị tắt đột ngột: tạo mới, after click:new-save | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J20 | RPA bị tắt đột ngột: tạo mới, after read_edit | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J21 | RPA bị tắt đột ngột: tạo mới, after set_text:edit-dob | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J22 | RPA bị tắt đột ngột: tạo mới, before click:edit-save | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J23 | RPA bị tắt đột ngột: tạo mới, after click:edit-save | S5 không có nhật ký tiến độ: dòng 5 đang dở không để lại dấu vết nào; S5 dòng lỗi dữ liệu 3 (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: chưa có fi… | ĐẠT: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · T… |
| J24 | Người dùng bấm Dừng: tạo mới, after click:new-save | S4 hồ sơ nửa vời NEW000001 không được nêu trong thông báo của RPA | ĐẠT: RPA báo ERROR: ReviewRequired: Đã dừng; dòng này chưa xử lý xong. · LƯU Ý: hồ sơ NEW000001 đã được tạo nhưng chưa bổ sung đủ thông tin; chạy lại RPA … |
| J25 | Người dùng bấm Dừng: tạo mới, after set_text:edit-dob | S4 hồ sơ nửa vời NEW000001 không được nêu trong thông báo của RPA | ĐẠT: RPA báo ERROR: ReviewRequired: Đã dừng; dòng này chưa xử lý xong. · LƯU Ý: hồ sơ NEW000001 đã được tạo nhưng chưa bổ sung đủ thông tin; chạy lại RPA … |

## 6. Kết quả chi tiết từng ca

Cột "Đối soát": **khớp** = hồ sơ đọc lại từ OH khớp dữ liệu gốc; **—** = không áp dụng (ca báo lỗi, hoặc chưa đọc lại); còn lại nêu sai lệch. "Tác động phụ" cho ca mong đợi Lỗi: số hồ sơ cùng tên trước → sau.

### A. Người mới hợp lệ (sinh tự động)

*Rủi ro kiểm tra:* Luồng chính: tìm không thấy → tạo → điền đủ trường → lưu. Đa dạng tên có dấu, định dạng ngày, địa chỉ 2-3 phần, quốc tịch có/không.

| Mã | Dòng | Dữ liệu vào | Mong đợi | Thực tế | PID | Đối soát | Kết quả | Giây |
|---|---:|---|---|---|---|---|---|---:|
| A001 | 3 | Họ=Cao; Đệm=Thùy Thanh; Tên=Anh; NS=23/10/1982; GT=Nữ; SĐT=0909785488; ĐC=Số 156 Đường Láng Hạ, Xã Kiều Phú, Hải Phòng; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000004 | khớp | ĐẠT | 3.77 |
| A002 | 4 | Họ=Vũ; Đệm=Tiến; Tên=Bình; NS=13/06/1971; GT=Nam; SĐT=0994167938; ĐC=Thôn B, Xã M, Tỉnh Bắc Ninh; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000005 | khớp | ĐẠT | 3.9 |
| A003 | 5 | Họ=Đỗ; Đệm=(trống); Tên=Cường; NS=06/08/1962; GT=Nam; SĐT=0927763672; ĐC=Số 147 Đường Hoàng Diệu, Phường Tân Hiệp, Đồng Nai; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000006 | khớp | ĐẠT | 4.16 |
| A004 | 6 | Họ=Lê; Đệm=Thu; Tên=Hồng; NS=10/03/2007; GT=Nữ; SĐT=0974995569; ĐC=Số 171 Đường Phạm Văn Đồng, Phường Lê Lợi, Thái Bình; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000007 | khớp | ĐẠT | 3.89 |
| A005 | 7 | Họ=Hồ; Đệm=Công; Tên=Tùng; NS=02/01/1990; GT=Nam; SĐT=0972168028; ĐC=Số 199 Đường Láng Hạ, Xã Kiều Phú, Hà Nội; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000008 | khớp | ĐẠT | 3.79 |
| A006 | 8 | Họ=Nguyễn; Đệm=Ngọc; Tên=Dung; NS=19/02/2008; GT=Nữ; SĐT=0901215768; ĐC=Số 101 Đường Số 3, Phường Tân Hiệp, Nam Định; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000009 | khớp | ĐẠT | 4.13 |
| A007 | 9 | Họ=Lý; Đệm=Công Công; Tên=Long; NS=21/07/1951; GT=Nam; SĐT=0907540556; ĐC=Thôn A, Xã K, Tỉnh Hà Nội; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000010 | khớp | ĐẠT | 3.77 |
| A008 | 10 | Họ=Vũ; Đệm=Gia; Tên=Đạt; NS=15/04/1999; GT=Nam; SĐT=0933737935; ĐC=Số 144 Đường Hoàng Diệu, Xã Tây Phương, Đồng Nai; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000011 | khớp | ĐẠT | 3.78 |
| A009 | 11 | Họ=Đinh; Đệm=(trống); Tên=Huy; NS=1954-04-15; GT=Nam; SĐT=0944078779; ĐC=Số 168 Đường Trần Phú, Phường Láng Hạ, Hưng Yên; QT=(trống); Title=Anh | Tạo mới | Tạo mới | NEW000012 | khớp | ĐẠT | 4.14 |
| A010 | 12 | Họ=Đặng; Đệm=Quang; Tên=Lâm; NS=17/08/2001; GT=Nam; SĐT=0975765708; ĐC=Số 92 Đường Nguyễn Trãi, Phường Láng Hạ, Hà Nội; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000013 | khớp | ĐẠT | 4.06 |
| A011 | 13 | Họ=Từ; Đệm=Công; Tên=Trung; NS=1969-09-16; GT=Nam; SĐT=0929668315; ĐC=Số 55 Đường Lê Lợi, Phường Mới, Hải Phòng; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000014 | khớp | ĐẠT | 3.78 |
| A012 | 14 | Họ=Trịnh; Đệm=Thùy; Tên=Thúy; NS=24/04/1983; GT=Nữ; SĐT=0992903169; ĐC=Thôn F, Xã K, Tỉnh Đà Nẵng; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000015 | khớp | ĐẠT | 3.78 |
| A013 | 15 | Họ=Đỗ; Đệm=Phương; Tên=Trang; NS=05/09/1978; GT=Nữ; SĐT=0998408783; ĐC=Số 47 Đường Phạm Văn Đồng, Phường Đông Hải, Hà Nội; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000016 | khớp | ĐẠT | 3.8 |
| A014 | 16 | Họ=Đỗ; Đệm=Minh; Tên=An; NS=21/11/1997; GT=Nam; SĐT=0984173701; ĐC=Số 74 Đường Lê Lợi, Phường Đông Hải, Thái Bình; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000017 | khớp | ĐẠT | 3.76 |
| A015 | 17 | Họ=Lý; Đệm=Hồng; Tên=Thúy; NS=08/05/2003; GT=Nữ; SĐT=0971112161; ĐC=Số 177 Đường Hoàng Diệu, Phường Đông Hải, Bắc Ninh; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000018 | khớp | ĐẠT | 3.71 |
| A016 | 18 | Họ=Phạm; Đệm=Đức Xuân; Tên=Nam; NS=02/11/1951; GT=Nam; SĐT=0931504970; ĐC=Số 167 Đường Trần Phú, Phường Tân Hiệp, Hải Phòng; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000019 | khớp | ĐẠT | 4.06 |
| A017 | 19 | Họ=Hồ; Đệm=Phương; Tên=Vy; NS=13/08/1987; GT=Nữ; SĐT=0993452622; ĐC=Thôn B, Xã I, Tỉnh Bắc Ninh; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000020 | khớp | ĐẠT | 3.84 |
| A018 | 20 | Họ=Ngô; Đệm=Bích; Tên=Ngân; NS=11/04/1974; GT=Nữ; SĐT=0970223563; ĐC=Số 47 Đường Phạm Văn Đồng, Phường Mới, Ninh Bình; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000021 | khớp | ĐẠT | 3.83 |
| A019 | 21 | Họ=Huỳnh; Đệm=Đức; Tên=Nam; NS=19/10/1990; GT=Nam; SĐT=0989573128; ĐC=Số 166 Đường Số 3, Phường Láng Hạ, Bắc Ninh; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000022 | khớp | ĐẠT | 3.8 |
| A020 | 22 | Họ=Bùi; Đệm=Kim Thùy; Tên=Ánh; NS=08/03/1980; GT=Nữ; SĐT=0951608045; ĐC=Số 109 Đường Điện Biên Phủ, Phường Lê Lợi, Hải Phòng; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000023 | khớp | ĐẠT | 4.21 |
| A021 | 23 | Họ=Nguyễn; Đệm=Thị; Tên=Lan; NS=01/10/1954; GT=Nữ; SĐT=0986426295; ĐC=Số 79 Đường Điện Biên Phủ, Xã Tây Phương, Hà Nội; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000024 | khớp | ĐẠT | 4.04 |
| A022 | 24 | Họ=Đoàn; Đệm=Quốc; Tên=An; NS=12/01/1970; GT=Nam; SĐT=0900384791; ĐC=Số 181 Đường Nguyễn Trãi, Phường Tân Hiệp, Đồng Nai; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000025 | khớp | ĐẠT | 3.78 |
| A023 | 25 | Họ=Nguyễn; Đệm=(trống); Tên=Trang; NS=27/03/1957; GT=Nữ; SĐT=0940717695; ĐC=Số 69 Đường Phạm Văn Đồng, Phường Đông Hải, Nam Định; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000026 | khớp | ĐẠT | 3.77 |
| A024 | 26 | Họ=Nguyễn; Đệm=(trống); Tên=Quỳnh; NS=17/03/1999; GT=Nữ; SĐT=0992629860; ĐC=Số 131 Đường Phạm Văn Đồng, Phường Lê Lợi, Thái Bình; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000027 | khớp | ĐẠT | 4.13 |
| A025 | 27 | Họ=Cao; Đệm=Tiến; Tên=Tùng; NS=18/02/2009; GT=Nam; SĐT=0971561215; ĐC=Số 24 Đường Láng Hạ, Phường Mới, Ninh Bình; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000028 | khớp | ĐẠT | 3.73 |
| A026 | 28 | Họ=Từ; Đệm=Diệu; Tên=Diễm; NS=24/10/1980; GT=Nữ; SĐT=0938334042; ĐC=Số 172 Đường Lê Lợi, Phường Đông Hải, Bắc Ninh; QT=(trống); Title=Chị | Tạo mới | Tạo mới | NEW000029 | khớp | ĐẠT | 3.87 |
| A027 | 29 | Họ=Đỗ; Đệm=Tiến; Tên=Long; NS=16/09/1973; GT=Nam; SĐT=0949590758; ĐC=Số 85 Đường Hoàng Diệu, Xã Tây Phương, Thái Bình; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000030 | khớp | ĐẠT | 4.1 |
| A028 | 30 | Họ=Lý; Đệm=Thanh; Tên=Hà; NS=ngày giờ 2012-12-22; GT=Nữ; SĐT=0924081516; ĐC=Số 104 Đường Hoàng Diệu, Phường Mới, Hải Phòng; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000031 | khớp | ĐẠT | 3.72 |
| A029 | 31 | Họ=Hoàng; Đệm=Công; Tên=Dũng; NS=ngày giờ 2011-10-28; GT=Nam; SĐT=0925519237; ĐC=Số 182 Đường Hoàng Diệu, Xã Kiều Phú, Bắc Ninh; QT=(trống); Title=Anh | Tạo mới | Tạo mới | NEW000032 | khớp | ĐẠT | 3.73 |
| A030 | 32 | Họ=Đinh; Đệm=Thanh Quang; Tên=Hải; NS=28/09/1963; GT=Nam; SĐT=0937153692; ĐC=Thôn F, Xã L, Tỉnh Ninh Bình; QT=(trống); Title=Ông | Tạo mới | Tạo mới | NEW000033 | khớp | ĐẠT | 3.75 |
| A031 | 33 | Họ=Lương; Đệm=Hồng; Tên=Quỳnh; NS=1952-04-13; GT=Nữ; SĐT=0907795237; ĐC=Số 77 Đường Nguyễn Trãi, Phường Tân Hiệp, Hải Phòng; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000034 | khớp | ĐẠT | 3.75 |
| A032 | 34 | Họ=Nguyễn; Đệm=Quang; Tên=Bình; NS=13/09/1977; GT=Nam; SĐT=0911470703; ĐC=Số 119 Đường Trần Phú, Phường Lê Lợi, Đồng Nai; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000035 | khớp | ĐẠT | 3.7 |
| A033 | 35 | Họ=Tạ; Đệm=Thị; Tên=Yến; NS=02/10/2002; GT=Nữ; SĐT=0942000177; ĐC=Số 112 Đường Nguyễn Trãi, Phường Đông Hải, Hưng Yên; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000036 | khớp | ĐẠT | 3.86 |
| A034 | 36 | Họ=Hồ; Đệm=Kim Kim; Tên=Dung; NS=03/12/1988; GT=Nữ; SĐT=0972240980; ĐC=Thôn C, Xã H, Tỉnh Hà Nội; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000037 | khớp | ĐẠT | 4.01 |
| A035 | 37 | Họ=Trịnh; Đệm=Hữu; Tên=Phúc; NS=11/08/1974; GT=Nam; SĐT=0966863473; ĐC=Số 101 Đường Lê Lợi, Xã Kiều Phú, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000038 | khớp | ĐẠT | 3.73 |
| A036 | 38 | Họ=Huỳnh; Đệm=Thùy; Tên=Mai; NS=04/03/1973; GT=Nữ; SĐT=0981595125; ĐC=Số 130 Đường Phạm Văn Đồng, Phường Láng Hạ, Đồng Nai; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000039 | khớp | ĐẠT | 3.72 |
| A037 | 39 | Họ=Phan; Đệm=Công; Tên=Việt; NS=12/10/1978; GT=Nam; SĐT=0930168312; ĐC=Số 163 Đường Số 3, Xã Tây Phương, Hải Phòng; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000040 | khớp | ĐẠT | 4.06 |
| A038 | 40 | Họ=Chử; Đệm=(trống); Tên=Nghĩa; NS=1957-06-23; GT=Nam; SĐT=0996410970; ĐC=Số 74 Đường Điện Biên Phủ, Xã Kiều Phú, Thái Bình; QT=(trống); Title=Ông | Tạo mới | Tạo mới | NEW000041 | khớp | ĐẠT | 4.12 |
| A039 | 41 | Họ=Đoàn; Đệm=Hồng Thị; Tên=Hồng; NS=03/01/2008; GT=Nữ; SĐT=0943822823; ĐC=Số 72 Đường Lê Lợi, Phường Tân Hiệp, Ninh Bình; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000042 | khớp | ĐẠT | 3.81 |
| A040 | 42 | Họ=Huỳnh; Đệm=Thu; Tên=Ngân; NS=ngày giờ 1986-08-15; GT=Nữ; SĐT=0951301030; ĐC=Số 194 Đường Láng Hạ, Phường Đông Hải, Hải Phòng; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000043 | khớp | ĐẠT | 3.82 |
| A041 | 43 | Họ=Bùi; Đệm=(trống); Tên=Quân; NS=26/01/1995; GT=Nam; SĐT=0921377926; ĐC=5 Nguyễn Trãi, Bắc Ninh; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000044 | khớp | ĐẠT | 4.08 |
| A042 | 44 | Họ=Dương; Đệm=(trống); Tên=Châu; NS=13/02/2007; GT=Nữ; SĐT=0989154819; ĐC=Số 49 Đường Nguyễn Trãi, Phường Lê Lợi, Thái Bình; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000045 | khớp | ĐẠT | 3.76 |
| A043 | 45 | Họ=Bùi; Đệm=Đức; Tên=Tùng; NS=23/02/2008; GT=Nam; SĐT=0920177298; ĐC=Số 84 Đường Hoàng Diệu, Phường Lê Lợi, Đà Nẵng; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000046 | khớp | ĐẠT | 3.81 |
| A044 | 46 | Họ=Phạm; Đệm=Văn; Tên=Tuấn; NS=13/09/1972; GT=Nam; SĐT=0952246394; ĐC=42 Điện Biên Phủ, Ninh Bình; QT=(trống); Title=Ông | Tạo mới | Tạo mới | NEW000047 | khớp | ĐẠT | 4.18 |
| A045 | 47 | Họ=Lê; Đệm=Văn; Tên=Dũng; NS=ngày giờ 1965-11-17; GT=Nam; SĐT=0969089321; ĐC=9 Láng Hạ, Bắc Ninh; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000048 | khớp | ĐẠT | 3.88 |
| A046 | 48 | Họ=Lý; Đệm=Tiến; Tên=Đạt; NS=23/05/1972; GT=Nam; SĐT=0986630453; ĐC=Số 197 Đường Hoàng Diệu, Xã Kiều Phú, Đà Nẵng; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000049 | khớp | ĐẠT | 3.7 |
| A047 | 49 | Họ=Dương; Đệm=Thanh; Tên=Thúy; NS=11/01/1973; GT=Nữ; SĐT=0959122870; ĐC=Thôn G, Xã L, Tỉnh Đà Nẵng; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000050 | khớp | ĐẠT | 3.75 |
| A048 | 50 | Họ=Hồ; Đệm=Tiến; Tên=Tuấn; NS=02/11/1980; GT=Nam; SĐT=0945324080; ĐC=Số 185 Đường Láng Hạ, Phường Láng Hạ, Ninh Bình; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000051 | khớp | ĐẠT | 3.77 |
| A049 | 51 | Họ=Hồ; Đệm=(trống); Tên=Long; NS=23/09/1983; GT=Nam; SĐT=0957338611; ĐC=Thôn A, Xã H, Tỉnh Đồng Nai; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000052 | khớp | ĐẠT | 3.73 |
| A050 | 52 | Họ=Trịnh; Đệm=Gia; Tên=Huy; NS=21/11/2012; GT=Nam; SĐT=0949604350; ĐC=Số 84 Đường Lê Lợi, Phường Lê Lợi, Hải Phòng; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000053 | khớp | ĐẠT | 3.72 |
| A051 | 53 | Họ=Hồ; Đệm=Công; Tên=Huy; NS=03/05/2015; GT=Nam; SĐT=0973482912; ĐC=Thôn A, Xã I, Tỉnh Đồng Nai; QT=Việt Nam; Title=Bé | Tạo mới | Tạo mới | NEW000054 | khớp | ĐẠT | 4.28 |
| A052 | 54 | Họ=Đinh; Đệm=Thu; Tên=Quỳnh; NS=20/07/1960; GT=Nữ; SĐT=0944019081; ĐC=Số 8 Đường Phạm Văn Đồng, Xã Tây Phương, Hà Nội; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000055 | khớp | ĐẠT | 3.87 |
| A053 | 55 | Họ=Ngô; Đệm=Ngọc; Tên=Thúy; NS=11/12/2016; GT=Nữ; SĐT=0955246171; ĐC=Thôn F, Xã K, Tỉnh Nam Định; QT=Việt Nam; Title=Bé | Tạo mới | Tạo mới | NEW000056 | khớp | ĐẠT | 3.76 |
| A054 | 56 | Họ=Hoàng; Đệm=Thu Thanh; Tên=Diễm; NS=04/08/1994; GT=Nữ; SĐT=0976402641; ĐC=Số 23 Đường Điện Biên Phủ, Xã Kiều Phú, Thái Bình; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000057 | khớp | ĐẠT | 3.88 |
| A055 | 57 | Họ=Cao; Đệm=Hồng; Tên=Thúy; NS=16/09/1969; GT=Nữ; SĐT=0914064298; ĐC=Thôn F, Xã L, Tỉnh Thái Bình; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000058 | khớp | ĐẠT | 4.32 |
| A056 | 58 | Họ=Cao; Đệm=Minh; Tên=Tuấn; NS=ngày giờ 1995-07-26; GT=Nam; SĐT=0966831608; ĐC=12 Lê Lợi, Hà Nội; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000059 | khớp | ĐẠT | 3.86 |
| A057 | 59 | Họ=Lê; Đệm=Hữu; Tên=Việt; NS=14/09/2006; GT=Nam; SĐT=0970065710; ĐC=Thôn E, Xã K, Tỉnh Hưng Yên; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000060 | khớp | ĐẠT | 3.81 |
| A058 | 60 | Họ=Quản; Đệm=Diệu; Tên=Phương; NS=15/10/1953; GT=Nữ; SĐT=0959056252; ĐC=Thôn E, Xã I, Tỉnh Thái Bình; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000061 | khớp | ĐẠT | 3.77 |
| A059 | 61 | Họ=Chử; Đệm=Xuân; Tên=Cường; NS=24/11/1998; GT=Nam; SĐT=0918989527; ĐC=Thôn B, Xã K, Tỉnh Đà Nẵng; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000062 | khớp | ĐẠT | 4.07 |
| A060 | 62 | Họ=Đoàn; Đệm=Ngọc; Tên=Thảo; NS=15/01/1967; GT=Nữ; SĐT=0905911978; ĐC=Số 131 Đường Hoàng Diệu, Phường Lê Lợi, Hưng Yên; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000063 | khớp | ĐẠT | 3.86 |
| A061 | 63 | Họ=Tạ; Đệm=Văn Văn; Tên=Cường; NS=09/03/1989; GT=Nam; SĐT=0947007681; ĐC=Số 48 Đường Hoàng Diệu, Xã Tây Phương, Hà Nội; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000064 | khớp | ĐẠT | 4.16 |
| A062 | 64 | Họ=Đỗ; Đệm=Thị Thị; Tên=Mai; NS=23/12/2004; GT=Nữ; SĐT=0932657004; ĐC=Số 152 Đường Hoàng Diệu, Xã Tây Phương, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000065 | khớp | ĐẠT | 3.94 |
| A063 | 65 | Họ=Lý; Đệm=Thanh; Tên=Nam; NS=02/12/1980; GT=Nam; SĐT=0998999988; ĐC=Số 16 Đường Phạm Văn Đồng, Phường Tân Hiệp, Nam Định; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000066 | khớp | ĐẠT | 3.74 |
| A064 | 66 | Họ=Trần; Đệm=Hữu; Tên=Lâm; NS=13/02/2010; GT=Nam; SĐT=0906392747; ĐC=Số 4 Đường Trần Phú, Phường Lê Lợi, Nam Định; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000067 | khớp | ĐẠT | 3.71 |
| A065 | 67 | Họ=Hồ; Đệm=(trống); Tên=Thành; NS=27/07/1953; GT=Nam; SĐT=0950753719; ĐC=Thôn E, Xã L, Tỉnh Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000068 | khớp | ĐẠT | 3.93 |
| A066 | 68 | Họ=Trần; Đệm=(trống); Tên=Long; NS=10/01/1981; GT=Nam; SĐT=0946182438; ĐC=Số 199 Đường Nguyễn Trãi, Phường Tân Hiệp, Nam Định; QT=(trống); Title=Ông | Tạo mới | Tạo mới | NEW000069 | khớp | ĐẠT | 3.73 |
| A067 | 69 | Họ=Đặng; Đệm=Diệu; Tên=Dung; NS=24/05/1965; GT=Nữ; SĐT=0909226760; ĐC=Số 177 Đường Nguyễn Trãi, Xã Tây Phương, Thái Bình; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000070 | khớp | ĐẠT | 3.73 |
| A068 | 70 | Họ=Lý; Đệm=Quang; Tên=Đạt; NS=1960-02-26; GT=Nam; SĐT=0928789532; ĐC=Số 175 Đường Trần Phú, Xã Kiều Phú, Bắc Ninh; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000071 | khớp | ĐẠT | 3.98 |
| A069 | 71 | Họ=Bùi; Đệm=Kim; Tên=Thúy; NS=15/06/1953; GT=Nữ; SĐT=0989353331; ĐC=Số 113 Đường Trần Phú, Phường Láng Hạ, Hưng Yên; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000072 | khớp | ĐẠT | 4.05 |
| A070 | 72 | Họ=Phan; Đệm=Quang; Tên=Sơn; NS=05/02/1980; GT=Nam; SĐT=0956745926; ĐC=Số 80 Đường Hoàng Diệu, Phường Mới, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000073 | khớp | ĐẠT | 3.8 |
| A071 | 73 | Họ=Bùi; Đệm=Quốc; Tên=Thành; NS=12/01/2016; GT=Nam; SĐT=0904950369; ĐC=Số 2 Đường Lê Lợi, Phường Lê Lợi, Đà Nẵng; QT=Việt Nam; Title=Bé | Tạo mới | Tạo mới | NEW000074 | khớp | ĐẠT | 3.82 |
| A072 | 74 | Họ=Phạm; Đệm=Gia; Tên=Huy; NS=16/10/1956; GT=Nam; SĐT=0977550017; ĐC=Thôn A, Xã N, Tỉnh Ninh Bình; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000075 | khớp | ĐẠT | 4.71 |
| A073 | 75 | Họ=Phan; Đệm=(trống); Tên=Nghĩa; NS=01/07/1978; GT=Nam; SĐT=0906521454; ĐC=Số 69 Đường Số 3, Phường Đông Hải, Thái Bình; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000076 | khớp | ĐẠT | 3.83 |
| A074 | 76 | Họ=Đoàn; Đệm=Thu; Tên=Diễm; NS=14/11/1989; GT=Nữ; SĐT=0909893967; ĐC=Thôn C, Xã N, Tỉnh Hưng Yên; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000077 | khớp | ĐẠT | 3.77 |
| A075 | 77 | Họ=Đỗ; Đệm=Ngọc; Tên=Quân; NS=15/11/1962; GT=Nam; SĐT=0949480281; ĐC=Số 188 Đường Số 3, Phường Đông Hải, Hưng Yên; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000078 | khớp | ĐẠT | 3.79 |
| A076 | 78 | Họ=Dương; Đệm=Minh; Tên=Kiên; NS=05/06/1989; GT=Nam; SĐT=0903981405; ĐC=31 Lê Lợi, Hưng Yên; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000079 | khớp | ĐẠT | 4.06 |
| A077 | 79 | Họ=Dương; Đệm=Ngọc; Tên=An; NS=01/03/1952; GT=Nam; SĐT=0949420910; ĐC=Thôn A, Xã N, Tỉnh Đồng Nai; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000080 | khớp | ĐẠT | 3.88 |
| A078 | 80 | Họ=Võ; Đệm=Ngọc; Tên=Sơn; NS=27/07/1951; GT=Nam; SĐT=0924810135; ĐC=39 Điện Biên Phủ, Bắc Ninh; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000081 | khớp | ĐẠT | 3.97 |
| A079 | 81 | Họ=Ngô; Đệm=Hồng; Tên=Hà; NS=24/04/1952; GT=Nữ; SĐT=0901369330; ĐC=Số 96 Đường Lê Lợi, Phường Láng Hạ, Hưng Yên; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000082 | khớp | ĐẠT | 3.99 |
| A080 | 82 | Họ=Lê; Đệm=Đức; Tên=Nghĩa; NS=24/01/1962; GT=Nam; SĐT=0937932591; ĐC=Số 144 Đường Láng Hạ, Phường Đông Hải, Bắc Ninh; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000083 | khớp | ĐẠT | 3.91 |

### B. Chạy lại lần 2 (không được tạo trùng)

*Rủi ro kiểm tra:* Chạy lại cùng dữ liệu phải ra "Không đổi", không tạo thêm hồ sơ.

| Mã | Dòng | Dữ liệu vào | Mong đợi | Thực tế | PID | Đối soát | Kết quả | Giây |
|---|---:|---|---|---|---|---|---|---:|
| A001-L2 | 3 | Họ=Cao; Đệm=Thùy Thanh; Tên=Anh; NS=23/10/1982; GT=Nữ; SĐT=0909785488; ĐC=Số 156 Đường Láng Hạ, Xã Kiều Phú, Hải Phòng; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000004 | — | ĐẠT | 2.24 |
| A002-L2 | 4 | Họ=Vũ; Đệm=Tiến; Tên=Bình; NS=13/06/1971; GT=Nam; SĐT=0994167938; ĐC=Thôn B, Xã M, Tỉnh Bắc Ninh; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000005 | — | ĐẠT | 2.12 |
| A003-L2 | 5 | Họ=Đỗ; Đệm=(trống); Tên=Cường; NS=06/08/1962; GT=Nam; SĐT=0927763672; ĐC=Số 147 Đường Hoàng Diệu, Phường Tân Hiệp, Đồng Nai; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000006 | — | ĐẠT | 2.12 |
| A004-L2 | 6 | Họ=Lê; Đệm=Thu; Tên=Hồng; NS=10/03/2007; GT=Nữ; SĐT=0974995569; ĐC=Số 171 Đường Phạm Văn Đồng, Phường Lê Lợi, Thái Bình; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000007 | — | ĐẠT | 2.1 |
| A005-L2 | 7 | Họ=Hồ; Đệm=Công; Tên=Tùng; NS=02/01/1990; GT=Nam; SĐT=0972168028; ĐC=Số 199 Đường Láng Hạ, Xã Kiều Phú, Hà Nội; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000008 | — | ĐẠT | 2.13 |
| A006-L2 | 8 | Họ=Nguyễn; Đệm=Ngọc; Tên=Dung; NS=19/02/2008; GT=Nữ; SĐT=0901215768; ĐC=Số 101 Đường Số 3, Phường Tân Hiệp, Nam Định; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000009 | — | ĐẠT | 2.25 |
| A007-L2 | 9 | Họ=Lý; Đệm=Công Công; Tên=Long; NS=21/07/1951; GT=Nam; SĐT=0907540556; ĐC=Thôn A, Xã K, Tỉnh Hà Nội; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000010 | — | ĐẠT | 2.22 |
| A008-L2 | 10 | Họ=Vũ; Đệm=Gia; Tên=Đạt; NS=15/04/1999; GT=Nam; SĐT=0933737935; ĐC=Số 144 Đường Hoàng Diệu, Xã Tây Phương, Đồng Nai; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000011 | — | ĐẠT | 2.23 |
| A009-L2 | 11 | Họ=Đinh; Đệm=(trống); Tên=Huy; NS=1954-04-15; GT=Nam; SĐT=0944078779; ĐC=Số 168 Đường Trần Phú, Phường Láng Hạ, Hưng Yên; QT=(trống); Title=Anh | Không đổi | Không đổi | NEW000012 | — | ĐẠT | 2.15 |
| A010-L2 | 12 | Họ=Đặng; Đệm=Quang; Tên=Lâm; NS=17/08/2001; GT=Nam; SĐT=0975765708; ĐC=Số 92 Đường Nguyễn Trãi, Phường Láng Hạ, Hà Nội; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000013 | — | ĐẠT | 2.13 |
| A011-L2 | 13 | Họ=Từ; Đệm=Công; Tên=Trung; NS=1969-09-16; GT=Nam; SĐT=0929668315; ĐC=Số 55 Đường Lê Lợi, Phường Mới, Hải Phòng; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000014 | — | ĐẠT | 2.15 |
| A012-L2 | 14 | Họ=Trịnh; Đệm=Thùy; Tên=Thúy; NS=24/04/1983; GT=Nữ; SĐT=0992903169; ĐC=Thôn F, Xã K, Tỉnh Đà Nẵng; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000015 | — | ĐẠT | 2.27 |
| A013-L2 | 15 | Họ=Đỗ; Đệm=Phương; Tên=Trang; NS=05/09/1978; GT=Nữ; SĐT=0998408783; ĐC=Số 47 Đường Phạm Văn Đồng, Phường Đông Hải, Hà Nội; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000016 | — | ĐẠT | 2.48 |
| A014-L2 | 16 | Họ=Đỗ; Đệm=Minh; Tên=An; NS=21/11/1997; GT=Nam; SĐT=0984173701; ĐC=Số 74 Đường Lê Lợi, Phường Đông Hải, Thái Bình; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000017 | — | ĐẠT | 2.41 |
| A015-L2 | 17 | Họ=Lý; Đệm=Hồng; Tên=Thúy; NS=08/05/2003; GT=Nữ; SĐT=0971112161; ĐC=Số 177 Đường Hoàng Diệu, Phường Đông Hải, Bắc Ninh; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000018 | — | ĐẠT | 2.11 |
| A016-L2 | 18 | Họ=Phạm; Đệm=Đức Xuân; Tên=Nam; NS=02/11/1951; GT=Nam; SĐT=0931504970; ĐC=Số 167 Đường Trần Phú, Phường Tân Hiệp, Hải Phòng; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000019 | — | ĐẠT | 2.09 |
| A017-L2 | 19 | Họ=Hồ; Đệm=Phương; Tên=Vy; NS=13/08/1987; GT=Nữ; SĐT=0993452622; ĐC=Thôn B, Xã I, Tỉnh Bắc Ninh; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000020 | — | ĐẠT | 2.15 |
| A018-L2 | 20 | Họ=Ngô; Đệm=Bích; Tên=Ngân; NS=11/04/1974; GT=Nữ; SĐT=0970223563; ĐC=Số 47 Đường Phạm Văn Đồng, Phường Mới, Ninh Bình; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000021 | — | ĐẠT | 2.12 |
| A019-L2 | 21 | Họ=Huỳnh; Đệm=Đức; Tên=Nam; NS=19/10/1990; GT=Nam; SĐT=0989573128; ĐC=Số 166 Đường Số 3, Phường Láng Hạ, Bắc Ninh; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000022 | — | ĐẠT | 2.16 |
| A020-L2 | 22 | Họ=Bùi; Đệm=Kim Thùy; Tên=Ánh; NS=08/03/1980; GT=Nữ; SĐT=0951608045; ĐC=Số 109 Đường Điện Biên Phủ, Phường Lê Lợi, Hải Phòng; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000023 | — | ĐẠT | 2.05 |
| A021-L2 | 23 | Họ=Nguyễn; Đệm=Thị; Tên=Lan; NS=01/10/1954; GT=Nữ; SĐT=0986426295; ĐC=Số 79 Đường Điện Biên Phủ, Xã Tây Phương, Hà Nội; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000024 | — | ĐẠT | 2.11 |
| A022-L2 | 24 | Họ=Đoàn; Đệm=Quốc; Tên=An; NS=12/01/1970; GT=Nam; SĐT=0900384791; ĐC=Số 181 Đường Nguyễn Trãi, Phường Tân Hiệp, Đồng Nai; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000025 | — | ĐẠT | 2.15 |
| A023-L2 | 25 | Họ=Nguyễn; Đệm=(trống); Tên=Trang; NS=27/03/1957; GT=Nữ; SĐT=0940717695; ĐC=Số 69 Đường Phạm Văn Đồng, Phường Đông Hải, Nam Định; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000026 | — | ĐẠT | 2.12 |
| A024-L2 | 26 | Họ=Nguyễn; Đệm=(trống); Tên=Quỳnh; NS=17/03/1999; GT=Nữ; SĐT=0992629860; ĐC=Số 131 Đường Phạm Văn Đồng, Phường Lê Lợi, Thái Bình; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000027 | — | ĐẠT | 2.24 |
| A025-L2 | 27 | Họ=Cao; Đệm=Tiến; Tên=Tùng; NS=18/02/2009; GT=Nam; SĐT=0971561215; ĐC=Số 24 Đường Láng Hạ, Phường Mới, Ninh Bình; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000028 | — | ĐẠT | 2.29 |
| A026-L2 | 28 | Họ=Từ; Đệm=Diệu; Tên=Diễm; NS=24/10/1980; GT=Nữ; SĐT=0938334042; ĐC=Số 172 Đường Lê Lợi, Phường Đông Hải, Bắc Ninh; QT=(trống); Title=Chị | Không đổi | Không đổi | NEW000029 | — | ĐẠT | 2.2 |
| A027-L2 | 29 | Họ=Đỗ; Đệm=Tiến; Tên=Long; NS=16/09/1973; GT=Nam; SĐT=0949590758; ĐC=Số 85 Đường Hoàng Diệu, Xã Tây Phương, Thái Bình; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000030 | — | ĐẠT | 2.15 |
| A028-L2 | 30 | Họ=Lý; Đệm=Thanh; Tên=Hà; NS=ngày giờ 2012-12-22; GT=Nữ; SĐT=0924081516; ĐC=Số 104 Đường Hoàng Diệu, Phường Mới, Hải Phòng; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000031 | — | ĐẠT | 2.13 |
| A029-L2 | 31 | Họ=Hoàng; Đệm=Công; Tên=Dũng; NS=ngày giờ 2011-10-28; GT=Nam; SĐT=0925519237; ĐC=Số 182 Đường Hoàng Diệu, Xã Kiều Phú, Bắc Ninh; QT=(trống); Title=Anh | Không đổi | Không đổi | NEW000032 | — | ĐẠT | 2.13 |
| A030-L2 | 32 | Họ=Đinh; Đệm=Thanh Quang; Tên=Hải; NS=28/09/1963; GT=Nam; SĐT=0937153692; ĐC=Thôn F, Xã L, Tỉnh Ninh Bình; QT=(trống); Title=Ông | Không đổi | Không đổi | NEW000033 | — | ĐẠT | 2.2 |
| A031-L2 | 33 | Họ=Lương; Đệm=Hồng; Tên=Quỳnh; NS=1952-04-13; GT=Nữ; SĐT=0907795237; ĐC=Số 77 Đường Nguyễn Trãi, Phường Tân Hiệp, Hải Phòng; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000034 | — | ĐẠT | 2.16 |
| A032-L2 | 34 | Họ=Nguyễn; Đệm=Quang; Tên=Bình; NS=13/09/1977; GT=Nam; SĐT=0911470703; ĐC=Số 119 Đường Trần Phú, Phường Lê Lợi, Đồng Nai; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000035 | — | ĐẠT | 2.23 |
| A033-L2 | 35 | Họ=Tạ; Đệm=Thị; Tên=Yến; NS=02/10/2002; GT=Nữ; SĐT=0942000177; ĐC=Số 112 Đường Nguyễn Trãi, Phường Đông Hải, Hưng Yên; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000036 | — | ĐẠT | 2.14 |
| A034-L2 | 36 | Họ=Hồ; Đệm=Kim Kim; Tên=Dung; NS=03/12/1988; GT=Nữ; SĐT=0972240980; ĐC=Thôn C, Xã H, Tỉnh Hà Nội; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000037 | — | ĐẠT | 2.12 |
| A035-L2 | 37 | Họ=Trịnh; Đệm=Hữu; Tên=Phúc; NS=11/08/1974; GT=Nam; SĐT=0966863473; ĐC=Số 101 Đường Lê Lợi, Xã Kiều Phú, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000038 | — | ĐẠT | 2.19 |
| A036-L2 | 38 | Họ=Huỳnh; Đệm=Thùy; Tên=Mai; NS=04/03/1973; GT=Nữ; SĐT=0981595125; ĐC=Số 130 Đường Phạm Văn Đồng, Phường Láng Hạ, Đồng Nai; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000039 | — | ĐẠT | 2.1 |
| A037-L2 | 39 | Họ=Phan; Đệm=Công; Tên=Việt; NS=12/10/1978; GT=Nam; SĐT=0930168312; ĐC=Số 163 Đường Số 3, Xã Tây Phương, Hải Phòng; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000040 | — | ĐẠT | 2.32 |
| A038-L2 | 40 | Họ=Chử; Đệm=(trống); Tên=Nghĩa; NS=1957-06-23; GT=Nam; SĐT=0996410970; ĐC=Số 74 Đường Điện Biên Phủ, Xã Kiều Phú, Thái Bình; QT=(trống); Title=Ông | Không đổi | Không đổi | NEW000041 | — | ĐẠT | 2.21 |
| A039-L2 | 41 | Họ=Đoàn; Đệm=Hồng Thị; Tên=Hồng; NS=03/01/2008; GT=Nữ; SĐT=0943822823; ĐC=Số 72 Đường Lê Lợi, Phường Tân Hiệp, Ninh Bình; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000042 | — | ĐẠT | 2.17 |
| A040-L2 | 42 | Họ=Huỳnh; Đệm=Thu; Tên=Ngân; NS=ngày giờ 1986-08-15; GT=Nữ; SĐT=0951301030; ĐC=Số 194 Đường Láng Hạ, Phường Đông Hải, Hải Phòng; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000043 | — | ĐẠT | 2.13 |
| A041-L2 | 43 | Họ=Bùi; Đệm=(trống); Tên=Quân; NS=26/01/1995; GT=Nam; SĐT=0921377926; ĐC=5 Nguyễn Trãi, Bắc Ninh; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000044 | — | ĐẠT | 2.23 |
| A042-L2 | 44 | Họ=Dương; Đệm=(trống); Tên=Châu; NS=13/02/2007; GT=Nữ; SĐT=0989154819; ĐC=Số 49 Đường Nguyễn Trãi, Phường Lê Lợi, Thái Bình; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000045 | — | ĐẠT | 2.19 |
| A043-L2 | 45 | Họ=Bùi; Đệm=Đức; Tên=Tùng; NS=23/02/2008; GT=Nam; SĐT=0920177298; ĐC=Số 84 Đường Hoàng Diệu, Phường Lê Lợi, Đà Nẵng; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000046 | — | ĐẠT | 2.17 |
| A044-L2 | 46 | Họ=Phạm; Đệm=Văn; Tên=Tuấn; NS=13/09/1972; GT=Nam; SĐT=0952246394; ĐC=42 Điện Biên Phủ, Ninh Bình; QT=(trống); Title=Ông | Không đổi | Không đổi | NEW000047 | — | ĐẠT | 2.32 |
| A045-L2 | 47 | Họ=Lê; Đệm=Văn; Tên=Dũng; NS=ngày giờ 1965-11-17; GT=Nam; SĐT=0969089321; ĐC=9 Láng Hạ, Bắc Ninh; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000048 | — | ĐẠT | 2.36 |
| A046-L2 | 48 | Họ=Lý; Đệm=Tiến; Tên=Đạt; NS=23/05/1972; GT=Nam; SĐT=0986630453; ĐC=Số 197 Đường Hoàng Diệu, Xã Kiều Phú, Đà Nẵng; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000049 | — | ĐẠT | 2.25 |
| A047-L2 | 49 | Họ=Dương; Đệm=Thanh; Tên=Thúy; NS=11/01/1973; GT=Nữ; SĐT=0959122870; ĐC=Thôn G, Xã L, Tỉnh Đà Nẵng; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000050 | — | ĐẠT | 2.18 |
| A048-L2 | 50 | Họ=Hồ; Đệm=Tiến; Tên=Tuấn; NS=02/11/1980; GT=Nam; SĐT=0945324080; ĐC=Số 185 Đường Láng Hạ, Phường Láng Hạ, Ninh Bình; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000051 | — | ĐẠT | 2.11 |
| A049-L2 | 51 | Họ=Hồ; Đệm=(trống); Tên=Long; NS=23/09/1983; GT=Nam; SĐT=0957338611; ĐC=Thôn A, Xã H, Tỉnh Đồng Nai; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000052 | — | ĐẠT | 2.15 |
| A050-L2 | 52 | Họ=Trịnh; Đệm=Gia; Tên=Huy; NS=21/11/2012; GT=Nam; SĐT=0949604350; ĐC=Số 84 Đường Lê Lợi, Phường Lê Lợi, Hải Phòng; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000053 | — | ĐẠT | 2.13 |
| A051-L2 | 53 | Họ=Hồ; Đệm=Công; Tên=Huy; NS=03/05/2015; GT=Nam; SĐT=0973482912; ĐC=Thôn A, Xã I, Tỉnh Đồng Nai; QT=Việt Nam; Title=Bé | Không đổi | Không đổi | NEW000054 | — | ĐẠT | 2.13 |
| A052-L2 | 54 | Họ=Đinh; Đệm=Thu; Tên=Quỳnh; NS=20/07/1960; GT=Nữ; SĐT=0944019081; ĐC=Số 8 Đường Phạm Văn Đồng, Xã Tây Phương, Hà Nội; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000055 | — | ĐẠT | 2.15 |
| A053-L2 | 55 | Họ=Ngô; Đệm=Ngọc; Tên=Thúy; NS=11/12/2016; GT=Nữ; SĐT=0955246171; ĐC=Thôn F, Xã K, Tỉnh Nam Định; QT=Việt Nam; Title=Bé | Không đổi | Không đổi | NEW000056 | — | ĐẠT | 2.04 |
| A054-L2 | 56 | Họ=Hoàng; Đệm=Thu Thanh; Tên=Diễm; NS=04/08/1994; GT=Nữ; SĐT=0976402641; ĐC=Số 23 Đường Điện Biên Phủ, Xã Kiều Phú, Thái Bình; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000057 | — | ĐẠT | 2.12 |
| A055-L2 | 57 | Họ=Cao; Đệm=Hồng; Tên=Thúy; NS=16/09/1969; GT=Nữ; SĐT=0914064298; ĐC=Thôn F, Xã L, Tỉnh Thái Bình; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000058 | — | ĐẠT | 2.22 |
| A056-L2 | 58 | Họ=Cao; Đệm=Minh; Tên=Tuấn; NS=ngày giờ 1995-07-26; GT=Nam; SĐT=0966831608; ĐC=12 Lê Lợi, Hà Nội; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000059 | — | ĐẠT | 2.22 |
| A057-L2 | 59 | Họ=Lê; Đệm=Hữu; Tên=Việt; NS=14/09/2006; GT=Nam; SĐT=0970065710; ĐC=Thôn E, Xã K, Tỉnh Hưng Yên; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000060 | — | ĐẠT | 2.31 |
| A058-L2 | 60 | Họ=Quản; Đệm=Diệu; Tên=Phương; NS=15/10/1953; GT=Nữ; SĐT=0959056252; ĐC=Thôn E, Xã I, Tỉnh Thái Bình; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000061 | — | ĐẠT | 2.17 |
| A059-L2 | 61 | Họ=Chử; Đệm=Xuân; Tên=Cường; NS=24/11/1998; GT=Nam; SĐT=0918989527; ĐC=Thôn B, Xã K, Tỉnh Đà Nẵng; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000062 | — | ĐẠT | 2.1 |
| A060-L2 | 62 | Họ=Đoàn; Đệm=Ngọc; Tên=Thảo; NS=15/01/1967; GT=Nữ; SĐT=0905911978; ĐC=Số 131 Đường Hoàng Diệu, Phường Lê Lợi, Hưng Yên; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000063 | — | ĐẠT | 2.05 |
| A061-L2 | 63 | Họ=Tạ; Đệm=Văn Văn; Tên=Cường; NS=09/03/1989; GT=Nam; SĐT=0947007681; ĐC=Số 48 Đường Hoàng Diệu, Xã Tây Phương, Hà Nội; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000064 | — | ĐẠT | 2.39 |
| A062-L2 | 64 | Họ=Đỗ; Đệm=Thị Thị; Tên=Mai; NS=23/12/2004; GT=Nữ; SĐT=0932657004; ĐC=Số 152 Đường Hoàng Diệu, Xã Tây Phương, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000065 | — | ĐẠT | 2.16 |
| A063-L2 | 65 | Họ=Lý; Đệm=Thanh; Tên=Nam; NS=02/12/1980; GT=Nam; SĐT=0998999988; ĐC=Số 16 Đường Phạm Văn Đồng, Phường Tân Hiệp, Nam Định; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000066 | — | ĐẠT | 2.15 |
| A064-L2 | 66 | Họ=Trần; Đệm=Hữu; Tên=Lâm; NS=13/02/2010; GT=Nam; SĐT=0906392747; ĐC=Số 4 Đường Trần Phú, Phường Lê Lợi, Nam Định; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000067 | — | ĐẠT | 2.14 |
| A065-L2 | 67 | Họ=Hồ; Đệm=(trống); Tên=Thành; NS=27/07/1953; GT=Nam; SĐT=0950753719; ĐC=Thôn E, Xã L, Tỉnh Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000068 | — | ĐẠT | 2.2 |
| A066-L2 | 68 | Họ=Trần; Đệm=(trống); Tên=Long; NS=10/01/1981; GT=Nam; SĐT=0946182438; ĐC=Số 199 Đường Nguyễn Trãi, Phường Tân Hiệp, Nam Định; QT=(trống); Title=Ông | Không đổi | Không đổi | NEW000069 | — | ĐẠT | 2.16 |
| A067-L2 | 69 | Họ=Đặng; Đệm=Diệu; Tên=Dung; NS=24/05/1965; GT=Nữ; SĐT=0909226760; ĐC=Số 177 Đường Nguyễn Trãi, Xã Tây Phương, Thái Bình; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000070 | — | ĐẠT | 2.2 |
| A068-L2 | 70 | Họ=Lý; Đệm=Quang; Tên=Đạt; NS=1960-02-26; GT=Nam; SĐT=0928789532; ĐC=Số 175 Đường Trần Phú, Xã Kiều Phú, Bắc Ninh; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000071 | — | ĐẠT | 2.23 |
| A069-L2 | 71 | Họ=Bùi; Đệm=Kim; Tên=Thúy; NS=15/06/1953; GT=Nữ; SĐT=0989353331; ĐC=Số 113 Đường Trần Phú, Phường Láng Hạ, Hưng Yên; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000072 | — | ĐẠT | 2.29 |
| A070-L2 | 72 | Họ=Phan; Đệm=Quang; Tên=Sơn; NS=05/02/1980; GT=Nam; SĐT=0956745926; ĐC=Số 80 Đường Hoàng Diệu, Phường Mới, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000073 | — | ĐẠT | 2.2 |
| A071-L2 | 73 | Họ=Bùi; Đệm=Quốc; Tên=Thành; NS=12/01/2016; GT=Nam; SĐT=0904950369; ĐC=Số 2 Đường Lê Lợi, Phường Lê Lợi, Đà Nẵng; QT=Việt Nam; Title=Bé | Không đổi | Không đổi | NEW000074 | — | ĐẠT | 2.18 |
| A072-L2 | 74 | Họ=Phạm; Đệm=Gia; Tên=Huy; NS=16/10/1956; GT=Nam; SĐT=0977550017; ĐC=Thôn A, Xã N, Tỉnh Ninh Bình; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000075 | — | ĐẠT | 2.17 |
| A073-L2 | 75 | Họ=Phan; Đệm=(trống); Tên=Nghĩa; NS=01/07/1978; GT=Nam; SĐT=0906521454; ĐC=Số 69 Đường Số 3, Phường Đông Hải, Thái Bình; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000076 | — | ĐẠT | 2.19 |
| A074-L2 | 76 | Họ=Đoàn; Đệm=Thu; Tên=Diễm; NS=14/11/1989; GT=Nữ; SĐT=0909893967; ĐC=Thôn C, Xã N, Tỉnh Hưng Yên; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000077 | — | ĐẠT | 2.23 |
| A075-L2 | 77 | Họ=Đỗ; Đệm=Ngọc; Tên=Quân; NS=15/11/1962; GT=Nam; SĐT=0949480281; ĐC=Số 188 Đường Số 3, Phường Đông Hải, Hưng Yên; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000078 | — | ĐẠT | 2.39 |
| A076-L2 | 78 | Họ=Dương; Đệm=Minh; Tên=Kiên; NS=05/06/1989; GT=Nam; SĐT=0903981405; ĐC=31 Lê Lợi, Hưng Yên; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000079 | — | ĐẠT | 2.38 |
| A077-L2 | 79 | Họ=Dương; Đệm=Ngọc; Tên=An; NS=01/03/1952; GT=Nam; SĐT=0949420910; ĐC=Thôn A, Xã N, Tỉnh Đồng Nai; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000080 | — | ĐẠT | 2.26 |
| A078-L2 | 80 | Họ=Võ; Đệm=Ngọc; Tên=Sơn; NS=27/07/1951; GT=Nam; SĐT=0924810135; ĐC=39 Điện Biên Phủ, Bắc Ninh; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000081 | — | ĐẠT | 2.13 |
| A079-L2 | 81 | Họ=Ngô; Đệm=Hồng; Tên=Hà; NS=24/04/1952; GT=Nữ; SĐT=0901369330; ĐC=Số 96 Đường Lê Lợi, Phường Láng Hạ, Hưng Yên; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000082 | — | ĐẠT | 2.13 |
| A080-L2 | 82 | Họ=Lê; Đệm=Đức; Tên=Nghĩa; NS=24/01/1962; GT=Nam; SĐT=0937932591; ĐC=Số 144 Đường Láng Hạ, Phường Đông Hải, Bắc Ninh; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000083 | — | ĐẠT | 2.11 |
| H001-L2 | 83 | Họ=Phan; Đệm=Hữu; Tên=Phát; NS=01/11/2008; GT=Nam; SĐT=0926178329; ĐC=Số 57 Đường Lê Lợi, Phường Tân Hiệp, Đà Nẵng; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000084 | — | ĐẠT | 2.15 |
| H002-L2 | 84 | Họ=Quản; Đệm=Xuân; Tên=Phúc; NS=06/04/1957; GT=Nam; SĐT=0921265116; ĐC=Thôn E, Xã M, Tỉnh Đà Nẵng; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000085 | — | ĐẠT | 2.16 |
| H003-L2 | 85 | Họ=Phan; Đệm=(trống); Tên=Oanh; NS=16031985; GT=Nữ; SĐT=0940469986; ĐC=Thôn G, Xã M, Tỉnh Ninh Bình; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000086 | — | ĐẠT | 2.13 |
| H004-L2 | 86 | Họ=Phan; Đệm=Xuân; Tên=Hiếu; NS=07/02/2012; GT=Nam; SĐT=0945090551; ĐC=Số 25 Đường Láng Hạ, Xã Kiều Phú, Đà Nẵng; QT=(trống); Title=Ông | Không đổi | Không đổi | NEW000087 | — | ĐẠT | 2.12 |
| H005-L2 | 87 | Họ=Dương; Đệm=Thị; Tên=Nhi; NS=1974-11-24; GT=Nữ; SĐT=0975220160; ĐC=Số 197 Đường Hoàng Diệu, Xã Kiều Phú, Hà Nội; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000088 | — | ĐẠT | 2.14 |
| H006-L2 | 88 | Họ=Trịnh; Đệm=Phương; Tên=Thúy; NS=12/08/1967; GT=Nữ; SĐT=0995873184; ĐC=34 Láng Hạ, Hà Nội; QT=(trống); Title=Chị | Không đổi | Không đổi | NEW000089 | — | ĐẠT | 2.23 |
| H007-L2 | 89 | Họ=Lương; Đệm=Xuân; Tên=Phúc; NS=24/03/1983; GT=Nam; SĐT=0911922878; ĐC=Số 173 Đường Nguyễn Trãi, Phường Mới, Bắc Ninh; QT=(trống); Title=Anh | Không đổi | Không đổi | NEW000090 | — | ĐẠT | 2.21 |
| H008-L2 | 90 | Họ=Lương; Đệm=Ngọc; Tên=Quân; NS=ngày giờ 2005-11-17; GT=Nam; SĐT=0966557572; ĐC=Số 194 Đường Phạm Văn Đồng, Phường Đông Hải, Nam Định; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000091 | — | ĐẠT | 2.3 |
| H009-L2 | 91 | Họ=Chử; Đệm=Thanh; Tên=Trung; NS=03/05/1995; GT=Nam; SĐT=0905301851; ĐC=Thôn G, Xã L, Tỉnh Đà Nẵng; QT=(trống); Title=Anh | Không đổi | Không đổi | NEW000092 | — | ĐẠT | 2.07 |
| H010-L2 | 92 | Họ=Quản; Đệm=Xuân; Tên=Khánh; NS=ngày giờ 1982-09-28; GT=Nam; SĐT=0906322965; ĐC=Số 176 Đường Nguyễn Trãi, Phường Lê Lợi, Hà Nội; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000093 | — | ĐẠT | 2.16 |
| H011-L2 | 93 | Họ=Vũ; Đệm=Hữu; Tên=Nam; NS=03/01/1970; GT=Nam; SĐT=0987105728; ĐC=Số 200 Đường Hoàng Diệu, Xã Kiều Phú, Đồng Nai; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000094 | — | ĐẠT | 2.08 |
| H012-L2 | 94 | Họ=Lương; Đệm=Ngọc; Tên=Nghĩa; NS=26101982; GT=Nam; SĐT=0910374583; ĐC=Thôn G, Xã M, Tỉnh Hà Nội; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000095 | — | ĐẠT | 2.46 |
| H013-L2 | 95 | Họ=Vũ; Đệm=Thanh Thùy; Tên=Vy; NS=07/11/1958; GT=Nữ; SĐT=0943175606; ĐC=93 Nguyễn Trãi, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000096 | — | ĐẠT | 2.17 |
| H014-L2 | 96 | Họ=Vũ; Đệm=Công; Tên=Hiếu; NS=21/06/1997; GT=Nam; SĐT=0935045567; ĐC=Thôn E, Xã L, Tỉnh Thái Bình; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000097 | — | ĐẠT | 2.13 |
| H015-L2 | 97 | Họ=Nguyễn; Đệm=Quốc; Tên=Nghĩa; NS=23062007; GT=Nam; SĐT=0924612495; ĐC=Số 27 Đường Nguyễn Trãi, Phường Lê Lợi, Đà Nẵng; QT=(trống); Title=Anh | Không đổi | Không đổi | NEW000098 | — | ĐẠT | 2.11 |
| H016-L2 | 98 | Họ=Từ; Đệm=Phương; Tên=Ngân; NS=ngày giờ 1982-09-11; GT=Nữ; SĐT=0980123791; ĐC=Số 106 Đường Trần Phú, Phường Láng Hạ, Hưng Yên; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000099 | — | ĐẠT | 2.14 |
| H017-L2 | 99 | Họ=Phạm; Đệm=(trống); Tên=Phát; NS=ngày giờ 2012-08-22; GT=Nam; SĐT=0907666996; ĐC=Thôn G, Xã M, Tỉnh Thái Bình; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000100 | — | ĐẠT | 2.14 |
| H018-L2 | 100 | Họ=Lương; Đệm=Ngọc; Tên=Phúc; NS=26/08/1980; GT=Nam; SĐT=0998430181; ĐC=Số 46 Đường Lê Lợi, Phường Mới, Hải Phòng; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000101 | — | ĐẠT | 2.21 |
| H019-L2 | 101 | Họ=Từ; Đệm=Ngọc Thanh; Tên=Diễm; NS=19/06/2000; GT=Nữ; SĐT=0982816650; ĐC=Thôn E, Xã L, Tỉnh Thành phố Hồ Chí Minh; QT=(trống); Title=Bà | Không đổi | Không đổi | NEW000102 | — | ĐẠT | 2.21 |
| H020-L2 | 102 | Họ=Lê; Đệm=(trống); Tên=Hà; NS=21/04/2003; GT=Nữ; SĐT=0996561212; ĐC=Số 29 Đường Điện Biên Phủ, Phường Láng Hạ, Hải Phòng; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000103 | — | ĐẠT | 2.22 |
| H021-L2 | 103 | Họ=Hoàng; Đệm=(trống); Tên=Vy; NS=26/08/1961; GT=Nữ; SĐT=0925984746; ĐC=Số 79 Đường Láng Hạ, Phường Tân Hiệp, Hải Phòng; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000104 | — | ĐẠT | 2.17 |
| H022-L2 | 104 | Họ=Vũ; Đệm=(trống); Tên=Dung; NS=14/04/2016; GT=Nữ; SĐT=0958325952; ĐC=Số 179 Đường Điện Biên Phủ, Xã Kiều Phú, Đà Nẵng; QT=Việt Nam; Title=Bé | Không đổi | Không đổi | NEW000105 | — | ĐẠT | 2.19 |
| H023-L2 | 105 | Họ=Huỳnh; Đệm=Thanh; Tên=Nghĩa; NS=03091986; GT=Nam; SĐT=0963407179; ĐC=88 Số 3, Đà Nẵng; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000106 | — | ĐẠT | 2.12 |
| H024-L2 | 106 | Họ=Đoàn; Đệm=Diệu; Tên=Châu; NS=06/03/2010; GT=Nữ; SĐT=0992194032; ĐC=Số 28 Đường Số 3, Phường Láng Hạ, Đồng Nai; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000107 | — | ĐẠT | 2.17 |
| H025-L2 | 107 | Họ=Tạ; Đệm=Đức; Tên=Phúc; NS=28/07/1954; GT=Nam; SĐT=0941649642; ĐC=30 Phạm Văn Đồng, Bắc Ninh; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000108 | — | ĐẠT | 2.3 |
| H026-L2 | 108 | Họ=Dương; Đệm=Hữu; Tên=Khánh; NS=09/07/1987; GT=Nam; SĐT=0922035441; ĐC=Thôn E, Xã I, Tỉnh Ninh Bình; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000109 | — | ĐẠT | 2.36 |
| H027-L2 | 109 | Họ=Chử; Đệm=Thanh; Tên=Nghĩa; NS=17/02/1958; GT=Nam; SĐT=0910356611; ĐC=96 Láng Hạ, Nam Định; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000110 | — | ĐẠT | 2.33 |
| H028-L2 | 110 | Họ=Phạm; Đệm=Xuân; Tên=Dũng; NS=21/12/1969; GT=Nam; SĐT=0990026634; ĐC=Số 140 Đường Trần Phú, Xã Tây Phương, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000111 | — | ĐẠT | 2.13 |
| H029-L2 | 111 | Họ=Võ; Đệm=(trống); Tên=Tùng; NS=ngày giờ 2011-02-25; GT=Nam; SĐT=0971686350; ĐC=Số 50 Đường Phạm Văn Đồng, Xã Kiều Phú, Ninh Bình; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000112 | — | ĐẠT | 2.14 |
| H030-L2 | 112 | Họ=Phạm; Đệm=(trống); Tên=Sơn; NS=17/12/2007; GT=Nam; SĐT=0940340048; ĐC=Thôn F, Xã I, Tỉnh Đồng Nai; QT=(trống); Title=Anh | Không đổi | Không đổi | NEW000113 | — | ĐẠT | 2.11 |
| H031-L2 | 113 | Họ=Phan; Đệm=Thanh Tiến; Tên=Trung; NS=12/02/1956; GT=Nam; SĐT=0902508758; ĐC=Thôn G, Xã H, Tỉnh Hải Phòng; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000114 | — | ĐẠT | 2.06 |
| H032-L2 | 114 | Họ=Vũ; Đệm=(trống); Tên=Phát; NS=22/07/1955; GT=Nam; SĐT=0903709080; ĐC=Số 12 Đường Điện Biên Phủ, Xã Tây Phương, Hưng Yên; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000115 | — | ĐẠT | 2.12 |
| H033-L2 | 115 | Họ=Trịnh; Đệm=Thùy; Tên=Trang; NS=11/03/2006; GT=Nữ; SĐT=0999224342; ĐC=Thôn D, Xã I, Tỉnh Hải Phòng; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000116 | — | ĐẠT | 2.08 |
| H034-L2 | 116 | Họ=Huỳnh; Đệm=(trống); Tên=Đạt; NS=09/06/2003; GT=Nam; SĐT=0913366366; ĐC=Số 163 Đường Láng Hạ, Phường Đông Hải, Nam Định; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000117 | — | ĐẠT | 2.15 |
| H035-L2 | 117 | Họ=Quản; Đệm=Hồng; Tên=Lan; NS=09/11/1982; GT=Nữ; SĐT=0934774818; ĐC=Số 127 Đường Hoàng Diệu, Phường Mới, Đà Nẵng; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000118 | — | ĐẠT | 2.14 |
| H036-L2 | 118 | Họ=Dương; Đệm=Thanh; Tên=Lan; NS=18/04/1962; GT=Nữ; SĐT=0948525649; ĐC=Thôn G, Xã N, Tỉnh Hưng Yên; QT=(trống); Title=Bà | Không đổi | Không đổi | NEW000119 | — | ĐẠT | 2.09 |
| H037-L2 | 119 | Họ=Đinh; Đệm=Đức; Tên=Phát; NS=09/03/1980; GT=Nam; SĐT=0977429066; ĐC=Số 63 Đường Lê Lợi, Phường Láng Hạ, Hưng Yên; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000120 | — | ĐẠT | 2.28 |
| H038-L2 | 120 | Họ=Võ; Đệm=Bích Thị; Tên=Yến; NS=18/09/2000; GT=Nữ; SĐT=0996244160; ĐC=Thôn B, Xã K, Tỉnh Nam Định; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000121 | — | ĐẠT | 2.29 |
| H039-L2 | 121 | Họ=Lý; Đệm=Xuân Đức; Tên=Thành; NS=24/03/1975; GT=Nam; SĐT=0999074412; ĐC=95 Láng Hạ, Hải Phòng; QT=(trống); Title=Anh | Không đổi | Không đổi | NEW000122 | — | ĐẠT | 2.15 |
| H040-L2 | 122 | Họ=Đỗ; Đệm=Thanh; Tên=Thúy; NS=01/09/1977; GT=Nữ; SĐT=0936170967; ĐC=Số 141 Đường Hoàng Diệu, Xã Kiều Phú, Thành phố Hồ Chí Minh; QT=(trống); Title=Chị | Không đổi | Không đổi | NEW000123 | — | ĐẠT | 2.2 |
| H041-L2 | 123 | Họ=Lê; Đệm=Quang Tiến; Tên=Phát; NS=ngày giờ 1979-05-07; GT=Nam; SĐT=0915743473; ĐC=Số 116 Đường Điện Biên Phủ, Phường Đông Hải, Ninh Bình; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000124 | — | ĐẠT | 2.14 |
| H042-L2 | 124 | Họ=Huỳnh; Đệm=Gia; Tên=Thành; NS=1961-01-25; GT=Nam; SĐT=0951863338; ĐC=Thôn F, Xã I, Tỉnh Bắc Ninh; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000125 | — | ĐẠT | 2.12 |
| H043-L2 | 125 | Họ=Tạ; Đệm=Xuân; Tên=Nam; NS=ngày giờ 1981-08-28; GT=Nam; SĐT=0989486669; ĐC=Số 177 Đường Hoàng Diệu, Phường Lê Lợi, Nam Định; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000126 | — | ĐẠT | 2.2 |
| H044-L2 | 126 | Họ=Cao; Đệm=Minh Đức; Tên=Trung; NS=03/06/1977; GT=Nam; SĐT=0903101990; ĐC=Số 182 Đường Điện Biên Phủ, Phường Tân Hiệp, Hà Nội; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000127 | — | ĐẠT | 2.15 |
| H045-L2 | 127 | Họ=Võ; Đệm=Thùy; Tên=Hồng; NS=25/03/1969; GT=Nữ; SĐT=0977152607; ĐC=Số 132 Đường Láng Hạ, Xã Kiều Phú, Ninh Bình; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000128 | — | ĐẠT | 2.14 |
| H046-L2 | 128 | Họ=Huỳnh; Đệm=Tiến; Tên=Hiếu; NS=02/02/1992; GT=Nam; SĐT=0913913007; ĐC=30 Điện Biên Phủ, Hải Phòng; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000129 | — | ĐẠT | 2.15 |
| H047-L2 | 129 | Họ=Lê; Đệm=(trống); Tên=Tâm; NS=ngày giờ 2013-12-25; GT=Nữ; SĐT=0902146461; ĐC=Số 97 Đường Điện Biên Phủ, Phường Tân Hiệp, Hưng Yên; QT=Việt Nam; Title=Bé | Không đổi | Không đổi | NEW000130 | — | ĐẠT | 2.14 |
| H048-L2 | 130 | Họ=Phạm; Đệm=Minh; Tên=Phát; NS=ngày giờ 1995-07-13; GT=Nam; SĐT=0902157131; ĐC=Thôn D, Xã K, Tỉnh Đồng Nai; QT=(trống); Title=Anh | Không đổi | Không đổi | NEW000131 | — | ĐẠT | 2.06 |
| H049-L2 | 131 | Họ=Lý; Đệm=(trống); Tên=Đạt; NS=05/10/2015; GT=Nam; SĐT=0990300467; ĐC=88 Láng Hạ, Hải Phòng; QT=Việt Nam; Title=Bé | Không đổi | Không đổi | NEW000132 | — | ĐẠT | 2.22 |
| H050-L2 | 132 | Họ=Đinh; Đệm=Thùy; Tên=Dung; NS=14/01/2011; GT=Nữ; SĐT=0984623217; ĐC=Thôn F, Xã I, Tỉnh Bắc Ninh; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000133 | — | ĐẠT | 2.25 |
| H051-L2 | 133 | Họ=Bùi; Đệm=Thị; Tên=Tâm; NS=07/09/1962; GT=Nữ; SĐT=0913115914; ĐC=Số 16 Đường Phạm Văn Đồng, Xã Tây Phương, Đồng Nai; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000134 | — | ĐẠT | 2.23 |
| H052-L2 | 134 | Họ=Quản; Đệm=Bích; Tên=Diễm; NS=04051991; GT=Nữ; SĐT=0938502456; ĐC=Thôn A, Xã M, Tỉnh Hưng Yên; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000135 | — | ĐẠT | 2.15 |
| H053-L2 | 135 | Họ=Đoàn; Đệm=Bích; Tên=Quỳnh; NS=16/01/1983; GT=Nữ; SĐT=0977394937; ĐC=Thôn D, Xã N, Tỉnh Thái Bình; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000136 | — | ĐẠT | 2.24 |
| H054-L2 | 136 | Họ=Lý; Đệm=(trống); Tên=Phát; NS=16/12/1975; GT=Nam; SĐT=0951428924; ĐC=Số 160 Đường Nguyễn Trãi, Phường Tân Hiệp, Hà Nội; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000137 | — | ĐẠT | 2.18 |
| H055-L2 | 137 | Họ=Lê; Đệm=Thị; Tên=Thúy; NS=15/01/1979; GT=Nữ; SĐT=0956144482; ĐC=Số 86 Đường Phạm Văn Đồng, Phường Lê Lợi, Ninh Bình; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000138 | — | ĐẠT | 2.17 |
| H056-L2 | 138 | Họ=Ngô; Đệm=Quốc Xuân; Tên=Long; NS=05/02/1972; GT=Nam; SĐT=0935753233; ĐC=Số 131 Đường Số 3, Phường Tân Hiệp, Đà Nẵng; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000139 | — | ĐẠT | 2.21 |
| H057-L2 | 139 | Họ=Huỳnh; Đệm=Tiến; Tên=Phát; NS=15/04/1986; GT=Nam; SĐT=0967231661; ĐC=Thôn D, Xã N, Tỉnh Nam Định; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000140 | — | ĐẠT | 2.34 |
| H058-L2 | 140 | Họ=Chử; Đệm=Đức; Tên=Khánh; NS=1994-10-21; GT=Nam; SĐT=0928069000; ĐC=Số 189 Đường Số 3, Phường Láng Hạ, Đồng Nai; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000141 | — | ĐẠT | 2.36 |
| H059-L2 | 141 | Họ=Trịnh; Đệm=Quang; Tên=Việt; NS=07/06/2006; GT=Nam; SĐT=0942862381; ĐC=Thôn B, Xã N, Tỉnh Đồng Nai; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000142 | — | ĐẠT | 2.14 |
| H060-L2 | 142 | Họ=Từ; Đệm=Tiến; Tên=Bình; NS=09/03/1953; GT=Nam; SĐT=0909081872; ĐC=Số 51 Đường Số 3, Phường Đông Hải, Nam Định; QT=(trống); Title=Ông | Không đổi | Không đổi | NEW000143 | — | ĐẠT | 2.13 |
| H061-L2 | 143 | Họ=Dương; Đệm=Ngọc Gia; Tên=Sơn; NS=27/10/2002; GT=Nam; SĐT=0980114587; ĐC=Số 163 Đường Lê Lợi, Phường Tân Hiệp, Bắc Ninh; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000144 | — | ĐẠT | 2.15 |
| H062-L2 | 144 | Họ=Chử; Đệm=Tiến; Tên=Kiên; NS=08/09/1970; GT=Nam; SĐT=0939812921; ĐC=Số 11 Đường Phạm Văn Đồng, Phường Láng Hạ, Đồng Nai; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000145 | — | ĐẠT | 2.08 |
| H063-L2 | 145 | Họ=Bùi; Đệm=Ngọc Xuân; Tên=Thành; NS=10/12/1997; GT=Nam; SĐT=0952876915; ĐC=Số 95 Đường Điện Biên Phủ, Phường Láng Hạ, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000146 | — | ĐẠT | 2.15 |
| H064-L2 | 146 | Họ=Tạ; Đệm=Quốc Minh; Tên=Dũng; NS=05/04/1983; GT=Nam; SĐT=0913921805; ĐC=Số 192 Đường Láng Hạ, Phường Láng Hạ, Đà Nẵng; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000147 | — | ĐẠT | 2.13 |
| H065-L2 | 147 | Họ=Vũ; Đệm=Quốc; Tên=Quân; NS=23/10/1969; GT=Nam; SĐT=0908460647; ĐC=Số 129 Đường Phạm Văn Đồng, Phường Tân Hiệp, Nam Định; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000148 | — | ĐẠT | 2.13 |
| H066-L2 | 148 | Họ=Ngô; Đệm=(trống); Tên=Dung; NS=19/12/2004; GT=Nữ; SĐT=0987484599; ĐC=Số 48 Đường Số 3, Xã Kiều Phú, Hưng Yên; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000149 | — | ĐẠT | 2.19 |
| H067-L2 | 149 | Họ=Võ; Đệm=Phương; Tên=Thảo; NS=ngày giờ 1993-12-15; GT=Nữ; SĐT=0921085792; ĐC=Số 158 Đường Hoàng Diệu, Phường Tân Hiệp, Bắc Ninh; QT=(trống); Title=Chị | Không đổi | Không đổi | NEW000150 | — | ĐẠT | 2.24 |
| H068-L2 | 150 | Họ=Cao; Đệm=Công; Tên=Thành; NS=ngày giờ 1995-01-01; GT=Nam; SĐT=0995666451; ĐC=Thôn C, Xã K, Tỉnh Đà Nẵng; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000151 | — | ĐẠT | 2.23 |
| H069-L2 | 151 | Họ=Chử; Đệm=Thị; Tên=Yến; NS=ngày giờ 1989-04-27; GT=Nữ; SĐT=0939776151; ĐC=Số 63 Đường Trần Phú, Phường Láng Hạ, Nam Định; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000152 | — | ĐẠT | 2.24 |
| H070-L2 | 152 | Họ=Quản; Đệm=Hồng; Tên=Dung; NS=03/09/1954; GT=Nữ; SĐT=0918801215; ĐC=49 Láng Hạ, Đồng Nai; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000153 | — | ĐẠT | 2.2 |
| H071-L2 | 153 | Họ=Lý; Đệm=(trống); Tên=Tùng; NS=ngày giờ 2016-11-14; GT=Nam; SĐT=0931967450; ĐC=Số 51 Đường Số 3, Phường Tân Hiệp, Thái Bình; QT=Việt Nam; Title=Bé | Không đổi | Không đổi | NEW000154 | — | ĐẠT | 2.14 |
| H072-L2 | 154 | Họ=Ngô; Đệm=Kim; Tên=Nhi; NS=1975-03-06; GT=Nữ; SĐT=0947403205; ĐC=Số 163 Đường Lê Lợi, Phường Láng Hạ, Hà Nội; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000155 | — | ĐẠT | 2.13 |
| H073-L2 | 155 | Họ=Lý; Đệm=Thu; Tên=Thảo; NS=17/08/2006; GT=Nữ; SĐT=0953678447; ĐC=Số 136 Đường Trần Phú, Phường Mới, Hưng Yên; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000156 | — | ĐẠT | 2.08 |
| H074-L2 | 156 | Họ=Bùi; Đệm=Diệu; Tên=Trang; NS=1983-10-01; GT=Nữ; SĐT=0965197858; ĐC=Số 42 Đường Số 3, Xã Tây Phương, Nam Định; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000157 | — | ĐẠT | 2.12 |
| H075-L2 | 157 | Họ=Hồ; Đệm=Minh; Tên=Trung; NS=08/10/1957; GT=Nam; SĐT=0930732572; ĐC=Số 175 Đường Láng Hạ, Xã Kiều Phú, Hà Nội; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000158 | — | ĐẠT | 2.42 |
| H076-L2 | 158 | Họ=Lê; Đệm=Công; Tên=Tùng; NS=05/03/1974; GT=Nam; SĐT=0936771669; ĐC=Số 132 Đường Điện Biên Phủ, Xã Tây Phương, Thành phố Hồ Chí Minh; QT=(trống); Title=Anh | Không đổi | Không đổi | NEW000159 | — | ĐẠT | 2.12 |
| H077-L2 | 159 | Họ=Trịnh; Đệm=Ngọc; Tên=Thúy; NS=25/12/2014; GT=Nữ; SĐT=0985025789; ĐC=Số 65 Đường Láng Hạ, Phường Tân Hiệp, Hà Nội; QT=Việt Nam; Title=Bé | Không đổi | Không đổi | NEW000160 | — | ĐẠT | 2.17 |
| H078-L2 | 160 | Họ=Chử; Đệm=Bích; Tên=Lan; NS=04/07/2000; GT=Nữ; SĐT=0926430203; ĐC=Thôn E, Xã N, Tỉnh Bắc Ninh; QT=(trống); Title=Chị | Không đổi | Không đổi | NEW000161 | — | ĐẠT | 2.11 |
| H079-L2 | 161 | Họ=Chử; Đệm=(trống); Tên=Hải; NS=1957-03-02; GT=Nam; SĐT=0958811936; ĐC=Số 171 Đường Trần Phú, Phường Tân Hiệp, Ninh Bình; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000162 | — | ĐẠT | 2.16 |
| H080-L2 | 162 | Họ=Chử; Đệm=Xuân; Tên=Huy; NS=14/09/1994; GT=Nam; SĐT=0906812411; ĐC=Số 103 Đường Trần Phú, Xã Tây Phương, Ninh Bình; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000163 | — | ĐẠT | 2.32 |
| H081-L2 | 163 | Họ=Vũ; Đệm=Minh; Tên=Long; NS=09/05/1990; GT=Nam; SĐT=0916973618; ĐC=Số 183 Đường Nguyễn Trãi, Phường Lê Lợi, Hà Nội; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000164 | — | ĐẠT | 2.31 |
| H082-L2 | 164 | Họ=Bùi; Đệm=Thanh; Tên=Hà; NS=06/05/1991; GT=Nữ; SĐT=0921480395; ĐC=Số 71 Đường Hoàng Diệu, Xã Tây Phương, Đồng Nai; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000165 | — | ĐẠT | 2.24 |
| H083-L2 | 165 | Họ=Huỳnh; Đệm=Thu; Tên=Thúy; NS=26/04/2006; GT=Nữ; SĐT=0958683229; ĐC=Số 165 Đường Lê Lợi, Phường Lê Lợi, Hà Nội; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000166 | — | ĐẠT | 2.16 |
| H084-L2 | 166 | Họ=Vũ; Đệm=Bích Thanh; Tên=Nhi; NS=17/10/2000; GT=Nữ; SĐT=0916904295; ĐC=Số 70 Đường Lê Lợi, Phường Láng Hạ, Hải Phòng; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000167 | — | ĐẠT | 2.12 |
| H085-L2 | 167 | Họ=Dương; Đệm=Đức; Tên=Hiếu; NS=17/09/2007; GT=Nam; SĐT=0974710469; ĐC=Thôn A, Xã H, Tỉnh Hải Phòng; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000168 | — | ĐẠT | 2.12 |
| H086-L2 | 168 | Họ=Lương; Đệm=Quốc; Tên=Bình; NS=07/03/1959; GT=Nam; SĐT=0901139275; ĐC=Thôn A, Xã N, Tỉnh Nam Định; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000169 | — | ĐẠT | 2.11 |
| H087-L2 | 169 | Họ=Tạ; Đệm=(trống); Tên=Giang; NS=13/02/1983; GT=Nữ; SĐT=0960933443; ĐC=84 Số 3, Hải Phòng; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000170 | — | ĐẠT | 2.4 |
| H088-L2 | 170 | Họ=Huỳnh; Đệm=Công Ngọc; Tên=Quân; NS=07/10/1956; GT=Nam; SĐT=0992439657; ĐC=Số 93 Đường Nguyễn Trãi, Phường Tân Hiệp, Bắc Ninh; QT=(trống); Title=Anh | Không đổi | Không đổi | NEW000171 | — | ĐẠT | 2.34 |
| H089-L2 | 171 | Họ=Bùi; Đệm=(trống); Tên=Giang; NS=18/10/1958; GT=Nữ; SĐT=0982883131; ĐC=Số 88 Đường Điện Biên Phủ, Phường Lê Lợi, Hải Phòng; QT=(trống); Title=Chị | Không đổi | Không đổi | NEW000172 | — | ĐẠT | 2.27 |
| H090-L2 | 172 | Họ=Đỗ; Đệm=Ngọc; Tên=Hồng; NS=12/05/1957; GT=Nữ; SĐT=0966747098; ĐC=Số 136 Đường Số 3, Phường Láng Hạ, Hưng Yên; QT=(trống); Title=Bà | Không đổi | Không đổi | NEW000173 | — | ĐẠT | 2.12 |
| H091-L2 | 173 | Họ=Lê; Đệm=Diệu; Tên=Ánh; NS=ngày giờ 1979-01-18; GT=Nữ; SĐT=0942253051; ĐC=58 Phạm Văn Đồng, Hải Phòng; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000174 | — | ĐẠT | 2.13 |
| H092-L2 | 174 | Họ=Đỗ; Đệm=(trống); Tên=Quỳnh; NS=10/09/1953; GT=Nữ; SĐT=0907733157; ĐC=Số 113 Đường Nguyễn Trãi, Phường Đông Hải, Đà Nẵng; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000175 | — | ĐẠT | 2.12 |
| H093-L2 | 175 | Họ=Từ; Đệm=Kim Diệu; Tên=Hạnh; NS=28/08/1972; GT=Nữ; SĐT=0900050291; ĐC=Thôn B, Xã H, Tỉnh Nam Định; QT=Việt Nam; Title=Chị | Không đổi | Không đổi | NEW000176 | — | ĐẠT | 2.18 |
| H094-L2 | 176 | Họ=Đinh; Đệm=Gia; Tên=Phát; NS=ngày giờ 1953-09-02; GT=Nam; SĐT=0957618791; ĐC=Số 98 Đường Trần Phú, Xã Kiều Phú, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000177 | — | ĐẠT | 2.13 |
| H095-L2 | 177 | Họ=Cao; Đệm=Hồng; Tên=Quỳnh; NS=23/05/1994; GT=Nữ; SĐT=0993685574; ĐC=Số 70 Đường Điện Biên Phủ, Phường Lê Lợi, Nam Định; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000178 | — | ĐẠT | 2.16 |
| H096-L2 | 178 | Họ=Phạm; Đệm=Đức; Tên=Khoa; NS=16/05/1987; GT=Nam; SĐT=0914263484; ĐC=Số 72 Đường Lê Lợi, Phường Láng Hạ, Ninh Bình; QT=Việt Nam; Title=Ông | Không đổi | Không đổi | NEW000179 | — | ĐẠT | 2.15 |
| H097-L2 | 179 | Họ=Dương; Đệm=Thanh; Tên=Trung; NS=2009-01-11; GT=Nam; SĐT=0916527728; ĐC=Số 92 Đường Số 3, Phường Lê Lợi, Ninh Bình; QT=(trống); Title=Anh | Không đổi | Không đổi | NEW000180 | — | ĐẠT | 2.13 |
| H098-L2 | 180 | Họ=Nguyễn; Đệm=Diệu; Tên=Hương; NS=ngày giờ 2015-11-22; GT=Nữ; SĐT=0910139877; ĐC=Thôn F, Xã L, Tỉnh Hải Phòng; QT=(trống); Title=Bé | Không đổi | Không đổi | NEW000181 | — | ĐẠT | 2.22 |
| H099-L2 | 181 | Họ=Bùi; Đệm=Thùy; Tên=Vy; NS=27/03/1995; GT=Nữ; SĐT=0967473182; ĐC=Thôn A, Xã H, Tỉnh Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Bà | Không đổi | Không đổi | NEW000182 | — | ĐẠT | 2.26 |
| H100-L2 | 182 | Họ=Phan; Đệm=Xuân Gia; Tên=Hiếu; NS=27/07/1965; GT=Nam; SĐT=0959663381; ĐC=Số 33 Đường Trần Phú, Phường Mới, Nam Định; QT=Việt Nam; Title=Anh | Không đổi | Không đổi | NEW000183 | — | ĐẠT | 2.14 |

### C. Cập nhật người đã có

**C01. Đổi số điện thoại** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Trường điện thoại thay đổi phải được cập nhật. |
| Dữ liệu vào (dòng 184) | Họ=Trần; Đệm=Ngọc; Tên=Bình; NS=26/12/1986; GT=Nam; SĐT=0902808321; ĐC=Số 1 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Anh |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID NEW000184 · Điện thoại |
| Đối soát | khớp |
| Thời gian | 4.01 giây |

**C02. Đổi ngày sinh trong cùng năm (10/05 → 20/05)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Cùng người (trùng năm sinh) nhưng ngày sinh khác: phải cập nhật ngày sinh, không tạo người mới. |
| Dữ liệu vào (dòng 186) | Họ=Đặng; Đệm=Thùy Kim; Tên=Hạnh; NS=20/05/1987; GT=Nữ; SĐT=0961655233; ĐC=Số 2 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Bà |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID NEW000185 · Ngày sinh |
| Đối soát | khớp |
| Thời gian | 3.5 giây |

**C03. Thêm địa chỉ mới** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Địa chỉ mới được thêm vào danh sách (OH giữ cả địa chỉ cũ). |
| Dữ liệu vào (dòng 188) | Họ=Lê; Đệm=Thùy; Tên=Hà; NS=12/07/1989; GT=Nữ; SĐT=0973685139; ĐC=Số 99 Đường Mới, Phường Mới, Đà Nẵng; QT=Việt Nam; Title=Bà |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID NEW000186 · Địa chỉ |
| Đối soát | khớp |
| Thời gian | 4.01 giây |

**C04. Địa chỉ giống hệt cũ** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Không được thêm địa chỉ trùng; kết quả phải là Không đổi. |
| Dữ liệu vào (dòng 190) | Họ=Dương; Đệm=(trống); Tên=Long; NS=25/07/1986; GT=Nam; SĐT=0952467291; ĐC=Số 4 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Anh |
| Mong đợi | Không đổi |
| Thực tế | Không đổi: Không đổi · PID NEW000187 |
| Đối soát | khớp |
| Thời gian | 2.12 giây |

**C05. Đổi Title Ông → Anh** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Danh mục Title. |
| Dữ liệu vào (dòng 192) | Họ=Huỳnh; Đệm=Thu Thu; Tên=Diễm; NS=27/09/1987; GT=Nữ; SĐT=0908384822; ĐC=Số 5 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Anh |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID NEW000188 · Title |
| Đối soát | khớp |
| Thời gian | 3.57 giây |

**C06. Họ tên viết HOA toàn bộ** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Khớp người cũ theo tên không phân biệt hoa/thường; Excel mới nhất ghi đè cách viết. |
| Dữ liệu vào (dòng 194) | Họ=CAO; Đệm=HỒNG; Tên=NHI; NS=ngày giờ 1989-04-18; GT=Nữ; SĐT=0939018796; ĐC=Số 6 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Chị |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID NEW000189 · Họ, Đệm, Tên |
| Đối soát | khớp |
| Thời gian | 3.53 giây |

**C07. Họ tên viết thường toàn bộ** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Như C06 với chữ thường. |
| Dữ liệu vào (dòng 196) | Họ=võ; Đệm=phương; Tên=oanh; NS=ngày giờ 1985-03-04; GT=Nữ; SĐT=0954882631; ĐC=Số 7 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Bà |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID NEW000190 · Họ, Đệm, Tên |
| Đối soát | khớp |
| Thời gian | 3.82 giây |

**C08. Họ tên dạng Unicode tổ hợp (NFD)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Cùng một người nhưng mã hóa chữ có dấu khác (hay gặp khi dán từ nguồn khác). Mong đợi: nhận ra là cùng người và KHÔNG coi là thay đổi. |
| Dữ liệu vào (dòng 198) | Họ=Trần; Đệm=(trống); Tên=Thành; NS=09/08/1988; GT=Nam; SĐT=0983261582; ĐC=Số 8 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Ông |
| Mong đợi | Không đổi |
| Thực tế | Không đổi: Không đổi · PID NEW000191 |
| Đối soát | khớp |
| Ghi chú | Nếu thực tế là UPDATE: RPA ghi đè lại đúng chữ đó dưới dạng mã hóa khác (không sai nội dung nhưng là thay đổi thừa). |
| Thời gian | 2.05 giây |

**C09. Khoảng trắng thừa đầu/cuối ở họ tên** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Khoảng trắng thừa trong Excel phải được loại bỏ, không tạo người mới. |
| Dữ liệu vào (dòng 200) | Họ= Từ ; Đệm=Diệu; Tên=  Dung; NS=ngày giờ 1985-06-07; GT=Nữ; SĐT=0924142189; ĐC=Số 9 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Chị |
| Mong đợi | Không đổi |
| Thực tế | Không đổi: Không đổi · PID NEW000192 |
| Đối soát | khớp |
| Thời gian | 2.2 giây |

**C10. Thêm quốc tịch cho người chưa có** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Điền thêm trường còn trống. |
| Dữ liệu vào (dòng 202) | Họ=Phạm; Đệm=Kim; Tên=Trang; NS=1990-05-16; GT=Nữ; SĐT=0998930897; ĐC=Số 10 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Chị |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID NEW000193 · Nationality |
| Đối soát | khớp |
| Thời gian | 3.55 giây |

**C11. Đổi nhiều trường cùng lúc (SĐT + địa chỉ + Title)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Nhiều thay đổi trong một lần lưu. |
| Dữ liệu vào (dòng 204) | Họ=Đoàn; Đệm=Quốc; Tên=Trung; NS=19/07/1985; GT=Nam; SĐT=0977000011; ĐC=Số 5 Đường E, Phường F, Hải Phòng; QT=Việt Nam; Title=Anh |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID NEW000194 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 4.38 giây |

**C12. Đổi giới tính Nam → Nữ** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Trường giới tính và hộp chọn. |
| Dữ liệu vào (dòng 206) | Họ=Đặng; Đệm=(trống); Tên=Dũng; NS=01/05/1986; GT=Nữ; SĐT=0929705807; ĐC=Số 12 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Bà |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID NEW000195 · Title, Sex |
| Đối soát | khớp |
| Thời gian | 3.49 giây |

**C13. Xóa trống số điện thoại** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Thiếu SĐT phải bị chặn, hồ sơ cũ giữ nguyên. |
| Dữ liệu vào (dòng 208) | Họ=Lý; Đệm=Kim; Tên=Hương; NS=ngày giờ 1985-11-28; GT=Nữ; SĐT=(trống); ĐC=Số 13 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Chị |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Số điện thoại |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Số điện thoại phải gồm chữ số (có thể có dấu cách, gạch, dấu chấm, +84). |
| Đối soát | — |
| Thời gian | 0.0 giây |

**C14. Địa chỉ để trống khi cập nhật** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Ô Excel trống không được xóa địa chỉ đã có. |
| Dữ liệu vào (dòng 210) | Họ=Tạ; Đệm=(trống); Tên=Vy; NS=12/06/1989; GT=Nữ; SĐT=0900892166; ĐC=(trống); QT=Việt Nam; Title=Bà |
| Mong đợi | Không đổi |
| Thực tế | Không đổi: Không đổi · PID NEW000197 |
| Đối soát | khớp |
| Thời gian | 2.23 giây |

**C15. Sửa tên đệm (thêm 1 từ)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Quy tắc khớp theo họ tên đầy đủ: tên đệm khác nghĩa là người khác → tạo hồ sơ mới. Rủi ro: tạo trùng người nếu Excel chỉ sửa chính tả. |
| Dữ liệu vào (dòng 212) | Họ=Võ; Đệm=Thùy Hữu; Tên=Vy; NS=19/10/1988; GT=Nữ; SĐT=0900020126; ĐC=Số 15 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000199 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Quan sát: hành vi theo thiết kế, ghi nhận để người dùng quyết định có chấp nhận không. |
| Thời gian | 4.06 giây |


### C. Cập nhật (bước chuẩn bị: tạo người gốc)

*Rủi ro kiểm tra:* Tạo người gốc để cập nhật.

**C01S. Chuẩn bị cho C01** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 183) | Họ=Trần; Đệm=Ngọc; Tên=Bình; NS=26/12/1986; GT=Nam; SĐT=0976883971; ĐC=Số 1 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Anh |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000184 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.79 giây |

**C02S. Chuẩn bị cho C02** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 185) | Họ=Đặng; Đệm=Thùy Kim; Tên=Hạnh; NS=10/05/1987; GT=Nữ; SĐT=0961655233; ĐC=Số 2 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000185 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 4.02 giây |

**C03S. Chuẩn bị cho C03** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 187) | Họ=Lê; Đệm=Thùy; Tên=Hà; NS=12/07/1989; GT=Nữ; SĐT=0973685139; ĐC=Số 3 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000186 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.72 giây |

**C04S. Chuẩn bị cho C04** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 189) | Họ=Dương; Đệm=(trống); Tên=Long; NS=25/07/1986; GT=Nam; SĐT=0952467291; ĐC=Số 4 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Anh |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000187 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.74 giây |

**C05S. Chuẩn bị cho C05** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 191) | Họ=Huỳnh; Đệm=Thu Thu; Tên=Diễm; NS=27/09/1987; GT=Nữ; SĐT=0908384822; ĐC=Số 5 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Chị |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000188 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.79 giây |

**C06S. Chuẩn bị cho C06** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 193) | Họ=Cao; Đệm=Hồng; Tên=Nhi; NS=ngày giờ 1989-04-18; GT=Nữ; SĐT=0939018796; ĐC=Số 6 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Chị |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000189 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.88 giây |

**C07S. Chuẩn bị cho C07** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 195) | Họ=Võ; Đệm=Phương; Tên=Oanh; NS=ngày giờ 1985-03-04; GT=Nữ; SĐT=0954882631; ĐC=Số 7 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000190 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.71 giây |

**C08S. Chuẩn bị cho C08** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 197) | Họ=Trần; Đệm=(trống); Tên=Thành; NS=09/08/1988; GT=Nam; SĐT=0983261582; ĐC=Số 8 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000191 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 4.21 giây |

**C09S. Chuẩn bị cho C09** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 199) | Họ=Từ; Đệm=Diệu; Tên=Dung; NS=ngày giờ 1985-06-07; GT=Nữ; SĐT=0924142189; ĐC=Số 9 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Chị |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000192 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.82 giây |

**C10S. Chuẩn bị cho C10** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 201) | Họ=Phạm; Đệm=Kim; Tên=Trang; NS=1990-05-16; GT=Nữ; SĐT=0998930897; ĐC=Số 10 Đường A, Phường B, Hà Nội; QT=(trống); Title=Chị |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000193 · Title, Sex, Ngày sinh, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.75 giây |

**C11S. Chuẩn bị cho C11** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 203) | Họ=Đoàn; Đệm=Quốc; Tên=Trung; NS=19/07/1985; GT=Nam; SĐT=0960809055; ĐC=Số 11 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Anh |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000194 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.86 giây |

**C12S. Chuẩn bị cho C12** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 205) | Họ=Đặng; Đệm=(trống); Tên=Dũng; NS=01/05/1986; GT=Nam; SĐT=0929705807; ĐC=Số 12 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Anh |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000195 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.79 giây |

**C13S. Chuẩn bị cho C13** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 207) | Họ=Lý; Đệm=Kim; Tên=Hương; NS=ngày giờ 1985-11-28; GT=Nữ; SĐT=0922179538; ĐC=Số 13 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Chị |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000196 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.71 giây |

**C14S. Chuẩn bị cho C14** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 209) | Họ=Tạ; Đệm=(trống); Tên=Vy; NS=12/06/1989; GT=Nữ; SĐT=0900892166; ĐC=Số 14 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000197 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.78 giây |

**C15S. Chuẩn bị cho C15** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tạo người gốc để cập nhật. |
| Dữ liệu vào (dòng 211) | Họ=Võ; Đệm=Thùy; Tên=Vy; NS=19/10/1988; GT=Nữ; SĐT=0901698500; ĐC=Số 15 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000198 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.88 giây |


### D. Trùng lặp và nhập nhằng

**D01. Hai hồ sơ có sẵn cùng họ tên và năm sinh** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Không đoán: phải dừng và báo người chọn tay, không sửa nhầm hồ sơ nào. |
| Tiền điều kiện | Tạo trước 2 hồ sơ "Hồ Thanh Tùng" sinh 1990, SĐT khác nhau. |
| Dữ liệu vào (dòng 213) | Họ=Hồ; Đệm=Thanh; Tên=Tùng; NS=05/06/1990; GT=Nam; SĐT=0911000003; ĐC=Số 1 Đường A, Phường B, Hà Nội; QT=Việt Nam; Title=Ông |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: cùng tên và năm sinh |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Có 2 hồ sơ cùng tên và năm sinh (NEW000001, NEW000002); chọn tay. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 2 → 2 |
| Thời gian | 0.62 giây |

**D02. Cùng họ tên với người có sẵn nhưng khác năm sinh** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Hai người khác nhau trùng tên phải được tạo riêng, không ghi đè người cũ. |
| Tiền điều kiện | Có sẵn DEMO0001/0004/0005 "Nguyễn Văn Mẫu" sinh 1980/1992/1975. |
| Dữ liệu vào (dòng 214) | Họ=Nguyễn; Đệm=Văn; Tên=Mẫu; NS=09/09/1999; GT=Nam; SĐT=0922000002; ĐC=Số 7 Đường G, Phường H, Hà Nội; QT=Việt Nam; Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000200 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 3.76 giây |

**D03. Cùng họ tên và SĐT với người có sẵn nhưng khác năm sinh** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Nghi trùng người (nhập sai năm sinh): không tạo mới, báo kiểm tra tay. |
| Tiền điều kiện | DEMO0001 "Nguyễn Văn Mẫu" SĐT 0900000001. |
| Dữ liệu vào (dòng 215) | Họ=Nguyễn; Đệm=Văn; Tên=Mẫu; NS=01/01/1970; GT=Nam; SĐT=0900000001; ĐC=Số 8 Đường K, Phường L, Hà Nội; QT=Việt Nam; Title=Ông |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Trùng tên và số điện thoại |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Trùng tên và số điện thoại nhưng khác năm sinh; kiểm tra tay. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 4 → 4 |
| Thời gian | 0.59 giây |

**D04. Tên là phần đầu của tên người khác ("Nguyễn Văn An" so với "Nguyễn Văn Anh")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Ô tìm của OH tìm theo "chứa"; RPA phải lọc đúng tên, không cập nhật nhầm người tên dài hơn. |
| Tiền điều kiện | Tạo trước hồ sơ "Nguyễn Văn Anh" sinh 1990. |
| Dữ liệu vào (dòng 216) | Họ=Nguyễn; Đệm=Văn; Tên=An; NS=11/11/1990; GT=Nam; SĐT=0933000004; ĐC=Số 9 Đường M, Phường N, Hà Nội; QT=Việt Nam; Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000201 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 3.75 giây |

**D05A. Cùng một người xuất hiện 2 lần trong Excel (lần 1)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Lần 1 tạo hồ sơ. |
| Dữ liệu vào (dòng 217) | Họ=Trần; Đệm=Minh; Tên=Sơn; NS=28/10/1972; GT=Nam; SĐT=0936072448; ĐC=Số 23 Đường Nguyễn Trãi, Xã Tây Phương, Ninh Bình; QT=Việt Nam; Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000202 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 4.18 giây |

**D05B. Cùng một người xuất hiện 2 lần trong Excel (lần 2, giống hệt)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Lần 2 không được tạo trùng. |
| Dữ liệu vào (dòng 218) | Họ=Trần; Đệm=Minh; Tên=Sơn; NS=28/10/1972; GT=Nam; SĐT=0936072448; ĐC=Số 23 Đường Nguyễn Trãi, Xã Tây Phương, Ninh Bình; QT=Việt Nam; Title=Ông |
| Mong đợi | Không đổi |
| Thực tế | Không đổi: Không đổi · PID NEW000202 |
| Đối soát | khớp |
| Thời gian | 2.29 giây |

**D06A. Người xuất hiện 2 lần, lần 2 khác SĐT (lần 1)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Lần 1 tạo hồ sơ. |
| Dữ liệu vào (dòng 219) | Họ=Hoàng; Đệm=Thùy; Tên=Ngân; NS=12/05/1972; GT=Nữ; SĐT=0951782957; ĐC=Thôn C, Xã H, Tỉnh Đồng Nai; QT=Việt Nam; Title=Chị |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000203 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.9 giây |

**D06B. Người xuất hiện 2 lần, lần 2 khác SĐT (lần 2)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Lần 2 phải cập nhật SĐT, không tạo người mới. |
| Dữ liệu vào (dòng 220) | Họ=Hoàng; Đệm=Thùy; Tên=Ngân; NS=12/05/1972; GT=Nữ; SĐT=0906375442; ĐC=Thôn C, Xã H, Tỉnh Đồng Nai; QT=Việt Nam; Title=Chị |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID NEW000203 · Điện thoại |
| Đối soát | khớp |
| Thời gian | 3.61 giây |

**D07. Người có sẵn trong OH, đổi SĐT** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Cập nhật hồ sơ có sẵn từ trước khi chạy RPA. |
| Tiền điều kiện | DEMO0004 "Nguyễn Văn Mẫu" 03/09/1992. |
| Dữ liệu vào (dòng 221) | Họ=Nguyễn; Đệm=Văn; Tên=Mẫu; NS=03/09/1992; GT=Nam; SĐT=0944000007; ĐC=Thôn A, Xã B, Tỉnh Demo; QT=Việt Nam; Title=Ông |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID DEMO0004 · Điện thoại |
| Đối soát | khớp |
| Thời gian | 3.7 giây |

**D08. Cùng người, Excel viết không dấu ("Nguyen Van Mau")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Khớp theo tên không dấu nhận ra DEMO0005; nhưng Excel mới nhất ghi đè → tên trong OH bị đổi thành không dấu. |
| Tiền điều kiện | DEMO0005 "Nguyễn Văn Mẫu" 12/12/1975. |
| Dữ liệu vào (dòng 222) | Họ=Nguyen; Đệm=Van; Tên=Mau; NS=12/12/1975; GT=Nam; SĐT=0900000005; ĐC=5 Đường C, Phường D, Thành phố Demo; QT=Việt Nam; Title=Ông |
| Mong đợi | Cập nhật |
| Thực tế | Cập nhật: Đã cập nhật · PID DEMO0005 · Họ, Đệm, Tên |
| Đối soát | khớp |
| Ghi chú | Quan sát: tên trong OH có dấu bị ghi đè thành tên không dấu. Nên cân nhắc không ghi đè tên khi chỉ khác dấu. |
| Thời gian | 3.77 giây |


### E. Dữ liệu sai, lỗi, thiếu

**E01. Thiếu họ** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Không được tạo hồ sơ thiếu họ. |
| Dữ liệu vào (dòng 223) | Họ=(trống); Đệm=Ngọc; Tên=Phát; NS=11/10/1985; GT=Nam; SĐT=0937017597; ĐC=Số 122 Đường Phạm Văn Đồng, Phường Lê Lợi, Hải Phòng; QT=Việt Nam; Title=Ông |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: họ hoặc tên |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Thiếu họ hoặc tên. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E02. Thiếu tên (Given)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Không được tạo hồ sơ thiếu tên. |
| Dữ liệu vào (dòng 224) | Họ=Đặng; Đệm=Thanh; Tên=(trống); NS=01/12/1994; GT=Nữ; SĐT=0990024598; ĐC=Số 111 Đường Số 3, Phường Đông Hải, Nam Định; QT=Việt Nam; Title=Bà |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: họ hoặc tên |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Thiếu họ hoặc tên. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E03. Thiếu cả họ và tên** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Chỉ còn tên đệm. |
| Dữ liệu vào (dòng 225) | Họ=(trống); Đệm=Văn Tiến; Tên=(trống); NS=17/07/1988; GT=Nam; SĐT=0950452482; ĐC=Số 72 Đường Nguyễn Trãi, Phường Mới, Thái Bình; QT=Việt Nam; Title=Ông |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: họ hoặc tên |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Thiếu họ hoặc tên. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E04. Họ chỉ gồm khoảng trắng** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Khoảng trắng phải coi là trống. |
| Dữ liệu vào (dòng 226) | Họ=   ; Đệm=Thanh Ngọc; Tên=Hồng; NS=26/11/1984; GT=Nữ; SĐT=0923102423; ĐC=Thôn C, Xã M, Tỉnh Ninh Bình; QT=Việt Nam; Title=Chị |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: họ hoặc tên |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Thiếu họ hoặc tên. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E05. Thiếu tên đệm** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tên đệm không bắt buộc. |
| Dữ liệu vào (dòng 227) | Họ=Hoàng; Đệm=(trống); Tên=Diễm; NS=27/04/1985; GT=Nữ; SĐT=0926614456; ĐC=Thôn F, Xã I, Tỉnh Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000204 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 4.43 giây |

**E06. Tên có chữ số ("An2")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tên chứa số là dữ liệu sai, không nên nhập thầm lặng vào OH. |
| Dữ liệu vào (dòng 228) | Họ=Quản; Đệm=Thanh; Tên=An2; NS=1995-11-22; GT=Nữ; SĐT=0922742133; ĐC=Số 171 Đường Số 3, Phường Tân Hiệp, Đà Nẵng; QT=Việt Nam; Title=Chị |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: tên |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Tên có ký tự không hợp lệ ('2'); kiểm tra lại tên trong Excel. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E07. Tên chứa emoji** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Ký tự ngoài chữ cái. |
| Dữ liệu vào (dòng 229) | Họ=Quản; Đệm=Ngọc; Tên=Nam😀; NS=18/10/1993; GT=Nam; SĐT=0923071570; ĐC=Số 67 Đường Láng Hạ, Phường Láng Hạ, Đà Nẵng; QT=Việt Nam; Title=Anh |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: tên |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Tên có ký tự không hợp lệ ('😀'); kiểm tra lại tên trong Excel. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E08. Tên chứa mã giống HTML/script** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Chuỗi như <script> không được đưa vào hồ sơ. |
| Dữ liệu vào (dòng 230) | Họ=Ngô; Đệm=Thị Thị; Tên=<script>x</script>; NS=12/06/1982; GT=Nữ; SĐT=0940196696; ĐC=Thôn E, Xã N, Tỉnh Nam Định; QT=Việt Nam; Title=Chị |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: tên |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Tên có ký tự không hợp lệ ('<'); kiểm tra lại tên trong Excel. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E09. Tên chứa dấu nháy và dấu gạch ("O'Brien-Lê")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Ký tự đặc biệt thường gặp ở tên nước ngoài. |
| Dữ liệu vào (dòng 231) | Họ=Đoàn; Đệm=Văn Gia; Tên=O'Brien-Lê; NS=03/04/1989; GT=Nam; SĐT=0940056146; ĐC=Thôn A, Xã K, Tỉnh Hưng Yên; QT=(trống); Title=Anh |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000205 · Title, Sex, Ngày sinh, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Quan sát: tên có dấu nháy/gạch nối là hợp lệ. |
| Thời gian | 4.32 giây |

**E10. Họ rất dài (80 ký tự)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Giới hạn độ dài của ô. |
| Dữ liệu vào (dòng 232) | Họ=NguyễnNguyễnNguyễnNguyễnNguyễnNguyễnNguyễnNguyễnNguyễnNguyễnNguyễnNgu…; Đệm=(trống); Tên=Lan; NS=18/06/1985; GT=Nữ; SĐT=0907062065; ĐC=Thôn D, Xã K, Tỉnh Ninh Bình; QT=Việt Nam; Title=Chị |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000206 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Quan sát độ dài chấp nhận được. |
| Thời gian | 3.75 giây |

**E11. Giới tính trống** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Thiếu giới tính phải bị chặn. |
| Dữ liệu vào (dòng 233) | Họ=Lương; Đệm=Đức; Tên=Khoa; NS=1985-07-10; GT=(trống); SĐT=0931171678; ĐC=Số 26 Đường Điện Biên Phủ, Phường Lê Lợi, Bắc Ninh; QT=Việt Nam; Title=Anh |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Giới tính |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Giới tính phải là Nam / Nữ / Khác. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E12. Giới tính viết tiếng Anh ("Male")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Giá trị ngoài danh mục. |
| Dữ liệu vào (dòng 234) | Họ=Đỗ; Đệm=Bích; Tên=Ngân; NS=10/10/1985; GT=Male; SĐT=0919197189; ĐC=Thôn D, Xã H, Tỉnh Đà Nẵng; QT=Việt Nam; Title=Chị |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Giới tính |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Giới tính phải là Nam / Nữ / Khác. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E13. Giới tính viết thường ("nam")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Lỗi gõ phổ biến; nên chấp nhận. |
| Dữ liệu vào (dòng 235) | Họ=Đinh; Đệm=Bích; Tên=Lan; NS=22/10/1984; GT=nam; SĐT=0987053400; ĐC=73 Nguyễn Trãi, Hưng Yên; QT=Việt Nam; Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000207 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Mong đợi tiêu chí thực tế: chuẩn hóa chữ hoa/thường. |
| Thời gian | 4.45 giây |

**E14. Giới tính viết HOA ("NAM")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Như E13. |
| Dữ liệu vào (dòng 236) | Họ=Bùi; Đệm=Phương; Tên=Châu; NS=1979-07-11; GT=NAM; SĐT=0959500545; ĐC=Thôn D, Xã N, Tỉnh Hưng Yên; QT=(trống); Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000208 · Title, Sex, Ngày sinh, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 4.05 giây |

**E15. Giới tính "Nữ" dạng Unicode tổ hợp** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Cùng chữ nhưng khác mã hóa. |
| Dữ liệu vào (dòng 237) | Họ=Đoàn; Đệm=Bích; Tên=Hương; NS=14/02/1988; GT=Nữ; SĐT=0946313113; ĐC=Số 29 Đường Trần Phú, Phường Mới, Hưng Yên; QT=Việt Nam; Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000209 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 3.74 giây |

**E16. Giới tính có khoảng trắng ("Nam ")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Khoảng trắng thừa phải được cắt. |
| Dữ liệu vào (dòng 238) | Họ=Ngô; Đệm=(trống); Tên=Trung; NS=14/03/1990; GT=Nam ; SĐT=0948441618; ĐC=Thôn A, Xã K, Tỉnh Thái Bình; QT=Việt Nam; Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000210 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 3.74 giây |

**E17. Giới tính "Khác"** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Giá trị hợp lệ thứ ba. |
| Dữ liệu vào (dòng 239) | Họ=Huỳnh; Đệm=Thanh; Tên=Ngân; NS=03/05/1986; GT=Khác; SĐT=0947692122; ĐC=Số 63 Đường Điện Biên Phủ, Phường Lê Lợi, Hà Nội; QT=Việt Nam; Title=(trống) |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000211 · Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 4.13 giây |

**E18. Ngày sinh trống** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Thiếu ngày sinh phải bị chặn. |
| Dữ liệu vào (dòng 240) | Họ=Đoàn; Đệm=Quang Công; Tên=Hải; NS=(trống); GT=Nam; SĐT=0912666823; ĐC=Thôn F, Xã H, Tỉnh Hưng Yên; QT=Việt Nam; Title=Anh |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Ngày sinh |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Ngày sinh không hợp lệ (cần dd/mm/yyyy). |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E19. Ngày sinh không tồn tại (31/02/2000)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Ngày sai lịch. |
| Dữ liệu vào (dòng 241) | Họ=Đỗ; Đệm=Quốc; Tên=Khoa; NS=31/02/2000; GT=Nam; SĐT=0901499160; ĐC=Số 119 Đường Lê Lợi, Phường Tân Hiệp, Hải Phòng; QT=(trống); Title=Ông |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Ngày sinh |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Ngày sinh không hợp lệ (cần dd/mm/yyyy). |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E20. Ngày sinh là chữ ("abc")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Dữ liệu rác. |
| Dữ liệu vào (dòng 242) | Họ=Lê; Đệm=Công; Tên=Khoa; NS=abc; GT=Nam; SĐT=0984608019; ĐC=89 Số 3, Hải Phòng; QT=Việt Nam; Title=Ông |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Ngày sinh |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Ngày sinh không hợp lệ (cần dd/mm/yyyy). |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E21. Ngày sinh dạng gạch ngang (15-03-1985)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Định dạng khác thường gặp. |
| Dữ liệu vào (dòng 243) | Họ=Võ; Đệm=Phương; Tên=Dung; NS=15-03-1985; GT=Nữ; SĐT=0947881878; ĐC=55 Láng Hạ, Ninh Bình; QT=Việt Nam; Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000212 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Mong đợi tiêu chí thực tế: chấp nhận định dạng dd-mm-yyyy. |
| Thời gian | 4.45 giây |

**E22. Chỉ có năm sinh ("1985")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Thiếu ngày/tháng; OH cần ngày đủ ở trang Edit. |
| Dữ liệu vào (dòng 244) | Họ=Phạm; Đệm=Thu; Tên=Lan; NS=1985; GT=Nữ; SĐT=0972535287; ĐC=Số 133 Đường Nguyễn Trãi, Phường Tân Hiệp, Ninh Bình; QT=Việt Nam; Title=Bà |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Ngày sinh |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Ngày sinh không hợp lệ (cần dd/mm/yyyy). |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E23. Ngày sinh ở tương lai (01/01/2099)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Ngày vô lý phải bị chặn thay vì nhập thầm lặng. |
| Dữ liệu vào (dòng 245) | Họ=Chử; Đệm=Công Công; Tên=Cường; NS=01/01/2099; GT=Nam; SĐT=0917334351; ĐC=Số 186 Đường Nguyễn Trãi, Phường Láng Hạ, Nam Định; QT=Việt Nam; Title=Ông |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Ngày sinh |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Ngày sinh 01/01/2099 ở tương lai. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E24. Ngày sinh quá xa (01/01/1850)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tuổi trên 120. |
| Dữ liệu vào (dòng 246) | Họ=Bùi; Đệm=(trống); Tên=Huy; NS=01/01/1850; GT=Nam; SĐT=0991712078; ĐC=1 Lê Lợi, Thái Bình; QT=Việt Nam; Title=Ông |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Ngày sinh |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Ngày sinh 01/01/1850 quá xa (trên 120 tuổi); kiểm tra lại. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E25. Ngày sinh không có số 0 đầu (5/3/1985)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Định dạng d/m/yyyy. |
| Dữ liệu vào (dòng 247) | Họ=Lương; Đệm=Quang; Tên=Khánh; NS=5/3/1985; GT=Nam; SĐT=0908353787; ĐC=Số 74 Đường Nguyễn Trãi, Phường Láng Hạ, Nam Định; QT=Việt Nam; Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000213 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 4.44 giây |

**E26. Ngày sinh là ngày hôm nay (trẻ sơ sinh)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Biên: tuổi 0. |
| Dữ liệu vào (dòng 248) | Họ=Đỗ; Đệm=Bích; Tên=Nhi; NS=ngày giờ 2026-11-19; GT=Nữ; SĐT=0953755332; ĐC=Số 65 Đường Láng Hạ, Phường Mới, Hà Nội; QT=(trống); Title=Bé |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000214 · Title, Sex, Ngày sinh, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 3.96 giây |

**E27. SĐT trống** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Thiếu SĐT phải bị chặn. |
| Dữ liệu vào (dòng 249) | Họ=Lê; Đệm=Thanh; Tên=Hải; NS=19/05/1983; GT=Nam; SĐT=(trống); ĐC=Số 103 Đường Lê Lợi, Phường Láng Hạ, Bắc Ninh; QT=Việt Nam; Title=Ông |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Số điện thoại |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Số điện thoại phải gồm chữ số (có thể có dấu cách, gạch, dấu chấm, +84). |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E28. SĐT quá ngắn ("123")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Dưới 8 chữ số. |
| Dữ liệu vào (dòng 250) | Họ=Quản; Đệm=Xuân; Tên=Đạt; NS=01/02/1978; GT=Nam; SĐT=123; ĐC=Số 92 Đường Lê Lợi, Phường Đông Hải, Đồng Nai; QT=Việt Nam; Title=Anh |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Số điện thoại |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Số điện thoại thiếu số 0 đầu (có thể Excel đã đổi thành số); kiểm tra lại. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E29. SĐT lẫn chữ ("0912abc456")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Dữ liệu rác. |
| Dữ liệu vào (dòng 251) | Họ=Lý; Đệm=Tiến; Tên=Dũng; NS=20/08/1979; GT=Nam; SĐT=0912abc456; ĐC=Số 178 Đường Láng Hạ, Phường Đông Hải, Hưng Yên; QT=Việt Nam; Title=Ông |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Số điện thoại |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Số điện thoại phải gồm chữ số (có thể có dấu cách, gạch, dấu chấm, +84). |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E30. SĐT có dấu cách ("091 234 5678")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Định dạng hay gặp; nên chuẩn hóa thành số liền. |
| Dữ liệu vào (dòng 252) | Họ=Vũ; Đệm=Gia; Tên=Sơn; NS=09/02/1991; GT=Nam; SĐT=091 234 5678; ĐC=80 Hoàng Diệu, Nam Định; QT=Việt Nam; Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000215 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 4.29 giây |

**E31. SĐT có dấu gạch ("091-234-5678")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Như E30. |
| Dữ liệu vào (dòng 253) | Họ=Đinh; Đệm=Công; Tên=Việt; NS=ngày giờ 1979-10-10; GT=Nam; SĐT=091-234-5678; ĐC=Số 54 Đường Hoàng Diệu, Xã Kiều Phú, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000216 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Mong đợi tiêu chí thực tế: chuẩn hóa bỏ dấu gạch. |
| Thời gian | 3.78 giây |

**E32. SĐT dạng quốc tế (+84912345678)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Định dạng hợp lệ và rất phổ biến. |
| Dữ liệu vào (dòng 254) | Họ=Bùi; Đệm=Thị Phương; Tên=Ngân; NS=11/09/1980; GT=Nữ; SĐT=+84912345678; ĐC=Thôn E, Xã I, Tỉnh Nam Định; QT=(trống); Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000217 · Title, Sex, Ngày sinh, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Chuẩn hóa +84 thành số 0 đầu. |
| Thời gian | 3.75 giây |

**E33. SĐT quá dài (20 chữ số)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Số vô lý không nên nhập thầm lặng. |
| Dữ liệu vào (dòng 255) | Họ=Phạm; Đệm=(trống); Tên=Hải; NS=22/01/1977; GT=Nam; SĐT=09123456789012345678; ĐC=Số 1 Đường Lê Lợi, Phường Tân Hiệp, Ninh Bình; QT=Việt Nam; Title=Anh |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Số điện thoại |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Số điện thoại phải có 8–11 chữ số. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E34. SĐT trong Excel là số (mất số 0 đầu: 912345678)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Excel hay đổi 0912... thành số 912...; nhập thầm lặng số thiếu 0 là lỗi dữ liệu nguy hiểm. |
| Dữ liệu vào (dòng 256) | Họ=Đỗ; Đệm=Thu; Tên=Ngân; NS=11/02/1977; GT=Nữ; SĐT=số 912345678; ĐC=Thôn D, Xã N, Tỉnh Hưng Yên; QT=Việt Nam; Title=Chị |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: Số điện thoại |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Số điện thoại thiếu số 0 đầu (có thể Excel đã đổi thành số); kiểm tra lại. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Ghi chú | Hiện RPA nhận chuỗi "912345678" như hợp lệ (đủ 9 chữ số). |
| Thời gian | 0.0 giây |

**E35. Title ngoài danh mục ("Dr")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Phải báo cần điền tay, không bỏ qua im lặng. |
| Dữ liệu vào (dòng 257) | Họ=Đoàn; Đệm=Văn Minh; Tên=Cường; NS=19/03/1985; GT=Nam; SĐT=0944386269; ĐC=Số 173 Đường Nguyễn Trãi, Phường Đông Hải, Hưng Yên; QT=Việt Nam; Title=Dr |
| Mong đợi | Cần điền tay · từ khóa: Title |
| Thực tế | Cần điền tay: PID NEW000218 · cần điền tay: Title "Dr" không có trong danh mục |
| Đối soát | khớp |
| Ghi chú | Title ngoài danh mục: để trống, RPA báo điền tay. |
| Thời gian | 4.77 giây |

**E36. Title trống** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Title không bắt buộc. |
| Dữ liệu vào (dòng 258) | Họ=Vũ; Đệm=Tiến; Tên=Việt; NS=03/02/1994; GT=Nam; SĐT=0927403491; ĐC=Thôn D, Xã K, Tỉnh Ninh Bình; QT=Việt Nam; Title=(trống) |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000219 · Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 3.93 giây |

**E37. Quốc tịch ngoài danh mục ("Lào")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Báo cần điền tay. |
| Dữ liệu vào (dòng 259) | Họ=Huỳnh; Đệm=Tiến Quốc; Tên=Đạt; NS=12/04/1983; GT=Nam; SĐT=0912140696; ĐC=92 Nguyễn Trãi, Hưng Yên; QT=Lào; Title=Ông |
| Mong đợi | Cần điền tay · từ khóa: Nationality |
| Thực tế | Cần điền tay: PID NEW000220 · cần điền tay: Nationality "Lào" không có trong danh mục |
| Đối soát | khớp |
| Thời gian | 3.94 giây |

**E38. Quốc tịch viết không dấu ("Viet Nam")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Gần đúng nhưng khác danh mục. |
| Dữ liệu vào (dòng 260) | Họ=Quản; Đệm=(trống); Tên=Phương; NS=11/05/1980; GT=Nữ; SĐT=0924501627; ĐC=Số 29 Đường Phạm Văn Đồng, Xã Kiều Phú, Hưng Yên; QT=Viet Nam; Title=Bà |
| Mong đợi | Cần điền tay · từ khóa: Nationality |
| Thực tế | Cần điền tay: PID NEW000221 · cần điền tay: Nationality "Viet Nam" không có trong danh mục |
| Đối soát | khớp |
| Thời gian | 3.93 giây |

**E39. Địa chỉ trống** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Địa chỉ không bắt buộc. |
| Dữ liệu vào (dòng 261) | Họ=Phan; Đệm=Thùy; Tên=Thảo; NS=07/10/1979; GT=Nữ; SĐT=0936618206; ĐC=(trống); QT=Việt Nam; Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000222 · Title, Sex, Ngày sinh, Nationality |
| Đối soát | khớp |
| Thời gian | 3.41 giây |

**E40. Địa chỉ chỉ 1 phần ("Hà Nội")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Không tách được tỉnh/phường/số nhà → báo điền tay. |
| Dữ liệu vào (dòng 262) | Họ=Lê; Đệm=(trống); Tên=Phúc; NS=11/11/1987; GT=Nam; SĐT=0922191947; ĐC=Hà Nội; QT=Việt Nam; Title=Ông |
| Mong đợi | Cần điền tay · từ khóa: Địa chỉ |
| Thực tế | Cần điền tay: PID NEW000223 · cần điền tay: Địa chỉ không tách được: "Hà Nội" |
| Đối soát | khớp |
| Thời gian | 3.88 giây |

**E41. Địa chỉ chỉ có dấu phẩy (",,,")** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Dữ liệu rác. |
| Dữ liệu vào (dòng 263) | Họ=Vũ; Đệm=Ngọc; Tên=Nghĩa; NS=07/09/1991; GT=Nam; SĐT=0999760259; ĐC=,,,; QT=(trống); Title=Anh |
| Mong đợi | Cần điền tay · từ khóa: Địa chỉ |
| Thực tế | Cần điền tay: PID NEW000224 · cần điền tay: Địa chỉ không tách được: ",,," |
| Đối soát | khớp |
| Thời gian | 3.67 giây |

**E42. Địa chỉ 4 phần** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Phần đầu gộp thành số nhà/đường. |
| Dữ liệu vào (dòng 264) | Họ=Bùi; Đệm=Xuân Ngọc; Tên=Tùng; NS=13/09/1976; GT=Nam; SĐT=0975561121; ĐC=Số 1, Ngõ 2, Phường B, Hà Nội; QT=Việt Nam; Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000225 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 3.81 giây |

**E43. Địa chỉ dài trên 250 ký tự** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Ô địa chỉ giới hạn 250 ký tự: không được cắt cụt thầm lặng. |
| Dữ liệu vào (dòng 265) | Họ=Ngô; Đệm=Thu; Tên=Trang; NS=13/12/1989; GT=Nữ; SĐT=0915533555; ĐC=Số 1 Đường rất dài Đường rất dài Đường rất dài Đường rất dài Đường rấ…; QT=(trống); Title=Chị |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: địa chỉ |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Địa chỉ quá dài (303 ký tự, tối đa 250); rút gọn rồi nhập tay. |
| Đối soát | — |
| Tác động phụ (số hồ sơ cùng tên) | 0 → 0 |
| Thời gian | 0.0 giây |

**E44. Địa chỉ có xuống dòng trong ô Excel** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Ô nhiều dòng; OH chỉ có ô một dòng. |
| Dữ liệu vào (dòng 266) | Họ=Hồ; Đệm=(trống); Tên=Yến; NS=19031991; GT=Nữ; SĐT=0928349362; ĐC=Số 3 ⏎ Đường D, Phường E, Hà Nội; QT=(trống); Title=Bà |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000226 · Title, Sex, Ngày sinh, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Quan sát cách lưu của OH. |
| Thời gian | 4.28 giây |

**E45. Thiếu số CCCD trong Excel** — **ĐẠT**

| | |
|---|---|
| Rủi ro | RPA không dùng CCCD (OHDemo không có ô CCCD): thiếu CCCD không được làm hỏng luồng. |
| Dữ liệu vào (dòng 267) | Họ=Ngô; Đệm=Tiến; Tên=Khánh; NS=22/07/1993; GT=Nam; SĐT=0902880006; ĐC=Số 121 Đường Láng Hạ, Phường Tân Hiệp, Hải Phòng; QT=(trống); Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000227 · Title, Sex, Ngày sinh, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 3.75 giây |

**E46. Ngày sinh nhập dưới dạng số (15031985)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Excel có thể lưu ngày thành số nguyên. |
| Dữ liệu vào (dòng 268) | Họ=Vũ; Đệm=Công; Tên=Sơn; NS=số 15031985; GT=Nam; SĐT=0913263103; ĐC=Thôn C, Xã M, Tỉnh Nam Định; QT=Việt Nam; Title=Ông |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000228 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 3.86 giây |


### F. Lỗi ở file Excel / thư mục

**F01. Chưa có thư mục của ngày hôm nay** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Ngày chưa tạo thư mục: phải báo rõ, không đoán file của ngày khác. |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: thư mục |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Chưa có thư mục của ngày hôm nay: C:\Users\User\AppData\Local\Temp\tmpmswagn8r\none\19-11-2026 |
| Đối soát | — |
| Thời gian | 0.0 giây |

**F02. Thư mục ngày rỗng** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Chưa đặt file Excel. |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: .xlsx |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Thư mục C:\Users\User\AppData\Local\Temp\tmpmswagn8r\empty\19-11-2026 chưa có file .xlsx. |
| Đối soát | — |
| Thời gian | 0.0 giây |

**F03. Thư mục chỉ có ds lỗi.xlsx** — **ĐẠT**

| | |
|---|---|
| Rủi ro | File kết quả không được đọc nhầm làm danh sách. |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: .xlsx |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Thư mục C:\Users\User\AppData\Local\Temp\tmpmswagn8r\onlyerr\19-11-2026 chưa có file .xlsx. |
| Đối soát | — |
| Thời gian | 0.02 giây |

**F04. Thư mục chỉ có file tạm ~$ (Excel đang mở)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | File khóa tạm của Excel phải bị bỏ qua. |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: .xlsx |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Thư mục C:\Users\User\AppData\Local\Temp\tmpmswagn8r\onlytmp\19-11-2026 chưa có file .xlsx. |
| Đối soát | — |
| Thời gian | 0.01 giây |

**F05. File .xlsx hỏng (thực chất là văn bản)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Phải báo "không đọc được file", không để chương trình lỗi hệ thống. |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: file |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Không đọc được file Excel ds.xlsx: file hỏng hoặc không phải .xlsx (BadZipFile). |
| Đối soát | — |
| Ghi chú | Nếu lỗi không được bắt, RPA khi khởi động sẽ ném ngoại lệ chưa xử lý. |
| Thời gian | 0.0 giây |

**F06. Workbook trống (không có dữ liệu)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Không có dòng nào. |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: tiêu đề |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Không tìm thấy hàng tiêu đề (cần cột Patient ID và National ID). |
| Đối soát | — |
| Thời gian | 0.03 giây |

**F07. Có tiêu đề nhưng 0 dòng dữ liệu** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Danh sách rỗng. |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: không có dòng |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: File không có dòng dữ liệu. |
| Đối soát | — |
| Thời gian | 0.04 giây |

**F08. Thiếu cột National ID trong tiêu đề** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Không nhận ra hàng tiêu đề. |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: tiêu đề |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Không tìm thấy hàng tiêu đề (cần cột Patient ID và National ID). |
| Đối soát | — |
| Thời gian | 0.04 giây |

**F09. Hàng tiêu đề ở hàng 14 (quá xa)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | RPA chỉ tìm tiêu đề trong 10 hàng đầu. |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: tiêu đề |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Không tìm thấy hàng tiêu đề (cần cột Patient ID và National ID). |
| Đối soát | — |
| Thời gian | 0.04 giây |

**F10. Hàng tiêu đề ở hàng 1 (không có hàng nhóm)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Cấu trúc hơi khác nhưng hợp lệ. |
| Mong đợi | Không đổi |
| Thực tế | Không đổi: Đọc được 1 dòng, 21 cột |
| Đối soát | — |
| Thời gian | 0.02 giây |

**F11. Có hàng trống xen giữa dữ liệu** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Hàng trống phải bị bỏ qua, các dòng còn lại vẫn đọc. |
| Mong đợi | Không đổi |
| Thực tế | Không đổi: Đọc được 2 dòng, 21 cột |
| Đối soát | — |
| Thời gian | 0.03 giây |

**F12. Hai file .xlsx trong thư mục: chọn file mới nhất** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Phải chọn đúng file mới nhất, không lẫn. |
| Mong đợi | Không đổi |
| Thực tế | Không đổi: Đọc được 3 dòng, 21 cột |
| Đối soát | — |
| Ghi chú | Kỳ vọng đọc 3 dòng của file mới. |
| Thời gian | 1.14 giây |

**F13. Dữ liệu nằm ở sheet thứ 2 (sheet đầu trống)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | RPA chỉ đọc sheet đầu tiên. |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: tiêu đề |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Không tìm thấy hàng tiêu đề (cần cột Patient ID và National ID). |
| Đối soát | — |
| Ghi chú | Giới hạn đã biết: nhiều sheet không được hỗ trợ. |
| Thời gian | 0.03 giây |

**F14. Thư mục ngày sai định dạng (YYYY-MM-DD thay vì DD-MM-YYYY)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Quy ước thư mục đặt sai. |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: thư mục |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Chưa có thư mục của ngày hôm nay: C:\Users\User\AppData\Local\Temp\tmpmswagn8r\wrongday\19-11-2026 |
| Đối soát | — |
| Thời gian | 0.01 giây |


### G. Tình huống môi trường

**G01. Hộp thoại xác nhận "Vẫn tạo mới?" đang kẹt trước khi chạy** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Hộp thoại do thao tác tay/lần chạy trước để lại; RPA phải tự dọn và xử lý bình thường. |
| Tiền điều kiện | Tạo hồ sơ trùng tên + SĐT với DEMO0001 rồi Save → hộp thoại hiện. |
| Dữ liệu vào (dòng 0) | Họ=Phan; Đệm=Xuân; Tên=Khánh; NS=04/01/1963; GT=Nam; SĐT=0955734447; ĐC=Số 130 Đường Láng Hạ, Xã Tây Phương, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Anh |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000001 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Ghi chú | Hộp thoại lúc đầu: ['Có thể trùng với DEMO0001 · Nguyễn Văn Mẫu. Vẫn tạo mới?'] |
| Thời gian | 3.96 giây |

**G02. OH đang ở trang Edit, có thay đổi chưa lưu** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Nhân viên đang sửa dở hồ sơ rồi bấm chạy RPA. |
| Tiền điều kiện | Mở DEMO0001 → Edit → sửa SĐT, chưa Save. |
| Dữ liệu vào (dòng 0) | Họ=Quản; Đệm=Thu; Tên=Vy; NS=08/05/1961; GT=Nữ; SĐT=0967510329; ĐC=Thôn F, Xã I, Tỉnh Hà Nội; QT=Việt Nam; Title=Chị |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000001 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Ghi chú | RPA bỏ thay đổi chưa lưu của người dùng (chọn Yes ở hộp xác nhận). Đã kiểm tra DEMO0001 không bị lưu nhầm. |
| Thời gian | 6.35 giây |

**G03. OH đang ở trang Search Results** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Trang bất kỳ đang mở khi bắt đầu. |
| Tiền điều kiện | Tìm "Nguyễn Văn Mẫu" → hiện danh sách. |
| Dữ liệu vào (dòng 0) | Họ=Hoàng; Đệm=(trống); Tên=Tùng; NS=18102005; GT=Nam; SĐT=0923140777; ĐC=Số 185 Đường Láng Hạ, Phường Tân Hiệp, Hà Nội; QT=Việt Nam; Title=Anh |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000001 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 3.7 giây |

**G04. OH đang ở khung New Patient, đã nhập dở** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Khung tạo mới đang mở với dữ liệu dở dang. |
| Tiền điều kiện | Mở New Patient, nhập tên "Dở Dang". |
| Dữ liệu vào (dòng 0) | Họ=Dương; Đệm=Ngọc; Tên=Trung; NS=ngày giờ 2006-07-13; GT=Nam; SĐT=0972273706; ĐC=Số 103 Đường Trần Phú, Phường Đông Hải, Đà Nẵng; QT=Việt Nam; Title=Anh |
| Mong đợi | Tạo mới |
| Thực tế | Tạo mới: Đã tạo · PID NEW000001 · Title, Sex, Ngày sinh, Nationality, Địa chỉ |
| Đối soát | — |
| Thời gian | 4.33 giây |

**G05. Cửa sổ OH bị thu nhỏ khi chạy** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Người dùng thu nhỏ OH; UI Automation không thấy ô. Phải báo rõ nguyên nhân, không treo, không ghi sai. |
| Tiền điều kiện | Thu nhỏ cửa sổ OHDemo. |
| Dữ liệu vào (dòng 0) | Họ=Đặng; Đệm=Tiến; Tên=Đạt; NS=25/06/1979; GT=Nam; SĐT=0943899494; ĐC=Thôn D, Xã I, Tỉnh Hưng Yên; QT=Việt Nam; Title=Anh |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: THU NHỎ |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Hết thời gian chờ: control pid-search [cửa sổ OH đang THU NHỎ (RPA không điều khiển được cửa sổ thu nhỏ); trang đang mở: blank] |
| Đối soát | — |
| Ghi chú | Sau khi khôi phục cửa sổ, chạy lại cùng dòng: CREATE (Đã tạo · PID NEW000001 · Title, Sex, Ngày sinh, Nationality,) |
| Thời gian | 10.53 giây |

**G06. OH bị đóng giữa lúc chạy** — **ĐẠT**

| | |
|---|---|
| Rủi ro | OH tắt đột ngột; RPA phải báo lỗi rõ ràng, không treo. |
| Tiền điều kiện | Đóng OHDemo ngay trước khi xử lý dòng. |
| Dữ liệu vào (dòng 0) | Họ=Huỳnh; Đệm=Diệu; Tên=Anh; NS=1962-05-12; GT=Nữ; SĐT=0936350617; ĐC=Số 77 Đường Hoàng Diệu, Phường Láng Hạ, Đồng Nai; QT=Việt Nam; Title=Bà |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: OH |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Mất kết nối: cửa sổ OH đã bị đóng. Mở lại OHDemo.exe rồi chạy lại; dòng này chưa xử lý xong. |
| Đối soát | — |
| Thời gian | 0.0 giây |

**G07. Người dùng bấm Dừng** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tín hiệu dừng phải chặn dòng đang chờ, không ghi dở dang. |
| Tiền điều kiện | Bật cờ dừng trước khi xử lý. |
| Dữ liệu vào (dòng 0) | Họ=Cao; Đệm=Gia; Tên=Thành; NS=25/04/2007; GT=Nam; SĐT=0966686890; ĐC=Số 178 Đường Điện Biên Phủ, Phường Lê Lợi, Hải Phòng; QT=Việt Nam; Title=Anh |
| Mong đợi | Lỗi (dừng dòng) · từ khóa: dừng |
| Thực tế | Lỗi (dừng dòng): ReviewRequired: Đã dừng; dòng này chưa xử lý xong. |
| Đối soát | — |
| Thời gian | 1.2 giây |

**G08. Ghi và xóa file ds lỗi.xlsx** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Dòng lỗi phải được ghi đủ, đúng số dòng và lý do, để điền tay. |
| Dữ liệu vào (dòng 0) | Họ=Chử; Đệm=(trống); Tên=Kiên; NS=24/04/2011; GT=Nam; SĐT=0915562510; ĐC=Số 22 Đường Hoàng Diệu, Xã Tây Phương, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Ông |
| Mong đợi | Không đổi |
| Thực tế | Không đổi: Đã ghi 2 dòng, lý do và số dòng đúng |
| Đối soát | — |
| Thời gian | 0.03 giây |


### H. Khối lượng (sinh tự động)

*Rủi ro kiểm tra:* Ổn định khi chạy dài liên tục: không rơi dòng, không lỗi ngẫu nhiên, không chậm dần.

| Mã | Dòng | Dữ liệu vào | Mong đợi | Thực tế | PID | Đối soát | Kết quả | Giây |
|---|---:|---|---|---|---|---|---|---:|
| H001 | 83 | Họ=Phan; Đệm=Hữu; Tên=Phát; NS=01/11/2008; GT=Nam; SĐT=0926178329; ĐC=Số 57 Đường Lê Lợi, Phường Tân Hiệp, Đà Nẵng; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000084 | khớp | ĐẠT | 3.78 |
| H002 | 84 | Họ=Quản; Đệm=Xuân; Tên=Phúc; NS=06/04/1957; GT=Nam; SĐT=0921265116; ĐC=Thôn E, Xã M, Tỉnh Đà Nẵng; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000085 | khớp | ĐẠT | 3.72 |
| H003 | 85 | Họ=Phan; Đệm=(trống); Tên=Oanh; NS=16031985; GT=Nữ; SĐT=0940469986; ĐC=Thôn G, Xã M, Tỉnh Ninh Bình; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000086 | khớp | ĐẠT | 3.74 |
| H004 | 86 | Họ=Phan; Đệm=Xuân; Tên=Hiếu; NS=07/02/2012; GT=Nam; SĐT=0945090551; ĐC=Số 25 Đường Láng Hạ, Xã Kiều Phú, Đà Nẵng; QT=(trống); Title=Ông | Tạo mới | Tạo mới | NEW000087 | khớp | ĐẠT | 3.72 |
| H005 | 87 | Họ=Dương; Đệm=Thị; Tên=Nhi; NS=1974-11-24; GT=Nữ; SĐT=0975220160; ĐC=Số 197 Đường Hoàng Diệu, Xã Kiều Phú, Hà Nội; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000088 | khớp | ĐẠT | 4.45 |
| H006 | 88 | Họ=Trịnh; Đệm=Phương; Tên=Thúy; NS=12/08/1967; GT=Nữ; SĐT=0995873184; ĐC=34 Láng Hạ, Hà Nội; QT=(trống); Title=Chị | Tạo mới | Tạo mới | NEW000089 | khớp | ĐẠT | 3.93 |
| H007 | 89 | Họ=Lương; Đệm=Xuân; Tên=Phúc; NS=24/03/1983; GT=Nam; SĐT=0911922878; ĐC=Số 173 Đường Nguyễn Trãi, Phường Mới, Bắc Ninh; QT=(trống); Title=Anh | Tạo mới | Tạo mới | NEW000090 | khớp | ĐẠT | 3.72 |
| H008 | 90 | Họ=Lương; Đệm=Ngọc; Tên=Quân; NS=ngày giờ 2005-11-17; GT=Nam; SĐT=0966557572; ĐC=Số 194 Đường Phạm Văn Đồng, Phường Đông Hải, Nam Định; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000091 | khớp | ĐẠT | 3.74 |
| H009 | 91 | Họ=Chử; Đệm=Thanh; Tên=Trung; NS=03/05/1995; GT=Nam; SĐT=0905301851; ĐC=Thôn G, Xã L, Tỉnh Đà Nẵng; QT=(trống); Title=Anh | Tạo mới | Tạo mới | NEW000092 | khớp | ĐẠT | 4.17 |
| H010 | 92 | Họ=Quản; Đệm=Xuân; Tên=Khánh; NS=ngày giờ 1982-09-28; GT=Nam; SĐT=0906322965; ĐC=Số 176 Đường Nguyễn Trãi, Phường Lê Lợi, Hà Nội; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000093 | khớp | ĐẠT | 3.97 |
| H011 | 93 | Họ=Vũ; Đệm=Hữu; Tên=Nam; NS=03/01/1970; GT=Nam; SĐT=0987105728; ĐC=Số 200 Đường Hoàng Diệu, Xã Kiều Phú, Đồng Nai; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000094 | khớp | ĐẠT | 3.72 |
| H012 | 94 | Họ=Lương; Đệm=Ngọc; Tên=Nghĩa; NS=26101982; GT=Nam; SĐT=0910374583; ĐC=Thôn G, Xã M, Tỉnh Hà Nội; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000095 | khớp | ĐẠT | 3.78 |
| H013 | 95 | Họ=Vũ; Đệm=Thanh Thùy; Tên=Vy; NS=07/11/1958; GT=Nữ; SĐT=0943175606; ĐC=93 Nguyễn Trãi, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000096 | khớp | ĐẠT | 3.77 |
| H014 | 96 | Họ=Vũ; Đệm=Công; Tên=Hiếu; NS=21/06/1997; GT=Nam; SĐT=0935045567; ĐC=Thôn E, Xã L, Tỉnh Thái Bình; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000097 | khớp | ĐẠT | 4.34 |
| H015 | 97 | Họ=Nguyễn; Đệm=Quốc; Tên=Nghĩa; NS=23062007; GT=Nam; SĐT=0924612495; ĐC=Số 27 Đường Nguyễn Trãi, Phường Lê Lợi, Đà Nẵng; QT=(trống); Title=Anh | Tạo mới | Tạo mới | NEW000098 | khớp | ĐẠT | 3.94 |
| H016 | 98 | Họ=Từ; Đệm=Phương; Tên=Ngân; NS=ngày giờ 1982-09-11; GT=Nữ; SĐT=0980123791; ĐC=Số 106 Đường Trần Phú, Phường Láng Hạ, Hưng Yên; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000099 | khớp | ĐẠT | 3.97 |
| H017 | 99 | Họ=Phạm; Đệm=(trống); Tên=Phát; NS=ngày giờ 2012-08-22; GT=Nam; SĐT=0907666996; ĐC=Thôn G, Xã M, Tỉnh Thái Bình; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000100 | khớp | ĐẠT | 4.16 |
| H018 | 100 | Họ=Lương; Đệm=Ngọc; Tên=Phúc; NS=26/08/1980; GT=Nam; SĐT=0998430181; ĐC=Số 46 Đường Lê Lợi, Phường Mới, Hải Phòng; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000101 | khớp | ĐẠT | 3.77 |
| H019 | 101 | Họ=Từ; Đệm=Ngọc Thanh; Tên=Diễm; NS=19/06/2000; GT=Nữ; SĐT=0982816650; ĐC=Thôn E, Xã L, Tỉnh Thành phố Hồ Chí Minh; QT=(trống); Title=Bà | Tạo mới | Tạo mới | NEW000102 | khớp | ĐẠT | 3.76 |
| H020 | 102 | Họ=Lê; Đệm=(trống); Tên=Hà; NS=21/04/2003; GT=Nữ; SĐT=0996561212; ĐC=Số 29 Đường Điện Biên Phủ, Phường Láng Hạ, Hải Phòng; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000103 | khớp | ĐẠT | 3.7 |
| H021 | 103 | Họ=Hoàng; Đệm=(trống); Tên=Vy; NS=26/08/1961; GT=Nữ; SĐT=0925984746; ĐC=Số 79 Đường Láng Hạ, Phường Tân Hiệp, Hải Phòng; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000104 | khớp | ĐẠT | 3.74 |
| H022 | 104 | Họ=Vũ; Đệm=(trống); Tên=Dung; NS=14/04/2016; GT=Nữ; SĐT=0958325952; ĐC=Số 179 Đường Điện Biên Phủ, Xã Kiều Phú, Đà Nẵng; QT=Việt Nam; Title=Bé | Tạo mới | Tạo mới | NEW000105 | khớp | ĐẠT | 3.89 |
| H023 | 105 | Họ=Huỳnh; Đệm=Thanh; Tên=Nghĩa; NS=03091986; GT=Nam; SĐT=0963407179; ĐC=88 Số 3, Đà Nẵng; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000106 | khớp | ĐẠT | 3.91 |
| H024 | 106 | Họ=Đoàn; Đệm=Diệu; Tên=Châu; NS=06/03/2010; GT=Nữ; SĐT=0992194032; ĐC=Số 28 Đường Số 3, Phường Láng Hạ, Đồng Nai; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000107 | khớp | ĐẠT | 3.73 |
| H025 | 107 | Họ=Tạ; Đệm=Đức; Tên=Phúc; NS=28/07/1954; GT=Nam; SĐT=0941649642; ĐC=30 Phạm Văn Đồng, Bắc Ninh; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000108 | khớp | ĐẠT | 3.75 |
| H026 | 108 | Họ=Dương; Đệm=Hữu; Tên=Khánh; NS=09/07/1987; GT=Nam; SĐT=0922035441; ĐC=Thôn E, Xã I, Tỉnh Ninh Bình; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000109 | khớp | ĐẠT | 4.11 |
| H027 | 109 | Họ=Chử; Đệm=Thanh; Tên=Nghĩa; NS=17/02/1958; GT=Nam; SĐT=0910356611; ĐC=96 Láng Hạ, Nam Định; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000110 | khớp | ĐẠT | 4.16 |
| H028 | 110 | Họ=Phạm; Đệm=Xuân; Tên=Dũng; NS=21/12/1969; GT=Nam; SĐT=0990026634; ĐC=Số 140 Đường Trần Phú, Xã Tây Phương, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000111 | khớp | ĐẠT | 3.73 |
| H029 | 111 | Họ=Võ; Đệm=(trống); Tên=Tùng; NS=ngày giờ 2011-02-25; GT=Nam; SĐT=0971686350; ĐC=Số 50 Đường Phạm Văn Đồng, Xã Kiều Phú, Ninh Bình; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000112 | khớp | ĐẠT | 3.75 |
| H030 | 112 | Họ=Phạm; Đệm=(trống); Tên=Sơn; NS=17/12/2007; GT=Nam; SĐT=0940340048; ĐC=Thôn F, Xã I, Tỉnh Đồng Nai; QT=(trống); Title=Anh | Tạo mới | Tạo mới | NEW000113 | khớp | ĐẠT | 3.78 |
| H031 | 113 | Họ=Phan; Đệm=Thanh Tiến; Tên=Trung; NS=12/02/1956; GT=Nam; SĐT=0902508758; ĐC=Thôn G, Xã H, Tỉnh Hải Phòng; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000114 | khớp | ĐẠT | 4.15 |
| H032 | 114 | Họ=Vũ; Đệm=(trống); Tên=Phát; NS=22/07/1955; GT=Nam; SĐT=0903709080; ĐC=Số 12 Đường Điện Biên Phủ, Xã Tây Phương, Hưng Yên; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000115 | khớp | ĐẠT | 3.84 |
| H033 | 115 | Họ=Trịnh; Đệm=Thùy; Tên=Trang; NS=11/03/2006; GT=Nữ; SĐT=0999224342; ĐC=Thôn D, Xã I, Tỉnh Hải Phòng; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000116 | khớp | ĐẠT | 4.0 |
| H034 | 116 | Họ=Huỳnh; Đệm=(trống); Tên=Đạt; NS=09/06/2003; GT=Nam; SĐT=0913366366; ĐC=Số 163 Đường Láng Hạ, Phường Đông Hải, Nam Định; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000117 | khớp | ĐẠT | 3.78 |
| H035 | 117 | Họ=Quản; Đệm=Hồng; Tên=Lan; NS=09/11/1982; GT=Nữ; SĐT=0934774818; ĐC=Số 127 Đường Hoàng Diệu, Phường Mới, Đà Nẵng; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000118 | khớp | ĐẠT | 3.76 |
| H036 | 118 | Họ=Dương; Đệm=Thanh; Tên=Lan; NS=18/04/1962; GT=Nữ; SĐT=0948525649; ĐC=Thôn G, Xã N, Tỉnh Hưng Yên; QT=(trống); Title=Bà | Tạo mới | Tạo mới | NEW000119 | khớp | ĐẠT | 3.74 |
| H037 | 119 | Họ=Đinh; Đệm=Đức; Tên=Phát; NS=09/03/1980; GT=Nam; SĐT=0977429066; ĐC=Số 63 Đường Lê Lợi, Phường Láng Hạ, Hưng Yên; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000120 | khớp | ĐẠT | 3.72 |
| H038 | 120 | Họ=Võ; Đệm=Bích Thị; Tên=Yến; NS=18/09/2000; GT=Nữ; SĐT=0996244160; ĐC=Thôn B, Xã K, Tỉnh Nam Định; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000121 | khớp | ĐẠT | 3.72 |
| H039 | 121 | Họ=Lý; Đệm=Xuân Đức; Tên=Thành; NS=24/03/1975; GT=Nam; SĐT=0999074412; ĐC=95 Láng Hạ, Hải Phòng; QT=(trống); Title=Anh | Tạo mới | Tạo mới | NEW000122 | khớp | ĐẠT | 3.73 |
| H040 | 122 | Họ=Đỗ; Đệm=Thanh; Tên=Thúy; NS=01/09/1977; GT=Nữ; SĐT=0936170967; ĐC=Số 141 Đường Hoàng Diệu, Xã Kiều Phú, Thành phố Hồ Chí Minh; QT=(trống); Title=Chị | Tạo mới | Tạo mới | NEW000123 | khớp | ĐẠT | 3.99 |
| H041 | 123 | Họ=Lê; Đệm=Quang Tiến; Tên=Phát; NS=ngày giờ 1979-05-07; GT=Nam; SĐT=0915743473; ĐC=Số 116 Đường Điện Biên Phủ, Phường Đông Hải, Ninh Bình; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000124 | khớp | ĐẠT | 3.8 |
| H042 | 124 | Họ=Huỳnh; Đệm=Gia; Tên=Thành; NS=1961-01-25; GT=Nam; SĐT=0951863338; ĐC=Thôn F, Xã I, Tỉnh Bắc Ninh; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000125 | khớp | ĐẠT | 3.72 |
| H043 | 125 | Họ=Tạ; Đệm=Xuân; Tên=Nam; NS=ngày giờ 1981-08-28; GT=Nam; SĐT=0989486669; ĐC=Số 177 Đường Hoàng Diệu, Phường Lê Lợi, Nam Định; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000126 | khớp | ĐẠT | 3.73 |
| H044 | 126 | Họ=Cao; Đệm=Minh Đức; Tên=Trung; NS=03/06/1977; GT=Nam; SĐT=0903101990; ĐC=Số 182 Đường Điện Biên Phủ, Phường Tân Hiệp, Hà Nội; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000127 | khớp | ĐẠT | 4.17 |
| H045 | 127 | Họ=Võ; Đệm=Thùy; Tên=Hồng; NS=25/03/1969; GT=Nữ; SĐT=0977152607; ĐC=Số 132 Đường Láng Hạ, Xã Kiều Phú, Ninh Bình; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000128 | khớp | ĐẠT | 3.99 |
| H046 | 128 | Họ=Huỳnh; Đệm=Tiến; Tên=Hiếu; NS=02/02/1992; GT=Nam; SĐT=0913913007; ĐC=30 Điện Biên Phủ, Hải Phòng; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000129 | khớp | ĐẠT | 3.7 |
| H047 | 129 | Họ=Lê; Đệm=(trống); Tên=Tâm; NS=ngày giờ 2013-12-25; GT=Nữ; SĐT=0902146461; ĐC=Số 97 Đường Điện Biên Phủ, Phường Tân Hiệp, Hưng Yên; QT=Việt Nam; Title=Bé | Tạo mới | Tạo mới | NEW000130 | khớp | ĐẠT | 3.79 |
| H048 | 130 | Họ=Phạm; Đệm=Minh; Tên=Phát; NS=ngày giờ 1995-07-13; GT=Nam; SĐT=0902157131; ĐC=Thôn D, Xã K, Tỉnh Đồng Nai; QT=(trống); Title=Anh | Tạo mới | Tạo mới | NEW000131 | khớp | ĐẠT | 3.9 |
| H049 | 131 | Họ=Lý; Đệm=(trống); Tên=Đạt; NS=05/10/2015; GT=Nam; SĐT=0990300467; ĐC=88 Láng Hạ, Hải Phòng; QT=Việt Nam; Title=Bé | Tạo mới | Tạo mới | NEW000132 | khớp | ĐẠT | 4.17 |
| H050 | 132 | Họ=Đinh; Đệm=Thùy; Tên=Dung; NS=14/01/2011; GT=Nữ; SĐT=0984623217; ĐC=Thôn F, Xã I, Tỉnh Bắc Ninh; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000133 | khớp | ĐẠT | 3.95 |
| H051 | 133 | Họ=Bùi; Đệm=Thị; Tên=Tâm; NS=07/09/1962; GT=Nữ; SĐT=0913115914; ĐC=Số 16 Đường Phạm Văn Đồng, Xã Tây Phương, Đồng Nai; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000134 | khớp | ĐẠT | 3.97 |
| H052 | 134 | Họ=Quản; Đệm=Bích; Tên=Diễm; NS=04051991; GT=Nữ; SĐT=0938502456; ĐC=Thôn A, Xã M, Tỉnh Hưng Yên; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000135 | khớp | ĐẠT | 3.82 |
| H053 | 135 | Họ=Đoàn; Đệm=Bích; Tên=Quỳnh; NS=16/01/1983; GT=Nữ; SĐT=0977394937; ĐC=Thôn D, Xã N, Tỉnh Thái Bình; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000136 | khớp | ĐẠT | 3.77 |
| H054 | 136 | Họ=Lý; Đệm=(trống); Tên=Phát; NS=16/12/1975; GT=Nam; SĐT=0951428924; ĐC=Số 160 Đường Nguyễn Trãi, Phường Tân Hiệp, Hà Nội; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000137 | khớp | ĐẠT | 3.74 |
| H055 | 137 | Họ=Lê; Đệm=Thị; Tên=Thúy; NS=15/01/1979; GT=Nữ; SĐT=0956144482; ĐC=Số 86 Đường Phạm Văn Đồng, Phường Lê Lợi, Ninh Bình; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000138 | khớp | ĐẠT | 3.73 |
| H056 | 138 | Họ=Ngô; Đệm=Quốc Xuân; Tên=Long; NS=05/02/1972; GT=Nam; SĐT=0935753233; ĐC=Số 131 Đường Số 3, Phường Tân Hiệp, Đà Nẵng; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000139 | khớp | ĐẠT | 3.74 |
| H057 | 139 | Họ=Huỳnh; Đệm=Tiến; Tên=Phát; NS=15/04/1986; GT=Nam; SĐT=0967231661; ĐC=Thôn D, Xã N, Tỉnh Nam Định; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000140 | khớp | ĐẠT | 3.89 |
| H058 | 140 | Họ=Chử; Đệm=Đức; Tên=Khánh; NS=1994-10-21; GT=Nam; SĐT=0928069000; ĐC=Số 189 Đường Số 3, Phường Láng Hạ, Đồng Nai; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000141 | khớp | ĐẠT | 3.96 |
| H059 | 141 | Họ=Trịnh; Đệm=Quang; Tên=Việt; NS=07/06/2006; GT=Nam; SĐT=0942862381; ĐC=Thôn B, Xã N, Tỉnh Đồng Nai; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000142 | khớp | ĐẠT | 3.73 |
| H060 | 142 | Họ=Từ; Đệm=Tiến; Tên=Bình; NS=09/03/1953; GT=Nam; SĐT=0909081872; ĐC=Số 51 Đường Số 3, Phường Đông Hải, Nam Định; QT=(trống); Title=Ông | Tạo mới | Tạo mới | NEW000143 | khớp | ĐẠT | 3.73 |
| H061 | 143 | Họ=Dương; Đệm=Ngọc Gia; Tên=Sơn; NS=27/10/2002; GT=Nam; SĐT=0980114587; ĐC=Số 163 Đường Lê Lợi, Phường Tân Hiệp, Bắc Ninh; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000144 | khớp | ĐẠT | 4.04 |
| H062 | 144 | Họ=Chử; Đệm=Tiến; Tên=Kiên; NS=08/09/1970; GT=Nam; SĐT=0939812921; ĐC=Số 11 Đường Phạm Văn Đồng, Phường Láng Hạ, Đồng Nai; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000145 | khớp | ĐẠT | 4.13 |
| H063 | 145 | Họ=Bùi; Đệm=Ngọc Xuân; Tên=Thành; NS=10/12/1997; GT=Nam; SĐT=0952876915; ĐC=Số 95 Đường Điện Biên Phủ, Phường Láng Hạ, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000146 | khớp | ĐẠT | 3.73 |
| H064 | 146 | Họ=Tạ; Đệm=Quốc Minh; Tên=Dũng; NS=05/04/1983; GT=Nam; SĐT=0913921805; ĐC=Số 192 Đường Láng Hạ, Phường Láng Hạ, Đà Nẵng; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000147 | khớp | ĐẠT | 3.71 |
| H065 | 147 | Họ=Vũ; Đệm=Quốc; Tên=Quân; NS=23/10/1969; GT=Nam; SĐT=0908460647; ĐC=Số 129 Đường Phạm Văn Đồng, Phường Tân Hiệp, Nam Định; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000148 | khớp | ĐẠT | 3.93 |
| H066 | 148 | Họ=Ngô; Đệm=(trống); Tên=Dung; NS=19/12/2004; GT=Nữ; SĐT=0987484599; ĐC=Số 48 Đường Số 3, Xã Kiều Phú, Hưng Yên; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000149 | khớp | ĐẠT | 3.81 |
| H067 | 149 | Họ=Võ; Đệm=Phương; Tên=Thảo; NS=ngày giờ 1993-12-15; GT=Nữ; SĐT=0921085792; ĐC=Số 158 Đường Hoàng Diệu, Phường Tân Hiệp, Bắc Ninh; QT=(trống); Title=Chị | Tạo mới | Tạo mới | NEW000150 | khớp | ĐẠT | 4.14 |
| H068 | 150 | Họ=Cao; Đệm=Công; Tên=Thành; NS=ngày giờ 1995-01-01; GT=Nam; SĐT=0995666451; ĐC=Thôn C, Xã K, Tỉnh Đà Nẵng; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000151 | khớp | ĐẠT | 4.02 |
| H069 | 151 | Họ=Chử; Đệm=Thị; Tên=Yến; NS=ngày giờ 1989-04-27; GT=Nữ; SĐT=0939776151; ĐC=Số 63 Đường Trần Phú, Phường Láng Hạ, Nam Định; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000152 | khớp | ĐẠT | 3.74 |
| H070 | 152 | Họ=Quản; Đệm=Hồng; Tên=Dung; NS=03/09/1954; GT=Nữ; SĐT=0918801215; ĐC=49 Láng Hạ, Đồng Nai; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000153 | khớp | ĐẠT | 3.78 |
| H071 | 153 | Họ=Lý; Đệm=(trống); Tên=Tùng; NS=ngày giờ 2016-11-14; GT=Nam; SĐT=0931967450; ĐC=Số 51 Đường Số 3, Phường Tân Hiệp, Thái Bình; QT=Việt Nam; Title=Bé | Tạo mới | Tạo mới | NEW000154 | khớp | ĐẠT | 3.72 |
| H072 | 154 | Họ=Ngô; Đệm=Kim; Tên=Nhi; NS=1975-03-06; GT=Nữ; SĐT=0947403205; ĐC=Số 163 Đường Lê Lợi, Phường Láng Hạ, Hà Nội; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000155 | khớp | ĐẠT | 3.71 |
| H073 | 155 | Họ=Lý; Đệm=Thu; Tên=Thảo; NS=17/08/2006; GT=Nữ; SĐT=0953678447; ĐC=Số 136 Đường Trần Phú, Phường Mới, Hưng Yên; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000156 | khớp | ĐẠT | 3.74 |
| H074 | 156 | Họ=Bùi; Đệm=Diệu; Tên=Trang; NS=1983-10-01; GT=Nữ; SĐT=0965197858; ĐC=Số 42 Đường Số 3, Xã Tây Phương, Nam Định; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000157 | khớp | ĐẠT | 3.8 |
| H075 | 157 | Họ=Hồ; Đệm=Minh; Tên=Trung; NS=08/10/1957; GT=Nam; SĐT=0930732572; ĐC=Số 175 Đường Láng Hạ, Xã Kiều Phú, Hà Nội; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000158 | khớp | ĐẠT | 4.02 |
| H076 | 158 | Họ=Lê; Đệm=Công; Tên=Tùng; NS=05/03/1974; GT=Nam; SĐT=0936771669; ĐC=Số 132 Đường Điện Biên Phủ, Xã Tây Phương, Thành phố Hồ Chí Minh; QT=(trống); Title=Anh | Tạo mới | Tạo mới | NEW000159 | khớp | ĐẠT | 3.81 |
| H077 | 159 | Họ=Trịnh; Đệm=Ngọc; Tên=Thúy; NS=25/12/2014; GT=Nữ; SĐT=0985025789; ĐC=Số 65 Đường Láng Hạ, Phường Tân Hiệp, Hà Nội; QT=Việt Nam; Title=Bé | Tạo mới | Tạo mới | NEW000160 | khớp | ĐẠT | 3.71 |
| H078 | 160 | Họ=Chử; Đệm=Bích; Tên=Lan; NS=04/07/2000; GT=Nữ; SĐT=0926430203; ĐC=Thôn E, Xã N, Tỉnh Bắc Ninh; QT=(trống); Title=Chị | Tạo mới | Tạo mới | NEW000161 | khớp | ĐẠT | 3.82 |
| H079 | 161 | Họ=Chử; Đệm=(trống); Tên=Hải; NS=1957-03-02; GT=Nam; SĐT=0958811936; ĐC=Số 171 Đường Trần Phú, Phường Tân Hiệp, Ninh Bình; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000162 | khớp | ĐẠT | 4.26 |
| H080 | 162 | Họ=Chử; Đệm=Xuân; Tên=Huy; NS=14/09/1994; GT=Nam; SĐT=0906812411; ĐC=Số 103 Đường Trần Phú, Xã Tây Phương, Ninh Bình; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000163 | khớp | ĐẠT | 3.85 |
| H081 | 163 | Họ=Vũ; Đệm=Minh; Tên=Long; NS=09/05/1990; GT=Nam; SĐT=0916973618; ĐC=Số 183 Đường Nguyễn Trãi, Phường Lê Lợi, Hà Nội; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000164 | khớp | ĐẠT | 3.73 |
| H082 | 164 | Họ=Bùi; Đệm=Thanh; Tên=Hà; NS=06/05/1991; GT=Nữ; SĐT=0921480395; ĐC=Số 71 Đường Hoàng Diệu, Xã Tây Phương, Đồng Nai; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000165 | khớp | ĐẠT | 3.89 |
| H083 | 165 | Họ=Huỳnh; Đệm=Thu; Tên=Thúy; NS=26/04/2006; GT=Nữ; SĐT=0958683229; ĐC=Số 165 Đường Lê Lợi, Phường Lê Lợi, Hà Nội; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000166 | khớp | ĐẠT | 3.93 |
| H084 | 166 | Họ=Vũ; Đệm=Bích Thanh; Tên=Nhi; NS=17/10/2000; GT=Nữ; SĐT=0916904295; ĐC=Số 70 Đường Lê Lợi, Phường Láng Hạ, Hải Phòng; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000167 | khớp | ĐẠT | 3.88 |
| H085 | 167 | Họ=Dương; Đệm=Đức; Tên=Hiếu; NS=17/09/2007; GT=Nam; SĐT=0974710469; ĐC=Thôn A, Xã H, Tỉnh Hải Phòng; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000168 | khớp | ĐẠT | 4.09 |
| H086 | 168 | Họ=Lương; Đệm=Quốc; Tên=Bình; NS=07/03/1959; GT=Nam; SĐT=0901139275; ĐC=Thôn A, Xã N, Tỉnh Nam Định; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000169 | khớp | ĐẠT | 3.92 |
| H087 | 169 | Họ=Tạ; Đệm=(trống); Tên=Giang; NS=13/02/1983; GT=Nữ; SĐT=0960933443; ĐC=84 Số 3, Hải Phòng; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000170 | khớp | ĐẠT | 3.81 |
| H088 | 170 | Họ=Huỳnh; Đệm=Công Ngọc; Tên=Quân; NS=07/10/1956; GT=Nam; SĐT=0992439657; ĐC=Số 93 Đường Nguyễn Trãi, Phường Tân Hiệp, Bắc Ninh; QT=(trống); Title=Anh | Tạo mới | Tạo mới | NEW000171 | khớp | ĐẠT | 3.74 |
| H089 | 171 | Họ=Bùi; Đệm=(trống); Tên=Giang; NS=18/10/1958; GT=Nữ; SĐT=0982883131; ĐC=Số 88 Đường Điện Biên Phủ, Phường Lê Lợi, Hải Phòng; QT=(trống); Title=Chị | Tạo mới | Tạo mới | NEW000172 | khớp | ĐẠT | 3.75 |
| H090 | 172 | Họ=Đỗ; Đệm=Ngọc; Tên=Hồng; NS=12/05/1957; GT=Nữ; SĐT=0966747098; ĐC=Số 136 Đường Số 3, Phường Láng Hạ, Hưng Yên; QT=(trống); Title=Bà | Tạo mới | Tạo mới | NEW000173 | khớp | ĐẠT | 3.76 |
| H091 | 173 | Họ=Lê; Đệm=Diệu; Tên=Ánh; NS=ngày giờ 1979-01-18; GT=Nữ; SĐT=0942253051; ĐC=58 Phạm Văn Đồng, Hải Phòng; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000174 | khớp | ĐẠT | 3.73 |
| H092 | 174 | Họ=Đỗ; Đệm=(trống); Tên=Quỳnh; NS=10/09/1953; GT=Nữ; SĐT=0907733157; ĐC=Số 113 Đường Nguyễn Trãi, Phường Đông Hải, Đà Nẵng; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000175 | khớp | ĐẠT | 3.98 |
| H093 | 175 | Họ=Từ; Đệm=Kim Diệu; Tên=Hạnh; NS=28/08/1972; GT=Nữ; SĐT=0900050291; ĐC=Thôn B, Xã H, Tỉnh Nam Định; QT=Việt Nam; Title=Chị | Tạo mới | Tạo mới | NEW000176 | khớp | ĐẠT | 3.93 |
| H094 | 176 | Họ=Đinh; Đệm=Gia; Tên=Phát; NS=ngày giờ 1953-09-02; GT=Nam; SĐT=0957618791; ĐC=Số 98 Đường Trần Phú, Xã Kiều Phú, Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000177 | khớp | ĐẠT | 3.73 |
| H095 | 177 | Họ=Cao; Đệm=Hồng; Tên=Quỳnh; NS=23/05/1994; GT=Nữ; SĐT=0993685574; ĐC=Số 70 Đường Điện Biên Phủ, Phường Lê Lợi, Nam Định; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000178 | khớp | ĐẠT | 3.71 |
| H096 | 178 | Họ=Phạm; Đệm=Đức; Tên=Khoa; NS=16/05/1987; GT=Nam; SĐT=0914263484; ĐC=Số 72 Đường Lê Lợi, Phường Láng Hạ, Ninh Bình; QT=Việt Nam; Title=Ông | Tạo mới | Tạo mới | NEW000179 | khớp | ĐẠT | 4.12 |
| H097 | 179 | Họ=Dương; Đệm=Thanh; Tên=Trung; NS=2009-01-11; GT=Nam; SĐT=0916527728; ĐC=Số 92 Đường Số 3, Phường Lê Lợi, Ninh Bình; QT=(trống); Title=Anh | Tạo mới | Tạo mới | NEW000180 | khớp | ĐẠT | 4.12 |
| H098 | 180 | Họ=Nguyễn; Đệm=Diệu; Tên=Hương; NS=ngày giờ 2015-11-22; GT=Nữ; SĐT=0910139877; ĐC=Thôn F, Xã L, Tỉnh Hải Phòng; QT=(trống); Title=Bé | Tạo mới | Tạo mới | NEW000181 | khớp | ĐẠT | 3.74 |
| H099 | 181 | Họ=Bùi; Đệm=Thùy; Tên=Vy; NS=27/03/1995; GT=Nữ; SĐT=0967473182; ĐC=Thôn A, Xã H, Tỉnh Thành phố Hồ Chí Minh; QT=Việt Nam; Title=Bà | Tạo mới | Tạo mới | NEW000182 | khớp | ĐẠT | 3.93 |
| H100 | 182 | Họ=Phan; Đệm=Xuân Gia; Tên=Hiếu; NS=27/07/1965; GT=Nam; SĐT=0959663381; ĐC=Số 33 Đường Trần Phú, Phường Mới, Nam Định; QT=Việt Nam; Title=Anh | Tạo mới | Tạo mới | NEW000183 | khớp | ĐẠT | 3.86 |

### I. Người dùng can thiệp khi RPA đang chạy

**I01. Người dùng tìm hồ sơ khác ngay sau khi RPA tìm xong** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Trang đổi từ danh sách sang hồ sơ khác trước khi RPA mở hồ sơ. |
| Tiền điều kiện | after search → search_other |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Kết quả tìm kiếm không phải của dòng này (trang đang mở: list; có thao tác khác trên OH trong lúc RPA chạy?); dừng để không  ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Vết: >> search_other None |
| Thời gian | 43.1 giây |

**I02. Người dùng mở hồ sơ khác khi RPA vừa mở DEMO0001** — **ĐẠT**

| | |
|---|---|
| Rủi ro | RPA sắp bấm Edit nhưng màn hình đã là hồ sơ khác. |
| Tiền điều kiện | after open_pid → search_other |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Trang Edit đang mở là hồ sơ DEMO0002, không phải DEMO0001 (có thao tác khác trên OH?); dừng để không ghi nhầm người. ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Vết: >> search_other None |
| Thời gian | 31.5 giây |

**I03. Người dùng mở hồ sơ khác ngay khi RPA bấm Edit** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Cuộc đua giữa bấm Edit của RPA và tìm kiếm của người dùng. |
| Tiền điều kiện | after click:edit-toggle → search_other |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Hết thời gian chờ: mở trang Edit [trang đang mở: view; dòng trạng thái OH: "Đã mở hồ sơ DEMO0002. Bấm Edit để chỉnh sửa."] ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Vết: >> search_other None |
| Thời gian | 37.6 giây |

**I04. Người dùng chuyển sang sửa hồ sơ khác (DEMO0002) sau khi RPA đọc xong DEMO0001** — **ĐẠT**

| | |
|---|---|
| Rủi ro | RPA điền dữ liệu của DEMO0001 vào form đang mở của người khác: nguy cơ ghi nhầm người. |
| Tiền điều kiện | after read_edit → search_other_edit |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Lỗi khi điều khiển OH (ElementNotVisible: ). [trang đang mở: view; dòng trạng thái OH: "Không lưu thay đổi."] ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Vết: >> search_other_edit None |
| Thời gian | 32.9 giây |

**I05. Người dùng gõ SĐT khác vào form trước khi RPA bấm Lưu** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Dữ liệu người dùng gõ lẫn vào dữ liệu RPA rồi vẫn được lưu. |
| Tiền điều kiện | before click:edit-save → type ('edit-phone', '0111111111') |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Sau khi lưu, hồ sơ DEMO0001 không khớp dữ liệu Excel (SĐT: OH="0111111111" ≠ Excel="0900000009"); cần kiểm tra tay. ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại |
| Đối soát | khớp |
| Ghi chú | Vết: >> type ('edit-phone', '0111111111') |
| Thời gian | 34.6 giây |

**I06. Người dùng đổi họ trên form trước khi RPA bấm Lưu** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Họ bị sửa thành giá trị lạ rồi vẫn được lưu. |
| Tiền điều kiện | before click:edit-save → type ('edit-local-first', 'Sai') |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Sau khi lưu, hồ sơ DEMO0001 không khớp dữ liệu Excel (Họ: OH="Sai" ≠ Excel="Nguyễn"); cần kiểm tra tay. |
| Đối soát | khớp |
| Ghi chú | Vết: >> type ('edit-local-first', 'Sai') Không kiểm tra hồi phục tự động: hồ sơ đã bị lưu dữ liệu lạ do chính người dùng gõ, RPA đã báo lỗi nêu rõ PID để người sửa tay. |
| Thời gian | 20.1 giây |

**I07. Người dùng bấm thoát Edit khi form đang có thay đổi dở** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Hộp thoại "Bỏ các thay đổi?" hiện giữa chừng. |
| Tiền điều kiện | after set_text:edit-phone → click edit-toggle |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Lỗi khi điều khiển OH (COMError: (-2147220992, None, (None, None, None, 0, None))). [trang đang mở: view; dòng trạng thái OH ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Vết: >> click edit-toggle |
| Thời gian | 32.5 giây |

**I08. Người dùng bấm New Patient khi RPA sắp mở hồ sơ** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Màn hình đổi sang khung tạo mới. |
| Tiền điều kiện | before click:results-open → click new-patient |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Lỗi khi điều khiển OH (error: (1400, 'PostMessage', 'Invalid window handle.')). [trang đang mở: new; dòng trạng thái OH: "Nh ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Vết: >> click new-patient |
| Thời gian | 30.4 giây |

**I09. Người dùng đổi nội dung ô tìm kiếm thành PID** — **ĐẠT**

| | |
|---|---|
| Rủi ro | OH mở thẳng hồ sơ DEMO0001; RPA tưởng là "không có kết quả" nên có thể tạo trùng. |
| Tiền điều kiện | after set_text:pid-search → set_search_text DEMO0001 |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Kết quả tìm kiếm không phải của dòng này (trang đang mở: view; có thao tác khác trên OH trong lúc RPA chạy?); dừng để không  ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Vết: >> set_search_text DEMO0001 |
| Thời gian | 29.9 giây |

**I10. Người dùng tìm hồ sơ khác ngay sau khi RPA bấm Lưu** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Dòng trạng thái đổi trước khi RPA đọc "Đã lưu". |
| Tiền điều kiện | after click:edit-save → search_other |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: OH không báo đã lưu hồ sơ DEMO0001 trong 5 giây. [trang đang mở: view; dòng trạng thái OH: "Đã mở hồ sơ DEMO0002. Bấm Edit đ ¦ chạy lại: SAME Không đổi · PID DEMO0001 |
| Đối soát | khớp |
| Ghi chú | Vết: >> search_other None |
| Thời gian | 34.7 giây |

**I11. Người dùng tự mở khung địa chỉ trước khi RPA bấm "+"** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Khung địa chỉ đã mở sẵn khi RPA bấm "+". |
| Tiền điều kiện | before click:edit-add-address → click edit-add-address |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Hết thời gian chờ: mở các ô địa chỉ [trang đang mở: edit; dòng trạng thái OH: "Chế độ chỉnh sửa. Bấm Save để lưu hoặc View đ ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Vết: >> click edit-add-address |
| Thời gian | 37.4 giây |

**I12. Người dùng thu nhỏ cửa sổ OH giữa dòng** — **ĐẠT**

| | |
|---|---|
| Rủi ro | RPA không điều khiển được cửa sổ thu nhỏ. |
| Tiền điều kiện | after click:edit-toggle → minimize |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Hết thời gian chờ: mở trang Edit [cửa sổ OH đang THU NHỎ (RPA không điều khiển được cửa sổ thu nhỏ); trang đang mở: blank] ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Vết: >> minimize None |
| Thời gian | 37.6 giây |

**I13. Người dùng kéo di chuyển cửa sổ OH giữa dòng** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Dời cửa sổ không được làm RPA sai. |
| Tiền điều kiện | after open_pid → move |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo UPDATE: Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ ¦ chạy lại: SAME Không đổi · PID DEMO0001 |
| Đối soát | khớp |
| Ghi chú | Vết: >> move None |
| Thời gian | 31.3 giây |

**I14. Người dùng bấm chuột thật vào vùng trống của OH giữa dòng** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Đổi tiêu điểm không được làm RPA sai. |
| Tiền điều kiện | after read_edit → mouse_click |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Lỗi khi điều khiển OH (ElementNotVisible: ). [trang đang mở: new; dòng trạng thái OH: "Nhập tên, năm sinh, số điện thoại rồi ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Vết: >> mouse_click None |
| Thời gian | 30.5 giây |

**I21. Người dùng tìm hồ sơ khác ngay sau khi RPA bấm New Patient** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Khung tạo mới bị thay bằng hồ sơ khác khi RPA đang gõ tên. |
| Tiền điều kiện | after click:new-patient → search_other |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo CREATE: Đã tạo · PID NEW000001 · Title, Sex, Ngày sinh, Nationality, Địa chỉ ¦ chạy lại: SAME Không đổi · PID NEW000001 |
| Đối soát | khớp |
| Ghi chú | Vết: >> search_other None |
| Thời gian | 39.7 giây |

**I22. Người dùng sửa Tên trong khung New Patient sau khi RPA điền** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Hồ sơ mới có thể bị tạo với tên lạ. |
| Tiền điều kiện | after set_text:new-last → type ('new-last', 'Sai') |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo CREATE: Đã tạo · PID NEW000001 · Title, Tên, Sex, Ngày sinh, Nationality, Địa chỉ ¦ chạy lại: SAME Không đổi · PID NEW000001 |
| Đối soát | khớp |
| Ghi chú | Vết: >> type ('new-last', 'Sai') |
| Thời gian | 35.4 giây |

**I23. Người dùng sửa năm sinh trong khung New Patient trước khi RPA bấm Lưu** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Hồ sơ mới có thể bị tạo với năm sinh sai. |
| Tiền điều kiện | before click:new-save → type ('new-year', '1950') |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo CREATE: Đã tạo · PID NEW000001 · Title, Sex, Ngày sinh, Nationality, Địa chỉ ¦ chạy lại: SAME Không đổi · PID NEW000001 |
| Đối soát | khớp |
| Ghi chú | Vết: >> type ('new-year', '1950') |
| Thời gian | 36.0 giây |

**I24. Người dùng tìm hồ sơ khác ngay sau khi hồ sơ mới được tạo** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Hồ sơ mới đã tạo (chỉ có tên, năm sinh, SĐT) nhưng RPA mất trang Edit. |
| Tiền điều kiện | after click:new-save → search_other |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Hết thời gian chờ: cấp PID mới [trang đang mở: view; dòng trạng thái OH: "Đã mở hồ sơ DEMO0002. Bấm Edit để chỉnh sửa."] · L ¦ chạy lại: UPDATE Đã cập nhật · PID NEW000001 · Title, Sex, Ngày sinh, Nationa |
| Đối soát | khớp |
| Ghi chú | Vết: >> search_other None |
| Thời gian | 40.1 giây |

**I25. Người dùng bấm thoát Edit trước khi RPA bấm Lưu (hồ sơ mới)** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Hộp thoại "Bỏ các thay đổi?" làm mất phần bổ sung. |
| Tiền điều kiện | before click:edit-save → click edit-toggle |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Lỗi khi điều khiển OH (COMError: (-2147220992, None, (None, None, None, 0, None))). [trang đang mở: view; dòng trạng thái OH ¦ chạy lại: SAME Không đổi · PID NEW000001 |
| Đối soát | khớp |
| Ghi chú | Vết: >> click edit-toggle |
| Thời gian | 35.8 giây |

**I26. Người dùng mở New Patient ngay sau khi hồ sơ mới được tạo** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Trang Edit của hồ sơ mới bị che bởi khung tạo mới. |
| Tiền điều kiện | after click:new-save → click new-patient |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Hết thời gian chờ: cấp PID mới [trang đang mở: new; dòng trạng thái OH: "Nhập tên, năm sinh, số điện thoại rồi Save để cấp P ¦ chạy lại: UPDATE Đã cập nhật · PID NEW000001 · Title, Sex, Ngày sinh, Nationa |
| Đối soát | khớp |
| Ghi chú | Vết: >> click new-patient |
| Thời gian | 39.6 giây |

**I27. Người dùng tự bấm Save trong khung New Patient trước RPA** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Hồ sơ được tạo hai lần (bởi người và bởi RPA)? |
| Tiền điều kiện | after set_text:new-phone → click new-save |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Lỗi khi điều khiển OH (error: (1400, 'PostMessage', 'Invalid window handle.')). [trang đang mở: view; dòng trạng thái OH: "K ¦ chạy lại: UPDATE Đã cập nhật · PID NEW000001 · Title, Sex, Ngày sinh, Nationa |
| Đối soát | khớp |
| Ghi chú | Vết: >> click new-save |
| Thời gian | 35.8 giây |

**I28. Người dùng thu nhỏ cửa sổ OH khi RPA đang điền khung New Patient** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Dòng bị ngắt trước khi tạo hồ sơ. |
| Tiền điều kiện | after set_text:new-first → minimize |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Hết thời gian chờ: cấp PID mới [cửa sổ OH đang THU NHỎ (RPA không điều khiển được cửa sổ thu nhỏ); trang đang mở: blank] · L ¦ chạy lại: UPDATE Đã cập nhật · PID NEW000001 · Title, Sex, Ngày sinh, Nationa |
| Đối soát | khớp |
| Ghi chú | Vết: >> minimize None |
| Thời gian | 41.7 giây |


### J. OH hoặc RPA bị ngắt/dừng giữa chừng

**J01. OH bị tắt: cập nhật, after search** — **ĐẠT**

| | |
|---|---|
| Rủi ro | OH bị đóng ở đúng bước này; RPA không được báo thành công, không treo; mở lại OH rồi chạy lại phải đúng. |
| Tiền điều kiện | after search → kill_oh |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Mất kết nối: cửa sổ OH đã bị đóng. Mở lại OHDemo.exe rồi chạy lại; dòng này chưa xử lý xong. (1.4s) ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 24.5 giây |

**J02. OH bị tắt: cập nhật, after click:edit-toggle** — **ĐẠT**

| | |
|---|---|
| Rủi ro | OH bị đóng ở đúng bước này; RPA không được báo thành công, không treo; mở lại OH rồi chạy lại phải đúng. |
| Tiền điều kiện | after click:edit-toggle → kill_oh |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Mất kết nối: cửa sổ OH đã bị đóng. Mở lại OHDemo.exe rồi chạy lại; dòng này chưa xử lý xong. (1.2s) ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 24.1 giây |

**J03. OH bị tắt: cập nhật, before click:edit-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | OH bị đóng ở đúng bước này; RPA không được báo thành công, không treo; mở lại OH rồi chạy lại phải đúng. |
| Tiền điều kiện | before click:edit-save → kill_oh |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Mất kết nối: cửa sổ OH đã bị đóng. Mở lại OHDemo.exe rồi chạy lại; dòng này chưa xử lý xong. (2.1s) ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 25.4 giây |

**J04. OH bị tắt: cập nhật, after click:edit-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | OH bị đóng ở đúng bước này; RPA không được báo thành công, không treo; mở lại OH rồi chạy lại phải đúng. |
| Tiền điều kiện | after click:edit-save → kill_oh |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Mất kết nối: cửa sổ OH đã bị đóng. Mở lại OHDemo.exe rồi chạy lại; dòng này chưa xử lý xong. (2.3s) ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 25.0 giây |

**J05. OH bị tắt: tạo mới, after set_text:new-first** — **ĐẠT**

| | |
|---|---|
| Rủi ro | OH bị đóng ở đúng bước này; RPA không được báo thành công, không treo; mở lại OH rồi chạy lại phải đúng. |
| Tiền điều kiện | after set_text:new-first → kill_oh |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Mất kết nối: cửa sổ OH đã bị đóng. Mở lại OHDemo.exe rồi chạy lại; dòng này chưa xử lý xong. (1.7s) ¦ chạy lại: CREATE Đã tạo · PID NEW000001 · Title, Sex, Ngày sinh, Địa chỉ |
| Đối soát | khớp |
| Thời gian | 26.8 giây |

**J06. OH bị tắt: tạo mới, after click:new-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | OH bị đóng ở đúng bước này; RPA không được báo thành công, không treo; mở lại OH rồi chạy lại phải đúng. |
| Tiền điều kiện | after click:new-save → kill_oh |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Mất kết nối: cửa sổ OH đã bị đóng. Mở lại OHDemo.exe rồi chạy lại; dòng này chưa xử lý xong. · LƯU Ý: có thể đã tạo hồ sơ mớ (1.8s) ¦ chạy lại: CREATE Đã tạo · PID NEW000001 · Title, Sex, Ngày sinh, Nationality, |
| Đối soát | khớp |
| Thời gian | 27.8 giây |

**J07. OH bị tắt: tạo mới, before click:edit-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | OH bị đóng ở đúng bước này; RPA không được báo thành công, không treo; mở lại OH rồi chạy lại phải đúng. |
| Tiền điều kiện | before click:edit-save → kill_oh |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Mất kết nối: cửa sổ OH đã bị đóng. Mở lại OHDemo.exe rồi chạy lại; dòng này chưa xử lý xong. · LƯU Ý: hồ sơ NEW000001 đã đượ (2.7s) ¦ chạy lại: CREATE Đã tạo · PID NEW000001 · Title, Sex, Ngày sinh, Nationality, |
| Đối soát | khớp |
| Thời gian | 28.1 giây |

**J08. OH bị tắt: tạo mới, after click:edit-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | OH bị đóng ở đúng bước này; RPA không được báo thành công, không treo; mở lại OH rồi chạy lại phải đúng. |
| Tiền điều kiện | after click:edit-save → kill_oh |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Mất kết nối: cửa sổ OH đã bị đóng. Mở lại OHDemo.exe rồi chạy lại; dòng này chưa xử lý xong. · LƯU Ý: hồ sơ NEW000001 đã đượ (2.6s) ¦ chạy lại: CREATE Đã tạo · PID NEW000001 · Title, Sex, Ngày sinh, Nationality, |
| Đối soát | khớp |
| Thời gian | 28.1 giây |

**J11. RPA bị tắt đột ngột: cập nhật, after search** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | after search → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Đã cập nh… |
| Đối soát | khớp |
| Thời gian | 47.1 giây |

**J12. RPA bị tắt đột ngột: cập nhật, after click:edit-toggle** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | after click:edit-toggle → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Đã cập nh… |
| Đối soát | khớp |
| Thời gian | 48.9 giây |

**J13. RPA bị tắt đột ngột: cập nhật, after read_edit** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | after read_edit → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Đã cập nh… |
| Đối soát | khớp |
| Thời gian | 49.7 giây |

**J14. RPA bị tắt đột ngột: cập nhật, after set_text:edit-phone** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | after set_text:edit-phone → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Đã cập nh… |
| Đối soát | khớp |
| Thời gian | 49.1 giây |

**J15. RPA bị tắt đột ngột: cập nhật, before click:edit-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | before click:edit-save → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Đã cập nh… |
| Đối soát | khớp |
| Thời gian | 50.4 giây |

**J16. RPA bị tắt đột ngột: cập nhật, after click:edit-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | after click:edit-save → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Không đổi… |
| Đối soát | khớp |
| Thời gian | 47.3 giây |

**J17. RPA bị tắt đột ngột: tạo mới, after click:new-patient** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | after click:new-patient → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Đã tạo · … |
| Đối soát | khớp |
| Thời gian | 49.2 giây |

**J18. RPA bị tắt đột ngột: tạo mới, after set_text:new-last** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | after set_text:new-last → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Đã tạo · … |
| Đối soát | khớp |
| Thời gian | 48.9 giây |

**J19. RPA bị tắt đột ngột: tạo mới, after click:new-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | after click:new-save → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Đã cập nh… |
| Đối soát | khớp |
| Thời gian | 53.3 giây |

**J20. RPA bị tắt đột ngột: tạo mới, after read_edit** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | after read_edit → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Đã cập nh… |
| Đối soát | khớp |
| Thời gian | 53.8 giây |

**J21. RPA bị tắt đột ngột: tạo mới, after set_text:edit-dob** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | after set_text:edit-dob → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Đã cập nh… |
| Đối soát | khớp |
| Thời gian | 54.0 giây |

**J22. RPA bị tắt đột ngột: tạo mới, before click:edit-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | before click:edit-save → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Đã cập nh… |
| Đối soát | khớp |
| Thời gian | 53.3 giây |

**J23. RPA bị tắt đột ngột: tạo mới, after click:edit-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng. |
| Tiền điều kiện | after click:edit-save → kill_rpa |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: Tiến trình RPA kết thúc (mã 137); báo cáo trước khi bị tắt: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu (có thể Ex; dòng 4: Đã tạo · PID NEW000001 · Title, Sex, Ngày sin; dòng 5: Đang xử lý… ¦ chạy lại: dòng 3: Lỗi · Số điện thoại thiếu số 0 đầu ; dòng 4: Không đổi · PID NEW000001; dòng 5: Không đổi… |
| Đối soát | khớp |
| Thời gian | 50.7 giây |

**J24. Người dùng bấm Dừng: tạo mới, after click:new-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Cờ Dừng bật giữa dòng; dòng dở phải được nêu rõ và chạy lại phải hoàn tất. |
| Tiền điều kiện | after click:new-save → set_stop |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Đã dừng; dòng này chưa xử lý xong. · LƯU Ý: hồ sơ NEW000001 đã được tạo nhưng chưa bổ sung đủ thông tin; chạy lại RPA để hoà ¦ chạy lại: UPDATE Đã cập nhật · PID NEW000001 · Title, Sex, Ngày sinh, Nationa |
| Đối soát | khớp |
| Ghi chú | Vết: >> set_stop None |
| Thời gian | 35.4 giây |

**J25. Người dùng bấm Dừng: tạo mới, after set_text:edit-dob** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Cờ Dừng bật giữa dòng; dòng dở phải được nêu rõ và chạy lại phải hoàn tất. |
| Tiền điều kiện | after set_text:edit-dob → set_stop |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Đã dừng; dòng này chưa xử lý xong. · LƯU Ý: hồ sơ NEW000001 đã được tạo nhưng chưa bổ sung đủ thông tin; chạy lại RPA để hoà ¦ chạy lại: UPDATE Đã cập nhật · PID NEW000001 · Title, Sex, Ngày sinh, Nationa |
| Đối soát | khớp |
| Ghi chú | Vết: >> set_stop None |
| Thời gian | 36.9 giây |

**J26. Người dùng bấm Dừng: cập nhật, after click:edit-toggle** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Cờ Dừng bật giữa dòng; dòng dở phải được nêu rõ và chạy lại phải hoàn tất. |
| Tiền điều kiện | after click:edit-toggle → set_stop |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo ERROR: ReviewRequired: Đã dừng; dòng này chưa xử lý xong. ¦ chạy lại: UPDATE Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ |
| Đối soát | khớp |
| Ghi chú | Vết: >> set_stop None |
| Thời gian | 31.8 giây |

**J27. Người dùng bấm Dừng: cập nhật, before click:edit-save** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Cờ Dừng bật giữa dòng; dòng dở phải được nêu rõ và chạy lại phải hoàn tất. |
| Tiền điều kiện | before click:edit-save → set_stop |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA báo UPDATE: Đã cập nhật · PID DEMO0001 · Điện thoại, Địa chỉ ¦ chạy lại: SAME Không đổi · PID DEMO0001 |
| Đối soát | khớp |
| Ghi chú | Vết: >> set_stop None |
| Thời gian | 31.2 giây |


### K. Phát hiện và hoàn tác sau khi RPA đã ghi

**K01. Vết trước/sau của từng hồ sơ đầy đủ và khớp OH** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Muốn kiểm tra hoặc hoàn tác phải biết chính xác RPA đã đổi gì. |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: 3 mục nhật ký, 20 dòng báo cáo |
| Đối soát | khớp |
| Thời gian | 53.3 giây |

**K02. Khôi phục hồ sơ đã cập nhật về giá trị trước lượt chạy** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Cập nhật nhầm phải đưa lại được; hồ sơ tạo mới không được tự ý đụng tới. |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: đã khôi phục 1 hồ sơ; kết quả: DEMO0001: Đã khôi phục ¦ NEW000001: CẦN NGƯỜI CÓ QUYỀN XỬ LÝ ¦ NEW000002: CẦN NGƯỜI CÓ QUYỀN XỬ LÝ |
| Đối soát | khớp |
| Thời gian | 49.3 giây |

**K03. Từ chối khôi phục khi hồ sơ đã bị người khác sửa sau lượt chạy** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Khôi phục không được ghi đè thay đổi của người khác. |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: DEMO0001: BỎ QUA ¦ NEW000001: CẦN NGƯỜI CÓ QUYỀN XỬ LÝ |
| Đối soát | khớp |
| Thời gian | 29.4 giây |

**K04. Đối soát chỉ đọc khi mọi thứ đúng** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Đối soát phải báo Khớp và không được ghi gì vào OH. |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: kết quả đối soát: ['Khớp', 'Khớp', 'Khớp'] |
| Đối soát | khớp |
| Thời gian | 52.1 giây |

**K05. Đối soát phát hiện hồ sơ bị sửa lệch và bị tạo trùng** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Sai sót phát sinh sau khi RPA ghi phải bị phát hiện. |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: kết quả: ['Khớp', 'LỆCH', 'TRÙNG']; chi tiết:  ¦ SĐT: OH="0977000555" ≠ Excel="0933737935" ¦ Có 2 hồ sơ cùng tên và năm sinh: NEW000002, NEW000003 |
| Đối soát | khớp |
| Thời gian | 28.5 giây |

**K06. Đối soát phát hiện hồ sơ biến mất / OH mất dữ liệu** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Hồ sơ RPA đã tạo mà không còn trong OH phải được báo. |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: kết quả: ['LỆCH', 'KHÔNG TÌM THẤY', 'KHÔNG TÌM THẤY'] |
| Đối soát | khớp |
| Thời gian | 25.8 giây |

**K07. Khôi phục sau khi RPA bị tắt giữa lượt chạy** — **ĐẠT**

| | |
|---|---|
| Rủi ro | Vết phải còn cho các dòng đã xong; khôi phục vẫn dùng được. |
| Mong đợi | Không ghi sai, chạy lại hội tụ |
| Thực tế | Không ghi sai, chạy lại hội tụ: RPA bị tắt ở dòng 3; nhật ký [3, 4]; khôi phục: DEMO0001: Đã khôi phục ¦ NEW000001: CẦN NGƯỜI CÓ QUYỀN XỬ LÝ |
| Đối soát | khớp |
| Thời gian | 35.9 giây |


## 7. Điều chưa kiểm thử được và giới hạn

- Chỉ thử với OHDemo (bản mô phỏng). Hành vi trên OH thật (tên ô, hộp thoại, tốc độ, quyền) có thể khác; cần nghiệm thu riêng.
- Chưa thử tình huống khóa màn hình, thoát Remote Desktop, máy ngủ, hoặc OH chạy ở màn hình/độ phân giải khác.
- Nhóm I mô phỏng người dùng bằng thao tác chèn đồng bộ giữa hai bước của RPA; chưa thử thao tác song song ngẫu nhiên nhiều người cùng lúc. Khoảng hở rất ngắn giữa lần kiểm tra cuối và lần bấm Lưu vẫn tồn tại, nên sau khi lưu RPA đọc lại hồ sơ và báo lỗi nếu lệch.
- Ca I06 (người dùng sửa họ rồi RPA lưu) và các ca tương tự: RPA báo lỗi nêu rõ PID nhưng hồ sơ đã bị lưu dữ liệu lạ; việc sửa lại là của người duyệt, RPA không tự hồi phục vì tìm hồ sơ theo họ tên.
- Chưa thử danh sách lớn hơn khoảng 200 dòng liên tục hoặc chạy nhiều giờ.
- Dữ liệu ngoài danh sách (ví dụ 1 triệu ký tự trong một ô) và bảng mã đặc biệt ngoài tiếng Việt chưa được thử.
- Nhóm F kiểm tra đọc file bằng đúng hàm của RPA và đối chiếu với kiểu lỗi mà `app.load()` bắt; chưa mở giao diện Tk cho từng ca.
- Kết quả đạt trên bộ dữ liệu này không bảo đảm đạt trên dữ liệu khác; chỉ chứng minh được trong phạm vi các ca đã nêu.

## 8. Cách chạy lại

```powershell
cd Prototype\RPA
conda activate vinmec
python kiem_thu\chay_kiem_thu.py      # khoảng 40 phút; cửa sổ OH sẽ nhảy lên trước
python kiem_thu\nhom_i_j.py sau            # nhóm I, J (khoảng 30 phút); tham số truoc = so sánh với bản mã đã lưu
python kiem_thu\viet_bao_cao.py       # sinh lại KIEM_THU_RPA.md từ ket_qua.json
```

Biến môi trường để thử nhanh: `KT_FAST=1` (rút gọn nhóm C, D, E), `KT_A=<số>` và `KT_H=<số>` (số người ở nhóm A và H). Trong lúc chạy, đừng thao tác trong cửa sổ OHDemo.
