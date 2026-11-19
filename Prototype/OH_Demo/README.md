# OH Demo — giao diện Patient Profile và kịch bản tự động điền

`OHDemo.exe` là một file duy nhất, chạy trên Windows 10/11 có .NET Framework 4.x (có sẵn). Không cần Python, RPA hay cài thêm. Toàn bộ dữ liệu là dữ liệu giả (PID `DEMO0001`–`DEMO0005`).

## Dùng

- Nhấp đúp `OHDemo.exe`. Giao diện không còn thanh/nút demo.
- Nhập PID hoặc tên (có thể không dấu) vào ô "Tìm hồ sơ" rồi **Enter** để tìm (không có nút Tìm).
- Kịch bản tự động vẫn còn, chạy bằng tham số dòng lệnh: `OHDemo.exe --demo=pid` (nhập PID → xem → Edit → điền → Save), `--demo=name` (tìm theo tên, chọn đúng người), `--demo=new` (bệnh nhân mới). Nhấn **Esc** để dừng.

## Tìm theo tên

- Nhập đúng PID → mở thẳng hồ sơ. Nhập tên (không dấu cũng được) → hiện trang **Search Results** liệt kê mọi người khớp tên, gồm PID, tên, giới tính, ngày sinh, tuổi, SĐT, địa chỉ. Người trùng tên được phân biệt bằng năm sinh/thông tin. Chọn dòng rồi bấm **Open** hoặc nhấp đúp.
- Dữ liệu mẫu: `DEMO0001`, `DEMO0004`, `DEMO0005` cùng tên "Nguyễn Văn Mẫu" nhưng khác năm sinh. Chạy thử bằng `--demo=name`.

## Bệnh nhân chưa có PID (chưa có trong danh sách gói khám)

- Tìm không thấy thì **để trống, không hiện thông báo**. Bấm **+ New Patient** ở thanh tìm kiếm để sang giao diện tạo mới (một trang riêng, ẩn phần tiêu đề hồ sơ).
- Khung **New Patient** nằm ở góc trên trang (tab nhỏ + khung viền, hàng nhãn căn phải/ô nhập, theo ảnh mẫu) chỉ nhập: tên, năm sinh, số điện thoại. Có kiểm tra trùng (cùng tên và SĐT).
- **Save** → cấp PID mới (`NEW000001`, ...) và mở ngay trang Edit với các trường còn lại **để trống**. Bổ sung rồi Save lần nữa; các trường có dấu * (giới tính, ngày sinh, quốc tịch, ngôn ngữ, dân tộc, nghề nghiệp, điện thoại) phải đủ mới lưu được.
- Chạy `OHDemo.exe --demo=new` để xem toàn bộ luồng tự chạy.
- Khung tạo mới dựng theo ảnh một màn hình tìm kiếm khác (OPD Activity) và mô tả của người dùng. Các ô và thứ tự là phỏng đoán, chưa đối chiếu với màn hình tạo mới thật của OH.

## Giao diện

- Trang 1 (xem): Identification, Contact, Personal, Employment theo ảnh tham chiếu; nút Edit ở cuối.
- Trang 2 (Edit): Name (Local/Other), Name Status, Sex, Date of Birth (nhập `dd/mm/yyyy`), Phone, Email, Addresses (bấm + thì các ô Tỉnh/Thành phố, Phường/Xã, Số nhà/Đường mở rộng ngay bên dưới trong cùng trang, bấm Add để thêm; không có cửa sổ riêng), Nationality, Language, Ethnicity, Occupation.
- Điều chỉnh so với ảnh: ô tìm PID/tên và nút Save do bên mô phỏng bổ sung; vị trí nút Save của OH thật chưa được xác nhận. Menu trái và các tab khác chỉ là hình thức.
- Các control có `Name`/`AccessibleName` cố định (ví dụ `pid-search`, `edit-toggle`, `edit-phone`) để công cụ UI Automation điều khiển được.

## Build lại từ mã nguồn

```powershell
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /codepage:65001 /target:winexe /out:OHDemo.exe `
  /reference:System.Windows.Forms.dll /reference:System.Drawing.dll OHDemo.cs
```

Hoặc chạy `build.cmd` (đường dẫn thư mục không được bắt đầu bằng dấu cách khi chạy từ cmd).
