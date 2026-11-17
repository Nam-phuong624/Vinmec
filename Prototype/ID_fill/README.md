# Demo đọc QR từ ảnh CCCD và đối chiếu địa chỉ

Ảnh được giải mã trên thiết bị, chỉ chuỗi QR được gửi về máy tính sau khi bấm gửi. Demo dùng HTTP trong Wi-Fi nội bộ, không có quét camera trực tiếp và không cần cài chứng chỉ.

## Chạy và gửi ảnh từ điện thoại

1. Trong thư mục `ID_fill`, chạy `start-demo.cmd` hoặc `python -B server.py`.
2. Máy tính mở <http://127.0.0.1:8765>, chọn **Ghép điện thoại**.
3. Điện thoại cùng Wi-Fi mở QR kết nối, hoặc nhập đường dẫn và mã 8 chữ số.
4. Chọn **Chụp ảnh CCCD** hoặc **Chọn ảnh có sẵn**, dùng mặt thẻ có mã QR rõ nét.
5. Kiểm tra thông tin đọc được rồi bấm **Gửi sang máy tính**. Không cần xác nhận địa chỉ trước khi gửi.
6. Chụp/chọn ảnh tiếp theo trong cùng phiên 10 phút. Kết quả mới thay thế kết quả cũ trên máy tính; xác nhận/xuất phiếu trước nếu cần giữ lượt trước.

Máy tính cũng có thể dùng **Chọn ảnh CCCD**. Chưa có OCR; ảnh phải có mã QR đọc được. Trình chọn ảnh mở camera hệ thống hay thư viện tùy trình duyệt/thiết bị.

**Bắt đầu lại** xóa biểu mẫu nhưng giữ ghép nối. **Hủy ghép nối** thu hồi phiên. Nếu tải lại trang điện thoại, tạo phiên ghép mới. Sau khi đổi IP/Wi-Fi, khởi động lại server. Điện thoại dùng IP hiển thị trên máy tính, không dùng localhost. Tường lửa cần cho Python truy cập mạng riêng ở cổng 8765.

Dừng server cũ bằng `Ctrl+C` trước khi chạy lại. Không cần OpenSSL hay HTTPS. Nếu từng cài CA demo, có thể gỡ **Vinmec QR Demo Local CA** trong phần chứng chỉ người dùng của Android.

## Biểu mẫu Patient Profile và dữ liệu lịch sử bổ sung

Biểu mẫu theo bố cục ảnh tham chiếu gồm Demographics, Identification Details, Contact Details, Personal Details và Employment Details. QR điền họ/tên đệm/tên, giới tính, ngày sinh và giấy tờ; cần kiểm tra lại cách tách tên. Số hồ sơ bệnh viện, số điện thoại, quốc tịch, ngôn ngữ, dân tộc và nghề nghiệp do người thao tác bổ sung. Circle of Care và Financial hiện chỉ có thông báo chưa có dữ liệu.

Địa chỉ đã chọn được đưa vào Addresses. Sửa trường hồ sơ sẽ hủy xác nhận trước đó; quét người mới sẽ xóa các trường đã nhập của người trước. Phiếu JSON giữ `person` gốc từ QR riêng với `patientProfile` đã chỉnh sửa. Đây là biểu mẫu trong bản demo; chưa kết nối hoặc tự bấm điền vào hệ thống HIS đang chạy ngoài ứng dụng.

`history.js` giữ các quy tắc có nguồn xác minh trước đây. `research-history.js` đóng gói riêng dữ liệu từ các bảng nghiên cứu Wiki, kèm URL, đoạn gốc, phiên bản trang, SHA-256 và trạng thái chưa kiểm chứng độc lập. Khi có quan hệ Wiki phù hợp, giao diện yêu cầu chọn kết quả, ghi căn cứ và tích xác nhận; không tự chấp nhận quan hệ một phần hoặc nhiều đích. Không coi ngày Wiki nêu, ngày đăng bài hoặc ngày thu thập là ngày hiệu lực pháp lý.

