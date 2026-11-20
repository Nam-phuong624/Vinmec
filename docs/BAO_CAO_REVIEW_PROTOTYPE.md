# Báo cáo rà soát code các prototype

Ngày rà soát: **20/11/2026**. Phạm vi: bảo mật, logic xử lý, lỗi dữ liệu và hardcode trong `Prototype/`, không bao gồm thư mục `Prototype/Data/`.

## 1. Kết luận

Các prototype có nhiều biện pháp bảo vệ hữu ích, nhưng **chưa nên dùng luồng tự động hiện tại để cập nhật hồ sơ thật khi chưa xử lý các phát hiện mức Cao**. Rủi ro nổi bật là nhận nhầm người, thiếu vết thay đổi khi đã ghi vào OH, khôi phục vượt phạm vi một lượt chạy và truyền CCCD qua HTTP trong mạng LAN.

Ghi nhận **17 phát hiện: 4 Cao, 10 Trung bình, 3 Thấp**. Đây là mức ưu tiên theo tác động trong bối cảnh xử lý hồ sơ; không phải điểm CVSS. Một số phát hiện là lỗi nghiệp vụ hoặc giới hạn thiết kế, không phải lỗ hổng khai thác từ Internet.

Không thấy mật khẩu hoặc API key hardcode trong phần mã nguồn đã rà soát. Có hardcode nghiệp vụ cần xem lại. Kết luận này không bao gồm toàn bộ lịch sử Git, nội dung nhị phân, dữ liệu cá nhân cục bộ hay kiểm toán dependency theo cơ sở dữ liệu CVE.

## 2. Phạm vi và cách kiểm tra

| Thành phần | Phạm vi đã xem |
| --- | --- |
| `ID_fill` | Server ghép đôi, phân quyền token, truyền QR, frontend, kiểm tra dữ liệu, ánh xạ địa chỉ và xuất JSON |
| `RPA` | Đọc Excel, nhận diện bệnh nhân, cập nhật giao diện OH, xử lý lỗi, nhật ký, đối soát, khôi phục và script chạy/kiểm thử |
| `In_Phieu` | Đọc QR, tìm khách, chọn mẫu, điền DOCX, tên file xuất, gọi in và server điện thoại |
| `OH_Demo` | Tìm kiếm, tạo PID, chỉnh sửa và lưu hồ sơ trong RAM |
| `RPA/oh_desktop` | Luồng SQLite/WinForms cũ; README xác nhận RPA hiện tại không còn sử dụng |
| `Demo` | Script chuẩn bị dữ liệu và cơ chế đọc cấu hình riêng tư |

Đã đọc code và chạy các phép kiểm chứng cục bộ bằng dữ liệu giả. Với `In_Phieu/fill.py`, các hàm thuần được nạp từ AST của chính file nguồn để không cần khởi động Word hay cài `python-docx`. Phép kiểm tra lỗi ghi audit dùng engine giả và giả lập `PermissionError`; không ghi vào OH thật.

Không sửa code ứng dụng, không chạy script reset/chuẩn bị demo, không commit/push. Không chạy lại bộ kiểm thử desktop kéo dài hoặc thử tấn công gây nghẽn mạng. Chưa kiểm tra động camera thật, Word, máy in, bản EXE đã đóng gói hay tương tác đồng thời giữa người dùng và RPA.

## 3. Các phát hiện mức Cao

### F01 — Tên và năm sinh vẫn có thể dẫn tới cập nhật nhầm người

