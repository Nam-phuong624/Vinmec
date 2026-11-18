# Demo tiếp đón khám sức khỏe theo đoàn

OH mô phỏng là **ứng dụng Windows native WinForms**, bản có danh sách hồ sơ build thành `runtime/OHDesktop-v5.exe`. Công cụ RPA Python/Tkinter điều khiển các control Windows bằng **pywinauto / Windows UI Automation**. Toàn bộ hồ sơ demo là dữ liệu giả; không kết nối OH thật. Không cần trình duyệt hoặc web server.

Patient Profile đã được sửa theo bố cục trong `OH_UI/OH.jpg`: nhãn trái/ô phải, hai hàng tên, nhóm Identification/Contact/Personal/Employment và thanh Notes/Documents/Functions. Cuộn thân form để xem Personal Details và gói khám bên dưới. Xem đối chiếu tại `docs/oh-reference-layout.md`; các form không có ảnh nguồn vẫn là mô phỏng.

Menu bên trái đã được bổ sung theo `OH_UI/OH_2.jpg`, gồm Registration, Cashier, Admission, Discharge, Transfer, Appointments, Visit và Maintenance. Bấm tên nhóm để thu/mở, cuộn riêng vùng menu; nút `‹`/`☰` thu/mở toàn thanh. Khi thu nhỏ cửa sổ, menu tự gọn để giữ chỗ cho hồ sơ. Các nghiệp vụ ngoài Patient Profile chỉ hiển thị phạm vi demo khi chọn, không thực hiện giao dịch thật.

**Luồng hiện tại:** RPA lần 1 điền hồ sơ khách mới và thông tin gói khám từ Excel → nhân viên lưu, OH cấp PID → xuất danh sách có PID → RPA lần 2 tiếp đón khi khách đến. Task tại `TASKS-TWO-STAGE.md`, báo cáo tại `docs/two-stage-report.md`.

Thay đổi desktop được theo dõi tại `TASKS-DESKTOP.md`, báo cáo tại `docs/desktop-report.md`. `TASKS.md` và báo cáo triển khai đầu tiên ghi lại bản prototype web trước đó.

## Chạy trên máy hiện tại

Mở PowerShell tại thư mục dự án:

```powershell
python .\scripts\start.py
```

Script sẽ build EXE nếu cần, mở OH Desktop và cửa sổ RPA. Cần Windows có .NET Framework 4.x với compiler `csc.exe`, Python có Tkinter và các thư viện trong `requirements.txt`. Máy hiện tại dùng thư viện có sẵn cùng thư viện bổ sung trong `.deps`; trên máy mới cài riêng theo phần bên dưới.

## Cài trên máy mới

Yêu cầu Windows, .NET Framework 4.x, Python 3.11 trở lên có Tkinter và mạng trong lần cài đầu:

```powershell
.\scripts\setup.ps1
.\scripts\start.ps1
```

