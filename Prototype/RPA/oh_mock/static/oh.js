const $ = id => document.getElementById(id);
let saved = null, draft = null, revision = 0, locked = false, loading = false;
const viewId = crypto.randomUUID();
const clone = value => JSON.parse(JSON.stringify(value));
const textAddress = value => [value.street, value.ward, value.province].filter(Boolean).join(', ');
function message(text, kind='') { $('message').textContent=text; $('message').className=kind; }
function touch() { revision++; $('save-state').textContent='Có thay đổi chưa lưu'; }
function setLock(value) {
  locked=value; document.body.classList.toggle('locked',value);
  for (const id of ['pid-input','open-record','cancel','save']) $(id).disabled=value;
  $('lock-record').textContent=value?'Kết thúc khóa hồ sơ':'Khóa hồ sơ để điền';
  $('save-state').textContent=value?'Đang điền · tạm khóa chuyển hồ sơ':'Kiểm tra thông tin trước khi lưu';
}
function paint() {
  $('empty').hidden=true; $('profile').hidden=false;
  for(const key of ['pid','name','dob','sex','company','batch']) {
    if(key==='pid') $(key).textContent=draft[key];
    else $(key).value=key==='dob'?draft[key].split('-').reverse().join('/'):draft[key];
  }
  $('national-id').value=draft.national_id;
  $('summary-name').textContent=draft.name; $('summary-company').textContent=draft.company+' · '+draft.batch;
  $('address-summary').textContent=textAddress(draft.address);
  $('save-state').textContent='Chưa có thay đổi';
  sessionStorage.setItem('oh-pid',draft.pid);
}
window.ohSnapshot = () => draft ? {record:clone({...draft,national_id:$('national-id').value}),
  saved:clone(saved),revision,viewId,locked,loading,dialogOpen:$('address-dialog').open} : null;
$('lookup').addEventListener('submit', async event => {
  event.preventDefault(); if(locked||loading) return;
  const pid=$('pid-input').value.trim(); if(!pid) return message('Cần nhập PID.','error');
  loading=true; $('open-record').disabled=true; message('Đang mở hồ sơ…');
  saved=null;draft=null;$('profile').hidden=true;$('empty').hidden=false;
  try {
    const response=await fetch('/api/patients/'+encodeURIComponent(pid)); const body=await response.json();
    if(!response.ok) { saved=null; draft=null; $('profile').hidden=true; $('empty').hidden=false; throw Error(body.error); }
    saved=body; draft=clone(body); revision++; paint(); message('Đã mở hồ sơ '+pid+'. Kiểm tra danh tính trước khi cập nhật.');
  } catch(error) { message(error.message||'Không kết nối được OH.','error'); }
  finally {loading=false; $('open-record').disabled=false;}
});
$('national-id').addEventListener('input',()=>{draft.national_id=$('national-id').value;touch();});
$('edit-address').onclick=()=>{
  if(!draft||loading) return;
  for(const key of ['province','ward','street']) $(key).value=draft.address[key];
  preview(); $('address-dialog').showModal();
};
function preview() { $('address-preview').textContent=textAddress(Object.fromEntries(['province','ward','street'].map(k=>[k,$(k).value]))); }
for(const key of ['province','ward','street']) $(key).addEventListener('input',()=>{revision++;preview();});
$('close-address').onclick=()=>{$('address-dialog').close();};
$('address-form').onsubmit=event=>{
  event.preventDefault();
  draft.address=Object.fromEntries(['province','ward','street'].map(k=>[k,$(k).value.trim()]));
  $('address-summary').textContent=textAddress(draft.address); touch(); $('address-dialog').close();
};
$('lock-record').onclick=()=>{if(draft&&!loading&&!$('address-dialog').open)setLock(!locked);};
$('cancel').onclick=()=>{if(locked||loading)return;draft=clone(saved);revision++;paint();message('Đã hủy thay đổi chưa lưu.');};
$('save').onclick=async()=>{
  if(locked||loading||!draft)return;
  const pid=draft.pid; loading=true; $('save').disabled=true; $('open-record').disabled=true; $('cancel').disabled=true; $('lock-record').disabled=true;
  message('Đang lưu hồ sơ…');
  try {
    const response=await fetch('/api/patients/'+encodeURIComponent(pid),{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...draft,national_id:$('national-id').value})});
    const body=await response.json();if(!response.ok)throw Error(body.error);
    saved=body;draft=clone(body);revision++;paint();$('save-state').textContent='Đã lưu · phiên bản '+body.version;
    message('Đã lưu hồ sơ '+pid+' thành công.','success');
  } catch(error) {message(error.message||'Lưu thất bại. Dữ liệu chưa được xác nhận lưu.','error');}
  finally{loading=false;for(const id of ['save','open-record','cancel','lock-record'])$(id).disabled=false;}
};
// Keep the same patient open on reload so a verified save can be read back.
const last=sessionStorage.getItem('oh-pid');
if(last){$('pid-input').value=last;$('lookup').requestSubmit();}
