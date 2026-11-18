# Kế hoạch triển khai demo OH và RPA tiếp đón Vinmec

Ngày lập: 17/11/2026. Cập nhật theo `SPEC.md` phiên bản 0.3: OH desktop native và RPA hai lần. Task hiện tại ở `TASKS-TWO-STAGE.md`; task chuyển desktop trước đó ở `TASKS-DESKTOP.md`.

## 1. Kết quả cần bàn giao

Một bộ demo chạy cục bộ trên Windows với hai cửa sổ đặt cạnh nhau:

- **OH mô phỏng:** quét/nhập PID, xem Patient Profile, chỉnh sửa và lưu hồ sơ giả.
- **RPA:** nạp Excel, nhận CCCD, đối chiếu đúng người và hồ sơ đang mở, xác nhận địa chỉ, tự thao tác điền trên OH.

Luồng trình diễn chính: **Excel khách mới chưa PID → RPA lần 1 điền hồ sơ/gói → nhân viên lưu để OH cấp PID → đọc lại và xuất danh sách PID → hôm sau mở hồ sơ bằng PID → quét CCCD → RPA lần 2 đối chiếu và cập nhật địa chỉ → lưu và xác minh.**

Phạm vi bổ sung đã triển khai: form tạo mới/gói trên OH; dữ liệu khách mới chưa PID; kiểm tra trùng CCCD ở OH trước tạo và trong giao dịch lưu; xuất Excel riêng sau xác minh PID; giao diện chuyển hai giai đoạn; kiểm thử xuyên suốt. Gói ở mức mô phỏng thông tin mã/tên gói, policy và ngày/giờ, chưa sinh dịch vụ/chỉ định hoặc tự lưu hàng loạt. Các mốc bên dưới ghi lại kế hoạch nền tảng ban đầu; xem bảng task mới để đánh giá phần hai giai đoạn.

Ưu tiên có một luồng chạy xuyên suốt sớm, sau đó hoàn thiện giao diện, các tình huống lỗi và tài liệu demo.

## 2. Quyết định triển khai cho bản đầu

| Hạng mục      | Lựa chọn                                                  | Mục đích                                                      |
| ------------- | --------------------------------------------------------- | ------------------------------------------------------------- |
| OH mô phỏng   | C#/WinForms native, SQLite qua helper Python             | Build EXE, control Windows thật, lưu và mở lại hồ sơ          |
| Giao diện RPA | Python Tkinter                                            | Có cửa sổ riêng, chọn file cục bộ và nhận dữ liệu máy quét    |
| Đọc Excel     | openpyxl                                                  | Đọc `.xlsx`/`.xlsm`, giữ nguyên file nguồn, không chạy macro  |
| Điều khiển OH | pywinauto + Windows UI Automation                        | Nhìn thấy RPA thao tác control native và hộp địa chỉ          |
| Đọc CCCD      | Adapter chuỗi quét + adapter dữ liệu giả                  | Demo được khi chưa có thiết bị; bổ sung định dạng thực tế sau |
| Kiểm thử      | pytest và OH WinForms thật qua Windows UI Automation     | Kiểm tra các lỗi có thể dẫn đến cập nhật nhầm                 |
| Khởi động     | Script PowerShell và hướng dẫn cài một lần                | Khởi động được trên máy trình diễn                            |

RPA kết nối theo PID tiến trình và HWND của OH Desktop do bộ demo mở. Lễ tân thao tác trực tiếp trên cửa sổ WinForms đó. Không khởi chạy trình duyệt hoặc server trong luồng demo hiện tại.

RPA chỉ đọc/ghi hồ sơ qua giao diện OH. Helper SQLite thuộc nội bộ ứng dụng OH, không được RPA gọi để cập nhật hồ sơ.

## 3. Các mốc triển khai

Ước lượng sơ bộ: **6–8 ngày công** cho một người phát triển chính có người nghiệp vụ hỗ trợ kiểm tra. Đây là ước lượng khối lượng, chưa phải lịch cam kết; không bao gồm tích hợp OH thật hoặc phát triển SDK đầu đọc.

