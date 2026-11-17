"""Đóng gói dữ liệu nghiên cứu công khai, giữ riêng với history.js đã xác minh."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--data-root',type=Path,default=ROOT.parent/'Data')
args=parser.parse_args()
data_root=args.data_root.resolve()
folder=data_root/'16-11-2026/crawl_dvhc/normalized/wiki_districts/structured_changes'
sources={}


def source_id(item):
    value={'title':'Wiki · '+item.get('source_locator','đoạn nguồn'),'url':item['source_url'],
           'quote':item.get('text',''),'locator':item.get('source_locator'),
           'revision':item.get('revision_id'),'sha256':item.get('source_sha256')}
    key=hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:24]
    sources[key]=value
    return key


def load(name):
    file=folder/(name+'.jsonl')
    rows=[json.loads(s) for s in file.read_text(encoding='utf-8').splitlines()]
    return [{'id':r['relation_id'],'eventId':r['event_id'],'province':r['province_name'],'district':r.get('district_name',''),
             'commune':r.get('commune_name'),'oldName':r['old_name'],'newName':r['new_name'],
             'oldParent':r.get('old_parent'),'newParent':r.get('new_parent'),'type':r['event_type'],'scope':r['scope'],
             'effectiveDate':r.get('effective_date'),'reportedDate':r.get('reported_date'),'dateBasis':r.get('date_basis'),
             'requiresLocationDetail':r.get('requires_location_detail',r['scope']!='whole'),
             'status':r.get('implementation_status','wiki_reports_change_not_independently_verified'),
             'reviewStatus':r['review_status'],'notes':r.get('notes',''),
             'sourceIds':[source_id(s) for s in r['sources']]} for r in rows]


communes=load('commune_changes')
villages=load('subcommune_changes')
snapshot=data_root/'16-11-2026/crawl_dvhc/normalized/snapshots/2026-11-16_DanhMucPhuongXa.json'
registry=json.loads(snapshot.read_text(encoding='utf-8'))
catalog=[{'commune':' '.join(r['TenPhuongXa'].split()),'province':' '.join(r['TenTinh'].split()),
          'code':r['MaPhuongXa'],'provinceCode':r['MaTinh']} for r in registry['rows']]
assert len(catalog)==3321 and all(r['code'].isdigit() and len(r['code'])==5 for r in catalog)
manifest={name:hashlib.sha256((folder/(name+'.jsonl')).read_bytes()).hexdigest() for name in ['commune_changes','subcommune_changes']}
data={'version':1,'builtAt':datetime.now(timezone.utc).isoformat(),'trust':'unverified_research_requires_operator_review',
      'sourceChecksums':manifest,'registryDate':'2026-11-16','communeTransitions':communes,'villageTransitions':villages,
      'currentUnits':catalog,'sources':sources}
(ROOT/'research-history.js').write_text('window.ADDRESS_RESEARCH = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
print(json.dumps({'communeRelations':len(communes),'villageRelations':len(villages),'sourceBlocks':len(sources),'currentUnits':len(catalog)}))