Bản dữ liệu này cập nhật từng đợt đọc: 1.150 quan hệ cấp xã trước 01/07/2025 và 3.512 quan hệ thôn/tổ, gồm cả đổi tên và đề án tách riêng trong bảng nguồn. **Crawl và đọc các xã hiện nay chưa hoàn tất**; không dùng số dòng làm số sự kiện hoặc cam kết phủ toàn quốc. Danh mục 3.321 đơn vị tải ngày 16/11/2026 chỉ hỗ trợ kiểm tra mã/tên; chưa thay thế toàn bộ workbook ánh xạ mốc 2025. Tên tỉnh thay đổi sau mốc nguồn có thể chưa đối chiếu được.

Sau khi bổ sung các bảng nguồn trong thư mục `Data`, chạy từ `ID_fill`:

```powershell
python -B import_research.py
```

Chỉ những quan hệ đã được đọc và đưa vào bảng mới được đóng gói. Script này không tự đọc hiểu bài Wiki mới tải. Tải lại trang ứng dụng để nhận gói mới. Nội dung trích Wiki ghi công Wikipedia contributors, theo [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); không coi các trích dẫn Wiki là kết luận đã kiểm chứng.

Kiểm tra thêm biểu mẫu và đề xuất Wiki bằng `python -B verify_profile.py`; có thể đặt biến `DEMO_TEST_URL` để kiểm tra server chạy ở cổng khác.

## Dữ liệu trong phiên

Server chỉ giữ chuỗi QR trong RAM, xóa sau khi máy tính xác nhận đã nhận, khi hủy hoặc hết hạn. Không lưu ảnh, hồ sơ hay token vào file/log/localStorage. Mã ghép dùng một lần, token riêng cho bên gửi và bên nhận. Chỉ máy tính qua localhost có thể nhận kết quả. Dùng dữ liệu giả trên mạng riêng tin cậy cho demo; không mở cổng ra Internet.

## Luồng trình diễn

1. Chọn **Ánh xạ rõ ràng** để đọc QR giả lập của người bệnh mẫu A.
2. Kiểm tra họ tên, số CCCD, ngày sinh, giới tính, ngày cấp và địa chỉ gốc.
3. Xem địa chỉ cũ tại phường Trúc Bạch, quận Ba Đình, Hà Nội được đối chiếu sang phường Ba Đình, Hà Nội theo bảng nguồn.
4. Đánh dấu đã kiểm tra với người bệnh, chọn **Xác nhận thông tin**.
5. Chọn **Tải phiếu JSON** để xem dữ liệu bàn giao mẫu. File chỉ được tạo khi người dùng bấm tải.
6. Thử **Cần kiểm tra thêm**: phường Ngọc Hà cũ có nhiều đơn vị tiếp nhận; cần chọn địa chỉ mới và nhập căn cứ xác nhận.
7. Thử **Chưa đủ địa chỉ**: bổ sung xã/phường, quận/huyện và tỉnh/thành cũ rồi bấm **Đối chiếu lại**.

Quét thẻ thật bằng **Chọn ảnh CCCD**, hoặc mở **Dùng đầu đọc USB / nhập chuỗi QR**. Nút chọn ảnh nhận ảnh toàn bộ mặt thẻ có mã QR hoặc ảnh cận mã QR; hệ thống tìm mã trên toàn ảnh và các vùng chồng lấn để đọc mã nhỏ. Ảnh tối đa 25 MB, 80 megapixel; nên dùng JPG, PNG hoặc WebP rõ nét, không lóa. Nếu không đọc được mã, giao diện yêu cầu chụp lại/cắt sát QR. Chức năng này đọc mã QR trong ảnh, chưa đọc chữ trên thẻ bằng OCR.

Đầu đọc phải xuất văn bản Unicode đúng dấu; đặt con trỏ trong ô nhận, quét rồi nhấn Enter. Demo hỗ trợ chuỗi 7 trường:

```text
Số CCCD|Số CMND cũ hoặc trống|Họ tên|DDMMYYYY|Giới tính|Địa chỉ thường trú|DDMMYYYY
```

Không đưa ảnh thẻ hoặc thông tin người thật vào mã nguồn hay commit.

## Dữ liệu và quy tắc đối chiếu