| Mốc                       | Công việc                                                                                       | Đầu ra/điều kiện hoàn thành                                              | Ước lượng  |
| ------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------- |
| M0 — Nền tảng và dữ liệu  | Kiểm tra Python/Chromium/Tkinter; tạo cấu trúc; chốt hợp đồng dữ liệu; sinh dữ liệu giả         | Chạy được ứng dụng rỗng; có 20 hồ sơ giả, Excel mẫu và các ca lỗi riêng  | 0,5 ngày   |
| M1 — OH mô phỏng          | Tra PID; Patient Profile theo ảnh; hộp địa chỉ; lưu/hủy; dữ liệu SQLite                         | Nhập tay, lưu và mở lại đúng hồ sơ; PID chỉ đọc; có trạng thái chưa lưu  | 1–1,5 ngày |
| M2 — Nhập và đối chiếu    | Đọc Excel; chọn sheet/công ty/đợt; phân tích CCCD; chuẩn hóa và phát hiện mâu thuẫn             | Đối chiếu đúng trên dữ liệu giả; trả lỗi rõ ràng với số dòng nguồn       | 1 ngày     |
| M3 — Luồng RPA xuyên suốt | Kết nối cửa sổ RPA với phiên OH; bản xem trước; xác nhận địa chỉ; điền và đọc lại; theo dõi lưu | Chạy được một ca từ quét PID đến lưu và xác minh, không sửa DB qua RPA   | 1–1,5 ngày |
| M4 — Kiểm soát lỗi        | Đổi hồ sơ giữa chừng; dữ liệu bị sửa sau xem trước; dừng; timeout; quét lặp; lỗi lưu            | Các trường hợp mục 11 của spec được kiểm thử; không báo hoàn tất sai     | 1–1,5 ngày |
| M5 — Hoàn thiện demo      | Chỉnh giao diện; script chạy/reset; mã demo; hướng dẫn; đo và diễn tập                          | Chạy lại từ dữ liệu sạch, thực hiện AC-01 đến AC-11, có biên bản kết quả | 1–1,5 ngày |

M0 → M1 → M2 → M3 → M4 → M5 là thứ tự bàn giao mặc định. Nếu nhóm chia việc, sau M0 có thể giao OH và phần xử lý dữ liệu cho hai người theo hợp đồng chung; M3 cần cả hai phần hoàn thành.

## 4. Danh sách công việc triển khai

### M0 — Nền tảng và dữ liệu

- [ ] Kiểm tra môi trường Windows, .NET Framework, Python, Tkinter và UI Automation.
- [ ] Tạo môi trường ảo, file phụ thuộc, build EXE và thư mục dữ liệu phát sinh.
- [ ] Định nghĩa `Patient`, `RosterEntry`, `ScannedIdentity`, `Address`, `ReceptionSession`, `UpdateProposal` và mã lỗi.
- [ ] Tách kho hồ sơ OH khỏi danh sách Excel để tạo được ca lệch dữ liệu.
- [ ] Sinh 20 hồ sơ giả thuộc 2 công ty; có CCCD bắt đầu bằng 0 và người trùng tên.
- [ ] Sinh Excel mẫu theo tiêu đề hàng 2 của `DS_bung_*`; thêm bộ file lỗi riêng.
- [ ] Tạo chuỗi CCCD giả có định dạng được tài liệu hóa và ánh xạ tới từng kịch bản.

### M1 — OH mô phỏng

- [ ] Làm trang tra PID với Enter từ máy quét; xử lý PID không tồn tại.
- [ ] Dựng Patient Profile theo nhóm trường trong ảnh, có PID và thông tin công ty rõ ràng.
- [ ] Làm hộp CCCD và địa chỉ; trường tên/ngày sinh dùng hiển thị và đối chiếu.
- [ ] Thêm Lưu, Hủy thay đổi, Quay lại và thông báo kết quả.
- [ ] Tách dữ liệu đang sửa khỏi dữ liệu đã lưu; hủy trả về giá trị đã lưu.
- [ ] Thêm phiên bản hồ sơ và dấu hiệu giao diện đã lưu để RPA phát hiện thay đổi.
- [ ] Gán selector ổn định cho PID, tên, ngày sinh, CCCD, địa chỉ và nút thao tác.

### M2 — Nhập dữ liệu và đối chiếu

