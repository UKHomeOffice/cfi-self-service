
import os
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.security import forget
from pyramid.view import view_config
from cfi_self_service.backend.aws.cognito import Cognito
from cfi_self_service.backend.aws.secrets import Secrets

@view_config(route_name='login', renderer='cfi_self_service:frontend/templates/login/log-in.jinja2')
def login_view(request):

    """
    Summary:
        This view handles the login process.
    Args:
        request (Request): The Pyramid request object.
    Returns:
        dict: Data for rendering the login template.
    """

    # Load any flash messages that are available to display to the user:
    messages = request.session.pop_flash()
    if request.method == "POST":
        # Extract form data:
        form_data = request.params
        username = form_data.get('emailAddress')
        password = form_data.get('password')
        # Store the username in the session for later use:
        request.session['email_address'] = username
        # Retrieve secrets from AWS Secrets Manager:
        region_name = os.environ.get('REGION_NAME')
        secrets_instance = Secrets(region_name)
        client_id = secrets_instance.get_secret(os.environ.get('COGNITO_CLIENT_ID_NAME'), os.environ.get('COGNITO_CLIENT_ID_KEY'))
        user_pool_id = secrets_instance.get_secret(os.environ.get('COGNITO_USER_POOL_ID_NAME'), os.environ.get('COGNITO_USER_POOL_ID_KEY'))
        # Initialize Cognito instance and handle MFA verification and user preferences:
        cognito = Cognito(client_id, user_pool_id, region_name)
        # Check if a force password change is required:
        force_password_check = cognito.check_force_password_change(username)
        if force_password_check is True:
            redirect_url = request.route_url('change-password-force')
            raise HTTPFound(redirect_url)
        # Authenticate user with Cognito if user is clear of force password change:
        auth_user_response = cognito.authenticate_user(username, password)
        if auth_user_response["ChallengeName"] == 'MFA_SETUP':
            # If MFA setup is required, initiate MFA setup process, including QR code generation:
            cognito.challenge_mfa_setup(request, auth_user_response, username)
            redirect_url = request.route_url('mfa-setup')
            raise HTTPFound(location=redirect_url)
        elif auth_user_response["ChallengeName"] == 'SOFTWARE_TOKEN_MFA':
            # If software token MFA is required, add session key and redirect to MFA request page:
            request.session['session_key'] = auth_user_response["Session"]
            redirect_url = request.route_url('mfa-request')
            raise HTTPFound(location=redirect_url)

    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Login',
        'message': messages
    }

@view_config(route_name='logout')
def logout(request):

    """
    Summary:
        Logs out the user and redirects to the login page.
        It removes any authentication headers associated with the current session, 
        effectively logging out the user. After logging out, it redirects the user to the login page.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        HTTPFound: Redirects the user to the login page after logging out.
    Note:
        - The forget() function removes any authentication headers associated with the current session.
    """

    # Remove authentication headers associated with the current session:
    headers = forget(request)
    # Generate the URL for the login route:
    url = request.route_url('login')
    # Redirect the user to the login page after logging out:
    return HTTPFound(location=url, headers=headers)
