
def test_notfound(testapp):
    res = testapp.get('/badurl', status=404)
    assert res.status_code == 404

#####################################################################################

# change-password-force > /login/change-password/force/
def test_change_password_force(testapp):
    res = testapp.get('/login/change-password/force/', status=200)
    assert res.status_code == 200

# change-password-reset-request > /login/change-password/request/
def test_change_password_reset_request(testapp):
    res = testapp.get('/login/change-password/request/', status=200)
    assert res.status_code == 200

# change-password > /login/change-password/
def test_change_password_request(testapp):
    res = testapp.get('/login/change-password/', status=200)
    assert res.status_code == 200

# mfa-setup > /login/mfa/setup/
def test_mfa_setup(testapp):
    res = testapp.get('/login/mfa/setup/', status=200)
    assert res.status_code == 200

# mfa-request > /login/mfa/request/
def test_mfa_request(testapp):
    res = testapp.get('/login/mfa/request/', status=200)
    assert res.status_code == 200

#####################################################################################

# home > /home/
def test_root(testapp):
    res = testapp.get('/', status=200)
    assert res.status_code == 200

#####################################################################################

# env-dashboard > /env/
def test_env_dashboard(testapp):
    res = testapp.get('/env/', status=200)
    assert res.status_code == 200

# env-new-request > /env/request/new/
def test_env_request(testapp):
    res = testapp.get('/env/request/new/', status=200)
    assert res.status_code == 200

# env-request > /env/request/{id}

# env-admin-control-panel > /env/admin/{id}

# env-export-data > /env/admin/export/
def test_env_export_data(testapp):
    res = testapp.get('/env/admin/export/', status=200)
    assert res.status_code == 200

#####################################################################################

# env-generate > /env/generate/
def test_env_generate(testapp):
    res = testapp.get('/env/generate/', status=200)
    assert res.status_code == 200

# env-update > /env/update/
def test_env_update(testapp):
    res = testapp.get('/env/update/', status=200)
    assert res.status_code == 200
