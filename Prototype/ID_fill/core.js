(function (root) {
  'use strict';
  const normalize = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase().replace(/[.]/g, ' ').replace(/\s+/g, ' ').trim();
  function unit(value) {
    return normalize(value).replace(/\s*\(\d+\)\s*$/, '').replace(/^(thanh pho|tinh|quan|huyen|thi xa|phuong|xa|thi tran|tp|q|p|h|tx|tt)\s+/, '').trim();
  }
  const province = value => ({'hcm': 'ho chi minh', 'tp hcm': 'ho chi minh', 'tphcm': 'ho chi minh'}[unit(value)] || unit(value));
  function date(value, label) {
    if (!/^\d{8}$/.test(value)) throw new Error(`${label} cần có dạng DDMMYYYY.`);
    const day = +value.slice(0, 2), month = +value.slice(2, 4), year = +value.slice(4);
    const parsed = new Date(year, month - 1, day);
    if (year < 1900 || parsed.getFullYear() !== year || parsed.getMonth() !== month - 1 || parsed.getDate() !== day || parsed > new Date()) throw new Error(`${label} không hợp lệ.`);
    return `${value.slice(0, 2)}/${value.slice(2, 4)}/${value.slice(4)}`;
  }
  function parseQR(raw) {
    const fields = String(raw).replace(/^\uFEFF/, '').trim().split('|').map(v => v.trim());
    if (fields.length !== 7) throw new Error('QR chưa đúng định dạng 7 trường phân cách bằng dấu |. Hãy quét lại mã QR CCCD.');
    const [id, oldId, name, birth, sex, address, issued] = fields;
    if (!/^\d{12}$/.test(id)) throw new Error('Số CCCD cần đủ 12 chữ số.');
    if (oldId && !/^\d{9}$/.test(oldId)) throw new Error('Số CMND cũ cần 9 chữ số hoặc để trống.');
    if (!name || !address) throw new Error('Thiếu họ tên hoặc địa chỉ thường trú trong QR.');
    if (!['nam', 'nu'].includes(normalize(sex))) throw new Error('Giới tính trong QR chưa được hỗ trợ.');
    const birthDate = date(birth, 'Ngày sinh'), issueDate = date(issued, 'Ngày cấp');
    if (issued.slice(4) + issued.slice(2, 4) + issued.slice(0, 2) < birth.slice(4) + birth.slice(2, 4) + birth.slice(0, 2)) throw new Error('Ngày cấp không thể trước ngày sinh.');
    return {id, oldId, name, birthDate, sex, address, issueDate};
  }
  function createMapper(records, history = root.ADDRESS_HISTORY || {transitions: [], localities: []}) {
    const index = new Map();
    const currentIndex = new Map();
    for (const row of records) {
      const key = [province(row[7]), unit(row[6]), unit(row[3])].join('|');
      if (!index.has(key)) index.set(key, []);
      index.get(key).push(row);
      const currentKey = [province(row[0]), unit(row[1])].join('|');
      if (!currentIndex.has(currentKey)) currentIndex.set(currentKey, new Map());
      const code = row[2].padStart(5, '0');
      currentIndex.get(currentKey).set(code, {province: row[0].replace(/\s*\(\d+\)\s*$/, ''), provinceCode: (row[0].match(/\((\d+)\)/) || [])[1] || '', commune: row[1], code, oldCode: null, changes: []});
    }
    return function mapAddress(address) {
      const parts = address.split(',').map(s => s.trim()).filter(Boolean);
      const [commune, district, prov] = parts.slice(-3);
      let rows = parts.length >= 3 ? index.get([province(prov), unit(district), unit(commune)].join('|')) || [] : [];
      const detail = parts.slice(0, -3).join(', ');
      let transition = null;
      if (!rows.length && parts.length >= 3) {
        transition = history.transitions.find(rule => province(rule.province) === province(prov) && unit(rule.district) === unit(district) && unit(rule.oldCommune) === unit(commune));
        if (transition) rows = index.get([province(prov), unit(district), unit(transition.nextCommune)].join('|')) || [];
      }
      // Nhận diện địa chỉ đã theo hai cấp; không nhầm "Quận Ba Đình" với "Phường Ba Đình".
      const penultimate = parts[parts.length - 2] || '';
      const hasDistrict = /^(quan|huyen|thi xa|q|h|tx)\s/.test(normalize(penultimate));
      const explicitCommune = /^(phuong|xa|dac khu|p|x)\s/.test(normalize(penultimate));
      if (!rows.length && parts.length >= 2 && !hasDistrict && (parts.length === 2 || explicitCommune)) {
        const current = [...(currentIndex.get([province(parts[parts.length - 1]), unit(penultimate)].join('|'))?.values() || [])];
        if (current.length === 1) return {status: 'exact', kind: 'already-current', candidates: current, detail: parts.slice(0, -2).join(', '), reason: 'Địa chỉ đã khớp xã/phường và tỉnh/thành theo mô hình hai cấp trong bảng nguồn mốc 01/07/2025.'};
      }
      if (parts.length < 3) return {status: 'missing', candidates: [], reason: 'Chưa khớp địa chỉ hai cấp. Nếu dùng địa chỉ cũ, bổ sung đủ xã/phường, quận/huyện và tỉnh/thành cũ, phân cách bằng dấu phẩy.'};
      const grouped = new Map();
      for (const row of rows) {
        const code = row[2].padStart(5, '0');
        const key = row[0] + '|' + code;
        if (!grouped.has(key)) grouped.set(key, {province: row[0].replace(/\s*\(\d+\)\s*$/, ''), provinceCode: (row[0].match(/\((\d+)\)/) || [])[1] || '', commune: row[1], code, oldCode: row[4].padStart(5, '0'), changes: []});
        grouped.get(key).changes.push(row[5]);
      }
      const candidates = [...grouped.values()];
      const localityName = value => normalize(value).replace(/^thon\s+/, '');
      const localityRule = parts.length >= 4 ? history.localities.find(rule =>
        province(rule.province) === province(prov) && unit(rule.district) === unit(district) &&
        rule.oldCommunes.some(value => unit(value) === unit(commune)) &&
        parts.slice(0, -3).some(value => localityName(value) === localityName(rule.locality)) &&
        candidates.some(candidate => candidate.code === rule.newCode)) : null;
      const provenance = transition ? [transition.source] : [];
      if (localityRule) {
        return {status: 'exact', kind: 'locality-verified', detail,
          candidates: candidates.filter(candidate => candidate.code === localityRule.newCode),
          provenance: [...provenance, localityRule.source, localityRule.corroboration],
          reason: `${transition ? `Đã nối lịch sử ${transition.oldCommune} → ${transition.nextCommune} từ 01/01/2025. ` : ''}${localityRule.locality} được tài liệu chính thức xác nhận thuộc xã Tây Phương, thành phố Hà Nội. Đối chiếu theo thôn, không suy rộng toàn bộ xã Quang Trung.`};
      }
      const full = candidates.length === 1 && candidates[0].changes.every(v => normalize(v) === 'nhap toan bo');
      const prefix = transition ? `Đã nối lịch sử ${transition.oldCommune} → ${transition.nextCommune} từ 01/01/2025. ` : '';
      return {status: !candidates.length ? 'missing' : full ? 'exact' : 'review', candidates, detail, provenance, reason: prefix + (!candidates.length ? 'Chưa khớp địa chỉ trong bảng chuyển đổi hoặc dữ liệu lịch sử đã bổ sung. Cần kiểm tra tên đơn vị tại thời điểm cấp CCCD.' : full ? 'Khớp đủ ba cấp địa chỉ cũ; bảng NSO ghi nhận nhập toàn bộ vào một đơn vị mới.' : 'Đơn vị cũ có quan hệ nhập một phần hoặc nhiều đơn vị tiếp nhận. Cần xác minh thôn/tổ hoặc địa bàn cụ thể.')};
    };
  }
  root.CCCD = {parseQR, createMapper, normalize};
})(globalThis);