- Nguồn: [Bảng chuyển đổi đơn vị hành chính mới–cũ của NSO](https://danhmuchanhchinh.nso.gov.vn/TAPTIN/BangChuyendoi%C4%90VHCmoi_cu_final.xlsx).
- Sheet: `Tổng hợp_không merge `; tải ngày **10/11/2026**; **10.565** dòng quan hệ có mã xã cũ và mới.
- Mốc chuyển đổi trong workbook: **01/07/2025**. Đây không phải cam kết danh mục hiện hành đến ngày tải; chưa đồng bộ các biến động phát sinh sau mốc nguồn.
- SHA-256 workbook: `213966723785859dedd7c88965d6f12f8c3c508c91796e003804cf60a1054fc2`.
- `data.js` giữ nguyên giá trị từ cột A–H của sheet; không suy diễn địa giới.
- Khi hiển thị/xuất kết quả, mã xã dạng số trong Excel được bổ sung số `0` bên trái để đủ 5 chữ số, ví dụ `1558` → `01558`; dữ liệu nguồn gốc vẫn giữ nguyên.
- So khớp đồng thời tỉnh/thành, quận/huyện và xã/phường cũ. Có chuẩn hóa dấu, khoảng trắng và một số tiền tố viết tắt; không so khớp gần đúng.
- Đầu vào địa chỉ cần phân cách các cấp bằng dấu phẩy; phần số nhà, đường, thôn/tổ được giữ lại khi ghép địa chỉ mới. Tên đường/thôn được giữ nguyên, chưa xác minh việc đổi tên.
- Chỉ đề xuất tự động khi có một đơn vị mới duy nhất và mọi dòng tương ứng ghi **Nhập toàn bộ**.
- Có quan hệ nhập một phần hoặc nhiều đích: yêu cầu người thao tác chọn đích, nhập căn cứ và xác nhận với người bệnh. Demo không tự xác định ranh giới từ số nhà.
- Không khớp: dừng xác nhận, cho phép bổ sung địa chỉ tra cứu; không ghi đè địa chỉ đọc từ QR.
- Địa chỉ đã có xã/phường và tỉnh/thành theo hai cấp được nhận diện khi khớp duy nhất trong bảng nguồn. Không nhầm một quận/huyện cũ với phường mới trùng tên. Kết quả mới không có cấp quận/huyện và hiển thị trên cả điện thoại/laptop; địa chỉ đọc từ QR vẫn giữ riêng.
- Không dùng ba chữ số đầu CCCD để suy ra nơi cư trú. Đọc QR không đồng nghĩa xác thực CCCD, đọc chip hay xác minh với cơ sở dữ liệu dân cư.

### Địa chỉ trước các đợt sáp nhập trung gian

`history.js` bổ sung các quan hệ lịch sử đã xác minh, không sửa workbook NSO gốc:

- Nghị quyết [1286/NQ-UBTVQH15, khoản 8b](https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2024/11/43247/52865-1-20241283-12841286-nq-ubtvqh15.pdf) nhập toàn bộ Bình Phú và Hữu Bằng (Thạch Thất, Hà Nội) vào Quang Trung từ 01/01/2025. Bảng NSO tháng 7/2025 dùng tên Quang Trung, nên không thể tra trực tiếp Bình Phú.
- Bảng NSO chia Quang Trung sang Tây Phương và Kiều Phú: chỉ biết tên xã cũ thì vẫn phải xác minh, không tự gán toàn bộ vào Tây Phương.
- [Danh sách trụ sở kèm Thông báo 729/TB-UBND, dòng 125](https://xdcs.cdnchinhphu.vn/446259493575335936/2025/6/26/danh-sach-126-xa-17509016620211864713480.pdf) xác nhận thôn Bình Xá thuộc Tây Phương; [thông báo của UBND xã Tây Phương ngày 12/01/2026](https://sqhx-hanoi.mediacdn.vn/91579363132710912/2026/1/12/121-thong-bao-so-07-lua-chon-to-chuc-dau-gia-qsd-dat-tai-thon-binh-xa-1768209021351812111133.pdf) cũng sử dụng địa chỉ này.
- Vì vậy `Bình Xá, Bình Phú, Thạch Thất, Hà Nội` được đối chiếu thành `Bình Xá, Xã Tây Phương, Thành phố Hà Nội`, mã xã `10003`. Giữ nguyên cách ghi thôn từ đầu vào.
- Quy tắc thôn chỉ áp dụng khi đồng thời khớp Bình Xá, xã cũ Bình Phú/Quang Trung, huyện Thạch Thất và Hà Nội. Không dùng từ khóa Bình Xá để đoán xã cho địa bàn khác.
- Kết quả hiển thị liên kết chứng minh; phiếu JSON giữ `mappingKind`, `mappingEvidence` và địa chỉ gốc. Có mẫu **Địa chỉ qua nhiều lần sáp nhập** để thử mà không cần CCCD thật.

Phần bổ sung lịch sử hiện chỉ gồm các địa danh đã kiểm chứng trên, chưa bao phủ mọi đợt thay đổi trước tháng 7/2025 trên toàn quốc.

## Tệp và thư viện

- `index.html`, `styles.css`, `app.js`: giao diện và thao tác ảnh/đầu đọc, xác nhận, xuất phiếu.
- `core.js`: đọc chuỗi QR, kiểm tra định dạng và đối chiếu địa chỉ.
- `server.py`, `pair.js`: ghép điện thoại làm máy quét liên tục trong phiên 10 phút, xác nhận từng lượt để xóa dữ liệu khỏi RAM server; chống gửi lại cùng mã lượt quét.
- `data.js`: bảng quan hệ hành chính được trích từ workbook.
- `history.js`: quan hệ lịch sử và quy tắc thôn đã kiểm chứng, có nguồn riêng.
- `import_data.py`: tái tạo dữ liệu bằng thư viện chuẩn Python, chạy `python import_data.py <đường-dẫn-workbook.xlsx>`.
- `vendor/jsQR.js`: [jsQR 1.4.0](https://github.com/cozmo/jsQR), giải mã QR trên thiết bị, giấy phép Apache-2.0 tại `vendor/LICENSE-jsQR.txt`.
- `vendor/zxing.js`: [ZXing JS 0.21.3](https://github.com/zxing-js/library), bộ giải mã dự phòng cho ảnh, thử ảnh xám/đảo màu/tăng tương phản; giấy phép Apache-2.0 tại `vendor/LICENSE-zxing.txt`. Ảnh thiếu nét, lóa hoặc mất một phần mã vẫn có thể không đọc được.
- `vendor/qrcode.js`: [qrcode-generator 1.4.4](https://github.com/kazuhikoarase/qrcode-generator), tạo QR ghép nối ngay trên laptop; giấy phép MIT tại `vendor/LICENSE-qrcode.txt`.
- Tham chiếu định dạng QR: [tài liệu trường CCCD của Cake Developers](https://developer.cake.vn/vi/identity/eid/nid-field-definitions/).

## Kiểm tra

Script `verify_demo.py` dùng Playwright Python và Chrome đã cài trên máy. Chạy khi máy chủ demo ở cổng 8765 đang hoạt động:

```powershell
python ID_fill/10-11-2026/verify_demo.py
```

Kiểm tra API và hai trình duyệt độc lập (script tự chạy server cổng tạm, không cần server 8765):

```powershell
python -B ID_fill/10-11-2026/verify_pair.py
```

Bao gồm ghép QR/mã tay, ảnh QR giả lập tiếng Việt, chỉ gửi sau khi bấm, tự điền/ánh xạ trên desktop, xóa dữ liệu sau nhận, hủy/hết hạn phiên, không truy cập chéo phiên, chống gửi lại, giới hạn thử mã, kiểm tra Origin/Host và giới hạn kích thước request. Kiểm tra chụp ảnh trên điện thoại và truy cập Wi-Fi/tường lửa cần hai thiết bị thực tế.

Kiểm thử giải mã ảnh giả lập dùng thêm `qrcode-generator@1.4.4/qrcode.js` tại `%TEMP%/vinmec-qr-test-generator.js`; nếu thiếu, script thông báo bỏ qua hai kiểm tra này. Bộ tạo QR chỉ phục vụ kiểm thử, không cần cho ứng dụng demo.