- **Vị trí:** `Prototype/RPA/rpa_tool/ohdemo_engine.py:418`, `:420`, `:427`, `:458`; `Prototype/RPA/shared/excel.py:164`.
- **Bằng chứng:** nhánh cập nhật chọn một kết quả có tên đã bỏ dấu và cùng năm sinh. Có chặn khi hai ngày sinh đầy đủ khác ngày/tháng, nhưng nếu OH chỉ có năm thì vẫn cập nhật; số điện thoại khác không chặn nhánh này. `ohdemo_record()` không dùng `Patient ID` hoặc `National ID` để xác định người.
- **Tình huống:** OH có một người cùng tên, chỉ lưu năm sinh; Excel là một người khác cùng tên/năm nhưng khác điện thoại và CCCD. RPA có thể ghi ngày sinh, điện thoại và địa chỉ của người thứ hai vào PID của người thứ nhất. Bỏ dấu còn gộp các tên khác nhau về cùng chuỗi so sánh.
- **Trạng thái:** xác định qua đọc luồng code; chưa chạy lại tình huống trên giao diện desktop. Đây cũng là giới hạn đã được README thừa nhận vì OHDemo không có ô CCCD.
- **Đề xuất:** dùng PID đã xác minh hoặc định danh mạnh được OH hỗ trợ. Khi không đủ định danh, chuyển duyệt tay; đặc biệt không tự cập nhật chỉ bằng tên và năm sinh khi điện thoại khác. Việc đọc lại sau lưu chỉ chứng minh đã nhập đúng dữ liệu dự kiến, không chứng minh đã chọn đúng người.

### F02 — Có thể ghi vào OH thành công nhưng không có vết đủ để khôi phục

- **Vị trí:** `Prototype/RPA/rpa_tool/ohdemo_engine.py:469`, `:481`; `Prototype/RPA/rpa_tool/runner.py:26`, `:34`, `:55`.
- **Bằng chứng:** `last_change` chỉ được tạo sau khi lưu và đọc lại thành công. Nếu lưu thành công nhưng đọc lại lỗi, nhánh exception của runner không ghi vết thay đổi. Ngoài ra, `trail()` nuốt `OSError`, bao gồm lỗi không mở được chính file JSONL, rồi vẫn cho dòng báo thành công.
- **Đã tái hiện:** giả lập `audit_trail.record()` ném `PermissionError`; kết quả runner vẫn là `updated=1, error=0`. Vì vậy không thể suy ra “JSONL đã ghi” từ việc exception bị bỏ qua.
- **Tác động:** OH đã đổi nhưng công cụ khôi phục không biết dữ liệu trước đó. Khi tiến trình chết sau lưu cũng có cùng khoảng trống giữa thao tác ghi và ghi audit.
- **Đề xuất:** lưu bền vững ý định và snapshot trước thao tác ghi, cập nhật trạng thái xác nhận sau lưu; nếu ghi audit thất bại thì dừng lượt chạy và báo rõ. Phân biệt trạng thái “có thể đã ghi, chưa xác nhận” với lỗi chưa ghi.

### F03 — “Khôi phục lượt chạy” thực tế gộp lịch sử nhiều lượt cùng tên file

- **Vị trí:** `Prototype/RPA/rpa_tool/hau_kiem.py:60`, `:64`, `:67`; `Prototype/RPA/rpa_tool/app.py:152`; `Prototype/RPA/rpa_tool/audit_trail.py:28`.
- **Bằng chứng:** nhật ký không có `run_id`. Khôi phục lọc theo tên file, giữ `before` của lần cập nhật đầu tiên và `after` của lần cuối cho mỗi PID.
- **Tình huống:** lượt 1 đổi A → B; nhân viên sửa B → C; lượt 2 cùng file đổi C → D. Khôi phục khi OH đang là D sẽ vượt qua kiểm tra `after`, rồi đưa về A thay vì C. Thay đổi hợp lệ của nhân viên giữa hai lượt bị mất.
- **Trạng thái:** xác định qua đọc code; chưa thực hiện khôi phục trên OH.
- **Đề xuất:** gắn `run_id`, hash file nguồn và thời điểm bắt đầu/kết thúc; cho chọn đúng lượt cần hoàn tác. Chỉ nối chuỗi cập nhật trong cùng lượt, không gộp mọi lịch sử theo tên file.

### F04 — `ID_fill` gửi token và dữ liệu CCCD qua HTTP trên LAN

