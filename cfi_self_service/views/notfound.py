
from pyramid.view import notfound_view_config

@notfound_view_config(renderer='cfi_self_service:frontend/templates/not_found.jinja2')
def notfound_view(request):

    """
    Summary:
        Renders the view for handling not found (404) errors.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict: A dictionary containing data to be passed to the renderer for rendering the template.
            It includes information such as subtitle, title, and error message.
    Example:
        This view is used to handle not found errors gracefully.
        It displays a custom error message along with details about the original exception.
    Note:
        - The view retrieves the original exception causing the not found error for logging or debugging purposes.
        - It sets the response status to 404 to indicate that the requested resource was not found.
        - The rendered template includes information to guide users on what to do next or who to contact.
    """

    # Retrieve the original exception causing the not found error:
    original_exception = request.exception.__cause__
    # Set the response status to 404:
    request.response.status = 404
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Page Not Found',
        'error_message': original_exception
    }
