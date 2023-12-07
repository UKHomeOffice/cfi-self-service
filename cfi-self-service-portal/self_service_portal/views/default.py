from pyramid.view import view_config

@view_config(route_name='home', renderer='self_service_portal:templates/home.jinja2')
def home_view(request):
    return {'project': 'Self Service Portal'}
