def test_unknown_pid(app):
    assert app.test_client().get('/api/patients/NO', headers={'Host':'localhost'}).status_code == 404


def test_save_persistence_and_stale_version(app):
    client=app.test_client()
    record=client.get('/api/patients/DEMO0001').get_json()
    record['address']={'province':'Thành phố Demo','ward':'Phường Mới','street':'12 Đường Demo'}
    record['national_id']='000999000001'
    response=client.post('/api/patients/DEMO0001',json=record)
    assert response.status_code == 200
    saved=client.get('/api/patients/DEMO0001').get_json()
    assert saved['version'] == record['version']+1
    assert saved['address'] == record['address']
    assert client.post('/api/patients/DEMO0001',json=record).status_code == 409


def test_invalid_address_and_remote_origin(app):
    client=app.test_client()
    assert client.post('/api/patients/DEMO0001',json={}).status_code == 400
    assert client.post('/api/patients/DEMO0001',json={},headers={'Origin':'https://foreign.example'}).status_code == 403
    assert client.get('/',headers={'Host':'foreign.example'}).status_code == 403