- [ ] Cho chọn file, liệt kê sheet, chọn hàng tiêu đề và ánh xạ cột.
- [ ] Với danh sách thiếu cột công ty/đợt khám, yêu cầu gán ngữ cảnh khi nạp; không suy diễn từ tên policy.
- [ ] Kiểm tra kiểu dữ liệu CCCD/PID, ngày sinh, công thức thiếu giá trị và trường bắt buộc.
- [ ] CCCD bắt buộc ở mọi dòng Excel: thiếu/sai CCCD thì chặn nạp toàn bộ danh sách và báo dòng cần sửa. Các lỗi khác báo theo dòng; khóa các định danh trùng trong phạm vi đã chọn.
- [ ] Xây adapter nhận chuỗi quét kết thúc bằng Enter; tách adapter giả lập khỏi định dạng thiết bị thực tế.
- [ ] Chốt cách ghép các thành phần tên theo trường OH; kiểm tra tên có dấu, khoảng trắng và Unicode.
- [ ] Áp dụng quy tắc CCCD chính xác + công ty/đợt + tên/ngày sinh + PID đang mở.
- [ ] Tạo bản đề xuất cập nhật có giá trị trước/sau, nguồn và dấu phiên bản hồ sơ.

### M3 — RPA chạy xuyên suốt

- [ ] Cửa sổ Tkinter gồm vùng nạp Excel, quét CCCD, kết quả khớp, địa chỉ và trạng thái chạy.
- [ ] Chạy Windows UI Automation ở worker riêng với COM được khởi tạo đúng luồng; trao đổi trạng thái qua hàng đợi.
- [ ] Chỉ cho một lượt ghi hoạt động; thao tác quét mới không thay dữ liệu của lượt đang chạy.
- [ ] RPA đọc hồ sơ OH và lập bản xem trước; nút điền chỉ bật khi đủ điều kiện.
- [ ] Cho nhập địa chỉ hiện tại và bắt buộc xác nhận với khách; sửa đề xuất phải làm mất hiệu lực xác nhận cũ.
- [ ] Kiểm tra PID/phiên bản trước từng nhóm ghi; mở đúng hộp thoại, điền CCCD còn trống và địa chỉ đã duyệt.
- [ ] Đọc lại giá trị đã điền; chuyển sang “Chờ lễ tân lưu”.
- [ ] Theo dõi đúng lần lưu của lượt hiện tại, đọc lại sau tải lại hồ sơ; chỉ khi đó báo hoàn tất.

### M4 — Các nhánh lỗi

- [ ] Mất hiệu lực bản xem trước khi đổi PID, nạp file khác, đổi công ty/đợt hoặc quét người khác.
- [ ] Chặn ghi nếu hồ sơ bị sửa sau lần xem trước; yêu cầu đối chiếu và xác nhận lại.
- [ ] Xử lý đóng cửa sổ OH, control mất hiệu lực và timeout từng bước.
- [ ] Nút Dừng ngăn thao tác tiếp theo; hiển thị trường đã điền một phần, không tự lưu.
- [ ] Chặn tương tác đổi hồ sơ trong nhóm thao tác ghi ngắn trên OH mô phỏng; kiểm tra PID lại sau nhóm ghi và trước lưu để tránh khoảng hở giữa kiểm tra và thao tác.
- [ ] Kiểm thử bấm chạy hai lần, quét hai lần và dữ liệu mới giống dữ liệu cũ; không thêm địa chỉ trùng.
- [ ] Tạo cách giả lập lỗi lưu có kiểm soát, tách khỏi màn hình tiếp đón thông thường.
- [ ] Nhật ký chỉ ghi mã phiên, bước, thời gian, mã lỗi và định danh đã che; không ghi nguyên dữ liệu CCCD/địa chỉ.

### M5 — Đóng gói và diễn tập

- [ ] Tạo script cài phụ thuộc riêng và script khởi động hằng ngày; không tự tải phụ thuộc trong buổi demo.
- [ ] Script reset chỉ tác động SQLite/dữ liệu giả phát sinh trong thư mục runtime đã xác định; giữ nguyên tài liệu và Excel nguồn.
- [ ] Tạo thẻ demo có nhãn dữ liệu giả, mã PID và chuỗi/QR giả để dùng theo kịch bản.
- [ ] Viết hướng dẫn mở hai cửa sổ cạnh nhau, chọn danh sách và phục hồi sau lỗi.
- [ ] Chạy kiểm thử tích hợp, đối chiếu từng tiêu chí AC trong spec và ghi kết quả thực tế.
- [ ] Đo 20 lượt hợp lệ, tách thời gian máy xử lý khỏi thời gian lễ tân hỏi/xác nhận.
- [ ] Diễn tập 5–7 phút: ca đúng → sai PID → trùng tên → không có trong danh sách.

