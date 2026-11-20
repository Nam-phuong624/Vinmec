# Kịch bản video demo RPA: chuẩn bị danh sách khám

**Trạng thái: người dùng đã duyệt và cho phép bắt đầu quay. Phần mô tả vấn đề rút còn 15–20 giây.**

## Mục đích và phạm vi

Giới thiệu khó khăn trong bước chuẩn bị danh sách khám theo đoàn, sau đó trình diễn RPA đọc danh sách Excel và tạo/cập nhật thông tin hành chính trên OHDemo.

Thời lượng dự kiến: khoảng 2–3 phút, gồm lời thuyết minh và phụ đề tiếng Việt. Phần xử lý RPA được quay ở tốc độ thực tế; thời lượng cuối phụ thuộc lần chạy được ghi hình.

Nguồn bối cảnh: `Prototype/Báo cáo tuần 3 - Khoa Y học gia đình + CĐHA.pdf`, đặc biệt slide 2–5, 10–11.

- Slide 3 và 5 ghi nhận 4–5 đoàn, 80–120 khách/ngày; buổi sáng đông hơn buổi chiều.
- Slide 2–5 nêu dữ liệu đối tác không đồng nhất, thiếu thông tin; bước lên danh sách gói khám mất 30–60 phút cho 50 người. Đây là thời gian của quy trình chuẩn bị, không phải số đo riêng thao tác nhập trên OH.
- Slide 3 và 5 nêu sai sót về PID: những người trùng tên bị nhầm, hoặc một người có hai PID; dư khoảng cách khi nhập được nêu là một nguyên nhân có thể xảy ra.
- Slide 10 phân biệt RPA ở bước chuẩn bị với In_Phieu ở bước tại quầy.
- Các số về thời gian sau tự động hóa, chi phí và tiết kiệm trong slide có phần là ước tính hoặc chưa đo trên OH thật. Không dùng chúng làm kết quả đã chứng minh trong video.

Video này tập trung vào RPA nhập/cập nhật OH từ file đã chuẩn bị. Không trình diễn quét CCCD, in phiếu hoặc khẳng định RPA hiện đã tự chuẩn hóa và ghép mọi file policy đầu vào.

## Dữ liệu và cảnh quay

Dùng lại `ds bung/20-11-2026/DEMO_RPA_10_dong_tu_kiem_thu.xlsx`: 10 dòng, giữ nguyên đủ 22 cột từ file kiểm thử gốc. Các mã ca là A001–A007, E27, E06, E40. Toàn bộ dữ liệu là dữ liệu giả.

Khi trình bày Excel, không ẩn các cột. Có thể cuộn ngang để giới thiệu nhóm thông tin; ghi rõ demo rút gọn 10 dòng, không phải danh sách thực tế của bệnh viện.

Chỉ thao tác và quay sau khi người dùng duyệt kịch bản. Dùng phiên OHDemo và thư mục kết quả riêng, giữ nguyên dữ liệu thử hiện có của người dùng.

## 1. Vấn đề thực tế, khoảng 15–20 giây

**Hình ảnh:** danh sách Excel, chuyển sang OHDemo rồi mở RPA. File Excel giữ đủ 22 cột; có thể cuộn ngang, không ẩn cột.

**Lời thuyết minh đã duyệt:**

“Mỗi ngày, khoa tiếp nhận khoảng 80–120 khách khám theo đoàn. Nhân viên phải đối chiếu danh sách Excel rồi nhập, cập nhật thông tin trên OH. Công việc lặp lại này mất thời gian và có nguy cơ nhầm hoặc trùng hồ sơ. RPA được xây dựng để hỗ trợ bước nhập liệu đó.”

## 2. Giới thiệu giải pháp, khoảng 15–20 giây

**Hình ảnh:** mở RPA bên cạnh OHDemo, hiển thị tên file và số dòng đã nạp.

**Lời thuyết minh:**

“Trong bản demo này, RPA nhận file danh sách đã chuẩn bị, tìm hồ sơ trên OHDemo theo họ tên và năm sinh, rồi cập nhật hoặc tạo mới. Nhân viên theo dõi trạng thái từng dòng và xử lý các trường hợp được báo lỗi hoặc cần điền tay.”

