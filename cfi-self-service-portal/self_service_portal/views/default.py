from pyramid.view import view_config

@view_config(route_name='home', renderer='self_service_portal:templates/home.jinja2')
def home_view(request):
    return {'project': 'Self Service Portal', 'title': 'Welcome', 'description': 'Welcome to the self service user portal!'}

@view_config(route_name='env-request', renderer='self_service_portal:templates/env-request.jinja2')
def env_request_view(request):
    return {'project': 'Self Service Portal', 'title': 'Request Environment Access', 'description': 'Here you can make a request for access to an environment.'}