- **Vị trí:** `Prototype/ID_fill/server.py:199`, `:274`, `:319`; `Prototype/ID_fill/pair.js:12`.
- **Bằng chứng:** server mặc định bind `0.0.0.0`, đường dẫn điện thoại là `http://...`, API trả `httpsEnabled: false`. Token ghép, sender token và nội dung QR đi qua kết nối không mã hóa.
- **Tác động:** bên có khả năng quan sát hoặc can thiệp đường truyền có thể đọc CCCD, chiếm sender token hoặc thay payload. Cùng Wi-Fi tự nó không đảm bảo bí mật; khả năng tấn công phụ thuộc cấu hình mạng và vị trí kẻ tấn công.
- **Trạng thái:** xác minh cấu hình và luồng truyền; không thực hiện nghe lén.
- **Đề xuất:** HTTPS với chứng chỉ được tin cậy hoặc kênh USB/tunnel được bảo vệ. Mặc định chỉ mở localhost; bật LAN bằng lựa chọn rõ ràng và giới hạn mạng được phép.

## 4. Các phát hiện mức Trung bình

### F05 — Tự chọn nhầm báo cáo Excel làm danh sách nguồn

- **Vị trí:** `Prototype/RPA/shared/excel.py:47`, `:52`; ảnh hưởng cả RPA và `In_Phieu.load_customers()`.
- **Bằng chứng:** lấy `.xlsx` mới nhất, chỉ loại `~$...` và `ds lỗi.xlsx`. Các file `bao_cao_thay_doi.xlsx`, `bao_cao_doi_soat.xlsx`, `bao_cao_khoi_phuc.xlsx` được tạo trong cùng thư mục và thường mới hơn nguồn.
- **Đã tái hiện:** đặt nguồn và báo cáo mới hơn trong thư mục ngày; hàm chọn `bao_cao_thay_doi.xlsx`, rồi `read_daily()` ném `ReviewRequired` vì thiếu tiêu đề.
- **Đề xuất:** cho chọn/ghi nhớ file nguồn, hoặc dùng quy tắc nhận diện nguồn và kiểm tra schema. Tách báo cáo ra thư mục con; không chỉ dựa vào thời gian sửa.

### F06 — Đối soát so với snapshot cũ trong log, không so dữ liệu Excel hiện tại

- **Vị trí:** `Prototype/RPA/rpa_tool/hau_kiem.py:27`, `:31`, `:37`; `Prototype/RPA/rpa_tool/journal.py:11`.
- **Bằng chứng:** dùng tên file và số dòng để tìm log, lấy `e['expected']` làm chuẩn. Dữ liệu của `row` hiện tại không được dùng để dựng giá trị mong đợi. Nhật ký tiến độ cũng phân biệt file bằng tên, không bằng nội dung/ngày đầy đủ.
- **Tác động:** sửa dữ liệu hoặc đổi thứ tự dòng rồi lưu cùng tên có thể khiến đối soát báo “Khớp” với phiên bản cũ. Đánh dấu dòng bị gián đoạn cũng có thể bị áp sang file cùng tên khác ngày.
- **Trạng thái:** đọc code.
- **Đề xuất:** lưu hash nguồn, khóa dòng ổn định và `run_id`; từ chối đối soát với log khác phiên bản. Nếu mục tiêu là so Excel hiện tại, phải ánh xạ lại dòng hiện tại và thể hiện rõ khác biệt với snapshot.

### F07 — Ngày sinh kiểu ngày Excel bị mất trong luồng in phiếu

- **Vị trí:** `Prototype/In_Phieu/fill.py:76`, `:123`, `:133`, `:180`.
- **Bằng chứng:** `person()` và `check_scan()` chuyển mọi giá trị sang chuỗi. `datetime(1990, 1, 1)` thành `1990-01-01 00:00:00`, không khớp ba format của `ddmmyyyy()`.
- **Đã tái hiện:** `person(row)['dob']` trả chuỗi rỗng với ô ngày hợp lệ dạng `datetime`.
- **Tác động:** phiếu có thể trống ngày sinh/tuổi khi chỉ nhập CCCD; QR hợp lệ lại bị cảnh báo lệch ngày sinh với Excel.
- **Đề xuất:** nhận trực tiếp `date`/`datetime` và chuẩn hóa chung bằng hàm ngày sinh đã có trong `shared.identity`.

### F08 — Tên file DOCX lấy từ Excel có thể thoát khỏi thư mục xuất