## 3. Thao tác thật trên 10 dòng, khoảng 70–90 giây

**Chuẩn bị dự kiến:** tạo thủ công hồ sơ tương ứng A001 nhưng chưa có địa chỉ, để có ví dụ cập nhật hồ sơ cũ. Các người còn lại chưa có trên phiên OHDemo riêng. Việc chuẩn bị này phải được giới thiệu rõ, không trình bày như một phát hiện trên hệ thống thật.

**Hình ảnh và thao tác:**

1. Giới thiệu file có 10 dòng và đủ 22 cột; chỉ ba dòng được chọn để thử lỗi hoặc thiếu dữ liệu.
2. Chỉ tên file và số dòng trên RPA, bấm Chạy RPA.
3. Quay cả OHDemo và RPA trong lúc xử lý, không thao tác thêm trên OH.
4. Chuyển sang khung RPA lớn hơn khi cần đọc trạng thái.

**Lời thuyết minh:**

“Danh sách thử gồm bảy dòng hợp lệ, một dòng thiếu số điện thoại, một tên chứa chữ số và một địa chỉ chưa đủ chi tiết. Tất cả được lấy từ dữ liệu kiểm thử gốc.”

“Khi bấm chạy, RPA xử lý lần lượt từng dòng. Người đã có hồ sơ được đối chiếu để cập nhật phần khác với Excel; người chưa có được tạo mới và cấp PID. Chương trình kiểm tra dữ liệu trước khi lưu và đọc lại hồ sơ sau khi lưu.”

“Dòng thiếu hoặc sai dữ liệu được báo lý do. Địa chỉ không tách được sẽ cần người điền tay; các thông tin khác của hồ sơ có thể đã được lưu. Vì vậy, cần đọc cả trạng thái và PID khi xử lý tiếp.”

## 4. Kết quả và phần việc còn lại, khoảng 25–35 giây

**Hình ảnh:** chờ thông báo Xong; phóng phần tổng kết và các dòng lỗi/cần điền tay. Nếu mở được báo cáo Excel ổn định, giới thiệu `ds lỗi.xlsx` cùng lý do và số dòng gốc.

**Kết quả dự kiến với điều kiện chuẩn bị trên:** 6 dòng tạo mới, 1 cập nhật, 1 cần điền tay, 2 lỗi. Chỉ đọc các con số này sau khi xác nhận từ lượt quay thực tế; nếu khác thì dừng kiểm tra, không dựng lời đọc sai kết quả.

**Lời thuyết minh:**

“Lượt xử lý đã hoàn tất. RPA tổng kết số dòng tạo mới, cập nhật, cần điền tay và lỗi. Những trường hợp cần kiểm tra được ghi lại kèm lý do, để nhân viên tập trung vào phần còn lại thay vì rà lại toàn bộ danh sách.”

## 5. Kết thúc, khoảng 15 giây

**Hình ảnh:** mở lại một hồ sơ vừa xử lý; kết bằng màn hình kết quả RPA.

**Lời thuyết minh:**

“RPA hỗ trợ bước chuẩn bị danh sách bằng cách giảm nhập liệu lặp lại và giữ vết kết quả xử lý. Đây là bản thử trên OHDemo với dữ liệu giả; thời gian và độ chính xác trên OH thật vẫn cần được kiểm chứng. Quét CCCD và in phiếu là phần demo riêng.”

## Điều kiện trước khi quay

- Người dùng duyệt kế hoạch, lời thuyết minh và thời lượng.
- Kiểm tra lại đúng file 10 dòng, đủ 22 cột, không ẩn cột trong cảnh Excel.
- Diễn tập trên phiên OHDemo riêng, xác nhận kết quả thực tế trước khi thu lời đọc chốt số liệu.
- Không dùng mức 5–7 phút khách điền phiếu để mô tả thời gian mà RPA riêng lẻ tiết kiệm được.
- Không đưa tốc độ 2,5 giây/khách hoặc khoản tiết kiệm tài chính từ slide vào video như số đã đo trên OH thật.
