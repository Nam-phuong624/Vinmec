# In phiếu khám sức khỏe theo CCCD

Quét CCCD → đối chiếu CCCD với danh sách bung của **ngày hôm nay** (`ds bung\DD-MM-YYYY\*.xlsx`) → chọn đúng 1 trong 4 form → điền trang 1 và trang 4 → (tùy chọn) in.

## Thành phần

- `Mau/` — 4 form .docx: `Nam_CoBan`, `Nam_TieuChuan`, `Nu_CoBan`, `Nu_TieuChuan` (6 trang mỗi file, dựng từ 6 ảnh trong `in/`).
- `dist/In_Phieu.exe` — công cụ quét/điền/in (một file, đã gói sẵn 4 form; nếu có thư mục `Mau` cạnh exe thì dùng thư mục đó).
- `build_forms.py` — tạo lại 4 form (`python build_forms.py`). `fill.py`, `in_phieu.py` — mã nguồn công cụ.

## Thứ tự trang

1 Danh mục gói khám (điền **PID**) · 2 Phiếu sàng lọc bệnh truyền nhiễm · 3 Bìa · 4 Giấy khám sức khỏe — thông tin hành chính (điền) · 5 Giấy KSK: khám thể lực, lâm sàng (ảnh 6) · 6 Giấy KSK: cận lâm sàng, kết luận (ảnh 5).
Trang 5 và 6 theo nội dung (ảnh 6 đứng trước ảnh 5).

## Khác nhau giữa 4 form (chỉ trang 1)

- **Tiêu chuẩn** = đúng như ảnh. **Cơ bản** = bỏ "Siêu âm tuyến giáp" và "Điện tim thường" (STT được đánh lại).
- **Nam** = bỏ các dịch vụ chỉ dành cho nữ: siêu âm tử cung buồng trứng, siêu âm tuyến vú hai bên, KSK phụ khoa/khám vú, HPV genotype. Chưa thêm dịch vụ riêng cho nam vì ảnh mẫu không có.
- Tên gói: chỉ "2026 GÓI TIÊU CHUẨN NỮ <40" có trong ảnh; 3 tên còn lại đặt theo cùng quy ước (sửa ở `PACKAGE_TITLE` trong `build_forms.py`).
- Trang 2–6 giống nhau ở cả 4 form.

## Các trường được điền

Trang 1: PID (cột `Patient ID`).
Trang 2 (phiếu sàng lọc): họ tên (IN HOA), ngày sinh, giới tính (☒), số điện thoại, địa chỉ (nguyên văn từ ds bung), và **tên người khai** ở cuối trang (viết hoa chữ cái đầu mỗi từ, cách chữ "Người khai" 30px).
Trang 4: Họ và tên (IN HOA), giới tính (☒), ngày sinh, tuổi, số CCCD, ngày cấp (chỉ khi quét QR 7 phần, lấy "ngày cấp"), tỉnh/thành, phường/xã, số nhà (tách từ `Patient Address` theo dấu phẩy: cấp cuối = tỉnh/thành, áp chót = phường/xã), nơi cấp (mặc định "Cục Cảnh sát QLHC về TTXH"), đối tượng (mặc định "Người lao động"), nơi làm việc/học tập (= tên công ty, cột `Policy Name`), lý do khám (mặc định "Khám định kỳ").
Không điền (chấm để viết tay): dân tộc, nguồn chi trả, nhóm máu, nghề nghiệp.
Các giá trị mặc định (nơi cấp, đối tượng, lý do) có thể đổi bằng file `cau_hinh.json` cạnh exe, ví dụ `{"DOI_TUONG": "Người lao động", "LY_DO": "Khám định kỳ", "NOI_CAP": ""}` (để trống = không điền).

## Cách dùng

