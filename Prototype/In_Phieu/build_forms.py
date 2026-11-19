"""Tạo 4 form .docx (Nam/Nữ × Cơ bản/Tiêu chuẩn) từ 6 ảnh mẫu trong thư mục `in/`.

Chạy: python build_forms.py   → ghi vào thư mục Mau/
Các trường cần điền (trang 1 và trang 4) là Word content control (w:sdt) có `tag` cố định; phần còn lại là chữ in sẵn.
Thứ tự trang: 1 Danh mục gói khám · 2 Phiếu sàng lọc · 3 Bìa · 4 Giấy KSK (thông tin hành chính) · 5 Giấy KSK (khám thể lực/lâm sàng)
· 6 Giấy KSK (cận lâm sàng/kết luận). Trang 5 và 6 ứng với ảnh 6 và ảnh 5 vì nội dung ảnh 6 đứng trước ảnh 5.
"""
from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.table import _Cell

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
FONT = 'Times New Roman'
DOTS = '.' * 36
BOX = '☐'
OUT = Path(__file__).resolve().parent / 'Mau'
ALIGN = {'left': WD_ALIGN_PARAGRAPH.LEFT, 'center': WD_ALIGN_PARAGRAPH.CENTER, 'right': WD_ALIGN_PARAGRAPH.RIGHT}

# Tên gói trên tiêu đề trang 1. Chỉ "TIÊU CHUẨN NỮ <40" có trong ảnh mẫu; 3 tên còn lại suy ra theo cùng quy ước.
PACKAGE_TITLE = {
    ('nu', 'tieuchuan'): '2026 GÓI TIÊU CHUẨN NỮ <40',
    ('nu', 'coban'): '2026 GÓI CƠ BẢN NỮ <40',
    ('nam', 'tieuchuan'): '2026 GÓI TIÊU CHUẨN NAM',
    ('nam', 'coban'): '2026 GÓI CƠ BẢN NAM',
}
FILES = {('nam', 'coban'): 'Nam_CoBan.docx', ('nam', 'tieuchuan'): 'Nam_TieuChuan.docx',
         ('nu', 'coban'): 'Nu_CoBan.docx', ('nu', 'tieuchuan'): 'Nu_TieuChuan.docx'}

# Danh mục dịch vụ (ảnh 1). Mỗi nhóm = (phòng, [(mã DV, [(dòng, đậm)], hạn chế)]).
# Hạn chế: 'nu' = chỉ dành cho nữ; 'tieuchuan' = chỉ có trong gói tiêu chuẩn (gói cơ bản bỏ siêu âm tuyến giáp và điện tim thường).
SERVICES = [
    ('Quầy lễ tân', [('Tiếp nhận', [('Bộ hồ sơ: Giấy tờ tùy thân, bung gói, ảnh', 0)], None)]),
    ('Phòng B.08', [('24.264', [('XN máu       ☐', 0), ('Nước tiểu   ☐', 0), ('Phân          ☐', 0)], None)]),
    ('Khu ăn nhẹ', [('Ăn nhẹ', [('Ăn nhẹ sau lấy máu/Thủ thuật khác ', 0), ('(nếu có)', 1)], None)]),
    ('Phòng B.10', [('GD.0001', [('Kiểm tra Mạch: ……………Huyết áp: ………………', 0), ('Chiều cao: ………………Cân Nặng: ………………', 0), ('Vòng ngực:……………Vòng bụng:………………', 0)], None)]),
    ('Phòng B.02', [('FA.05.0055', [('Chụp Xquang ngực thẳng', 0)], None)]),
    ('Phòng B.04/B.05', [
        ('FA.04.0001', [('Siêu âm ổ bụng (gan mật, tụy, lách, thận, bàng quang)', 0)], None),
        ('FA.05.0048', [('Siêu âm tuyến giáp', 0)], 'tieuchuan'),
        ('FA.04.0095', [('Siêu âm tử cung buồng trứng qua đường bụng [Siêu âm phụ khoa thường quy]', 0)], 'nu'),
        ('FA.04.0027', [('Siêu âm tuyến vú hai bên', 0)], 'nu')]),
    ('Phòng B.09', [('FE.0027', [('Điện tim thường', 0)], 'tieuchuan')]),
    ('Phòng C.03', [('GD.0008', [('KSK_Khám da liễu', 0)], None)]),
    ('Phòng C.04', [('GD.0009', [('KSK_Khám ngoại khoa', 0)], None)]),
    ('Phòng C.05', [
        ('GD.0005', [('KSK_Khám phụ khoa, khám vú', 0)], 'nu'),
        ('25.5137', [('HPV genotype real-time PCR hệ thống tự động', 0)], 'nu')]),
    ('Phòng C.06', [('GD.0002', [('KSK_Khám kiểm tra răng miệng', 0)], None)]),
    ('Phòng C.07', [('E17.0132', [('Khám tai mũi họng với nội soi (có hẹn/ không hẹn)', 0)], None)]),
    ('Phòng C.08', [
        ('24.119', [('KSK_Kiểm tra thị lực (Điều dưỡng)', 0), ('Không kính MP:………………MT:………………', 0), ('Có kính MP:………………MT:………………', 0), ('Kính lỗ MP:………………MT:………………', 0)], None),
        ('GD.0010', [('Khám mắt', 0)], None)]),
    ('Phòng C.01/C.02', [('Kết luận', [('Bác sĩ Nội tổng quát', 0)], None)]),
    ('Quầy lễ tân', [('', [('Lễ tân xác nhận hoàn thành gói.', 0), ('Khách hàng trả hồ sơ tại quầy lễ tân sau khi hoàn thành khám', 1)], None)]),
    ('Phòng A.09', [('', [('Lưu hồ sơ: hành chính', 0)], None)]),
    ('', [('', [('Các dịch vụ khác do bác sỹ chỉ định (nếu có):', 0)], None)]),
]

