# Đối chiếu OH Desktop với ảnh tham chiếu

Nguồn thiết kế: `OH_UI/OH.jpg` cho Patient Profile / Demographics và ảnh bổ sung `OH_UI/OH_2.jpg` cho menu trái. Chưa có ảnh cho form tạo PID, hộp địa chỉ hay màn hình bung gói.

Mục tiêu: thay form hai cột của prototype bằng bố cục nhãn trái/ô phải, nền trắng/xám nhạt, mật độ trường và thứ tự nhóm giống ảnh. Giữ control Windows native và các AutomationId dùng bởi RPA.

Menu trái mới thay thanh biểu tượng tạm: đầu menu Patient Profile, nhóm REGISTRATION/CASHIER/ADMISSION/DISCHARGE/TRANSFER/APPOINTMENTS/VISIT/MAINTENANCE và các mục con đọc được từ ảnh. Có dấu sao ở Visit Manager/Patient Billing, nhóm mở/thu gọn, thanh cuộn riêng. Patient Profile là mục đang chọn. Các mục ngoài nghiệp vụ demo không điều hướng sang chức năng chưa triển khai; thanh trạng thái giải thích phạm vi khi chọn.

Thanh trái mở ở cửa sổ rộng, tự thu ở cửa sổ nhỏ để phần nội dung không che nút lưu. Bản chạy hiện tại là OHDesktop-v4.exe. Ảnh của phần bên trái ở `sidebar-evidence/`.

## Kiểm chứng sau bổ sung ảnh menu trái

**55/55 ca đạt**, JUnit tại `sidebar-test-results.xml`; có thêm kiểm thử thu/mở nhóm, thu toàn menu, cuộn riêng sidebar, cửa sổ nhỏ và giữ nguyên PID/phiên bản khi bấm mục tham chiếu. Kiểm thử tạo PID/bung gói rồi tiếp đón vẫn đạt. Trạng thái visibility đọc hiện tại để không dùng dữ liệu UIA đã cache trước khi thu/mở menu.

Ảnh đã xem: `sidebar-evidence/oh-sidebar.png` (menu trên), `oh-sidebar-bottom.png` (các nhóm dưới), `oh-sidebar-compact.png` (menu thu gọn). Nhóm và nhãn được lấy từ phần nhìn thấy trong ảnh mới, không suy diễn thêm màn hình nghiệp vụ ngoài Patient Profile.

Các điểm bám ảnh: Patient Profile; ba tab Demographics/Circle of Care/Financial; Hospital Number; hai hàng tên với Title và ba thành phần tên; Name Status/Other Names; Sex; DOB với độ chính xác và Age; Official Documents/Banner Indicators; Phone/Email/Addresses; Nationality/Primary Language/Ethnicity/Occupation; Employment Details; thanh Notes/Documents/Functions cuối màn hình.

Phần bổ sung cần cho demo: thanh quét PID/tạo mới phía trên; CCCD trực tiếp trong Official Documents; ba ô địa chỉ hiện tại dưới dòng Addresses; thao tác lưu/hủy/khóa và trạng thái; gói khám nằm phía dưới Employment Details. Các mục tham chiếu ngoài luồng nghiệp vụ chỉ là ngữ cảnh trình diễn, chưa mở rộng dữ liệu lưu trữ.

Kiểm tra cửa sổ native ở kích thước mặc định và kích thước tối thiểu; không che thanh thao tác; cho phép cuộn thân form; xem ảnh đã render và chạy lại hai lần RPA. Kiểm tra thêm các thành phần tên hiển thị tương ứng tên đầy đủ và nhãn theo ảnh. Các form không có ảnh nguồn vẫn dùng thiết kế mô phỏng đã có.

## Kết quả 18/11/2026

Đã thay bằng layout native tại `oh_desktop/OHDesktop.Reference.cs`, biên dịch cùng logic hiện có vào `runtime/OHDesktop-v3.exe`. Các AutomationId cho PID, CCCD, địa chỉ, gói và nút nghiệp vụ được giữ lại. RPA không cần chuyển sang tọa độ chuột để thích ứng bố cục mới.

**53/53 ca kiểm thử đạt** trong lượt đầy đủ, JUnit ở `reference-test-results.xml`. Bao gồm các quy tắc dữ liệu, hai giai đoạn RPA, tên chia ba ô đúng với tên đầy đủ, xóa tên cũ khi tra PID không tồn tại và thao tác lưu/hủy ở cửa sổ thu gọn.

Ảnh đã render và xem trực tiếp:

- `reference-evidence/patient-profile.png`: Patient Profile ở kích thước mặc định.
- `reference-evidence/patient-profile-compact.png`: cửa sổ 1120×680, vùng thao tác vẫn hiện.
- `reference-evidence/patient-profile-personal.png`: cuộn tới Personal/Employment và gói khám.

Không sao chép màu ám/xoay phối cảnh của ảnh chụp màn hình. Chưa cam kết khớp từng pixel hoặc hành vi toàn bộ OH. Tên riêng đã che trong ảnh không được phục hồi; màn hình chỉ hiển thị hồ sơ giả. Việc chia thành phần tên dùng quy ước demo, chưa dùng ảnh làm căn cứ xác định mapping tên trên OH thật.

Đã tách bước chụp ảnh cửa sổ Tkinter khỏi kiểm thử trạng thái vì PrintWindow đồng bộ khi Tk đang được bơm bằng root.update có thể treo. Chụp ảnh OH WinForms vẫn được thực hiện trong bộ kiểm thử; kiểm thử trạng thái/cuộn của RPA vẫn chạy đầy đủ.
