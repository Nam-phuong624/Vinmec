"""Kiểm tra luồng demo bằng dữ liệu giả lập; không lưu ảnh vào repo."""
import json
import os
from pathlib import Path
import sys
import tempfile
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1100}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    assert page.goto(os.environ.get('DEMO_TEST_URL', 'http://127.0.0.1:8765')).status == 200
    assert page.locator('#camera').count() == 0
    assert page.locator('video').count() == 0
    page.get_by_role('button', name='Ánh xạ rõ ràng').click()
    assert 'Phường Ba Đình' in page.locator('#new-address').inner_text()
    assert page.locator('#new-code').inner_text().startswith('Mã xã/phường: 00004')
    assert page.locator('#confirm').is_disabled()
    assert 'Tích ô' in page.locator('#confirm-help').inner_text()
    page.locator('#verified').check()
    page.locator('#confirm').click()
    with page.expect_download() as downloaded:
        page.locator('#export').click()
    receipt = json.loads(Path(downloaded.value.path()).read_text(encoding='utf-8'))
    assert receipt['mappingStatus'] == 'exact'
    assert receipt['person']['address'] != receipt['newAddress']
    assert receipt['syntheticPerson'] is True
    assert receipt['newCommuneCode'] == '00004'
    page.screenshot(path=str(Path(tempfile.gettempdir()) / 'vinmec-demo-desktop.png'), full_page=True)
    page.get_by_role('button', name='Cần kiểm tra thêm').click()
    assert page.locator('.candidate').count() > 1
    assert page.locator('#mapped-address').is_hidden()
    assert 'Chọn xã/phường' in page.locator('#confirm-help').inner_text()
    page.locator('.candidate input').first.check()
    page.locator('#verified').check()
    assert page.locator('#confirm').is_disabled()
    assert 'Căn cứ' in page.locator('#confirm-help').inner_text()
    page.locator('#review-note').fill('Kiểm tra mô phỏng với người bệnh mẫu.')
    assert page.locator('#confirm').is_enabled()
    page.locator('#confirm').click()
    page.locator('.address-edit summary').click()
    page.locator('#address-input').fill('Quận Ba Đình, Thành phố Hà Nội')
    assert page.locator('#confirm').is_disabled()
    assert page.locator('#export').is_hidden()
    page.locator('#remap').click()
    assert page.locator('#result-badge').inner_text() == 'Chưa ánh xạ'
    page.get_by_role('button', name='Chưa đủ địa chỉ').click()
    assert page.locator('#confirm').is_disabled()
    page.locator('#address-input').fill('Số 01 phố minh họa, P. Trúc Bạch, Q. Ba Đình, TP. Hà Nội')
    page.locator('#remap').click()
    assert page.locator('#result-badge').inner_text() == 'Đã đối chiếu'
    assert page.locator('#old-address').inner_text() == 'Quận Ba Đình, Thành phố Hà Nội'
    page.locator('#reader-details').evaluate('(el) => el.open = true')
    page.locator('#payload').fill('QR không hợp lệ')
    page.locator('#parse').click()
    assert page.locator('#result').is_hidden()
    assert '7 trường' in page.locator('#scan-status').inner_text()
    core_results = page.evaluate('''() => {
      const base = '000000000001||MẪU|01011990|Nam|Phường Trúc Bạch, Quận Ba Đình, Thành phố Hà Nội|01012021';
      let rejected = 0;
      for (const raw of [base.replace('01011990', '31021990'), base.replace('000000000001', '123'), base.replace('01012021', '01011899'), base.replace('01012021', '01011980'), base.replace('|Nam|', '|?|')]) {
        try { CCCD.parseQR(raw); } catch { rejected++; }
      }
      const rows = ADDRESS_DATA.records;
      const mapper = CCCD.createMapper(rows);
      return {rejected, rows: rows.length, validCodes: rows.every(r => /^\\d{1,5}$/.test(r[2]) && /^\\d{1,5}$/.test(r[4])), count: mapper('Phường Trúc Bạch, Quận Ba Đình, Thành phố Hà Nội').candidates.length, padded: mapper('Thị trấn Thanh Nhật, Huyện Hạ Lang, Tỉnh Cao Bằng').candidates[0].code, storage: localStorage.length};
    }''')
    assert core_results == {'rejected': 5, 'rows': 10565, 'validCodes': True, 'count': 1, 'padded': '01558', 'storage': 0}, core_results
    history_results = page.evaluate('''() => {
      const map = CCCD.createMapper(ADDRESS_DATA.records);
      const exact = ['Bình Xá, Bình Phú, Thạch Thất, Hà Nội',
        'Thôn Bình Xá, xã Bình Phú, huyện Thạch Thất, TP. Hà Nội',
        'Số 1, Thôn Bình Xá, Bình Phú, Thạch Thất, Hà Nội',
        'Bình Xá, Quang Trung, Thạch Thất, Hà Nội',
        'Binh Xa, Binh Phu, Thach That, Ha Noi'];
      const review = ['Bình Phú, Thạch Thất, Hà Nội', 'Thôn khác, Bình Phú, Thạch Thất, Hà Nội',
        'Bình Xá, Hữu Bằng, Thạch Thất, Hà Nội'];
      return {
        exact: exact.every(input => { const r=map(input);return r.status==='exact' && r.kind==='locality-verified' && r.candidates[0].code==='10003'; }),
        preserve: map(exact[2]).detail === 'Số 1, Thôn Bình Xá',
        sources: map(exact[0]).provenance.length === 3,
        review: review.every(input=>{const r=map(input);return r.status==='review' && r.candidates.length===2;}),
        wrongDistrict: map('Bình Xá, Bình Phú, Cầu Giấy, Hà Nội').status==='missing'
      };
    }''')
    assert all(history_results.values()), history_results
    page.locator('[data-sample="historical"]').click()
    assert page.locator('#result-badge').inner_text() == 'Cần xác minh'
    assert page.locator('#mapped-address').is_hidden()
    assert page.locator('.candidate').count() >= 2
    page.locator('.candidate input').first.check()
    assert page.locator('#new-address').inner_text() == 'Bình Xá, Xã Tây Phương, Thành phố Hà Nội'
    assert page.locator('#mapping-evidence a').count() > 3
    page.locator('#review-note').fill('Giữ tên thôn theo bảng gốc trong lượt kiểm thử giả lập; chưa xác minh Wiki.')
    page.locator('#verified').check()
    page.locator('#confirm').click()
    with page.expect_download() as history_download:
        page.locator('#export').click()
    history_receipt = json.loads(Path(history_download.value.path()).read_text(encoding='utf-8'))
    assert history_receipt['mappingKind'] == 'research-review'
    assert len(history_receipt['mappingEvidence']) > 3
    assert 'Bình Phú' in history_receipt['person']['address']
    print('PASS: Bình Xá/Bình Phú → Quang Trung → Tây Phương, nguồn chứng minh, không suy rộng xã, không khớp sai huyện và giữ địa chỉ gốc.')
    print('PASS: nhập toàn bộ, chia tách, thiếu địa chỉ, sửa địa chỉ, QR lỗi, phiếu JSON, định dạng ngày/mã và dữ liệu nguồn.')
    generator = Path(tempfile.gettempdir()) / 'vinmec-qr-test-generator.js'
    if generator.exists():
        page.add_script_tag(path=str(generator))
        data_url = page.evaluate('''() => {
          qrcode.stringToBytes = qrcode.stringToBytesFuncs['UTF-8'];
          const qr = qrcode(0, 'M');
          qr.addData('000000000001||NGƯỜI BỆNH MẪU|01011990|Nam|Phường Trúc Bạch, Quận Ba Đình, Thành phố Hà Nội|01012021'); qr.make();
          const count = qr.getModuleCount(), scale = 6, quiet = 4;
          const canvas = document.createElement('canvas'); canvas.width = canvas.height = (count + quiet * 2) * scale;
          const ctx = canvas.getContext('2d'); ctx.fillStyle = 'white'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.fillStyle = 'black';
          for (let r = 0; r < count; r++) for (let c = 0; c < count; c++) if(qr.isDark(r,c)) ctx.fillRect((c+quiet)*scale,(r+quiet)*scale,scale,scale);
          window.testCanvas = canvas; return canvas.toDataURL('image/png');
        }''')
        import base64
        fallback_result = page.evaluate('''() => {
          const c = window.testCanvas, pixels = c.getContext('2d').getImageData(0,0,c.width,c.height);
          const normal = decodeFallback(pixels);
          for(let i=0; i<pixels.data.length; i+=4) {
            const v = 255-pixels.data[i]; pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=v;
          }
          const inverted = decodeFallback(pixels);
          return !!normal && !!inverted && normal.data.includes('NGƯỜI BỆNH MẪU') && inverted.data === normal.data;
        }''')
        assert fallback_result, 'Bộ giải mã dự phòng phải đọc được QR tiếng Việt và QR đảo màu.'
        print('PASS: ZXing dự phòng đọc QR tiếng Việt, QR đảo màu.')
        page.locator('#image-file').set_input_files({'name': 'qr-gia-lap.png', 'mimeType': 'image/png', 'buffer': base64.b64decode(data_url.split(',')[1])})
        page.wait_for_function("document.getElementById('person-name').textContent === 'NGƯỜI BỆNH MẪU'")
        assert 'Phường Ba Đình' in page.locator('#new-address').inner_text()
        # Ảnh mô phỏng toàn thẻ, QR chiếm một phần nhỏ và ảnh xoay 90 độ.
        for rotated in (False, True):
            page.locator('#reset').click()
            card_url = page.evaluate('''rotated => {
              const card = document.createElement('canvas'); card.width = 4200; card.height = 2700;
              const ctx = card.getContext('2d'); ctx.fillStyle = '#f1ebdd'; ctx.fillRect(0,0,4200,2700);
              ctx.fillStyle = '#56736e'; ctx.font = '90px sans-serif'; ctx.fillText('THE GIA LAP - KIEM THU QR',500,500);
              ctx.fillStyle = '#bdc9c7'; ctx.fillRect(400,800,700,1000);
              ctx.drawImage(window.testCanvas,3500,300,330,330);
              if (!rotated) return card.toDataURL('image/png');
              const out = document.createElement('canvas'); out.width = card.height; out.height = card.width;
              const outCtx = out.getContext('2d'); outCtx.translate(out.width,0); outCtx.rotate(Math.PI/2); outCtx.drawImage(card,0,0);
              return out.toDataURL('image/png');
            }''', rotated)
            page.locator('#image-file').set_input_files({'name': 'cccd-toan-the-gia-lap.png', 'mimeType': 'image/png', 'buffer': base64.b64decode(card_url.split(',')[1])})
            page.wait_for_function("document.getElementById('person-name').textContent === 'NGƯỜI BỆNH MẪU'", timeout=60000)
            assert 'Phường Ba Đình' in page.locator('#new-address').inner_text()
            assert 'ảnh CCCD' in page.locator('#scan-status').inner_text()
        blank_url = page.evaluate('''() => { const c = document.createElement('canvas'); c.width=600; c.height=400; return c.toDataURL('image/png'); }''')
        page.locator('#image-file').set_input_files({'name': 'anh-khong-co-qr.png', 'mimeType': 'image/png', 'buffer': base64.b64decode(blank_url.split(',')[1])})
        page.wait_for_function("document.getElementById('result-badge').textContent === 'Chưa đọc được'")
        assert page.locator('#result').is_hidden()
        assert 'Chưa đọc được mã QR' in page.locator('#scan-status').inner_text()
        print('PASS: ảnh toàn thẻ có QR nhỏ, ảnh xoay 90 độ, ảnh không có QR không dùng lại kết quả cũ.')
    else:
        print('SKIP: image QR test generator unavailable.')
    page.locator('#reset').click()
    assert page.locator('#person-id').inner_text() == ''
    assert page.locator('#payload').input_value() == ''
    page.set_viewport_size({'width': 390, 'height': 844})
    page.get_by_role('button', name='Cần kiểm tra thêm').click()
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path=str(Path(tempfile.gettempdir()) / 'vinmec-demo-mobile.png'), full_page=True)
    assert not errors, errors
    print('PASS: xóa phiên, bố cục mobile 390px, không lỗi JavaScript.')
    browser.close()
