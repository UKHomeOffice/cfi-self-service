def test_root(testapp):
    res = testapp.get('/', status=200)
    assert res.status_code == 200

def test_notfound(testapp):
    res = testapp.get('/badurl', status=404)
    assert res.status_code == 404
