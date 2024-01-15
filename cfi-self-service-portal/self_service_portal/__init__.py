
import boto3
import secrets
from pyramid.session import SignedCookieSessionFactory
from pyramid.config import Configurator

####################################################################
# Boto3 - Cognito Integration
####################################################################

def get_user(request, username, poolID):
    # Use Boto3 to interact with Cognito and get user attributes
    client = boto3.client('cognito-idp', region_name='eu-west-2')
    response = client.admin_get_user(
        UserPoolId=poolID,
        Username=username
    )
    return response['UserAttributes']

####################################################################

def main(global_config, **settings):

    """ This function returns a Pyramid WSGI application. """

    # Setup the session factory and secret token key:
    secret_key = secrets.token_hex(32)
    session_factory = SignedCookieSessionFactory(secret_key)

    with Configurator(settings=settings) as config:

        config.set_session_factory(session_factory)

        #config.add_request_method(
        #    lambda request: get_user(request, request.authenticated_userid), 'user', reify=True
        #)

        config.include('pyramid_jinja2')
        config.include('.routes')

        config.scan()

    return config.make_wsgi_app()

####################################################################
