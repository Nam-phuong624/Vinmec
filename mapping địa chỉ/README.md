# Mapping địa chỉ cũ → mới (sáp nhập 2025)

## Nội dung

- `du-lieu/tat-ca.csv`: 12.216 dòng, 11.558 xã/phường/thị trấn cũ (63 tỉnh) → 3.321 xã/phường mới (34 tỉnh). Cột chính: `tinh_cu`, `huyen_cu`, `xa_cu`, `xa_moi`, `tinh_moi`, `phan`, `nghi_quyet`; cột `qua_don_vi`, `nghi_quyet_dot_truoc`, `hieu_luc_dot_truoc` cho biết đơn vị trung gian nếu xã đó đã sáp nhập ở đợt trước (2014–2025).
- `du-lieu/tinh-63-sang-34.csv`: 63 tỉnh cũ → 34 tỉnh mới.
- `tra_cuu.py`: tra cứu, ví dụ `python tra_cuu.py "Xã Châu Sơn" "Huyện Ba Vì" "Hà Nội" --thon "Thôn 3"`.

## Giới hạn

- Thôn/ấp không phải đơn vị hành chính chính thức nên không có trong dữ liệu; giữ nguyên khi đổi địa chỉ.
- `phan` = `mot_phan` / `phan_con_lai`: xã cũ bị chia cho nhiều xã mới, cần thôn/ấp đối chiếu nghị quyết để chọn đúng.
- Huyện/quận cũ bị bãi bỏ, địa chỉ mới chỉ gồm thôn/ấp, xã, tỉnh.

## Nguồn

Dorabot (dorabot.io/dia-chi/sap-nhap), chép từ nghị quyết của Ủy ban Thường vụ Quốc hội (1654–1687/NQ-UBTVQH15, 202/2025/QH15). Giấy phép CC BY 4.0. Cần đối chiếu nghị quyết gốc trước khi dùng chính thức.