Nếu chính sách máy không cho chạy `.ps1`, dùng trực tiếp các lệnh Python tương đương:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\scripts\start.py
```

Sau khi cài xong, buổi demo không cần mạng. Đóng cửa sổ RPA để kết thúc worker và đóng riêng tiến trình OH do bộ demo mở. Không cần Edge, Playwright hoặc Flask.

`OHDesktop-v5.exe` là giao diện native; kho dữ liệu SQLite được ứng dụng OH đọc/ghi qua helper Python cục bộ. Đây chưa phải gói EXE độc lập không cần Python. RPA không gọi helper hoặc ghi trực tiếp kho dữ liệu.

## Xem danh sách hồ sơ — không cần nhớ PID

Trên OH bấm **Danh sách hồ sơ** ở thanh trên, hoặc mục cùng tên dưới **Registration** ở menu trái. Danh sách bao gồm hồ sơ mẫu và khách mới đã được lưu/cấp PID, khách vừa tạo xếp trước.

- Gõ tên (có thể không dấu), CCCD, PID hoặc tên công ty rồi bấm Tìm kiếm/Enter.
- Chọn một dòng rồi bấm **Mở hồ sơ đã chọn**, hoặc nhấp đúp dòng đó. OH tự mở đúng PID.
- Dùng Trang trước/Trang sau khi danh sách dài; mỗi trang tối đa 50 hồ sơ. Nút Làm mới đọc lại danh sách.
- Nếu hồ sơ đang sửa chưa lưu, hãy lưu hoặc hủy thay đổi trước khi mở danh sách.

Danh sách hiển thị thông tin người khám, công ty/đợt và gói; không phải màn bệnh án lâm sàng/kết quả xét nghiệm.

## Lần 1 — Tạo PID và chuẩn bị gói khám

1. Chọn **1. Chuẩn bị — tạo PID / bung gói** (mặc định khi mở).
2. Dùng file `demo/new_customers_A.xlsx`, sheet `DS_bung_DEMO`, hàng tiêu đề `2`, công ty `Công ty Demo A`, đợt `DEMO-2026`. File có 3 khách mới, CCCD đầy đủ, PID để trống.
3. Bấm **Nạp danh sách**, chọn một khách, bấm **Điền hồ sơ & gói khám vào OH**.
4. RPA mở form tạo mới, điền hồ sơ/gói từ Excel và kiểm tra CCCD đã tồn tại hay chưa. Xem mã gói `KSK-A01`, ngày khám mẫu `2026-11-18` và các trường khác trên OH.
5. Trên OH kiểm tra rồi bấm **Lưu và cấp PID**. Nếu bấm Hủy tạo mới thì không có PID mới.
6. RPA đọc PID do OH cấp (ví dụ `NEW000001`), tải lại hồ sơ để xác minh, rồi tự xuất Excel riêng vào `runtime/prepared/<mã công ty-đợt>.xlsx`. Đường dẫn cụ thể hiện trên RPA.
7. Có thể chọn tiếp khách khác trong danh sách và lặp lại; khách đã tạo được ghi PID trên bộ chọn. Chưa hỗ trợ tự lưu cả danh sách hàng loạt.

CCCD có sẵn trong Excel nên lần 1 không cần quét thẻ. RPA không tự đặt PID. Gói khám hiện được mô phỏng bằng thông tin mã/tên gói, policy và ngày/giờ khám; chưa sinh dịch vụ/chỉ định bên trong gói. Địa chỉ từ Excel được lưu làm nguồn tham khảo, không mặc nhiên là địa chỉ đã xác nhận sau sáp nhập.

## Lần 2 — Tiếp đón cùng khách đã tạo PID

Hai chế độ chỉ hiện phần thao tác tương ứng. Ở lần 2, khu vực nạp Excel mặc định được ẩn, thay bằng **Đoàn đang tiếp đón — Đã nạp N khách**. Nếu đã có file PID xác minh cho công ty/đợt hiện tại, chọn chế độ lần 2 sẽ tự nạp file đó. Danh sách được dùng cho cả buổi; bấm Lượt mới không làm mất danh sách. Chỉ cần **Đổi đoàn / chọn danh sách** khi thay đoàn hoặc nạp một file khác.

1. Trên RPA bấm **Dùng danh sách đã có PID cho lần 2**. Công cụ chuyển chế độ và nạp file kết quả của công ty/đợt hiện tại.
2. Trên OH nhập PID vừa được cấp ở lần 1, bấm Mở hồ sơ/Enter. Đây là bước mô phỏng quét PID trên hồ sơ in từ hôm trước.
3. Bấm **CCCD demo theo PID**, rồi **Đối chiếu**. Nút lấy chuỗi CCCD giả tương ứng khách vừa tạo.
4. Hỏi/xác nhận địa chỉ hiện tại; nhập ví dụ `Thành phố Demo` / `Phường Mới` / `12 Đường Demo`.
5. Đánh dấu **Đã xác nhận địa chỉ với khách**, bấm **Điền vào OH**.
6. Kiểm tra trên OH, bấm **Lưu hồ sơ**. RPA chỉ báo hoàn tất sau khi tải lại xác minh. PID và gói khám lần 1 được giữ nguyên.

Để thử riêng khách đã có hồ sơ cũ, chọn chế độ **2. Khách đến — tiếp đón** rồi dùng luồng bên dưới.

## Thử riêng lần 2 với hồ sơ có sẵn

1. Chọn chế độ **2. Khách đến — tiếp đón**, bấm **Đổi đoàn / chọn danh sách** để mở phần thiết lập. Chọn công ty `Công ty Demo A`, đợt `DEMO-2026`, file `demo/company_A.xlsx`, sheet `DS_bung_DEMO`, tiêu đề hàng `2`; bấm **Nạp danh sách**. Phần thiết lập tự ẩn sau khi nạp; chỉ còn trạng thái đoàn và các thao tác tiếp đón.
2. Trên OH nhập `DEMO0001`, Enter.
3. Trên RPA bấm **CCCD demo theo PID**, sau đó **Đối chiếu**. Nút demo lấy chuỗi giả, không đọc CCCD thật.
4. Đọc bản đối chiếu và nguồn địa chỉ. Nhập địa chỉ giả hiện tại, ví dụ `Thành phố Demo` / `Phường Mới` / `12 Đường Demo`.
5. Đánh dấu **Đã xác nhận địa chỉ với khách**, bấm **Điền vào OH**. Quan sát OH khóa chuyển hồ sơ, điền và mở hộp địa chỉ.
6. Sau thông báo **CHỜ LƯU**, kiểm tra OH rồi bấm **Lưu hồ sơ** trên OH.
7. Công cụ tải lại hồ sơ để xác minh dữ liệu đã lưu, sau đó báo **HOÀN TẤT**. Bấm **Lượt mới** để tiếp tục.

Thử người trùng tên: `DEMO0001` và `DEMO0010` có cùng tên nhưng CCCD/ngày sinh khác nhau. Muốn dùng công ty B, chọn `company_B.xlsx`, gán `Công ty Demo B` và chọn lại sheet. Các hồ sơ B là `DEMO0011`–`DEMO0020`.

## Quy tắc Excel và CCCD

- Cột `National ID` bắt buộc có chuỗi 12 chữ số ở **mọi dòng người khám**. Nếu thiếu hoặc sai, toàn bộ danh sách bị chặn nạp và báo số dòng. Không tìm thay thế bằng tên.
- Lần 1 khách mới được trống PID hoặc chưa có cột PID. Lần 2 phải có PID dạng chuỗi. Không tự bù số 0 đã mất trong Excel.
- Lần 1 yêu cầu `Package Code` và `Visit Date Time`; ngày/giờ khám được giữ khi nhập và xuất. Các cột bổ sung dùng tên mẫu tham chiếu. Chỉ tạo mới cho khách chưa có PID; CCCD đã có trên OH thì chặn, không tự tạo/gán thêm gói cho hồ sơ cũ.
- File tham chiếu có tiêu đề hàng 2; dữ liệu từ hàng 3. Chọn rõ sheet, không chọn `KiemTra_*`.
- `.xlsx` và `.xlsm` đều được đọc, không chạy macro và không ghi vào file nguồn.
- Quy ước tên: Patient Last Name = họ, Patient Middle Name = tên đệm, Patient Given Name = tên. Cần kiểm tra quy ước của file thực tế trước khi dùng.
- Công ty/đợt khám được gán cho danh sách đang nạp. File có nhiều công ty cần tách danh sách trước khi demo.
- Cấu hình cột tùy chỉnh qua file JSON: xem `config/column-mapping.json` và nút **Ánh xạ cột**.

Chế độ `demo` nhận JSON có `format: VINMEC-DEMO-1`; mẫu trong `demo/scans.json` và `demo/cards.html`. Chế độ `qr-pipe` nhận đúng 7 phần phân cách `|`: CCCD, mã cũ, họ tên, ngày sinh, giới tính, địa chỉ, ngày cấp. Đây là adapter cần xác minh với đầu đọc thực tế, chưa được nghiệm thu thiết bị. Nhập/đọc chuỗi vào ô CCCD rồi Enter.

CCCD trên OH trống được bổ sung sau đối chiếu; CCCD đã có khác số đang quét thì chặn. Địa chỉ nguồn chỉ để tham khảo; không tự chuyển đổi địa chỉ sau sáp nhập.

## Lỗi và phục hồi

- **Sai PID:** mở đúng PID trên OH, đối chiếu lại.
- **OH có thay đổi chưa lưu:** lưu hoặc hủy trên OH trước khi đối chiếu.
- **Dữ liệu bị sửa sau xem trước:** đối chiếu lại, xác nhận địa chỉ lại.
- **Dừng/lỗi giữa chừng:** không tự lưu; kiểm tra OH và bấm Hủy thay đổi nếu muốn bỏ phần đã điền. Dừng có hiệu lực trước thao tác tiếp theo; thao tác đang chờ có thể mất tối đa timeout 5 giây.
- **Không build được OH:** kiểm tra .NET Framework và `C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe`.
- **Không điều khiển được OH:** chạy OH và RPA trong cùng phiên desktop và cùng mức quyền. Đóng phiên demo cũ rồi khởi động lại; RPA kết nối theo PID tiến trình của OH vừa mở.
- **Mất kết nối/đóng OH:** dừng lượt hiện tại, đóng RPA và khởi động lại bộ demo.

## Reset dữ liệu giả

Đóng demo, sau đó chạy:

```powershell
python .\scripts\reset.py
```

Reset tạo lại workbook/seed trong `demo/`, khôi phục hồ sơ trong `runtime/oh.sqlite3`, đặt lại bộ đếm PID demo và xóa các file bàn giao do công cụ sinh có tên mã tự động trong `runtime/prepared/`. Không thay đổi `Data/DS_bung_tool.xlsm` hoặc ảnh `OH_UI/OH.jpg`. Nhật ký kỹ thuật chỉ lưu sự kiện/thời gian; Excel bàn giao là dữ liệu nghiệp vụ riêng chứa CCCD và PID.

## Kiểm thử

```powershell
# Nếu dùng .deps trên máy hiện tại:
$env:PYTHONPATH = '.deps;.'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest tests -q

# Nếu dùng môi trường ảo trên máy mới:
.\.venv\Scripts\python.exe -m pytest tests -q
```

Kiểm thử hiện tại dùng SQLite tạm, OH WinForms thật và Windows UI Automation; fixture trong `demo/` được tạo lại. Kết quả đo ở `docs/native-timing.json`, ảnh ở `docs/native-evidence/`. Chạy kiểm thử khi đã đóng demo để tránh tạo lại Excel đang dùng; giữ phiên desktop đăng nhập và không khóa màn hình trong lúc kiểm thử.

Có thể dùng `scripts/test.ps1` để lưu JUnit mới nhất vào `docs/patient-browser-test-results.xml`. Ảnh danh sách ở `docs/patient-browser-evidence/`; ảnh menu trái ở `docs/sidebar-evidence/`; ảnh Patient Profile ở `docs/reference-evidence/`; ảnh hai giai đoạn ở `docs/two-stage-evidence/`. Bộ kiểm thử mở OH và RPA trong thời gian ngắn; chỉ chụp cửa sổ demo. `pytest.ini` loại các kiểm thử web cũ khỏi lượt chạy mặc định. Mã/bằng chứng web cũ được giữ để tham chiếu, không thuộc đường khởi động hiện tại.
