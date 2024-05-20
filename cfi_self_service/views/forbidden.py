
from pyramid.httpexceptions import HTTPFound
from pyramid.view import forbidden_view_config

@forbidden_view_config()
def forbidden_view(request):

    """
    Summary:
        This view is associated with a forbidden view configuration, meaning it is triggered when
        a user encounters a forbidden access error (HTTP status code 403). It redirects the user to the
        login page to prompt authentication.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        HTTPFound: Redirects the user to the login page.
    """

    # Generate the URL for the login route:
    redirect_url = HTTPFound(location=request.route_url('login'))
    # Redirect the user to the login page:
    return redirect_url
