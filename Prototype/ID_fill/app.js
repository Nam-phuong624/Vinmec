'use strict';
const $ = id => document.getElementById(id);
const mapAddress = HISTORY_RESEARCH.createMapper(CCCD.createMapper(ADDRESS_DATA.records), ADDRESS_RESEARCH);
let person = null, mapping = null, selected = null, generation = 0, confirmed = false, isSample = false, receipt = null;
const samples = {
  exact: '000000000001||NGƯỜI BỆNH MẪU A|01011990|Nam|Số 01 phố minh họa, Phường Trúc Bạch, Quận Ba Đình, Thành phố Hà Nội|01012021',
  partial: '000000000002||NGƯỜI BỆNH MẪU B|02021992|Nữ|Số 02 phố minh họa, Phường Ngọc Hà, Quận Ba Đình, Thành phố Hà Nội|02022022',
  missing: '000000000003||NGƯỜI BỆNH MẪU C|03031993|Nam|Quận Ba Đình, Thành phố Hà Nội|03032023',
  historical: '000000000004||NGƯỜI BỆNH MẪU D|01011990|Nam|Bình Xá, Bình Phú, Thạch Thất, Hà Nội|01012021'
};
$('data-summary').textContent = `${ADDRESS_DATA.records.length.toLocaleString('vi-VN')} quan hệ chuyển đổi · Tải ngày 10/11/2026 · Ánh xạ mốc 01/07/2025`;
function scanStatus(message, error = false) { $('scan-status').textContent = message; $('scan-status').classList.toggle('error', error); }
function invalidate() {
  document.dispatchEvent(new Event('cccd:clear'));
  confirmed = false; receipt = null;
  $('confirm').disabled = true;
  $('export').hidden = true;
  $('confirmation').textContent = '';
  $('verified').checked = false;
  $('step3').classList.remove('active');
}
function syncConfirm() {
  let reason = '';
  if (confirmed) reason = 'Đã xác nhận. Bạn có thể tải phiếu JSON.';
  else if (!person || !mapping) reason = 'Cần đọc được thông tin CCCD trước khi xác nhận.';
  else if (!selected) reason = mapping.status === 'review'
    ? 'Chọn xã/phường mới trong danh sách phía trên trước khi xác nhận.'
    : 'Chưa có địa chỉ mới để xác nhận. Bổ sung hoặc sửa địa chỉ rồi bấm “Đối chiếu lại”.';
  else if (mapping.status === 'review' && !$('review-note').value.trim()) reason = 'Điền “Căn cứ xác nhận địa bàn” vì địa chỉ có sáp nhập một phần hoặc nhiều nơi nhận.';
  else if (!$('verified').checked) reason = 'Tích ô “Tôi đã kiểm tra thông tin với người bệnh và xác nhận địa chỉ mới” để bật nút.';
  if (!reason && globalThis.PATIENT_PROFILE) reason = PATIENT_PROFILE.validationMessage();
  $('confirm').disabled = !!reason;
  $('confirm-help').textContent = reason || 'Đã đủ điều kiện. Bấm “Xác nhận thông tin” để hoàn tất.';
}
function renderSelected() {
  $('mapped-address').hidden = !selected;
  if (selected) {
    $('new-address').textContent = [selected.detail ?? mapping.detail, selected.commune, selected.province].filter(Boolean).join(', ');
    $('new-code').textContent = `Mã xã/phường: ${selected.code} · Mã tỉnh/thành: ${selected.provinceCode || 'chưa có'}`;
  }
  document.dispatchEvent(new Event('cccd:mapped'));
  syncConfirm();
}
function renderMapping() {
  selected = null;
  invalidate();
  $('review-note').value = '';
  mapping = mapAddress($('address-input').value.trim());
  const labels = {exact: 'Đã đối chiếu', review: 'Cần xác minh', missing: 'Chưa ánh xạ'};
  $('result-badge').textContent = labels[mapping.status];
  $('result-badge').className = 'badge ' + (mapping.status === 'exact' ? 'good' : 'warn');
  $('mapping-status').textContent = mapping.reason;
  $('mapping-status').className = 'mapping-status ' + mapping.status;
  $('mapping-evidence').replaceChildren();
  for (const source of mapping.provenance || []) {
    const link = document.createElement('a');
    link.textContent = source.title; link.href = source.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
    const line = document.createElement('p'); line.append(link); $('mapping-evidence').append(line);
  }
  $('candidates').replaceChildren();
  $('manual-review').hidden = mapping.status !== 'review';
  if (mapping.status === 'exact') selected = mapping.candidates[0];
  if (mapping.status === 'review') {
    for (const candidate of mapping.candidates) {
      const label = document.createElement('label'); label.className = 'candidate';
      const radio = document.createElement('input'); radio.type = 'radio'; radio.name = 'candidate'; radio.value = candidate.code;
      const content = document.createElement('span'), title = document.createElement('strong'), info = document.createElement('small');
      title.textContent = [candidate.detail, candidate.commune, candidate.province].filter(Boolean).join(', ');
      info.textContent = `Mã ${candidate.code} · ${[...new Set(candidate.changes)].join(', ')}`;
      content.append(title, info); label.append(radio, content); $('candidates').append(label);
      radio.addEventListener('change', () => { invalidate(); selected = candidate; renderSelected(); });
    }
  }
  renderSelected();
  $('step2').classList.add('active');
}
function readPayload(raw, sample = false, source = 'input') {
  try {
    const next = CCCD.parseQR(raw);
    generation++;
    person = next; isSample = sample;
    $('payload').value = raw.trim();
    $('empty').hidden = true; $('result').hidden = false;
    const fields = {'person-name': person.name, 'person-id': person.id, 'person-birth': person.birthDate, 'person-sex': person.sex, 'person-issued': person.issueDate, 'person-old-id': person.oldId || 'Không có', 'old-address': person.address};
    for (const [id, value] of Object.entries(fields)) $(id).textContent = value;
    $('initials').textContent = person.name.split(/\s+/).slice(-2).map(s => s[0]).join('');
    $('person-label').textContent = sample ? 'DỮ LIỆU GIẢ LẬP · Không phải hồ sơ thật' : 'Thông tin đọc từ mã QR · Chưa xác thực danh tính';
    $('address-input').value = person.address;
    renderMapping();
    scanStatus(sample ? 'Đã đọc mẫu giả lập. Bạn có thể thử tiếp bằng mã QR thật.' : 'Đã đọc mã QR. Vui lòng kiểm tra thông tin ở bên phải.');
    document.dispatchEvent(new CustomEvent('cccd:read', {detail: {payload: raw.trim(), sample, source}}));
    return true;
  } catch (error) {
    // Không cho xác nhận kết quả cũ sau một lượt quét bị lỗi.
    person = null; mapping = null; selected = null;
    invalidate(); $('empty').hidden = false; $('result').hidden = true;
    $('step2').classList.remove('active');
    scanStatus(error.message, true); return false;
  }
}
function decodeFallback(pixels) {
  if (!globalThis.ZXing) return null;
  const gray = new Uint8ClampedArray(pixels.width * pixels.height);
  const histogram = new Uint32Array(256);
  for (let i = 0; i < gray.length; i++) {
    const offset = i * 4;
    gray[i] = (pixels.data[offset] + 2 * pixels.data[offset + 1] + pixels.data[offset + 2]) / 4;
    histogram[gray[i]]++;
  }
  const hints = new Map([[ZXing.DecodeHintType.TRY_HARDER, true], [ZXing.DecodeHintType.CHARACTER_SET, 'UTF-8']]);
  function attempt(values) {
    const source = new ZXing.RGBLuminanceSource(values, pixels.width, pixels.height);
    for (const input of [source, source.invert()]) {
      try {
        const result = new ZXing.QRCodeReader().decode(new ZXing.BinaryBitmap(new ZXing.HybridBinarizer(input)), hints);
        return {data: result.getText()};
      } catch { /* Không nhận diện được trên biến thể này; thử biến thể tiếp theo. */ }
    }
    return null;
  }
  const found = attempt(gray);
  if (found) return found;
  let low = 0, high = 255, count = 0;
  const threshold = gray.length * .01;
  while (low < 255 && count + histogram[low] < threshold) count += histogram[low++];
  count = 0;
  while (high > low && count + histogram[high] < threshold) count += histogram[high--];
  if (high - low < 8) return null;
  const contrast = new Uint8ClampedArray(gray.length);
  for (let i = 0; i < gray.length; i++) contrast[i] = (gray[i] - low) * 255 / (high - low);
  return attempt(contrast);
}
function decode(source, width, height, region = {x: 0, y: 0, width, height}, limit = 1400, fallback = false) {
  const scale = Math.min(1, limit / Math.max(region.width, region.height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.round(region.width * scale)); canvas.height = Math.max(1, Math.round(region.height * scale));
  const context = canvas.getContext('2d', {willReadFrequently: true});
  context.fillStyle = 'white'; context.fillRect(0, 0, canvas.width, canvas.height);
  context.drawImage(source, region.x, region.y, region.width, region.height, 0, 0, canvas.width, canvas.height);
  const pixels = context.getImageData(0, 0, canvas.width, canvas.height);
  return jsQR(pixels.data, pixels.width, pixels.height, {inversionAttempts: 'attemptBoth'}) || (fallback ? decodeFallback(pixels) : null);
}
async function decodeCardPhoto(img, token) {
  const width = img.naturalWidth, height = img.naturalHeight;
  // Các vùng chồng lấn giúp giữ độ phân giải QR nhỏ trên ảnh toàn thẻ,
  // đồng thời tránh cắt mã nằm ở ranh giới giữa các vùng.
  const attempts = [{x: 0, y: 0, width, height}];
  for (const y of [0, .225, .45]) {
    for (const x of [.45, .225, 0]) attempts.push({x: width * x, y: height * y, width: width * .55, height: height * .55});
  }
  for (let i = 0; i < attempts.length; i++) {
    await new Promise(resolve => setTimeout(resolve, 0));
    if (token !== generation) return null;
    scanStatus(i === 0 ? 'Đang tìm mã QR trên ảnh CCCD…' : `Đang kiểm tra vùng ảnh ${i}/${attempts.length - 1}…`);
    const code = decode(img, width, height, attempts[i], 1400, true);
    if (code) return code;
  }
  await new Promise(resolve => setTimeout(resolve, 0));
  if (token !== generation) return null;
  return decode(img, width, height, {x: 0, y: 0, width, height}, 2400, true);
}
$('upload').addEventListener('click', () => $('image-file').click());
async function readImageFile(file) {
  if (!file) return;
  generation++;
  const token = generation;
  person = null; mapping = null; selected = null; invalidate();
  $('result').hidden = true; $('empty').hidden = false; $('step2').classList.remove('active');
  $('result-badge').textContent = 'Đang đọc ảnh'; $('result-badge').className = 'badge neutral';
  $('upload').disabled = true;
  const url = URL.createObjectURL(file);
  try {
    if (file.size > 25 * 1024 * 1024) throw new Error('Ảnh quá lớn. Chọn ảnh CCCD dưới 25 MB.');
    scanStatus('Đang mở ảnh CCCD…');
    const img = new Image(); img.src = url;
    try { await img.decode(); } catch { throw new Error('Không mở được ảnh. Hãy đổi sang JPG, PNG hoặc WebP rồi chọn lại.'); }
    if (token !== generation) return;
    if (img.naturalWidth * img.naturalHeight > 80000000) throw new Error('Ảnh có độ phân giải quá lớn. Giảm kích thước hoặc cắt sát thẻ CCCD rồi thử lại.');
    const code = await decodeCardPhoto(img, token);
    if (token !== generation) return;
    if (!code) throw new Error('Chưa đọc được mã QR trên ảnh CCCD. Chọn đúng mặt thẻ có mã QR; chụp gần hơn, tránh mờ/lóa hoặc cắt ảnh sát mã QR.');
    if (readPayload(code.data)) scanStatus('Đã đọc thông tin từ mã QR trên ảnh CCCD và đối chiếu địa chỉ. Vui lòng kiểm tra kết quả.');
  } catch (error) { if (token === generation) { person = null; selected = null; invalidate(); $('result').hidden = true; $('empty').hidden = false; $('step2').classList.remove('active'); $('result-badge').textContent = 'Chưa đọc được'; scanStatus(error.message || 'Không đọc được ảnh CCCD.', true); } }
  finally { URL.revokeObjectURL(url); $('image-file').value = ''; $('upload').disabled = false; }
}
$('image-file').addEventListener('change', event => readImageFile(event.target.files[0]));
$('parse').addEventListener('click', () => readPayload($('payload').value));
$('payload').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); readPayload($('payload').value); } });
document.querySelectorAll('[data-sample]').forEach(button => button.addEventListener('click', () => readPayload(samples[button.dataset.sample], true)));
$('remap').addEventListener('click', () => { if (person) renderMapping(); });
$('address-input').addEventListener('input', () => { selected = null; invalidate(); $('mapped-address').hidden = true; $('candidates').replaceChildren(); $('mapping-status').textContent = 'Địa chỉ đã thay đổi. Bấm “Đối chiếu lại” để cập nhật kết quả.'; $('result-badge').textContent = 'Chờ đối chiếu'; syncConfirm(); });
$('verified').addEventListener('change', () => { if (confirmed) invalidate(); syncConfirm(); });
$('review-note').addEventListener('input', () => { if (confirmed) invalidate(); syncConfirm(); });
$('confirm').addEventListener('click', () => {
  syncConfirm();
  if ($('confirm').disabled) return;
  confirmed = true; $('confirm').disabled = true; $('export').hidden = false;
  $('step3').classList.add('active'); $('result-badge').textContent = 'Đã xác nhận'; $('result-badge').className = 'badge good';
  receipt = {demo: true, syntheticPerson: isSample, confirmedAt: new Date().toISOString(), person: {...person}, lookupAddress: $('address-input').value.trim(), newAddress: $('new-address').textContent, newCommuneCode: selected.code, newProvinceCode: selected.provinceCode, mappingStatus: mapping.status, mappingKind: mapping.kind || 'converted', mappingEvidence: mapping.provenance || [], reviewNote: $('review-note').value.trim(), confirmedByOperator: true, source: {url: ADDRESS_DATA.source, effectiveFrom: ADDRESS_DATA.effectiveFrom, retrievedAt: ADDRESS_DATA.retrievedAt, sha256: ADDRESS_DATA.sha256}};
  if (globalThis.PATIENT_PROFILE) receipt.patientProfile = PATIENT_PROFILE.snapshot();
  receipt.researchRelationIds = selected.researchRelationIds || [];
  $('confirmation').textContent = '✓ Đã xác nhận trong phiên demo. Bạn có thể tải phiếu JSON để xem dữ liệu bàn giao cho hệ thống tiếp nhận.';
  syncConfirm();
});
$('export').addEventListener('click', () => {
  if (!receipt || !confirmed) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(receipt, null, 2)], {type: 'application/json;charset=utf-8'}));
  const link = document.createElement('a'); link.href = url; link.download = 'phieu-tiep-nhan-demo.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$('reset').addEventListener('click', () => {
  document.dispatchEvent(new Event('cccd:reset'));
  generation++; invalidate(); person = null; mapping = null; selected = null; isSample = false;
  $('payload').value = ''; $('address-input').value = ''; $('review-note').value = ''; $('old-address').textContent = ''; $('new-address').textContent = ''; $('new-code').textContent = '';
  for (const id of ['person-name', 'person-id', 'person-birth', 'person-sex', 'person-issued', 'person-old-id', 'initials', 'person-label']) $(id).textContent = '';
  $('result').hidden = true; $('empty').hidden = false; $('mapped-address').hidden = true;
  $('candidates').replaceChildren(); $('step2').classList.remove('active');
  $('result-badge').textContent = 'Chờ quét'; $('result-badge').className = 'badge neutral';
  scanStatus('Đã xóa thông tin trong phiên. Sẵn sàng quét thẻ tiếp theo.');
});
