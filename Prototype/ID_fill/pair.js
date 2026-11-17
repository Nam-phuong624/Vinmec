'use strict';
(function () {
  const el = id => document.getElementById(id);
  const onPhone = new URLSearchParams(location.search).get('phone') === '1';
  let owner = null, sender = null, pending = null, pollTimer = null, senderExpiryTimer = null, revision = 0, sending = false;
  async function api(path, {method = 'GET', token, body, keepalive = false} = {}) {
    const headers = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    if (body) headers['Content-Type'] = 'application/json';
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 10000);
    let response;
    try { response = await fetch(path, {method, headers, body: body ? JSON.stringify(body) : undefined, cache: 'no-store', keepalive, signal: controller.signal}); }
    finally { clearTimeout(timeout); }
    let result;
    try { result = await response.json(); } catch { throw new Error('Cần dừng server cũ và chạy lại start-demo.cmd để dùng ghép điện thoại.'); }
    if (!response.ok) { const error = new Error(result.error || 'Chưa kết nối được máy tính.'); error.status = response.status; throw error; }
    return result;
  }
  function status(id, message, error = false) {
    el(id).textContent = message; el(id).classList.toggle('error', error);
  }
  function closePair(unloading = false) {
    revision++; clearTimeout(pollTimer);
    const old = owner; owner = null;
    el('pair-session').hidden = true; el('pair-code').textContent = ''; el('phone-link').textContent = ''; el('phone-link').removeAttribute('href');
    el('pair-qr').getContext('2d').clearRect(0, 0, 250, 250);
    if (old) api(`/api/pair/${old.id}/close`, {method: 'POST', token: old.ownerToken, body: {}, keepalive: unloading}).catch(() => {});
  }
  function drawLink() {
    if (!owner) return;
    const base = el('phone-network').value;
    const link = new URL(base); link.hash = `join=${encodeURIComponent(owner.joinToken)}`;
    drawQR('pair-qr', link.href);
    // Link thủ công không chứa token; QR chứa token trong fragment, không gửi vào log HTTP.
    el('phone-link').href = base; el('phone-link').textContent = base;
  }
  function drawQR(id, text) {
    const qr = qrcode(0, 'M'); qr.addData(text); qr.make();
    const canvas = el(id), context = canvas.getContext('2d');
    const cells = qr.getModuleCount(), quiet = 4, size = Math.floor(250 / (cells + 2 * quiet));
    canvas.width = canvas.height = (cells + 2 * quiet) * size;
    context.fillStyle = 'white'; context.fillRect(0, 0, canvas.width, canvas.height); context.fillStyle = '#142e39';
    for (let row = 0; row < cells; row++) for (let col = 0; col < cells; col++) if (qr.isDark(row, col)) context.fillRect((col + quiet) * size, (row + quiet) * size, size, size);
  }
  async function poll(ticket) {
    if (!owner || ticket !== revision) return;
    try {
      const current = owner;
      const result = await api(`/api/pair/${current.id}/result`, {token: current.ownerToken});
      if (ticket !== revision || owner !== current) return;
      if (result.status === 'received') {
        if (result.continuous) {
          if (current.sequence !== result.sequence) {
            current.success = readPayload(result.payload, result.sample === true);
            current.sequence = result.sequence;
          }
          await api(`/api/pair/${current.id}/ack`, {method: 'POST', token: current.ownerToken, body: {sequence: result.sequence}});
          status('pair-status', current.success ? '✓ Đã nhận QR. Điện thoại vẫn kết nối, sẵn sàng quét thẻ tiếp theo.' : 'Đã nhận QR nhưng chưa đọc được thông tin.', !current.success);
          pollTimer = setTimeout(() => poll(ticket), 500);
          return;
        }
        if (!current.received) {
          current.success = readPayload(result.payload, result.sample === true);
          current.received = true;
        }
        try { await api(`/api/pair/${current.id}/close`, {method: 'POST', token: current.ownerToken, body: {}}); }
        catch (error) { if (error.status !== 410) throw error; }
        if (ticket !== revision) return;
        const success = current.success;
        owner = null;
        closePair();
        status('pair-status', success ? '✓ Đã nhận QR từ điện thoại và đối chiếu địa chỉ. Kiểm tra thông tin ở bên phải.' : 'Đã nhận chuỗi QR nhưng chưa đọc được thông tin. Xem thông báo ở phần quét.', !success);
        return;
      }
      status('pair-status', `${result.status === 'paired' ? 'Điện thoại đã ghép. Đang chờ QR từ điện thoại.' : 'Đang chờ điện thoại ghép nối.'} Còn ${Math.ceil(result.expiresIn / 60)} phút.`);
      pollTimer = setTimeout(() => poll(ticket), 1000);
    } catch (error) {
      if (ticket !== revision) return;
      if ([403, 410].includes(error.status)) { closePair(); status('pair-status', error.message, true); }
      else { status('pair-status', 'Chưa liên lạc được với server. Đang thử lại…', true); pollTimer = setTimeout(() => poll(ticket), 2500); }
    }
  }
  el('create-pair').addEventListener('click', async () => {
    closePair(); const ticket = revision; el('create-pair').disabled = true;
    try {
      const network = await api('/api/network');
      if (ticket !== revision) return;
      if (!network.phoneUrls.length) throw new Error('Chưa tìm thấy địa chỉ Wi-Fi. Kết nối máy tính vào Wi-Fi rồi chạy lại start-demo.cmd.');
      el('phone-network').replaceChildren(...network.phoneUrls.map(url => new Option(url, url)));
      const created = await api('/api/pair', {method: 'POST', body: {continuous: true}});
      if (ticket !== revision) { api(`/api/pair/${created.id}/close`, {method: 'POST', token: created.ownerToken, body: {}}).catch(() => {}); return; }
      owner = created; el('pair-code').textContent = created.code.replace(/(\d{4})(\d{4})/, '$1 $2');
      drawLink(); el('pair-session').hidden = false;
      status('pair-status', 'Dùng điện thoại cùng Wi-Fi mở mã QR, hoặc nhập đường dẫn và mã ghép.');
      poll(ticket);
    } catch (error) { if (ticket === revision) status('pair-status', error.message, true); }
    finally { el('create-pair').disabled = false; }
  });
  el('phone-network').addEventListener('change', drawLink);
  el('cancel-pair').addEventListener('click', () => { closePair(); status('pair-status', 'Đã hủy. Mã cũ không còn nhận thông tin.'); });
  document.addEventListener('cccd:reset', () => {
    if (!onPhone) { status('pair-status', owner ? 'Điện thoại vẫn kết nối, sẵn sàng nhận lượt quét mới.' : ''); }
    else { pending = null; el('send-phone').disabled = true; }
  });
  window.addEventListener('pagehide', () => closePair(true));
  if (!onPhone) return;
  document.body.classList.add('phone-mode');
  el('desktop-pair').hidden = true; el('mobile-pair').hidden = false;
  document.querySelector('h1').textContent = 'Gửi thông tin từ ảnh CCCD';
  document.querySelector('.intro p:not(.eyebrow)').textContent = 'Chụp hoặc chọn ảnh, kiểm tra thông tin rồi gửi về máy tính.';
  el('mobile-transport').textContent = 'Điện thoại và máy tính cùng Wi-Fi. Không cần cài chứng chỉ. Ảnh được xử lý ngay trên điện thoại.';
  async function join(joinToken) {
    el('join-pair').disabled = true;
    try {
      const code = el('join-code').value.replace(/\s/g, '');
      if (!joinToken && !/^\d{8}$/.test(code)) throw new Error('Nhập đủ 8 chữ số trên màn hình máy tính.');
      sender = await api('/api/join', {method: 'POST', body: joinToken ? {joinToken} : {code}});
      clearTimeout(senderExpiryTimer);
      senderExpiryTimer = setTimeout(() => {
        sender = null; pending = null;
        el('send-phone').disabled = true;
        el('phone-connected').hidden = true; el('phone-join').hidden = false;
        status('phone-status', 'Phiên 10 phút đã hết hạn. Tạo mã mới trên máy tính để kết nối lại.', true);
      }, sender.expiresIn * 1000);
      el('phone-join').hidden = true; el('phone-connected').hidden = false;
      el('send-phone').disabled = !pending;
      status('phone-status', 'Đã kết nối. Chụp ảnh CCCD hoặc chọn ảnh có sẵn, kiểm tra kết quả rồi bấm gửi.');
    } catch (error) { status('phone-status', error.message, true); }
    finally { el('join-pair').disabled = false; }
  }
  el('join-pair').addEventListener('click', () => join());
  el('phone-photo').addEventListener('click', () => el('phone-photo-file').click());
  el('phone-gallery').addEventListener('click', () => el('phone-gallery-file').click());
  el('phone-gallery-file').addEventListener('change', async event => {
    await readImageFile(event.target.files[0]); event.target.value = '';
  });
  el('phone-photo-file').addEventListener('change', async event => {
    await readImageFile(event.target.files[0]); event.target.value = '';
  });
  document.addEventListener('cccd:read', event => {
    if (sending) return;
    pending = {payload: event.detail.payload, sample: event.detail.sample, requestId: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`}; el('send-phone').disabled = !sender || sending;
    if (sender) status('phone-status', 'Đã đọc thông tin. Kiểm tra họ tên, số CCCD và địa chỉ bên dưới trước khi gửi.');
  });
  document.addEventListener('cccd:clear', () => { if (!sending) { pending = null; } el('send-phone').disabled = true; });
  async function sendToDesktop() {
    if (!sender || !pending || sending) return;
    sending = true;
    el('phone-photo').disabled = true; el('phone-gallery').disabled = true; el('upload').disabled = true;
    el('send-phone').disabled = true;
    try {
      for (let attempt = 0; ; attempt++) {
        try { await api(`/api/pair/${sender.id}/send`, {method: 'POST', token: sender.senderToken, body: pending}); break; }
        catch (error) {
          if (error.status !== 409 || attempt >= 9) throw error;
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
      pending = null;
      el('reset').click();
      navigator.vibrate?.(100);
      status('phone-status', '✓ Đã gửi sang máy tính. Bạn có thể chụp hoặc chọn ảnh tiếp theo trong cùng phiên.');
    } catch (error) {
      if ([403, 410].includes(error.status)) {
        sender = null;
        el('phone-connected').hidden = true; el('phone-join').hidden = false;
      }
      status('phone-status', error.message, true); el('send-phone').disabled = !sender || !pending;
    }
    finally { sending = false; el('phone-photo').disabled = false; el('phone-gallery').disabled = false; el('upload').disabled = false; }
  }
  el('send-phone').addEventListener('click', () => sendToDesktop());
  const token = new URLSearchParams(location.hash.slice(1)).get('join');
  if (token) { history.replaceState(null, '', location.pathname + location.search); join(token); }
})();
