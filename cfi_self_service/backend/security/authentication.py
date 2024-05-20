
import os
from pyramid.httpexceptions import HTTPFound
from cfi_self_service.backend.aws.secrets import Secrets
from cfi_self_service.backend.aws.cognito import Cognito

def authenticated_view(view_func):

    """
    Summary:
        Decorator to restrict access to authenticated users.
    Args:
        view_func (callable): The view function to be decorated.
    Returns:
        callable: The wrapped view function.
    Notes:
        This decorator checks if the user is authenticated using AWS Cognito.
        If authentication succeeds, it allows access to the decorated view function.
        If authentication fails, it redirects the user to the login page.
    """

    def wrapped_view(request):
        # Retrieve secrets from AWS Secrets Manager:
        region_name = os.environ.get('REGION_NAME')
        secrets_instance = Secrets(region_name)
        client_id = secrets_instance.get_secret(os.environ.get('COGNITO_CLIENT_ID_NAME'), os.environ.get('COGNITO_CLIENT_ID_KEY'))
        user_pool_id = secrets_instance.get_secret(os.environ.get('COGNITO_USER_POOL_ID_NAME'), os.environ.get('COGNITO_USER_POOL_ID_KEY'))
        # Initialize Cognito instance and handle MFA verification and user preferences:
        cognito = Cognito(client_id, user_pool_id, region_name)
        if cognito.check_cognito_authentication(request):
            # User is authenticated, proceed to the view function:
            return view_func(request)
        else:
            # Redirect to the login page or return an unauthorized response:
            redirect_url = request.route_url('login')
            raise HTTPFound(location=redirect_url)
    return wrapped_view
