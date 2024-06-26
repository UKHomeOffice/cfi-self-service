
import os
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.security import forget
from pyramid.view import view_config
from cfi_self_service.backend.aws.cognito import Cognito
from cfi_self_service.backend.aws.secrets import Secrets

@view_config(route_name='change-password-force', renderer='cfi_self_service:frontend/templates/login/password/reset.jinja2')
def password_force_reset_view(request):

    """
    Summary:
        Renders the forced password reset page and handles the submission of forced password reset requests.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict or HTTPFound: If accessed via GET request, returns data for rendering the forced password reset
                           template.
                           If accessed via POST request, redirects the user to the login page after changing
                           the password.
    Example:
        When the user accesses this route, it renders the forced password reset page, allowing the user to
        enter their new password. Upon form submission, it triggers the forced password change action, stores
        the email address in the session, and redirects the user to the login page after successfully 
        changing the password.
    Note:
        - The method relies on an instance of the Cognito class to perform the forced password reset action.
        - The request.session['email_address'] is used to store the user's email address temporarily during 
          the forced password reset process.
    """

    if request.method == "POST":
        # Extract form data:
        form_data = request.params
        username = form_data.get('emailAddress')
        new_password = form_data.get('newPassword')
        # Store username in session:
        request.session['email_address'] = username
        # Retrieve secrets from AWS Secrets Manager:
        region_name = os.environ.get('REGION_NAME')
        secrets_instance = Secrets(region_name)
        client_id = secrets_instance.get_secret(os.environ.get('COGNITO_CLIENT_ID_NAME'), os.environ.get('COGNITO_CLIENT_ID_KEY'))
        user_pool_id = secrets_instance.get_secret(os.environ.get('COGNITO_USER_POOL_ID_NAME'), os.environ.get('COGNITO_USER_POOL_ID_KEY'))
        # Initialize Cognito instance and perform forced password change:
        cognito = Cognito(client_id, user_pool_id, region_name)
        cognito.action_force_password_change(username, new_password)
        # Redirect user to login page after changing password:
        request.session.flash('Password Changed')
        redirect_url = request.route_url('login')
        raise HTTPFound(redirect_url)
    # Return data for rendering the template
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Login - Forced Password Reset Request',
     }

@view_config(route_name='password-reset-request', renderer='cfi_self_service:frontend/templates/login/password/request.jinja2')
def password_change_request_view(request):

    """
    Summary:
        Renders the password reset request page and handles the submission of password reset requests.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict or HTTPFound: If accessed via GET request, returns data for rendering the password reset request template.
                           If accessed via POST request, redirects the user to the password reset page.
    Example:
        This method is associated with a route named 'password-request'. When the user accesses this route,
        it renders the password reset request page, allowing the user to enter their email address and submit a request
        for manual password change. Upon form submission, it triggers the password reset request, stores the email address
        in the session, and redirects the user to the password reset page.
    Note:
        - The method relies on an instance of the Cognito class to perform the password reset request action.
        - The request.session['email_address'] is used to store the user's email address temporarily during the password reset request process.
    """

    if request.method == "POST":
        # Extract form data:
        form_data = request.params
        email = form_data.get('emailAddress')
        # Store email address in session:
        request.session['email_address'] = email
        # Initialize Cognito instance and request manual password change:
        region_name = os.environ.get('REGION_NAME')
        secrets_instance = Secrets(region_name)
        client_id = secrets_instance.get_secret(os.environ.get('COGNITO_CLIENT_ID_NAME'), os.environ.get('COGNITO_CLIENT_ID_KEY'))
        user_pool_id = secrets_instance.get_secret(os.environ.get('COGNITO_USER_POOL_ID_NAME'), os.environ.get('COGNITO_USER_POOL_ID_KEY'))
        cognito = Cognito(client_id, user_pool_id, region_name)
        cognito.request_manual_password_change(email)
        # Redirect user to password reset page after submitting request:
        redirect_url = request.route_url('password-reset')
        raise HTTPFound(redirect_url)
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Login - Password Reset Request',
    }

@view_config(route_name='password-reset', renderer='cfi_self_service:frontend/templates/login/password/reset.jinja2')
def password_reset_view(request):

    """
    Summary:
        Renders the password reset page and handles the password reset process.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict or HTTPFound: If accessed via GET request, returns data for rendering the password reset template.
                           If accessed via POST request, redirects the user to the login page.
    Example:
        This method is associated with a route named 'password-reset'. When the user accesses this route,
        it renders the password reset page, allowing the user to enter their email, new password, and verification code.
        Upon form submission, it triggers the password reset process, performs the necessary actions, and redirects
        the user to the login page.
    Note:
        - The method relies on an instance of the Cognito class to perform password reset actions.
        - The request.session['email_address'] is used to store the user's email address temporarily during the password reset process.
    """

    if request.method == "POST":
        # Extract form data:
        form_data = request.params
        email = form_data.get('emailAddress')
        new_password = form_data.get('newPassword')
        verification_code = form_data.get('verificationCode')
        # Store email address in session:
        request.session['email_address'] = email
        # Initialize Cognito instance and perform password change action:
        region_name = os.environ.get('REGION_NAME')
        secrets_instance = Secrets(region_name)
        client_id = secrets_instance.get_secret(os.environ.get('COGNITO_CLIENT_ID_NAME'), os.environ.get('COGNITO_CLIENT_ID_KEY'))
        user_pool_id = secrets_instance.get_secret(os.environ.get('COGNITO_USER_POOL_ID_NAME'), os.environ.get('COGNITO_USER_POOL_ID_KEY'))
        cognito = Cognito(client_id, user_pool_id, region_name)
        cognito.action_manual_password_change(email, verification_code, new_password)
        # Redirect user to login page after password reset:
        request.session.flash('Password Changed')
        redirect_url = request.route_url('login')
        raise HTTPFound(redirect_url)
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Login - Password Reset',
    }