- **Vị trí:** `Prototype/In_Phieu/fill.py:267`, `:287`; thao tác ghi tại `:210`.
- **Bằng chứng:** tên người chỉ được bỏ dấu, đổi khoảng trắng thành `_`; dấu `/`, `\` và `..` không bị loại. Không kiểm tra đường dẫn kết quả có còn nằm trong thư mục đích.
- **Đã tái hiện:** tên giả chứa `x/../../outside` tạo đường dẫn sau `resolve()` nằm ngoài `phieu_in`. Phép thử chỉ tính đường dẫn, không ghi DOCX ra ngoài.
- **Tác động:** người kiểm soát Excel có thể điều hướng nơi ghi hoặc ghi đè DOCX mà tiến trình có quyền ghi. Đuôi vẫn là `.docx`; chưa có bằng chứng thực thi mã hoặc ghi tùy ý mọi loại file.
- **Đề xuất:** dùng ID ngẫu nhiên/khóa dòng làm tên file; lọc ký tự tên và kiểm tra containment sau `resolve()` trước khi tạo thư mục/ghi.

### F09 — QR đủ 7 phần nhưng dữ liệu sai vẫn có thể qua kiểm tra

- **Vị trí:** `Prototype/In_Phieu/fill.py:60`, `:76`, `:177`.
- **Bằng chứng:** `parse_scan()` chỉ kiểm số phần và CCCD. Ngày sai biến thành chuỗi rỗng; nếu ngày trong Excel cũng không parse được thì hai giá trị rỗng được xem là bằng nhau. Ngày cấp không được kiểm tra tương quan với ngày sinh hoặc ngày hiện tại.
- **Đã tái hiện:** QR giả có ngày sinh/ngày cấp `INVALID`, Excel có ngày sinh `bad`, còn tên/giới tính trùng: `check_scan()` trả `[]`.
- **Tác động:** khi đã bật tự in, dữ liệu không hợp lệ có thể không bị chặn; phiếu có thể thiếu hoặc sai thông tin. QR cũng chỉ là dữ liệu đầu vào, không phải bằng chứng xác thực danh tính.
- **Đề xuất:** dùng validator chặt như `ID_fill.validate_payload()` cho chuỗi QR đầy đủ; phân biệt “không có dữ liệu” và “có nhưng không hợp lệ”. CCCD nhập tay cần chế độ kiểm tra riêng.

### F10 — Địa chỉ bốn cấp bị gán quận/huyện vào phường/xã

- **Vị trí:** `Prototype/RPA/shared/excel.py:96`; sử dụng tại `Prototype/In_Phieu/fill.py:160` và luồng thêm địa chỉ RPA.
- **Đã tái hiện:** `Số 1, Phường A, Quận B, Tỉnh C` được tách thành tỉnh `Tỉnh C`, phường/xã `Quận B`, số nhà/đường `Số 1, Phường A`.
- **Tác động:** có thể điền sai cấp hành chính vào phiếu/hồ sơ mà kiểm tra đọc lại vẫn coi là đúng vì dùng cùng kết quả tách sai. Đây là giới hạn quy ước đầu vào hiện tại, nhưng QR có thể mang địa chỉ cũ nhiều cấp.
- **Đề xuất:** nhận diện cấp hành chính; không tự đoán khi đầu vào ngoài schema. Dùng bộ ánh xạ có trạng thái cần xác minh của `ID_fill` hoặc chuyển nhập tay.

### F11 — Kết quả quét bị gắn số thứ tự của yêu cầu khác

- **Vị trí:** `Prototype/In_Phieu/phone_scan.py:159`, `:180`, `:248`; `Prototype/In_Phieu/in_phieu.py:206`.
- **Bằng chứng:** hàng đợi chỉ chứa chuỗi QR; `publish()` gắn kết quả với `self.seq` toàn cục ở thời điểm xử lý, không phải số thứ tự đi kèm QR đã lấy ra.
- **Đã tái hiện:** nhận A với seq 1, nhận B với seq 2, rồi xử lý A: kết quả A được publish với seq 2.
- **Tác động:** điện thoại chờ B có thể hiển thị kết quả của A. Một điện thoại theo UI thường chờ trước khi gửi tiếp, nhưng timeout, gửi lại hoặc nhiều client cùng token vẫn có thể tạo điều kiện này.
- **Đề xuất:** queue `(seq, request_id, code)`, publish theo đúng request, giữ kết quả theo request và chống gửi trùng.

### F12 — Server điện thoại chưa giới hạn tốt tài nguyên kết nối và hàng đợi

- **Vị trí:** `Prototype/In_Phieu/phone_scan.py:159`, `:188`, `:239`, `:251`, `:261`, `:271`.
- **Bằng chứng:** `Queue()` không có giới hạn; đọc body không đặt timeout riêng; không giới hạn số thread/rate. TLS wrap trên listening socket với handshake mặc định; code không đặt timeout cho handshake, nên cần kiểm tra thêm nguy cơ một kết nối TLS dở chặn vòng accept.
- **Đã kiểm tra:** `link.codes.maxsize == 0`. Các đường nghẽn kết nối/TLS chỉ đánh giá qua code, không thử tải hay giữ kết nối tấn công.
- **Tác động:** client có token có thể dồn QR làm ứng dụng xử lý kéo dài; client LAN có thể chiếm tài nguyên kết nối trước bước kiểm tra token. Giới hạn body 6 MB không giới hạn số yêu cầu hay thời gian chờ.
- **Đề xuất:** timeout kết nối/handshake/body, queue hữu hạn, giới hạn request đồng thời và rate; từ chối sớm khi đầy. Không để việc xử lý hết queue chiếm vòng lặp UI liên tục.

### F13 — Token ghép đôi in phiếu không hết hạn hoặc thu hồi từ giao diện

- **Vị trí:** `Prototype/In_Phieu/phone_scan.py:157`, `:170`, `:174`, `:208`; `Prototype/In_Phieu/in_phieu.py:163`, `:204`.
- **Bằng chứng:** token tạo một lần trong `PhoneLink`, dùng chung mọi client đến khi ứng dụng dừng; không có TTL, xác nhận thiết bị hoặc chức năng đổi token. Đóng hộp ghép đôi vẫn nhận nền. Token nằm trong query URL trang và path API.
- **Tác động:** người từng chụp QR hoặc có URL có thể tiếp tục gửi QR/đọc kết quả. Đây là rủi ro vòng đời và chia sẻ token, không phải kết luận token ngẫu nhiên dễ đoán.
- **Đề xuất:** hết hạn, hủy ghép/đổi token, xác nhận thiết bị và phân quyền gửi/nhận. Dùng fragment cho QR ban đầu rồi chuyển bearer token vào header; bổ sung `Referrer-Policy`. Chứng chỉ tự ký hiện có mã hóa nhưng cần cơ chế tin cậy chứng chỉ thay vì chỉ hướng dẫn bỏ qua cảnh báo.

### F14 — Luồng OH Desktop cũ cho phép đổi thành CCCD đã thuộc PID khác

- **Vị trí:** `Prototype/RPA/oh_desktop/store.py:66`, `:71`, `:98`.
- **Bằng chứng:** `create()` kiểm CCCD trùng trong transaction; `save()` chỉ kiểm định dạng và version, không kiểm CCCD thuộc PID khác. Schema không có ràng buộc unique cho CCCD nằm trong JSON.
- **Đã tái hiện:** tạo hai hồ sơ giả với CCCD khác nhau, sửa hồ sơ thứ hai thành CCCD hồ sơ thứ nhất; `save()` thành công. Sau đó `find_by_cccd()` ném `ValueError` vì tìm thấy nhiều hồ sơ.
- **Đề xuất:** kiểm trùng trong transaction cập nhật và thêm ràng buộc unique phù hợp. Mức ảnh hưởng hiện tại giới hạn ở bản OH Desktop cũ, không phải lỗi SQL injection của RPA hiện hành.

## 5. Các phát hiện mức Thấp và hardcode

### F15 — Một số giá trị nghiệp vụ được tự điền dù chưa có chứng cứ đầu vào

- **Vị trí:** `Prototype/In_Phieu/fill.py:22`, `:148`, `:172`; `Prototype/In_Phieu/build_forms.py` và phần mô tả mẫu trong README.
- `NOI_CAP`, `DOI_TUONG`, `LY_DO` có mặc định cố định; nơi cấp không có trong QR/Excel nhưng vẫn được điền vào phiếu. Có cơ chế ghi đè `cau_hinh.json`, tuy nhiên file cấu hình lỗi được bỏ qua và quay lại mặc định.
- Các biến thể gói/mẫu trong `build_forms.py` có nội dung suy ra từ mẫu tham chiếu; README đã ghi rõ một số tên gói được đặt theo quy ước. Chưa xác minh tính đúng nghiệp vụ của từng dịch vụ, độ tuổi và tiêu đề gói.
- **Đề xuất:** để trống dữ liệu chưa xác minh; hiện cấu hình đang dùng để người vận hành kiểm tra; lỗi cấu hình phải được báo. Mẫu biểu/gói cần được chủ nghiệp vụ duyệt và quản lý phiên bản.
- Hardcode phục vụ demo như tên cửa sổ, AutomationId, PID/dữ liệu giả, đường dẫn compiler Windows và cổng mặc định không tự nó là lỗ hổng. Chúng gây phụ thuộc môi trường; cổng in phiếu và đường dẫn dữ liệu đã có biến môi trường.

### F16 — Chuỗi Unicode trong mã ghép gây exception không được xử lý đúng

- **Vị trí:** `Prototype/ID_fill/server.py:123`, `:128`, `:289`.
- **Đã tái hiện:** `PairStore.join({'code': 'đ'}, peer)` ném `TypeError` vì `secrets.compare_digest()` với chuỗi không ASCII. Nhánh HTTP chỉ bắt `PairError` và lỗi I/O, nên có thể ngắt yêu cầu thay vì trả 400.
- **Đề xuất:** validate code đúng 8 chữ số ASCII, token theo charset/độ dài cho phép trước khi compare; xử lý thống nhất input không hợp lệ. Đây là lỗi độ bền API, chưa thấy đường bỏ qua xác thực.

### F17 — Lệnh kiểm thử RPA còn trỏ vào bộ test không có trong checkout

- **Vị trí:** `Prototype/RPA/scripts/test.ps1:7`; `Prototype/RPA/kiem_thu/vua_sua_ket_qua.py:9`.
- Thư mục `RPA/tests` hiện không có `test*.py`, nhưng script vẫn gọi `pytest tests`; các XML trong `docs` không chứng minh checkout hiện tại được kiểm thử lại.
- Có bộ kiểm thử UI khác trong `kiem_thu/`, nhưng chưa chạy trong đợt review này. Script `vua_sua_ket_qua.py` có chủ đích sửa một số verdict đã lưu sang “ĐẠT” với lý do bỏ qua đối soát cuối cho ca chuẩn bị. Đây là hậu xử lý có giải thích, không đủ cơ sở kết luận làm giả kết quả; tuy vậy không nên chỉ dựa vào báo cáo sau sửa để đánh giá an toàn.
- **Đề xuất:** cung cấp lệnh test phù hợp code hiện tại; giữ kết quả thô bất biến và biểu diễn skip/tiền điều kiện trong test runner. Thêm ca độc lập cho F01–F14, nhất là crash sau lưu và khôi phục nhiều lượt.

## 6. Những biện pháp đang làm tốt

- `ID_fill`: token ngẫu nhiên, so sánh token, TTL, giới hạn thử ghép, phân quyền owner/sender; tạo/nhận phiên giới hạn localhost; kiểm Host/Origin; allowlist file tĩnh; giới hạn JSON; không ghi URL/token/QR vào access log; frontend dùng `textContent` cho các trường dữ liệu đã xem.
- RPA: chặn nhiều kết quả cùng tên/năm; chặn xung đột ngày/tháng sinh đầy đủ; kiểm PID và nội dung trước lưu; đọc lại sau lưu; ghi dòng lỗi ra Excel; có đối soát và khôi phục với kiểm tra trạng thái hiện tại.
- Xuất báo cáo Excel: ép các ô chuỗi thành kiểu text trong `write_errors()` và `write_report()`, giảm nguy cơ dữ liệu bắt đầu bằng `=` bị hiểu là công thức.
- OH Desktop cũ: truy vấn giá trị SQL bằng tham số; kiểm version khi cập nhật; tạo PID trong transaction.
- Dữ liệu làm việc, `runtime/`, phiếu đã điền và cấu hình riêng tư demo có quy tắc Git ignore. Tuy nhiên Git ignore không thay thế phân quyền hệ điều hành, bảo vệ bản sao lưu hay chính sách xóa dữ liệu.
- `OH_Demo` lưu RAM và khởi tạo lại dữ liệu/PID khi mở lại: phù hợp mô phỏng nhưng không có tính bền vững để dùng như hệ thống hồ sơ thật. Không coi đó là lỗi mất dữ liệu bất ngờ trong bối cảnh demo đã công bố.

## 7. Kết quả kiểm chứng và giới hạn

| Kiểm tra | Kết quả thực tế |
| --- | --- |
| `python -m unittest verify_pair.StoreTests verify_pair.HttpTests -v`, trong `Prototype/ID_fill` | **4/4 đạt**; kiểm Store/API, không chạy `browser_flow()` |
| Parse AST các file Python trong phạm vi review, loại thư mục ngoài phạm vi, `.deps`, `.venv`, `runtime`, cache, build/dist | **38 file, không lỗi cú pháp** |
| Chọn Excel có báo cáo mới hơn | Chọn nhầm báo cáo; đọc nguồn thất bại |
| Hai hồ sơ giả trong SQLite, đổi trùng CCCD | Cập nhật được; lookup sau đó báo nhiều kết quả |
| Ngày Excel dạng `datetime` qua hàm in phiếu | Ngày sinh thành chuỗi rỗng |
| QR ngày sai và Excel ngày sai | `check_scan()` không phát hiện bất thường trong ca thử |
| Tên Excel chứa các đoạn đường dẫn cha | Đường dẫn tính ra thoát thư mục xuất; không ghi file ngoài đích |
| Hai QR đợi xử lý | Kết quả A mang seq của B |
| Queue nhận QR | Không có giới hạn kích thước |
| Địa chỉ bốn cấp | Quận/huyện bị gán thành phường/xã |
| Mã ghép có ký tự không ASCII | `TypeError` |
| Ghi audit giả lập bị `PermissionError` | Runner vẫn báo cập nhật thành công |

Các ca này chứng minh nhánh logic cụ thể, không thay thế kiểm thử tích hợp. Không sử dụng dữ liệu người bệnh thật cho phép thử. Dữ liệu giả trên đĩa của phép thử thành công đã được dọn. Hai lần tạo thư mục tạm bằng Python ban đầu gặp giới hạn quyền truy cập của môi trường; các lần đó không hoàn tất phép kiểm thử.

Không chạy audit dependency trực tuyến, không xác minh CVE theo phiên bản, không kiểm tra toàn bộ lịch sử secrets, không giải nén/kiểm toán VBA trong `.xlsm` hay liên kết/macro trong mọi DOCX/PDF/EXE. Vì vậy báo cáo không đưa ra chứng nhận “không còn lỗ hổng”.

## 8. Thứ tự xử lý đề nghị

1. **Trước khi dùng dữ liệu thật:** xử lý F01–F04; xác định cơ chế định danh, audit bền vững, hoàn tác theo lượt và kênh truyền an toàn.
2. **Trước đợt demo/kiểm thử tiếp:** sửa chọn Excel, ngày sinh, tên file xuất, validate QR, tách địa chỉ và sequence kết quả; bổ sung timeout, giới hạn hàng đợi và hủy ghép.
3. **Nếu tiếp tục dùng OH Desktop cũ:** bổ sung unique CCCD cho cập nhật.
4. **Để bảo trì:** cập nhật lệnh test, bổ sung các ca hồi quy và duyệt cấu hình/mẫu nghiệp vụ. Chạy E2E Word/máy in/camera/UIA trên môi trường riêng với dữ liệu giả trước khi mở rộng phạm vi sử dụng.

Đợt này chỉ tạo báo cáo; các phát hiện chưa được sửa trong code.
