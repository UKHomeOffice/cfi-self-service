
import logging
import boto3
import qrcode
import uuid

from pyramid.httpexceptions import HTTPFound

logger = logging.getLogger(__name__)

class Cognito:

    def __init__(self, request):
        self.request = request
        self.client_id, self.region_name, self.user_pool_id, self.email = self.get_cognito_config()

    def get_cognito_config(self):
        client_id = self.request.registry.settings.get('cognito.client_id')
        region_name = self.request.registry.settings.get('cognito.region_name')
        user_pool_id = self.request.registry.settings.get('cognito.user_pool_id')
        email = self.request.session.get('email_address')
        return client_id, region_name, user_pool_id, email

    def check_force_password_change_status(self):
        try:
            client = boto3.client('cognito-idp', region_name=self.region_name)
            response = client.admin_get_user(UserPoolId=self.user_pool_id, Username=self.email)
            user_status = response['UserStatus']
            return user_status == 'FORCE_CHANGE_PASSWORD'
        except Exception as e:
            logger.error(e)
            return False

    def handle_password_reset_request(self):
        try:
            client = boto3.client('cognito-idp', region_name=self.region_name)
            client.forgot_password(
                ClientId=self.client_id,
                Username=self.email
            )
        except Exception as e:
            logger.error(e)
            return False

    def handle_password_reset(self, verification_code, new_password):
        try:
            client = boto3.client('cognito-idp', region_name=self.region_name)
            client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=self.email,
                ConfirmationCode=verification_code,
                Password=new_password
            )
        except Exception as e:
            logger.error(e)
            return False

    def handle_force_password_change(self, new_password):
        try:
            client = boto3.client('cognito-idp', region_name=self.region_name)
            client.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=self.email,
                Password=new_password,
                Permanent=True
            )
        except Exception as e:
            logger.error(e)
            return False

    def handle_initiate_authentication(self, password):
        try:
            client = boto3.client('cognito-idp', region_name=self.region_name)
            response = client.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': self.email,
                    'PASSWORD': password,
                },
                ClientId=self.client_id,
            )
            return response
        except Exception as e:
            logger.error(e)
            Cognito.handle_error(self.request, e)

    def handle_associate_software_token(self, session):
        try:
            client = boto3.client('cognito-idp', region_name=self.region_name)
            response = client.associate_software_token(
                Session=session
            )
            return response
        except Exception as e:
            logger.error(e)
            Cognito.handle_error(self.request, e)

    def handle_respond_to_auth_challenge(self, request, verification_code):
        try:
            email = request.session.get('email_address')
            session_key = request.session.get('session_key')
            client = boto3.client('cognito-idp', region_name=self.region_name)
            response = client.respond_to_auth_challenge(
                ClientId=self.client_id,
                Session=session_key,
                ChallengeName="SOFTWARE_TOKEN_MFA",
                ChallengeResponses={
                    'USERNAME': email,
                    'SOFTWARE_TOKEN_MFA_CODE': verification_code
                }
            )
            return response
        except Exception as e:
            logger.error(e)
            Cognito.handle_error(self.request, e)

    def handle_verify_software_token(self, request, verification_code):
        try:
            secret_code = request.session.get('secret_code')
            session_key = request.session.get('session_key')
            client = boto3.client('cognito-idp', region_name=self.region_name)
            client.verify_software_token(
                AccessToken=secret_code,
                Session=session_key,
                UserCode=verification_code,
                FriendlyDeviceName='TOTP Device'
            )
        except Exception as e:
            logger.error(e)
            Cognito.handle_error(self.request, e)

    def handle_mfa_user_preferences(self):
        try:
            client = boto3.client('cognito-idp', region_name=self.region_name)
            client.admin_set_user_mfa_preference(
                SoftwareTokenMfaSettings={
                    'Enabled': True,
                    'PreferredMfa': True
                },
                Username=self.email,
                UserPoolId=self.user_pool_id
            )
        except Exception as e:
            logger.error(e)
            Cognito.handle_error(self.request, e)
    
    def handle_auth_response(self, response):
        # Handle different authentication challenges:
        if response["ChallengeName"] == "MFA_SETUP":
            Cognito.handle_multi_factor_auth_setup(self, response)
        elif response["ChallengeName"] == "SOFTWARE_TOKEN_MFA":
            Cognito.handle_multi_factor_auth_request(self, response)

    def handle_multi_factor_auth_setup(self, response):
        # Begin first time setup of TOTP for MFA:
        session_key = response['Session']
        software_token_response = Cognito.handle_associate_software_token(self, session_key)
        # Create QR Code for user to add TOTP app:
        qr_img = qrcode.make(f"otpauth://totp/{self.email}?secret={software_token_response['SecretCode']}" )
        qr_path = f"qr-{str(uuid.uuid4())}.png"
        qr_img.save(f"self_service_portal/assets/qr/{qr_path}")
        # Add key values to the session:
        self.request.session['qr_code_path'] = f"/static/qr/{qr_path}"
        self.request.session['secret_code'] = software_token_response['SecretCode']
        self.request.session['session_key'] = software_token_response['Session']
        # Redirect to MFA setup page:
        redirect_url = self.request.route_url('mfa-setup')
        raise HTTPFound(location=redirect_url)

    def handle_multi_factor_auth_request(self, response):
        # Add key values to the session required to complete a MFA request:
        self.request.session['session_key'] = response['Session']
        # Redirect to MFA request page:
        redirect_url = self.request.route_url('mfa-request')
        raise HTTPFound(location=redirect_url)

    def handle_error(self, error):
        return { 'subtitle': 'Self Service Portal', 'title': 'Welcome', 'error_message': str(error) }
