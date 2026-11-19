# RPA điền danh sách bung gói vào OHDemo

`dist/RPA_OHDemo.exe` (một file, ~34 MB, không cần cài Python) đọc danh sách bung gói của **ngày hôm nay** và tự điền vào `OHDemo.exe` (OH mô phỏng, xem `../OH_Demo`). Toàn bộ dữ liệu là dữ liệu giả.

## Chạy

1. Mở `OHDemo.exe`.
2. Đặt file Excel vào `ds bung\DD-MM-YYYY\` (ngày trùng ngày hệ thống). Chương trình tìm thư mục `ds bung` ở cạnh file exe hoặc các thư mục cha gần nhất (có thể đặt biến `DS_BUNG_DIR`).
3. Mở `RPA_OHDemo.exe`. RPA chờ OHDemo, nạp file mới nhất trong thư mục ngày rồi tự chạy nền (có nút Chạy RPA / Dừng / Nạp lại danh sách).

Từ mã nguồn: `python .\scripts\start.py` (cần `pip install -r requirements.txt`).

## Quy tắc xử lý mỗi dòng

1. Tìm theo họ tên (`Patient Last Name` = họ, `Middle` = đệm, `Given` = tên).
2. Chỉ lấy kết quả **trùng đúng họ tên (không phân biệt dấu/hoa thường)**; trong đó:
   - **Trùng năm sinh (1 hồ sơ):** mở hồ sơ, so với Excel và **cập nhật các trường khác** (Title, họ/đệm/tên, giới tính, ngày sinh đầy đủ, điện thoại, quốc tịch, địa chỉ). Không có gì khác thì báo "Không đổi".
   - **Không có hồ sơ nào trùng năm sinh:** tạo bệnh nhân mới (chỉ nhập tên, năm sinh, SĐT) → OH cấp PID → bổ sung các trường còn lại ở trang Edit → Save.
   - **Nhiều hồ sơ cùng tên và năm sinh**, hoặc **trùng tên + SĐT nhưng khác năm sinh:** không đoán, ghi lỗi để xử lý tay.
3. Địa chỉ Excel tách theo dấu phẩy (cấp cuối = tỉnh/thành, áp chót = phường/xã). Địa chỉ mới **được thêm** nếu chưa có, không xóa địa chỉ cũ. Địa chỉ chỉ có 1 phần thì "Cần điền tay".
4. Trường Excel trống thì không ghi đè dữ liệu có sẵn trong OH. Quốc tịch/ngôn ngữ/dân tộc/nghề nghiệp chỉ điền khi Excel có (hiện chỉ Nationality).

## Kết quả

- Cột "Trạng thái RPA" cho từng dòng: `Đã tạo` / `Đã cập nhật` / `Không đổi` / `Cần điền tay` / `Lỗi`.
- Dòng `Lỗi` và `Cần điền tay` được ghi vào `ds lỗi.xlsx` trong thư mục ngày (số dòng gốc, lý do, đủ các cột) để điền thủ công. Một dòng lỗi không làm RPA dừng.
- Chạy lại cùng file là an toàn: dòng đã có sẽ báo "Không đổi", không tạo trùng.
- Nhật ký kỹ thuật ở `runtime/audit.jsonl` (chỉ sự kiện, số dòng, PID; không ghi dữ liệu cá nhân).

## An toàn khi có thao tác khác hoặc bị ngắt giữa chừng

- Trước khi ghi, RPA kiểm tra lại: kết quả tìm kiếm đúng của dòng này, trang đang mở đúng hồ sơ (PID, họ tên, năm sinh), form đúng dữ liệu Excel. Sau khi lưu, RPA **đọc lại hồ sơ** và so với Excel. Có gì lệch thì không báo thành công mà báo "Lỗi" nêu rõ lý do (thêm khoảng 1,5 giây mỗi dòng).
- Nếu người dùng thao tác trên OH trong lúc RPA chạy (tìm hồ sơ khác, sửa ô, bấm nút), dòng đang chạy báo lỗi thay vì ghi nhầm; hồ sơ mới đã tạo dở được nêu trong thông báo (PID, hoặc "có thể đã tạo hồ sơ mới", tìm theo họ tên). Chạy lại sẽ hoàn tất, không tạo trùng. Nên tránh thao tác trên OH khi RPA đang chạy.
- OH bị đóng giữa chừng: báo "Mất kết nối: cửa sổ OH đã bị đóng", không báo thành công.
- Nhật ký tiến độ `runtime/journal_<tên file>.jsonl` ghi ngay khi bắt đầu/kết thúc từng dòng; mở lại RPA sẽ đánh dấu dòng bị ngắt giữa chừng và chạy lại. `ds lỗi.xlsx` được ghi ngay sau mỗi dòng lỗi/cần điền tay, không đợi hết lượt chạy.
- Giới hạn: nếu chính người dùng sửa họ tên của hồ sơ rồi RPA lưu, RPA báo lỗi nêu PID nhưng không tự sửa lại; người duyệt sửa tay.
- Kiểm thử: xem `KIEM_THU_RPA.md` (nhóm I, J) và `bieu_do/`.

## Kiểm tra và hoàn tác sau khi RPA đã ghi

OH là phần mềm đóng nên không có "hoàn tác" bên trong OH; RPA tự giữ vết và có công cụ kiểm tra, khôi phục. Các file nằm trong thư mục ngày của `ds bung` (đã `.gitignore`, chứa dữ liệu cá nhân thật, không đưa vào repo, nên hạn chế quyền truy cập):

- `nhat_ky_thay_doi.jsonl`: với mỗi dòng đã xử lý xong, ghi PID, hành động (tạo / cập nhật / giữ), **giá trị trước và sau** của hồ sơ, và dữ liệu Excel mong đợi. Ghi ngay sau mỗi dòng.
- `bao_cao_thay_doi.xlsx`: bản đọc được cho người duyệt (mỗi trường đã đổi một dòng, cũ → mới, và các mục cần điền tay).
- Nút **Đối soát (chỉ đọc)**: mở lại từng hồ sơ đã xử lý, so với Excel, báo Khớp / LỆCH / TRÙNG / KHÔNG TÌM THẤY (`bao_cao_doi_soat.xlsx`). Không ghi gì vào OH. Nên chạy lại vào ngày hôm sau để bắt cả thay đổi do người khác.
- Nút **Khôi phục lượt chạy…**: trả các hồ sơ đã **cập nhật** về giá trị trước. Hồ sơ đã bị ai sửa tiếp sau lượt chạy thì bỏ qua (không ghi đè). Địa chỉ RPA đã thêm không xóa được bằng giao diện: báo để xóa tay. Hồ sơ **tạo mới** không xóa được: chỉ liệt kê (`bao_cao_khoi_phuc.xlsx`) để người có quyền vô hiệu hoặc gộp theo quy trình của OH.
- Hạn chế: khôi phục chỉ đưa về đúng trạng thái RPA đã đọc trước khi ghi; nếu hồ sơ OH thật có trường RPA không đọc (ví dụ lịch sử, gói khám) thì không khôi phục được các trường đó.

## Chạy nền

RPA không gõ phím, không click chuột, không chiếm tiêu điểm: chỉ gửi giá trị/nút bấm thẳng vào control của OHDemo qua UI Automation (mỗi dòng ~2–3 giây).

## Build lại file exe

```powershell
# Python của conda cần thêm thư mục DLL vào PATH để PyInstaller gom đủ ffi/tcl/tk
$env:PATH = "$env:CONDA_PREFIX\Library\bin;$env:CONDA_PREFIX;" + $env:PATH
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name RPA_OHDemo --paths . --distpath dist `
  --collect-submodules pywinauto --collect-submodules comtypes --hidden-import win32timezone scripts\start.py
```

## Ghi chú

- OH Desktop WinForms cũ (`oh_desktop/`, `demo/`, `scripts/reset.py`) không còn được RPA dùng; bản sao lưu đầy đủ của luồng cũ ở `Prototype_RPA_backup_18-11-2026`.
- OHDemo không có ô CCCD nên việc nhận diện người dựa vào họ tên + năm sinh + số điện thoại; yếu hơn CCCD.