USED = set()


# ---------- tiện ích ----------
def set_font(run, size, bold=False, italic=False):
    run.font.name = FONT
    run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), FONT)
    run.font.size = Pt(size)
    run.bold = bold or None
    run.italic = italic or None


def add_field(p, tag, size, placeholder=None, bold=False):
    if placeholder is None:
        placeholder = BOX if tag.endswith('_BOX') else ('.' * 16 if tag == 'PID' else DOTS)
    b = '<w:b/>' if bold else ''
    xml = (f'<w:sdt xmlns:w="{W}"><w:sdtPr><w:alias w:val="{tag}"/><w:tag w:val="{tag}"/><w:showingPlcHdr/><w:text/></w:sdtPr>'
           f'<w:sdtContent><w:r><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:eastAsia="{FONT}" w:cs="{FONT}"/>{b}'
           f'<w:sz w:val="{int(size * 2)}"/></w:rPr><w:t xml:space="preserve">{placeholder}</w:t></w:r></w:sdtContent></w:sdt>')
    p._p.append(parse_xml(xml))


def new_par(container):
    if isinstance(container, _Cell) and len(container.paragraphs) == 1:
        first = container.paragraphs[0]
        if not first.runs and first._p.find(qn('w:sdt')) is None:   # ô còn trống → dùng luôn đoạn có sẵn
            return first
    return container.add_paragraph()


TEXT_WIDTH = [17.0]   # chiều rộng vùng chữ của section hiện tại (cm), cập nhật trong new_section


