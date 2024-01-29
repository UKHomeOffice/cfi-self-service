
from pyramid.view import notfound_view_config

@notfound_view_config(renderer='self_service_portal:templates/not_found.jinja2')
def notfound_view(request):
    original_exception = request.exception.__cause__
    request.response.status = 404
    return { 
        'subtitle': 'Self Service Portal',
        'title': 'Page Not Found',
        'error_message': original_exception
    }
