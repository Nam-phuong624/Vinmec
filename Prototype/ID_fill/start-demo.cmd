@echo off
chcp 65001 >nul
echo Mở trình duyệt tại http://127.0.0.1:8765
echo Giữ cửa sổ này khi dùng demo. Nhấn Ctrl+C để dừng.
echo Điện thoại và máy tính cần cùng Wi-Fi. Chỉ dùng dữ liệu giả trên mạng riêng tin cậy.
python -B "%~dp0server.py"
pause