1. Mở `In_Phieu.exe` (ds bung của ngày phải có file .xlsx; tìm thư mục `ds bung` cạnh exe hoặc các thư mục cha, hoặc đặt `DS_BUNG_DIR`).
2. Đặt con trỏ ở ô quét, quét CCCD (chuỗi QR `CCCD|CMND cũ|Họ tên|DDMMYYYY|Giới tính|Địa chỉ|Ngày cấp`) hoặc gõ 12 số CCCD, nhấn Enter.
3. Form lưu ở `ds bung\<ngày>\phieu_in\<dòng>_<tên không dấu>.docx` và **tự mở trong Word** (ô "Tự mở file Word để kiểm tra", mặc định bật). Kiểm tra thông tin rồi in bằng Ctrl+P của Word, hoặc bấm **In phiếu này**; tick **Tự in ngay** (mặc định tắt) để bỏ qua bước kiểm tra.
- **📱 Ghép điện thoại quét CCCD…** (Android, cùng cơ chế với `demo - ql vật tư`): máy tính chạy server HTTPS (chứng chỉ tự ký, cổng 8743) + HTTP localhost (cổng 8780, dùng với `adb reverse`) và hiện QR ghép đôi. Trên điện thoại mở QR/đường dẫn → Chrome báo "không an toàn" → Nâng cao → Tiếp tục → **Bật camera** → đưa mã QR mặt sau CCCD vào khung. Chuỗi QR gửi về máy tính, máy tính đối chiếu CCCD, điền form, mở Word; kết quả (họ tên, form, hoặc lỗi) hiện lại trên điện thoại. Mỗi phiên có token riêng; chuỗi QR chỉ nằm trong bộ nhớ, không ghi log. Mở sẵn hộp ghép đôi khi khởi động: `In_Phieu.exe --ghep-doi`.
  - **Thông tin điền:** họ tên, ngày sinh, giới tính, số CCCD, địa chỉ, ngày cấp lấy **từ thẻ**; số điện thoại, PID, tên công ty (nơi làm việc) và gói khám bổ sung **từ ds bung** theo CCCD. Thẻ và ds bung lệch họ tên/ngày sinh/giới tính thì vẫn tạo file nhưng không tự in.
  - Cổng 8743 phải được Windows Firewall cho phép (mạng riêng): lần đầu Windows sẽ hỏi; hoặc chạy bằng quyền Admin: `netsh advfirewall firewall add rule name="In_Phieu 8743" dir=in action=allow protocol=TCP localport=8743 profile=private`. Đổi cổng bằng biến môi trường `IN_PHIEU_HTTPS_PORT`, `IN_PHIEU_HTTP_PORT`.
- **Mô phỏng quét QR (khách mẫu)…**: chọn một khách trong ds bung → hiện thẻ có mã QR giả (đúng định dạng 7 phần, dựng từ ds bung, ngày cấp để trống) → bấm "Quét QR này" → chương trình giải mã ảnh QR rồi điền form như khi quét thật.
- **Quét từ ảnh CCCD…**: chọn ảnh chụp mặt sau CCCD có mã QR rõ nét (đọc bằng OpenCV, thử nhiều tỉ lệ).
- Gói khám chọn theo `Package Name` trong ds bung ("cơ bản" / "tiêu chuẩn"); không nhận ra thì chọn gói thủ công ở ô "Gói khám".
- CCCD không có trong ds bung → không điền. Quét QR mà họ tên/ngày sinh/giới tính khác ds bung → vẫn tạo file nhưng **không tự in**.
- In bằng Microsoft Word, máy in mặc định, toàn bộ 6 trang.
- Dòng lệnh: `In_Phieu.exe --cccd "<chuỗi quét>" [--package coban|tieuchuan] [--print]` (tạo form rồi thoát).

## Build exe

```powershell
$env:PATH = "$env:CONDA_PREFIX\Library\bin;$env:CONDA_PREFIX;" + $env:PATH
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name In_Phieu --paths ..\RPA --paths . --distpath dist `
  --add-data "<đường dẫn tuyệt đối>\Mau;Mau" --collect-submodules docx --hidden-import win32com.client --hidden-import pythoncom --hidden-import win32timezone in_phieu.py
```