def par(container, parts='', size=11, align='left', before=0, after=0, left=0.0, first=0.0, keep=False, leader=None):
    """Thêm đoạn văn. Ký tự '\\t' trong chữ sẽ tạo đường chấm tới lề phải (hoặc tới `leader` cm)."""
    p = new_par(container)
    f = p.paragraph_format
    f.space_before, f.space_after, f.line_spacing = Pt(before), Pt(after), 1.0
    if left:
        f.left_indent = Cm(left)
    if first:
        f.first_line_indent = Cm(first)
    f.keep_with_next = keep or None
    p.alignment = ALIGN[align]
    if isinstance(parts, (str, tuple)):
        parts = [parts]
    texts = [x if isinstance(x, str) else x[1] for x in parts if isinstance(x, str) or x[0] != 'F']
    if any('\t' in x for x in texts):
        if leader is None:
            leader = (container.width.cm - 0.45) if isinstance(container, _Cell) and container.width else TEXT_WIDTH[0]
        f.tab_stops.add_tab_stop(Cm(leader), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    for part in parts:
        if isinstance(part, str):
            set_font(p.add_run(part.replace('…', '...')), size)
        elif part[0] == 'F':
            add_field(p, part[1], size, placeholder=part[3] if len(part) > 3 else None, bold=len(part) > 2 and part[2])
        else:   # ('b'|'i'|'bi', text)
            set_font(p.add_run(part[1].replace('…', '...')), size, 'b' in part[0], 'i' in part[0])
    return p


def set_widths(table, widths):
    table.autofit = False
    for row in table.rows:
        for cell, w in zip(row.cells, widths):
            cell.width = Cm(w)


def grid(doc, rows, cols, widths, borders=True):
    t = doc.add_table(rows=rows, cols=cols)
    if borders:
        t.style = 'Table Grid'
    set_widths(t, widths)
    for row in t.rows:
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    return t


def shade(cell, color='D9D9D9'):
    cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd xmlns:w="{W}" w:val="clear" w:color="auto" w:fill="{color}"/>'))


def valign(cell, mode='center'):
    cell.vertical_alignment = {'center': WD_CELL_VERTICAL_ALIGNMENT.CENTER, 'top': WD_CELL_VERTICAL_ALIGNMENT.TOP}[mode]


def new_section(doc, left=1.5, right=1.5, top=1.2, bottom=1.2, first=False):
    s = doc.sections[0] if first else doc.add_section(WD_SECTION.NEW_PAGE)
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(left), Cm(right), Cm(top), Cm(bottom)
    TEXT_WIDTH[0] = 21.0 - left - right
    for border in s._sectPr.findall(qn('w:pgBorders')):
        s._sectPr.remove(border)
    return s


def logo(cell, size=16):
    par(cell, ('b', 'VINMEC'), size=size, align='center')
    par(cell, 'INTERNATIONAL HOSPITAL', size=6.5, align='center')


def check_line(container, items, size=11, **kw):
    return par(container, ['   '.join(f'{BOX} {x}' for x in items)], size=size, **kw)


# ---------- trang 1: danh mục gói khám ----------
def page1(doc, sex, package):
    new_section(doc, left=1.0, right=1.0, top=0.8, bottom=0.6, first=True)
    head = grid(doc, 1, 2, [3.6, 15.4], borders=False)
    logo(head.cell(0, 0))
    par(head.cell(0, 0), ['PID: ', ('F', 'PID', True)], size=9.5, align='left', before=4)
    c = head.cell(0, 1)
    par(c, ('b', 'DANH MỤC GÓI KHÁM SỨC KHỎE P&L_VINFAST'), size=13, align='center')
    par(c, ('b', 'TÊN GÓI KHÁM: ' + PACKAGE_TITLE[(sex, package)]), size=13, align='center', after=2)
    par(c, ('i', 'Quý khách vui lòng đưa phiếu này để các nhân viên y tế đánh dấu √ vào các ô bên dưới trước mỗi dịch vụ khi hoàn thành.'), size=9, align='center')
    par(c, ('i', 'Thứ tự các bước có thể thay đổi, các vị trí đánh giá vui lòng ký xác nhận'), size=9, align='center')
    for label in ('Ngày khám:', 'Ngày hoàn thiện:', 'Ngày tổng kết:'):
        par(doc, [f'{label} ………/……../………..    (Ký tên:……………………………)'], size=9.5, before=1)
    widths = [1.1, 2.5, 2.3, 7.2, 1.4, 2.3, 2.2]
    entries = []   # (phòng, [(mã, dòng)])
    for room, items in SERVICES:
        keep = [(code, lines) for code, lines, only in items
                if not (only == 'nu' and sex != 'nu') and not (only == 'tieuchuan' and package != 'tieuchuan')]
        if keep:
            entries.append((room, keep))
    total = sum(len(k) for _, k in entries)
    t = grid(doc, total + 1, 7, widths)
    for i, h in enumerate(['STT', 'PHÒNG THỰC HIỆN', 'MÃ DV', 'TÊN DỊCH VỤ', 'THỰC HIỆN', 'NGƯỜI THỰC HIỆN', 'GHI CHÚ']):
        cell = t.cell(0, i)
        shade(cell)
        valign(cell)
        par(cell, ('b', h), size=8.5, align='center')
    row, number = 1, 1
    for room, keep in entries:
        start = row
        for code, lines in keep:
            r = t.rows[row].cells
            valign(r[0]); valign(r[2]); valign(r[3]); valign(r[4])
            par(r[0], str(number), size=9.5, align='center')
            par(r[2], code, size=9.5)
            for text, bold in lines:
                par(r[3], ('b' if bold else '', text) if bold else text, size=9.5)
            par(r[4], BOX, size=9.5, align='center')
            row += 1
            number += 1
        cell = t.cell(start, 1)
        if row - 1 > start:
            cell = cell.merge(t.cell(row - 1, 1))
        valign(cell)
        par(cell, ('b', room), size=9.5)
    par(doc, ('b', 'Trả 01 số khám sức khỏe định kỳ'), size=9.5, align='center', before=4)


# ---------- trang 2: phiếu sàng lọc bệnh truyền nhiễm ----------
def page2(doc):
    new_section(doc, left=1.6, right=1.6, top=1.0, bottom=1.0)
    head = grid(doc, 1, 3, [5.0, 8.4, 3.8], borders=False)
    logo(head.cell(0, 0), 20)
    par(head.cell(0, 1), ('b', 'PHIẾU SÀNG LỌC'), size=14, align='center', before=6)
    par(head.cell(0, 1), ('b', 'BỆNH TRUYỀN NHIỄM'), size=14, align='center')
    box = head.cell(0, 2)
    box.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    box._tc.get_or_add_tcPr().append(parse_xml(
        f'<w:tcBorders xmlns:w="{W}">' + ''.join(f'<w:{s} w:val="single" w:sz="8" w:color="000000"/>' for s in ('top', 'left', 'bottom', 'right')) + '</w:tcBorders>'))
    par(box, ('b', 'PID'), size=11, align='center', before=10, after=14)
    par(doc, [('b', 'Họ tên:'), ' ', ('F', 'P2_HO_TEN', True, '.' * 52), '   ', ('b', 'Ngày tháng năm sinh:'), ' ', ('F', 'P2_NGAY_SINH', True, '....../....../.........')], size=10.5, before=6)
    par(doc, [('b', 'Giới:'), '   ', ('F', 'P2_NAM_BOX'), ' Nam      ', ('F', 'P2_NU_BOX'), ' Nữ.      ', ('b', 'Số điện thoại liên hệ/ Phone number:'), ' ', ('F', 'P2_SDT', True, '.' * 40)], size=10.5, before=3)
    par(doc, [('b', 'Địa chỉ:'), ' ', ('F', 'P2_DIA_CHI', True, '.' * 110)], size=10.5, before=3, after=6)
    par(doc, ('b', 'I.  Sàng lọc ban đầu bệnh dịch truyền nhiễm'), size=11, after=2)
    t = grid(doc, 5, 2, [15.0, 2.2])
    q = [
        [('1. Anh/ chị có đi có đi du lịch/ đến ', ), ('b', 'vùng dịch'), ' (cập nhật theo từng thời điểm) trong vòng ', ('b', '14 ngày'), ' qua không?'],
        [('2. Anh/ chị có ', ), ('b', 'tiếp xúc gần'), ' với ', ('b', 'người bệnh/ động vật'), ' nghi ngờ hoặc mắc ', ('b', 'dịch bệnh truyền nhiễm'), ' trong vòng 14 ngày qua không?'],
    ]
    for i, parts in enumerate(q):
        parts = [x[0] if isinstance(x, tuple) and len(x) == 1 else x for x in parts]
        par(t.cell(i, 0), parts, size=10.5)
        par(t.cell(i, 1), f'{BOX} Có', size=10.5)
        par(t.cell(i, 1), f'{BOX} Không', size=10.5)
    m = t.cell(2, 0).merge(t.cell(2, 1))
    par(m, ['3. Trong vòng 14 ngày qua, Anh/chị có ', ('b', 'triệu chứng'), ' nào sau đây?'], size=10.5)
    check_line(m, ['Sốt', 'Ho và khó thở', 'Ban', 'Tiêu chảy', 'Không'], size=10.5, left=0.4)
    m = t.cell(3, 0).merge(t.cell(3, 1))
    par(m, [('b', 'Kết quả sàng lọc:'), f'          {BOX} Âm tính        {BOX} Dương tính'], size=10.5)
    par(m, ['Người bệnh từ > ', ('b', '6 tuổi'), ' được đánh giá là ', ('b', 'dương tính'), ' nếu: Câu 1 hoặc Câu 2 trả lời “CÓ”, và/ hoặc khi NB có từ ', ('b', '2 triệu chứng'), ' trở lên tại câu 3.'], size=10)
    par(m, ['Đối với bệnh nhi ≤ ', ('b', '6 tuổi'), ', sàng lọc ', ('b', 'dương tính'), ' nếu câu 1 hoặc câu 2 trả lời “CÓ”.'], size=10)
    m = t.cell(4, 0).merge(t.cell(4, 1))
    par(m, [('b', 'Hướng xử trí:'), f'    {BOX} Khám bình thường                {BOX} Không khám'], size=10.5)
    par(m, [f'                          {BOX} Khám ưu tiên                    {BOX} Khám tại PK Nhiệt đới              {BOX} Không khám'], size=10.5)
    par(m, ['Khác: ' + '\t'], size=10.5)
    par(doc, ('b', 'II. Sàng lọc nguy cơ ngã cho người bệnh ngoại trú'), size=11, before=8)
    par(doc, ['    (Có nguy cơ ngã cao: ', ('b', 'Có ít nhất 1 trong 3'), ' câu hỏi sàng lọc được tick “', ('b', 'CÓ'), '”)'], size=10.5, after=2)
    screening = ['1.Người bệnh có cảm thấy hoa mắt, chóng mặt không', '2.Người bệnh có cần hỗ trợ khi đứng lên hoặc đi lại không?', '3.Người bệnh có bị ngã trong vòng 12 tháng qua không?']
    measures = ['1. Dán sticker nguy cơ ngã', '2. Cung cấp thông tin phòng ngã', '3.Hạn chế người bệnh đi lại và yêu cầu gọi hỗ trợ khi cần',
                '4. Hướng dẫn chuông gọi cấp cứu trong nhà vệ sinh', '5.Hỗ trợ người bệnh khi di chuyển', '6.Cung cấp dụng cụ hỗ trợ di chuyển: Cáng, nạng, xe đẩy',
                '7.Trẻ em dưới 3 tuổi: Lưu ý người chăm sóc giữ bé trong tầm kiểm soát, không để bé ngồi trên ghế hoặc chơi một mình.']
    n = 1 + len(screening) + 1 + len(measures) + 1
    t = grid(doc, n, 2, [14.0, 3.2])
    par(t.cell(0, 0), ('b', 'Câu hỏi sàng lọc (Bỏ qua mục này nếu là trẻ < 3 tuổi)'), size=10.5)
    par(t.cell(0, 1), ('b', 'Tích ✓ vào đáp án'), size=10)
    r = 1
    for text in screening:
        par(t.cell(r, 0), text, size=10.5); par(t.cell(r, 1), f'{BOX} Có    {BOX} Không', size=10); r += 1
    par(t.cell(r, 0), ('b', 'Biện pháp can thiệp'), size=10.5); par(t.cell(r, 1), ('b', 'Thực hiện'), size=10); r += 1
    for text in measures:
        par(t.cell(r, 0), text, size=10.5); par(t.cell(r, 1), f'{BOX} Có    {BOX} Không', size=10); r += 1
    par(t.cell(r, 0), '8.Biện pháp khác:', size=10.5)
    sign = grid(doc, 3, 2, [8.0, 9.2], borders=False)
    for row in sign.rows:                                    # căn trên để chữ hai bên cùng hàng
        for cell in row.cells:
            valign(cell, 'top')
    par(sign.cell(0, 0), ' ', size=10, before=4)             # hàng 1: bên trái trống, bên phải là dòng ngày tháng
    par(sign.cell(0, 1), '……………………, ……/……/ 20….', size=10, align='center', before=4)
    par(sign.cell(1, 0), ('b', 'Người khai'), size=11, align='center')            # hàng 2: cùng hàng với "Xác nhận của nhân viên"
    par(sign.cell(1, 1), ('b', 'Xác nhận của nhân viên'), size=11, align='center')
    # Tên người khai cách chữ "Người khai" 60px (= 45pt)
    par(sign.cell(2, 0), [('F', 'P2_NGUOI_KHAI', True, '.' * 30)], size=11, align='center', before=45)
    par(sign.cell(2, 1), ' ', size=11)


# ---------- trang 3: bìa ----------
def page3(doc):
    s = new_section(doc, left=2.2, right=2.2, top=2.5, bottom=2.5)
    s._sectPr.find(qn('w:pgMar')).addnext(parse_xml(
        f'<w:pgBorders xmlns:w="{W}" w:offsetFrom="page">' + ''.join(
            f'<w:{side} w:val="single" w:sz="8" w:space="28" w:color="000000"/>' for side in ('top', 'left', 'bottom', 'right')) + '</w:pgBorders>'))
    par(doc, '', size=11, before=150)
    par(doc, ('b', 'VINMEC'), size=40, align='center')
    par(doc, 'INTERNATIONAL HOSPITAL', size=11, align='center', after=70)
    par(doc, ('b', 'GIẤY KHÁM SỨC KHỎE'), size=26, align='center')
    par(doc, ('b', 'VÀ KHÁM SỨC KHOẺ ĐỊNH KỲ'), size=26, align='center', after=6)
    par(doc, ('bi', '(DÙNG CHO NGƯỜI TỪ ĐỦ 18 TUỔI TRỞ LÊN)'), size=11, align='center')


# ---------- trang 4: giấy khám sức khỏe (thông tin hành chính + tiền sử) ----------
def page4(doc):
    new_section(doc, left=1.6, right=1.6, top=1.1, bottom=1.0)
    head = grid(doc, 1, 2, [7.4, 9.8], borders=False)
    l, r = head.cell(0, 0), head.cell(0, 1)
    par(l, ('b', 'SỞ Y TẾ HƯNG YÊN'), size=10.5, align='center', before=8)
    par(l, ('b', 'BỆNH VIỆN ĐA KHOA QUỐC TẾ'), size=10.5, align='center')
    par(l, ('b', 'VINMEC OCEAN PARK 2'), size=10.5, align='center')
    par(l, 'Số:………….…./GKSK-VMOCP2', size=10.5, align='center', before=6)
    par(r, ('b', 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM'), size=11, align='center')
    par(r, ('b', 'Độc lập - Tự do - Hạnh phúc'), size=11, align='center', after=6)
    par(r, ('b', 'GIẤY KHÁM SỨC KHỎE'), size=15, align='center')
    par(r, ('b', 'VÀ KHÁM SỨC KHỎE ĐỊNH KỲ'), size=15, align='center')
    par(r, ('bi', '(DÙNG CHO NGƯỜI TỪ ĐỦ 18 TUỔI TRỞ LÊN)'), size=10.5, align='center')
    s = 11
    par(doc, ['1.\tHọ và tên ', ('i', '(viết chữ in hoa)'), ': ', ('F', 'HO_TEN', True)], size=s, before=8, left=1.2, first=-1.2)
    par(doc, ['2.\tGiới tính:     ', ('F', 'NAM_BOX', False), '  Nam          ', ('F', 'NU_BOX', False), '  Nữ'], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ['3.\tNgày tháng năm sinh: ', ('F', 'NGAY_SINH', True), ';   Tuổi: ', ('F', 'TUOI', True)], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ['4.\tSố CCCD/Hộ chiếu/Mã định danh: ', ('F', 'CCCD', True)], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ['5.\tCấp ngày: ', ('F', 'CAP_NGAY', True), '     Nơi cấp: ', ('F', 'NOI_CAP', True)], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ['6.\tDân tộc: ', ('F', 'DAN_TOC', True)], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ['7.\tĐối tượng: ', ('F', 'DOI_TUONG', True)], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ['8.\tNguồn chi trả: ', ('F', 'NGUON_CHI_TRA', True)], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ['9.\tNhóm máu: ', ('F', 'NHOM_MAU', True), '  (nếu có)'], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ['10.\tNơi ở hiện tại: Tỉnh/ thành: ', ('F', 'TINH', True), '   phường/ xã: ', ('F', 'PHUONG_XA', True)], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ['Số nhà/ thôn/ xóm: ', ('F', 'SO_NHA', True)], size=s, before=4, left=1.2)
    par(doc, ['11.\tNghề nghiệp: ', ('F', 'NGHE_NGHIEP', True)], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ['12.\tNơi làm việc, học tập: ', ('F', 'NOI_LAM_VIEC', True)], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ['13.\tLý do khám sức khỏe: ', ('F', 'LY_DO', True)], size=s, before=4, left=1.2, first=-1.2)
    par(doc, ('b', 'TIỀN SỬ BỆNH CỦA ĐỐI TƯỢNG KHÁM SỨC KHỎE'), size=11.5, align='center', before=8, after=4)
    par(doc, ('b', '1. Tiền sử gia đình:'), size=11)
    par(doc, 'Có ai trong gia đình ông (bà) mắc một trong các bệnh: truyền nhiễm, tim mạch, đái tháo đường, lao, hen phế quản, ung thư, động kinh, rối loạn tâm thần, bệnh khác:', size=10.5, left=0.8)
    par(doc, f'a) {BOX} Không                          b) {BOX} Có', size=10.5, left=1.8)
    par(doc, 'Nếu “có”, đề nghị ghi cụ thể tên bệnh: ' + '\t', size=10.5, left=0.8)
    par(doc, [('b', '2. Tiền sử bản thân:'), ' Ông (bà) đã/đang mắc bệnh, tình trạng bệnh nào sau đây không'], size=11, before=2, after=2)
    left_items = ['Có bệnh hay bị thương trong 5 năm qua', 'Có bệnh thần kinh hay bị thương ở đầu', 'Bệnh mắt hoặc giảm thị lực (trừ trường hợp đeo kính thuốc)',
                  'Bệnh ở tai, giảm sức nghe hoặc thăng bằng', 'Bệnh ở tim, hoặc nhồi máu cơ tim, các bệnh tim mạch khác',
                  'Phẫu thuật can thiệp tim - mạch (thay van, bắc cầu nối, tạo hình mạch, máy tạo nhịp, đặt stent mạch, ghép tim)',
                  'Tăng huyết áp', 'Khó thở', 'Bệnh phổi, hen, khí phế thũng, viêm phế quản mạn tính', 'Bệnh thận, lọc máu', 'Nghiện rượu, bia']
    right_items = ['Đái tháo đường hoặc kiểm soát tăng đường huyết', 'Bệnh tâm thần', 'Mất ý thức, rối loạn ý thức', 'Ngất, chóng mặt', 'Bệnh tiêu hóa',
                   'Rối loạn giấc ngủ, ngừng thở khi ngủ, ngủ rũ ban ngày, ngáy to', 'Tai biến mạch máu não hoặc liệt', 'Bệnh hoặc tổn thương cột sống',
                   'Sử dụng rượu thường xuyên, liên tục', 'Sử dụng ma túy và chất gây nghiện', 'Bệnh khác (ghi rõ) ……………………']
    widths = [1.0, 5.0, 0.9, 1.5, 1.0, 5.0, 0.9, 1.5]
    t = grid(doc, 12, 8, widths)
    for i, h in enumerate(['STT', 'Tên bệnh, tật', 'Có', 'Không'] * 2):
        shade(t.cell(0, i), 'EDEDED')
        par(t.cell(0, i), ('b', h), size=9, align='center')
    for k in range(11):
        for off, items, base in ((0, left_items, 1), (4, right_items, 12)):
            valign(t.cell(k + 1, off + 1))
            par(t.cell(k + 1, off), str(base + k), size=9, align='center')
            par(t.cell(k + 1, off + 1), items[k], size=9)
            par(t.cell(k + 1, off + 2), BOX, size=10, align='center')
            par(t.cell(k + 1, off + 3), BOX, size=10, align='center')
            for j in range(4):
                valign(t.cell(k + 1, off + j))


# ---------- trang 5: câu hỏi khác, khám thể lực, khám lâm sàng (ảnh 6) ----------
def page5(doc):
    new_section(doc, left=1.6, right=1.6, top=0.6, bottom=0.5)
    par(doc, ('b', '3. Câu hỏi khác (nếu có):'), size=11)
    par(doc, 'a)\tÔng (bà) có đang điều trị bệnh gì không?', size=10.5, left=1.2, first=-1.2, before=3)
    par(doc, f'{BOX} Không', size=10.5, left=1.8)
    par(doc, f'{BOX} Có (Nếu có, xin hãy liệt kê tên bệnh, các thuốc đang dùng và liều lượng): ' + '\t', size=10.5, left=1.8)
    par(doc, '\t', size=10.5, left=1.2)
    par(doc, 'b) Tiền sử thai sản (Đối với phụ nữ):', size=10.5, before=4)
    par(doc, f'{BOX} Không', size=10.5, left=1.8)
    par(doc, f'{BOX} Có (Nếu có, xin hãy liệt kê tên bệnh, các thuốc đang dùng và liều lượng): ' + '\t', size=10.5, left=1.8)
    par(doc, '\t', size=10.5, left=1.2, after=4)
    sign = grid(doc, 1, 2, [8.2, 9.0], borders=False)
    for cell in sign.rows[0].cells:
        valign(cell, 'top')
    par(sign.cell(0, 0), 'Tôi xin cam đoan những điều khai trên đây hoàn toàn đúng với sự thật theo sự hiểu biết của tôi.', size=10.5)
    par(sign.cell(0, 1), '…………… ngày ………. tháng………năm…………', size=10.5, align='center')
    par(sign.cell(0, 1), ('b', 'Người đề nghị khám sức khỏe'), size=10.5, align='center')
    par(sign.cell(0, 1), '(Ký và ghi rõ họ, tên)', size=10.5, align='center')
    par(sign.cell(0, 1), [('F', 'P5_NGUOI_KHAI', True, '.' * 30)], size=10.5, align='center', before=45, after=2)
    par(doc, [('b', 'I.      KHÁM THỂ LỰC')], size=11.5, before=6)
    par(doc, '- Chiều cao: ………………cm;          - Cân nặng: ……………… kg;          - Chỉ số BMI:……………………kg/m²', size=10.5, left=0.8, before=3)
    par(doc, '- Mạch: ……………… lần/phút;          - Huyết áp:…………………/. ………………………mmHg', size=10.5, left=0.8, before=3)
    par(doc, 'Phân loại thể lực: ' + '\t', size=10.5, left=0.8, before=3)
    par(doc, ('b', 'II.     KHÁM LÂM SÀNG'), size=11.5, before=4)
    rows = [('1.', 'Nội khoa', None)]
    sub = [('a)', 'Tuần hoàn:'), ('b)', 'Hô hấp:'), ('c)', 'Tiêu hóa:'), ('d)', 'Thận - Tiết niệu - Sinh dục'), ('đ)', 'Nội tiết:'), ('e)', 'Cơ - xương - khớp:'), ('g)', 'Thần kinh:'), ('h)', 'Tâm thần:')]
    singles = [('2.', 'Ngoại khoa:'), ('3.', 'Da liễu:'), ('4.', 'Sản phụ khoa:')]
    n = 1 + 1 + len(sub) + len(singles) + 1 + 1
    t = grid(doc, n, 3, [1.2, 10.8, 5.2])
    shade(t.cell(0, 0))
    m = t.cell(0, 0).merge(t.cell(0, 1))
    par(m, ('b', 'Nội dung khám'), size=10.5, align='center'); par(t.cell(0, 2), ('b', 'Họ tên và chữ ký của Bác sỹ'), size=10, align='center')
    r = 1
    m = t.cell(r, 0).merge(t.cell(r, 1))
    par(m, [('b', '1.   Nội khoa')], size=10.5); r += 1
    first = r
    for key, label in sub:
        par(t.cell(r, 0), key, size=10.5, align='center')
        par(t.cell(r, 1), label + '\t', size=10.5)
        par(t.cell(r, 1), ('i', 'Phân loại: ') if False else [('i', 'Phân loại:'), '\t'], size=10.5)
        r += 1
    t.cell(first, 2).merge(t.cell(r - 1, 2))
    for key, label in singles:
        par(t.cell(r, 0), ('b', key), size=10.5, align='center')
        par(t.cell(r, 1), [('b', label), '\t'], size=10.5)
        par(t.cell(r, 1), [('i', 'Phân loại:'), '\t'], size=10.5)
        r += 1
    m = t.cell(r, 0).merge(t.cell(r, 1))
    par(m, [('b', '5.   Mắt:')], size=10.5); r += 1
    eyes = t.cell(r, 0).merge(t.cell(r, 1))
    par(eyes, ('i', 'Kết quả khám thị lực:'), size=10.5)
    par(eyes, 'Không kính:   Mắt phải………………………  Mắt trái………………………', size=10.5)
    par(eyes, 'Có kính:   Mắt phải………………………  Mắt trái………………………', size=10.5)
    par(eyes, [('i', 'Các bệnh về mắt (nếu có):'), '\t'], size=10.5)
    par(eyes, [('i', 'Phân loại:'), '\t'], size=10.5)


# ---------- trang 6: tai mũi họng, răng hàm mặt, cận lâm sàng, kết luận (ảnh 5) ----------
def page6(doc):
    new_section(doc, left=1.6, right=1.6, top=0.8, bottom=0.5)
    t = grid(doc, 2, 2, [12.0, 5.2])
    par(t.cell(0, 0), [('b', '6.   Tai - Mũi - Họng')], size=10.5)
    for text in ('Kết quả khám thính lực:', 'Tai trái:  Nói thường…………………… m;  Nói thầm…………………… m', 'Tai phải: Nói thường…………………… m;  Nói thầm…………………… m',
                 'Các bệnh về tai mũi họng (nếu có): ' + '\t', 'Phân loại: ' + '\t'):
        par(t.cell(0, 0), ('i', text), size=10.5)
    par(t.cell(1, 0), [('b', '7.   Răng - Hàm - Mặt')], size=10.5)
    for text in ('Kết quả khám:   Hàm trên: ' + '\t', '                       Hàm dưới: ' + '\t', 'Các bệnh về răng hàm mặt (nếu có): ' + '\t', 'Phân loại: ' + '\t'):
        par(t.cell(1, 0), ('i', text), size=10.5)
    par(doc, [('b', 'I.      KHÁM CẬN LÂM SÀNG')], size=11.5, before=6)
    par(doc, ('b', '1. Khám phân loại sức khỏe để đi học, đi làm thực hiện khám cận lâm sàng sau:'), size=10.5, after=2)
    t = grid(doc, 5, 2, [12.0, 5.2])
    shade(t.cell(0, 0), 'FFFFFF')
    par(t.cell(0, 0), ('b', 'Nội dung khám'), size=10.5, align='center'); par(t.cell(0, 1), ('b', 'Họ tên, chữ ký của Bác sỹ'), size=10, align='center')
    blood = ['a) Xét nghiệm máu:', '- Huyết học (tổng phân tích tế bào máu ngoại vi):', '●  Số lượng hồng cầu………… T/L          ●  Số lượng bạch cầu………………… G/L',
             '●  Số lượng tiểu cầu………… G/L          ●  Huyết sắc tố……………………… g/L', '●  Khác: ' + '\t', '- Sinh hóa máu:',
             '●  Đường máu:……mmol/l   ●  Urê…… mmol/l;   ●  Creatinin:……………… mmol/l', '●  ASAT (GOT):………………… U/L; ALAT (GPT):…………………………… U/L']
    for i, text in enumerate(blood):
        par(t.cell(1, 0), ('b', text) if i == 0 else text, size=10)
    urine = ['b) Xét nghiệm nước tiểu:', 'Tổng phân tích nước tiểu (bằng máy tự động):', '●  Bạch cầu……………… tế bào/µl          ●  Hồng cầu…………………………… tế bào/µl',
             '●  Protein……………… g/l          ●  Glucose…………………………… mmol/l', '●  Khác: ' + '\t']
    for i, text in enumerate(urine):
        par(t.cell(2, 0), ('b', text) if i == 0 else text, size=10)
    par(t.cell(3, 0), ('b', 'c) Chẩn đoán hình ảnh (XQ tim phổi thẳng):'), size=10)
    par(t.cell(3, 0), '\t', size=10, before=6)
    par(t.cell(4, 0), ('b', 'd) Kết quả khám Cận lâm sàng khác'), size=10)
    par(t.cell(4, 0), f'{BOX} Không', size=10, left=0.4)
    par(t.cell(4, 0), f'{BOX} Có (Nếu có, hãy liệt kê kết quả chi tiết):' + '\t', size=10, left=0.4)
    par(t.cell(4, 0), '\t', size=10)
    par(doc, ('b', '2. Khám sức khỏe định kỳ (cận lâm sàng thực hiện theo chỉ định của bác sỹ)'), size=10.5, before=6, after=2)
    t = grid(doc, 2, 2, [12.0, 5.2])
    par(t.cell(0, 0), ('b', 'Nội dung khám'), size=10.5, align='center'); par(t.cell(0, 1), ('b', 'Họ tên, chữ ký của Bác sỹ'), size=10, align='center')
    par(t.cell(1, 0), ('i', 'Cận lâm sàng thực hiện theo chỉ định của bác sỹ'), size=10.5)
    par(t.cell(1, 0), [('i', 'Kết quả'), '\t'], size=10.5, before=4)
    for _ in range(4):
        par(t.cell(1, 0), '\t', size=10.5, before=4)
    par(doc, ('b', 'II.     KẾT LUẬN'), size=11.5, before=3)
    par(doc, '1. Tình trạng sức khỏe; mắc các bệnh, tật (nếu có) ' + '\t', size=10.5, before=3)
    par(doc, '\t', size=10.5, before=3)
    par(doc, '\t', size=10.5, before=3)
    par(doc, '2. Phân loại sức khỏe (theo quy định của Bộ Y tế): ' + '\t', size=10.5, before=3)
    par(doc, '\t', size=10.5, before=3)
    par(doc, '\t', size=10.5, before=3)
    par(doc, '………. ngày…… tháng….. năm………..', size=10.5, align='right', before=4)
    par(doc, ('b', 'NGƯỜI KẾT LUẬN'), size=11, align='right')
    par(doc, ('i', '(Ký, ghi rõ họ tên và đóng dấu)'), size=10.5, align='right')


def build(sex, package):
    USED.clear()
    doc = Document()
    normal = doc.styles['Normal']
    normal.font.name = FONT
    normal.font.size = Pt(10)
    normal.paragraph_format.space_before = normal.paragraph_format.space_after = Pt(0)   # ô trống không làm cao hàng
    normal.paragraph_format.line_spacing = 1.0
    for fn in (lambda d: page1(d, sex, package), page2, page3, page4, page5, page6):
        fn(doc)
    for p in doc.element.body.iter(qn('w:p')):
        ppr = p.find(qn('w:pPr'))
        if ppr is not None and ppr.find(qn('w:sectPr')) is not None:
            sect = ppr.find(qn('w:sectPr'))
            sect.addprevious(parse_xml(f'<w:rPr xmlns:w="{W}"><w:sz w:val="2"/><w:szCs w:val="2"/></w:rPr>'))
            ppr.insert(0, parse_xml(f'<w:spacing xmlns:w="{W}" w:before="0" w:after="0" w:line="20" w:lineRule="exact"/>'))
    return doc


def main():
    OUT.mkdir(exist_ok=True)
    for (sex, package), name in FILES.items():
        doc = build(sex, package)
        doc.save(OUT / name)
        print('đã tạo', OUT / name)


if __name__ == '__main__':
    main()