## 5. Cấu trúc mã nguồn dự kiến

```text
RPA/
  SPEC.md
  PLAN.md
  README.md
  requirements.txt
  oh_desktop/        # C#/WinForms native, build EXE và kho SQLite của OH
  rpa_tool/          # Tkinter, worker RPA và adapter điều khiển OH
  shared/            # Mô hình dữ liệu, mã lỗi và chuẩn hóa
  config/            # Ánh xạ cột, cấu hình demo, không chứa dữ liệu thật
  demo/              # Seed giả, Excel giả, chuỗi CCCD và thẻ demo
  tests/             # Kiểm thử dữ liệu và luồng giao diện quan trọng
  scripts/           # Cài đặt, khởi động, tạo lại dữ liệu demo
  runtime/           # SQLite demo và nhật ký phát sinh
  docs/              # Hướng dẫn demo, kết quả kiểm thử và đo thời gian
  Data/              # File tham chiếu hiện có, giữ nguyên
  OH_UI/       # Ảnh tham chiếu hiện có, giữ nguyên
```

## 6. Kế hoạch kiểm thử và điều kiện sẵn sàng demo

Kiểm thử tự động tập trung vào đối chiếu danh tính, chuẩn hóa dữ liệu, kiểm soát hồ sơ đang mở, lưu và xử lý chạy lặp. Bố cục, khả năng đọc, luồng dùng máy quét và kịch bản trình diễn được kiểm tra trực tiếp.

| Nhóm          | Ca kiểm tra trọng tâm                                           | Bằng chứng                                                 |
| ------------- | --------------------------------------------------------------- | ---------------------------------------------------------- |
| Excel/CCCD    | Số 0 đầu, sai sheet, thiếu cột, trùng ID, QR lỗi, sai ngày sinh | Kết quả pytest và danh sách lỗi theo dòng                  |
| Danh tính     | Đúng người, trùng tên, sai PID, khác CCCD trên OH               | Ca tích hợp chứng minh chặn trước ghi                      |
| Địa chỉ       | Chưa xác nhận, đổi địa chỉ sau xác nhận, địa chỉ không đổi      | Nút chạy đúng trạng thái; không thêm địa chỉ trùng         |
| Lượt xử lý    | Đổi hồ sơ, thao tác lặp, dừng, mất kết nối                      | Không tiếp tục ghi sang hồ sơ khác; trạng thái lỗi rõ ràng |
| Lưu           | Thành công, thất bại, hủy, tải lại hồ sơ                        | Chỉ báo hoàn tất khi dữ liệu đã lưu được xác minh          |
| Vận hành demo | Khởi động từ đầu, chạy offline sau cài, reset và chạy lại       | Checklist diễn tập trên máy trình diễn                     |

Chỉ đánh dấu sẵn sàng khi AC-01 đến AC-10 đạt, các ca lỗi bắt buộc đã chạy và kết quả AC-11 được ghi rõ đạt/chưa đạt. Nếu chưa đạt mục tiêu thời gian thì báo giới hạn, không ghi nhận là đã nghiệm thu đầy đủ theo spec.

## 7. Điểm cần khảo sát khi có thiết bị hoặc quyền truy cập OH

Không chặn M0–M5: dùng chuỗi CCCD giả và OH mô phỏng theo spec để triển khai trước.

Khi có thiết bị, kiểm tra chuỗi đầu ra, phím kết thúc và cách lấy focus; sau đó bổ sung adapter và chạy lại bộ đối chiếu. Khi có OH thật, xác nhận công nghệ giao diện, ý nghĩa PID/Hospital Number, cấu trúc địa chỉ, cách lưu và phạm vi trường cho phép cập nhật. Chỉ sau khảo sát mới ước lượng giai đoạn tích hợp thật.

## 8. Việc thực hiện đầu tiên

Bắt đầu M0 và M1: tạo bộ dữ liệu giả, dựng màn hình tra PID và Patient Profile có thể nhập tay, lưu và mở lại. Mốc review đầu tiên là **OH mô phỏng chạy được với dữ liệu giả**, trước khi nối RPA.
