import pytest
from oh_desktop.store import get, save


def test_store_updates_allowed_fields_and_rejects_stale_version(tmp_path):
    from oh_desktop.store import initialize
    path=tmp_path/'oh.sqlite3';initialize(path)
    record=get(path,'DEMO0001')
    record['national_id']='000999000001';record['name']='Không được đổi tên'
    result=save(path,record)
    assert result['name']=='Nguyễn Văn An'
    assert result['national_id']=='000999000001' and result['version']==2
    with pytest.raises(ValueError,match='đã thay đổi'):save(path,record)


@pytest.mark.parametrize('change',[{'national_id':123},{'national_id':'x'},{'address':{}},
                                  {'address':{'province':'','ward':'A','street':'B'}}])
def test_store_rejects_invalid_updates(tmp_path,change):
    from oh_desktop.store import initialize
    path=tmp_path/'oh.sqlite3';initialize(path)
    record=get(path,'DEMO0001');record.update(change)
    with pytest.raises(ValueError):save(path,record)
