(function () {
  'use strict';
  const el = id => document.getElementById('profile-' + id);
  let nameStatus = 'confirmed', emailStatus = 'unspecified';
  function birthValue() {
    const match = el('birth').value.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!match) return null;
    const [,d,m,y] = match, value = new Date(+y,+m-1,+d);
    return +y>=1900 && value.getFullYear()===+y && value.getMonth()===+m-1 && value.getDate()===+d && value<=new Date() ? value : null;
  }
  function updateAge() {
    const birth=birthValue(), today=new Date();
    if (!birth) { el('age').textContent='—'; return; }
    let age=today.getFullYear()-birth.getFullYear();
    if (today.getMonth()<birth.getMonth() || (today.getMonth()===birth.getMonth() && today.getDate()<birth.getDate())) age--;
    el('age').textContent=age+' y';
  }
  function setPressed(selector,attribute,value) {
    document.querySelectorAll(selector).forEach(button=>button.setAttribute('aria-pressed',String(button.getAttribute(attribute)===value)));
  }
  function reset() {
    el('form').reset(); el('extra-phones').replaceChildren(); nameStatus='confirmed';emailStatus='unspecified';
    setPressed('[data-name-status]','data-name-status',nameStatus);setPressed('[data-email-status]','data-email-status',emailStatus);
    el('email').hidden=true; el('age').textContent='—'; el('address-value').value='';
    el('document-number').value='';el('document-issued').value='';
  }
  function fill(value) {
    reset();
    const names=value.name.trim().split(/\s+/);
    el('first').value=names.pop()||'';el('last').value=names.shift()||'';el('middle').value=names.join(' ');
    el('sex').value=CCCD.normalize(value.sex)==='nam'?'Nam':'Nữ';el('birth').value=value.birthDate;
    el('document-number').value=value.id;el('document-issued').value=value.issueDate;
    el('origin').textContent='Đã điền từ QR: họ tên, ngày sinh, giới tính và giấy tờ. Kiểm tra cách tách họ/tên; số hồ sơ, điện thoại và thông tin cá nhân khác do người thao tác bổ sung.';
    updateAge();syncAddress();syncConfirm();
  }
  function syncAddress() {
    el('address-value').value=typeof selected!=='undefined' && selected ? document.getElementById('new-address').textContent : '';
  }
  function changed() { updateAge(); if (typeof person!=='undefined' && person) { invalidate();syncAddress();syncConfirm(); } }
  function snapshot() {
    const values={};document.querySelectorAll('#profile-form [data-profile]').forEach(input=>{if(input.id)values[input.id.replace('profile-','')]=input.type==='checkbox'?input.checked:input.value.trim();});
    return {fields:values,localFullName:[values.last,values.middle,values.first].filter(Boolean).join(' '),
      nameStatus,emailStatus,extraPhones:[...el('extra-phones').querySelectorAll('input')].map(input=>input.value.trim()).filter(Boolean),
      address:el('address-value').value,origin:'QR fields plus operator-entered profile; original QR preserved separately'};
  }
  function validationMessage() {
    if (!el('first').value.trim() && !el('last').value.trim()) return 'Kiểm tra Name (Local) trong Patient Profile.';
    if (!birthValue()) return 'Date of Birth trong Patient Profile cần là ngày hợp lệ dạng DD/MM/YYYY.';
    if (!el('sex').value) return 'Chọn Sex trong Patient Profile.';
    if (emailStatus==='provided' && el('email').value && !el('email').checkValidity()) return 'Email trong Patient Profile chưa hợp lệ.';
    return '';
  }
  document.querySelectorAll('[role=tab][id^=tab-]').forEach((button,index,tabs)=>{
    button.addEventListener('click',()=>tabs.forEach(tab=>{const active=tab===button;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;document.getElementById(tab.getAttribute('aria-controls')).hidden=!active;}));
    button.addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight'].includes(event.key)){event.preventDefault();const next=tabs[(index+(event.key==='ArrowRight'?1:tabs.length-1))%tabs.length];next.click();next.focus();}});
  });
  document.querySelectorAll('[data-toggle-profile]').forEach(button=>button.addEventListener('click',()=>{const target=document.getElementById(button.dataset.toggleProfile);target.hidden=!target.hidden;button.setAttribute('aria-expanded',String(!target.hidden));button.textContent=target.hidden?'+':'−';}));
  document.querySelectorAll('[data-name-status]').forEach(button=>button.addEventListener('click',()=>{nameStatus=button.dataset.nameStatus;setPressed('[data-name-status]','data-name-status',nameStatus);changed();}));
  document.querySelectorAll('[data-email-status]').forEach(button=>button.addEventListener('click',()=>{emailStatus=button.dataset.emailStatus;el('email').hidden=emailStatus!=='provided';if(emailStatus!=='provided')el('email').value='';setPressed('[data-email-status]','data-email-status',emailStatus);changed();}));
  el('add-phone').addEventListener('click',()=>{const row=document.createElement('div');row.className='profile-phone-extra';const input=document.createElement('input');input.type='tel';input.autocomplete='off';input.setAttribute('aria-label','Số điện thoại bổ sung');const remove=document.createElement('button');remove.type='button';remove.textContent='−';remove.setAttribute('aria-label','Xóa số điện thoại bổ sung');remove.onclick=()=>{row.remove();changed();};row.append(input,remove);el('extra-phones').append(row);input.focus();changed();});
  el('edit-address').addEventListener('click',()=>{const target=document.querySelector('.address-edit');if(target){target.open=true;document.getElementById('address-input').focus();}});
  el('form').addEventListener('submit',event=>event.preventDefault());el('form').addEventListener('input',changed);el('form').addEventListener('change',changed);
  document.addEventListener('cccd:read',event=>fill(CCCD.parseQR(event.detail.payload)));
  document.addEventListener('cccd:mapped',syncAddress);
  document.addEventListener('cccd:reset',reset);
  document.addEventListener('cccd:clear',()=>{if(typeof person==='undefined'||!person)reset();else if(!selected)el('address-value').value='';});
  globalThis.PATIENT_PROFILE={snapshot,validationMessage};
})();
