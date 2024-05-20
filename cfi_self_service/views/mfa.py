
import os
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid.view import view_config
from cfi_self_service.backend.aws.cognito import Cognito
from cfi_self_service.backend.aws.secrets import Secrets

@view_config(route_name='mfa-setup', renderer='cfi_self_service:frontend/templates/login/mfa/setup.jinja2')
def mfa_setup_view(request):

    """
    Summary:
        Renders the multi-factor authentication (MFA) setup page and handles MFA setup process.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict or HTTPFound: If accessed via GET request, returns data for rendering the MFA setup template.
                           If accessed via POST request, redirects the user to the login page after completing
                           the MFA setup process.
    Example:
        When the user accesses this route, it renders the MFA setup page, displaying the QR code for setting
        up the software token. Upon form submission with the verification code, it triggers the MFA setup 
        process, handles user preferences, and redirects the user to the login page after successful setup.
    Note:
        - The method relies on an instance of the Cognito class to handle MFA setup and user preferences.
        - The request.session['qr_code_path'] stores the path to the QR code image temporarily during the MFA 
          setup process.
    """

    # Retrieve the path to the QR code image from the session:
    qr_image = request.session.get('qr_code_path', 'Default')
    if request.method == "POST":
        # Extract form data:
        form_data = request.params
        verification_code = form_data.get('authVerificationCode')
        username = request.session['email_address']
        # Retrieve secrets from AWS Secrets Manager:
        region_name = os.environ.get('REGION_NAME')
        secrets_instance = Secrets(region_name)
        client_id = secrets_instance.get_secret(os.environ.get('COGNITO_CLIENT_ID_NAME'), os.environ.get('COGNITO_CLIENT_ID_KEY'))
        user_pool_id = secrets_instance.get_secret(os.environ.get('COGNITO_USER_POOL_ID_NAME'), os.environ.get('COGNITO_USER_POOL_ID_KEY'))
        # Initialize Cognito instance and handle MFA verification and user preferences:
        cognito = Cognito(client_id, user_pool_id, region_name)
        cognito.handle_verify_software_token(request, verification_code)
        cognito.handle_mfa_user_preferences(username)
        # Remove the QR code file after successful setup:
        os.remove(f"cfi_self_service/frontend/assets/qr/{request.session['qr_code_filename']}")
        # Redirect user to login page after completing MFA setup:
        request.session.flash('MFA Setup')
        redirect_url = request.route_url('login')
        raise HTTPFound(redirect_url)
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Multi-Factor Authentication Setup',
        'qr_image': qr_image
    }

@view_config(route_name='mfa-request', renderer='cfi_self_service:frontend/templates/login/mfa/request.jinja2')
def mfa_request_view(request):

    """
    Summary:
        Renders the multi-factor authentication (MFA) request page and handles MFA verification.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict or HTTPFound: If the MFA verification is successful, redirects the user to the home page.
                           If MFA verification fails or the user is not authenticated, returns data for
                           rendering the MFA request template.
    Example:
        When the user accesses this route via POST request and submits the MFA verification code, it 
        triggers the MFA verification process using Cognito. If verification is successful, it redirects
        the user to the home page. If verification fails or the user is not authenticated, it renders
        the MFA request page for re-entering the verification code.
    Note:
        - The method relies on an instance of the Cognito class to handle MFA verification.
    """

    if request.method == "POST":
        # Retrieve secrets from AWS Secrets Manager:
        region_name = os.environ.get('REGION_NAME')
        secrets_instance = Secrets(region_name)
        client_id = secrets_instance.get_secret(os.environ.get('COGNITO_CLIENT_ID_NAME'), os.environ.get('COGNITO_CLIENT_ID_KEY'))
        user_pool_id = secrets_instance.get_secret(os.environ.get('COGNITO_USER_POOL_ID_NAME'), os.environ.get('COGNITO_USER_POOL_ID_KEY'))
        # Initialize Cognito instance and handle MFA verification and user preferences:
        cognito = Cognito(client_id, user_pool_id, region_name)
        software_token_response = cognito.challenge_software_token_mfa(request)
        # Check that authentication has been successful and redirect accordingly:
        cognito.handle_verify_successful_auth(request, software_token_response)
    # Return data for rendering the MFA request template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Multi-Factor Authentication Request',
    }
