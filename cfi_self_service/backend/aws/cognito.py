
import boto3
import os
import qrcode
import uuid
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.security import forget, remember

class Cognito:

    def __init__(self, client_id, user_pool_id, region_name):

        """
        Summary:
            Initializes an instance of the Cognito class for handling user authentication using 
            Amazon Cognito.
        Args:
            user_pool_id (str): The ID of the Cognito user pool.
            client_id (str): The client ID associated with the user pool.
            region_name (str): The AWS region where the user pool is located.
        Example:
            This method is called when creating a new instance of the UserAuthenticator class.
            It initializes the instance with the provided user pool ID, client ID, and AWS region.
        Note:
            - The user_pool_id, client_id, and region_name parameters are required for the instance to 
            interact with Amazon Cognito.
            - The boto3 library is used to create a client for interacting with the Cognito service in 
            the specified region.
        """

        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region_name = region_name
        self.cognito_client = boto3.client('cognito-idp', region_name=self.region_name)

    def check_cognito_authentication(self, request):

        """
        Summary:
            Check if the user is authenticated with Cognito by validating the access token.
        Args:
            request (Request): The Pyramid request object.
        Returns:
            bool: True if the access token is valid and the user is authenticated, False otherwise.
        """

        try:
            # Attempt to retrieve user information from Cognito using the access token:
            self.cognito_client.get_user(
                AccessToken=request.session['access_token']
            )
            # If the response is successful, the user is authenticated:
            return True
        except Exception:
            # If an exception occurs (e.g., access token is invalid), the user is not authenticated:
            return False

    ##############################################################################################################
    ##############################################################################################################
    ##############################################################################################################

    def list_users_in_group(self, group_name):

        """
        Summary:
            Lists users in a specified group within an AWS Cognito User Pool.
            This method uses the AWS Cognito `list_users_in_group` API to retrieve a list
            of users that are members of the specified group within the associated User Pool.
        """

        try:
            response = self.cognito_client.list_users_in_group(
                UserPoolId=self.user_pool_id,
                GroupName=group_name,
                Limit=10
            )
            return response
        except Exception as e:
            # Handle general exceptions gracefully:
            print("list_users_in_group - an error occurred - ", e)
            raise HTTPNotFound from e

    def check_user_is_admin(self, admin_group, username):

        """
        Summary:
            Checks if a user is an admin by verifying their membership in the admin group.
            This method iterates through the users in the provided admin group and checks
            if the specified username (email) matches any of the users' email attributes.
            If a match is found, the user is considered an admin.        
        """

        for user in admin_group.get('Users', []):
            for attribute in user.get('Attributes', []):
                if attribute.get('Name') == 'email' and attribute.get('Value') == username:
                    return True
        return False

    ##############################################################################################################
    ##############################################################################################################
    ##############################################################################################################

    def authenticate_user(self, username, password):

        """
        Summary:
            Authenticates a user with username and password.
        Args:
            username (str): The username of the user attempting to authenticate.
            password (str): The password of the user attempting to authenticate.
        Example:
            This method is called when a user attempts to log in to the system using their username
            and password. It handles authentication challenges and redirects users to appropriate pages 
            if additional steps are required, such as MFA setup.
        """

        try:
            response = self.cognito_client.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                },
                ClientId=self.client_id
            )
            return response
        except self.cognito_client.exceptions.NotAuthorizedException as e:
            # If user is not authorized, authentication fails:
            print("authenticate_user - NotAuthorizedException - ", e)
            raise HTTPNotFound from e
        except self.cognito_client.exceptions.UserNotFoundException as e:
            # If user is not found, authentication fails:
            print("authenticate_user - UserNotFoundException - ", e)
            raise HTTPNotFound from e
        except Exception as e:
            # Handle general exceptions gracefully:
            print("authenticate_user - an error occurred - ", e)
            raise HTTPNotFound from e

    def challenge_mfa_setup(self, request, response, username):

        """
        Summary:
            Initiates multi-factor authentication (MFA) setup process.
        Args:
            response (dict): A dictionary containing response data from the authentication service.
                             It includes a session key necessary for associating the software token.
        Returns:
            bool: True if the MFA setup process is initiated successfully, False otherwise.
        Example:
            This method is called when a user needs to set up multi-factor authentication
            for the first time. It generates a QR code containing the TOTP secret and redirects the user
            to the MFA setup page to complete the setup process.
        """

        # Begin first-time setup of TOTP for MFA:
        session_key = response['Session']
        try:
            software_token_response = self.cognito_client.associate_software_token(
                Session=session_key
            )
            # Create QR Code for the user to add to the TOTP app:
            qr_img = qrcode.make(f"otpauth://totp/{username}?secret={software_token_response['SecretCode']}")
            qr_path = f"qr-{str(uuid.uuid4())}.png"
            qr_img.save(f"cfi_self_service/frontend/assets/qr/{qr_path}")
            # Add key values to the session:
            request.session['qr_code_filename'] = qr_path
            request.session['qr_code_path'] = f"/static/qr/{qr_path}"
            request.session['secret_code'] = software_token_response['SecretCode']
            request.session['session_key'] = software_token_response['Session']
        except Exception as e:
            # Handle any exceptions gracefully:
            print("An error occurred during software token association:", e)
            raise HTTPNotFound from e

    def challenge_software_token_mfa(self, request):

        """
        Summary:
            Responds to the challenge for software token multi-factor authentication (MFA).
        Args:
            response (dict): A dictionary containing response data from the authentication service.
            It includes information about the authentication challenge.
            request (Request): The Pyramid request object representing the HTTP request.
        Returns:
            If the response indicates that the challenge has been successfully completed, it redirects the 
            user to the home page.
        Example:
            This method is called when the user submits the verification code for software token MFA.
            It responds to the authentication challenge using the verification code and redirects the user 
            to the home page upon successful completion of the challenge.
        """

        try:
            # Extract verification code from the form data submitted by the user:
            form_data = request.POST
            verification_code = form_data.get('authVerificationCode')
            # Retrieve email address and session key from the session data:
            email = request.session.get('email_address')
            session_key = request.session.get('session_key')
            # Respond to the authentication challenge using the Cognito client:
            response = self.cognito_client.respond_to_auth_challenge(
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
            # Handle any exceptions gracefully:
            print("An error occurred during software token association:", e)
            raise HTTPNotFound from e

    def handle_verify_successful_auth(self, request, response):

        """
        Summary:
            Handle successful authentication verification. This method processes the response from an 
            authentication challenge. If the challenge is successfully completed, it stores the access
            token in the session, checks if the user is an admin, sets the admin status in the 
            session, and redirects the user to the home page with the appropriate headers. If the 
            challenge is not completed, it redirects the user to the login page.
        Args:
            request: The current request object containing session and routing information.
            response: The response object from the authentication challenge containing the 
                    challenge parameters and authentication result.
        Raises:
            HTTPFound: A Pyramid HTTP exception for redirection.
        """

        # Check if the authentication challenge has been successfully completed:
        if response["ChallengeParameters"] == {}:
            # Store the access token in the session:
            request.session["access_token"] = response["AuthenticationResult"]["AccessToken"]
            # Retrieve the admin group and check if the user is an admin:
            admin_group = Cognito.list_users_in_group(self, os.environ.get("COGNITO_USER_POOL_ADMIN_GROUP_NAME"))
            is_user_admin = Cognito.check_user_is_admin(self, admin_group, request.session["email_address"])
            request.session["admin_user"] = is_user_admin
            # If challenge completed, create headers for authentication and redirect the user to the home page:
            headers = remember(request, response["AuthenticationResult"]["AccessToken"])
            redirect_url = request.route_url('home')
            raise HTTPFound(location=redirect_url, headers=headers)
        else:
            # If the challenge is not completed, redirect the user back to the login page:
            redirect_url = request.route_url('login')
            raise HTTPFound(location=redirect_url)

    def handle_verify_software_token(self, request, verification_code):

        """
        Summary:
            Handles the verification of a software token (TOTP) provided by the user.
        Args:
            request (Request): The Pyramid request object representing the HTTP request.
            verification_code (str): The verification code provided by the user for the software token.
        Returns:
            None
        Example:
            To verify the provided software token (TOTP), this method retrieves the secret code and session key
            stored in the user's session. It then utilizes the Cognito client to verify the token by providing
            the access token, session key, and user-provided verification code. If verification fails, an error
            is logged.
        Note:
            - This method is invoked during multi-factor authentication (MFA) setup or verification.
        """

        try:
            # Retrieve the secret code and session key from the session:
            secret_code = request.session.get('secret_code')
            session_key = request.session.get('session_key')
            # Verify the software token (TOTP) using Cognito client:
            self.cognito_client.verify_software_token(
                AccessToken=secret_code,
                Session=session_key,
                UserCode=verification_code,
                FriendlyDeviceName='TOTP Device'
            )
        except Exception as e:
            # Log an error if verification fails:
            print("An error occurred:", e)
            raise HTTPNotFound from e

    def handle_mfa_user_preferences(self, username):

        """
        Summary:
            Handles the user's multi-factor authentication (MFA) preferences.
        Args:
            username (str): The username of the user whose MFA preferences are to be set.
        Example:
            To set the MFA preferences for a user, this method utilizes the Cognito client to set the 
            software token MFA settings as enabled and preferred for the specified user. If an error 
            occurs during this process, an error message is logged.
        """

        try:
            # Set the user's MFA preferences using the Cognito client
            self.cognito_client.admin_set_user_mfa_preference(
                SoftwareTokenMfaSettings={
                    'Enabled': True,
                    'PreferredMfa': True
                },
                Username=username,
                UserPoolId=self.user_pool_id
            )
        except Exception as e:
            # Log an error if setting MFA preferences fails
            print("An error occurred:", e)
            raise HTTPNotFound from e

    def check_force_password_change(self, username):

        """
        Summary:
            Checks if a force password change is required for a user.
        Args:
            username (str): The username of the user to check.
        Returns:
            bool: True if a force password change is required, False otherwise.
        Example:
            This method is called when a user attempts to log in. It checks if the user's
            status requires a password change, indicating that the user must change their password
            before being able to log in.
        Note:
            - The method relies on the Amazon Cognito client to query user attributes.
            - It handles the UserNotFoundException exception, returning False if the user is not found.
            - General exceptions are caught and logged, returning False to indicate an error occurred.
        """

        try:
            # Query user attributes from the user pool:
            response = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            # Check if the user requires a password change:
            user_attributes = response['UserStatus']
            if user_attributes == 'FORCE_CHANGE_PASSWORD':
                return True
            return False
        except self.cognito_client.exceptions.UserNotFoundException as e:
            # If the user is not found, return False:
            print("An error occurred - UserNotFound - ", e)
            return False
        except Exception as e:
            # Handle general exceptions gracefully:
            print("An error occurred - ", e)
            return False

    def action_force_password_change(self, username, new_password):

        """
        Summary:
            Complete the force password change flow by setting a new password for the user.
        Args:
            - username (str): The username of the user.
            - new_password (str): The new password to set for the user.
        Returns:
            - bool: True if the force password change is completed successfully, False otherwise.
        """

        try:
            self.cognito_client.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=username,
                Password=new_password,
                Permanent=True
            )
            # If no exceptions are raised, force password change is completed successfully:
            return True
        except self.cognito_client.exceptions.NotAuthorizedException as e:
            # If the user is not authorized, print the error and return False:
            print("Not authorized:", e)
            return False
        except Exception as e:
            # Handle other exceptions gracefully:
            print("An error occurred during force password change:", e)
            return False

    def request_manual_password_change(self, username):

        """
        Summary:
            Initiate the forgot password flow for the user.
        Args:
            - username (str): The username of the user.
        Returns:
            - bool: True if the forgot password flow is initiated successfully, False otherwise.
        """

        try:
            self.cognito_client.forgot_password(
                ClientId=self.client_id,
                Username=username
            )
            # If no exceptions are raised, forgot password flow is initiated successfully:
            return True
        except self.cognito_client.exceptions.InvalidParameterException as e:
            # If the username is invalid, print the error and return False:
            print("Invalid parameter:", e)
            return False
        except self.cognito_client.exceptions.UserNotFoundException as e:
            # If the user is not found, print the error and return False:
            print("User not found:", e)
            return False
        except Exception as e:
            # Handle other exceptions gracefully:
            print("An error occurred during forgot password:", e)
            return False

    def action_manual_password_change(self, username, confirmation_code, new_password):

        """
        Summary:
            Confirm the forgot password flow with the confirmation code and set a new password for the user.
        Args:
            - username (str): The username of the user.
            - confirmation_code (str): The confirmation code sent to the user's email or phone.
            - new_password (str): The new password to set for the user.
        Returns:
            - bool: True if the forgot password confirmation is successful, False otherwise.
        """

        try:
            self.cognito_client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
                Password=new_password
            )
            # If no exceptions are raised, forgot password confirmation is successful:
            return True
        except self.cognito_client.exceptions.ExpiredCodeException as e:
            # If the confirmation code has expired, print the error and return False:
            print("Confirmation code has expired:", e)
            return False
        except self.cognito_client.exceptions.CodeMismatchException as e:
            # If the confirmation code does not match, print the error and return False:
            print("Confirmation code does not match:", e)
            return False
        except Exception as e:
            # Handle other exceptions gracefully:
            print("An error occurred during forgot password confirmation:", e)
            return False
