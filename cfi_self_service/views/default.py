
from pyramid.view import view_config
from cfi_self_service.backend.security.authentication import authenticated_view

@view_config(route_name='home', renderer='cfi_self_service:frontend/templates/dashboard/home.jinja2')
@authenticated_view
def home_view(request):

    """
    Summary:
        This view is the landing page of the CFI Self Service Portal. It renders the template
        for displaying the home page, which contains an overview of available features
        or quick links to different sections of the portal.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict: A dictionary containing data to be passed to the renderer for rendering the template.
            It includes information such as subtitle and title for the home page.
    """

    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Home'
    }
