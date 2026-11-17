(function(root){
  'use strict';
  const norm=value=>CCCD.normalize(value||'');
  const unit=value=>norm(value).replace(/^(thanh pho|tinh|quan|huyen|thi xa|phuong|xa|thi tran|dac khu|tp|q|p|h|tx|tt)\s+/,'');
  const locality=value=>norm(value).replace(/^(thon|xom|ap|ban|buon|bon|khom|to dan pho|khu pho|khu dan cu)\s+(so\s+)?/,'');
  const typedMatch=(a,b)=>{const type=v=>(norm(v).match(/^(phuong|xa|thi tran|dac khu)\s/)||[])[1];return unit(a)===unit(b)&&(!type(a)||!type(b)||type(a)===type(b));};
  function createMapper(baseMap,data){
    if(!data) return baseMap;
    const current=(commune,province)=>data.currentUnits.filter(r=>typedMatch(r.commune,commune)&&unit(r.province)===unit(province));
    const refs=trail=>[...new Set(trail.flatMap(r=>r.sourceIds))].map(id=>data.sources[id]).filter(Boolean);
    const usable=r=>r.status!=='plan_approved_effective_date_unknown';
    function proposals(address){
      const base=baseMap(address), parts=address.split(',').map(s=>s.trim()).filter(Boolean);
      if(parts.length<2) return base;
      const proposals=[], trails=[];
      const add=(candidate,detail,trail)=>{proposals.push({...candidate,detail,changes:['Wiki · chưa kiểm chứng',...trail.map(r=>r.scope==='whole'?'Toàn bộ':'Có phần địa giới')],researchUnverified:true,researchRelationIds:trail.map(r=>r.id)});trails.push(...trail);};
      if(base.status==='missing'&&parts.length>=3){
        const [commune,district,province]=parts.slice(-3), detail=parts.slice(0,-3).join(', ');
        const queue=[{commune,district,province,trail:[],date:''}],visited=new Set();
        for(let cursor=0;cursor<queue.length&&cursor<64;cursor++){
          const state=queue[cursor],key=[norm(state.commune),unit(state.district),unit(state.province),state.date].join('|');
          if(visited.has(key)||state.trail.length>=8)continue;visited.add(key);
          for(const row of data.communeTransitions){
            if(!usable(row)||!typedMatch(row.oldName,state.commune)||unit(row.province)!==unit(state.province))continue;
            if(unit(row.oldParent||row.district)!==unit(state.district))continue;
            if(row.effectiveDate&&row.effectiveDate<state.date)continue;
            const next={commune:row.newName,district:row.newParent||state.district,province:state.province,trail:[...state.trail,row],date:row.effectiveDate||state.date};
            const mapped=baseMap([detail,next.commune,next.district,next.province].filter(Boolean).join(', '));
            mapped.candidates.forEach(candidate=>add(candidate,detail,next.trail));
            queue.push(next);
          }
        }
      }
      // Cùng số tổ ở các phường khác nhau phải khớp cả xã/phường và tỉnh.
      for(const candidate of base.candidates){
        const detail=base.detail||'', tokens=detail.split(',').map(v=>v.trim()).filter(Boolean);
        for(const row of data.villageTransitions){
          if(!usable(row)||unit(row.province)!==unit(candidate.province)||!typedMatch(row.commune||row.newParent,candidate.commune))continue;
          const found=tokens.findIndex(t=>locality(t)===locality(row.oldName));
          if(found<0)continue;
          const units=current(candidate.commune,candidate.province);
          if(!units.some(r=>r.code===candidate.code))continue;
          const next=[...tokens];next[found]=row.newName;add(candidate,next.join(', '),[row]);
        }
      }
      if(!proposals.length)return base;
      const combined=base.candidates.map(r=>({...r,detail:base.detail||'',changes:[...r.changes,'Giữ theo bảng nguồn mốc 01/07/2025']})).concat(proposals);
      const unique=[...new Map(combined.map(r=>[[r.provinceCode,r.code,r.detail].join('|'),r])).values()];
      return {...base,status:'review',kind:'research-review',candidates:unique,
        provenance:[...(base.provenance||[]),...refs(trails)],researchRelationIds:[...new Set(trails.map(r=>r.id))],
        reason:'Có quan hệ lịch sử hoặc thay đổi thôn từ nguồn Wiki chưa được kiểm chứng độc lập. Chọn địa chỉ phù hợp, đọc nguồn và ghi căn cứ xác nhận; chưa tự điền một đích khi còn phần địa giới hoặc mốc thời gian chưa rõ.'};
    }
    return proposals;
  }
  root.HISTORY_RESEARCH={createMapper};
})(globalThis);
