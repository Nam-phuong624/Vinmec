"""Kiểm tra biểu mẫu và lớp dữ liệu nghiên cứu, chỉ dùng người giả lập."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(os.environ.get('DEMO_TEST_URL','http://127.0.0.1:8765'))
    page.locator('[data-sample="exact"]').click()
    assert page.locator('#profile-first').input_value()=='A'
    assert page.locator('#profile-last').input_value()=='NGƯỜI'
    assert page.locator('#profile-middle').input_value()=='BỆNH MẪU'
    assert page.locator('#profile-birth').input_value()=='01/01/1990'
    assert page.locator('#profile-document-number').input_value()=='000000000001'
    for name in ['hospital-number','phone','nationality','language','ethnicity','occupation']:
        assert page.locator('#profile-'+name).input_value()==''
    page.locator('#verified').check()
    page.locator('#confirm').click()
    page.locator('#profile-first').fill('TÊN ĐÃ SỬA')
    assert page.locator('#export').is_hidden()
    assert not page.locator('#verified').is_checked()
    assert page.locator('#person-name').inner_text()=='NGƯỜI BỆNH MẪU A'
    page.locator('#profile-birth').fill('31/02/1990')
    page.locator('#verified').check()
    assert page.locator('#confirm').is_disabled()
    page.locator('#profile-birth').fill('01/01/1990')
    page.locator('#profile-phone').fill('0000000000')
    page.locator('#profile-add-phone').click()
    page.locator('#profile-extra-phones input').fill('0000000001')
    page.locator('#verified').check()
    page.locator('#confirm').click()
    with page.expect_download() as download:
        page.locator('#export').click()
    receipt=json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
    assert receipt['person']['name']=='NGƯỜI BỆNH MẪU A'
    assert receipt['patientProfile']['fields']['first']=='TÊN ĐÃ SỬA'
    assert receipt['patientProfile']['extraPhones']==['0000000001']
    assert receipt['patientProfile']['address']==receipt['newAddress']
    page.locator('[data-sample="partial"]').click()
    assert page.locator('#profile-sex').input_value()=='Nữ'
    assert page.locator('#profile-phone').input_value()==''
    assert page.locator('#profile-extra-phones input').count()==0
    assert page.locator('#profile-address-value').input_value()==''
    page.locator('#tab-care').click()
    assert page.locator('#profile-demographics').is_hidden()
    page.locator('#tab-care').press('ArrowRight')
    assert page.locator('#profile-financial').is_visible()
    page.locator('#tab-demographics').click()
    # Hai phường trùng số tổ: khớp ngữ cảnh và luôn yêu cầu xác nhận.
    results=page.evaluate('''() => {
      const base=CCCD.createMapper(ADDRESS_DATA.records);
      const map=HISTORY_RESEARCH.createMapper(base,ADDRESS_RESEARCH);
      const a=map('Tổ dân phố 8, Phường Ba Đình, Thành phố Hà Nội');
      const b=map('Tổ dân phố 6, Phường Giảng Võ, Thành phố Hà Nội');
      const wrong=map('Tổ dân phố 8, Phường Ba Đình, Tỉnh Cao Bằng');
      return {a:a.status,details:a.candidates.map(c=>c.detail),b:b.status,
        matching:a.candidates.filter(c=>c.researchUnverified).every(c=>c.code==='00004'),wrong:wrong.status,
        sources:a.provenance.some(s=>s.url.includes('wikipedia.org')&&s.quote)};
    }''')
    assert results['a']=='review' and results['b']=='review',results
    assert any('2' in s for s in results['details']) and any('3' in s for s in results['details']),results
    assert results['matching'] and results['sources'] and results['wrong']=='missing',results
    page.locator('#reset').click()
    assert page.locator('#profile-first').input_value()==''
    assert page.locator('#profile-document-number').input_value()==''
    assert not errors,errors
    browser.close()
print('PASS: profile fill/edit/reset, original QR, validation, tabs, research context and confirmation.')
