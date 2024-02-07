
from self_service_portal.views.default import home_view
from self_service_portal.views.default import env_request_view
from self_service_portal.views.notfound import notfound_view

def test_home__view(app_request):
    info = home_view(app_request)
    assert app_request.response.status_int == 200
    assert info['project'] == 'Self Service Portal'

def test_env_request_view(app_request):
    info = env_request_view(app_request)
    assert app_request.response.status_int == 200
    assert info['project'] == 'Self Service Portal'

def test_notfound_view(app_request):
    info = notfound_view(app_request)
    assert app_request.response.status_int == 404
    assert info['project'] == 'Self Service Portal'
