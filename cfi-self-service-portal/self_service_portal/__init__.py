
import boto3
import secrets
from pyramid.session import SignedCookieSessionFactory
from pyramid.config import Configurator
from .security import security
from .resources import resources

####################################################################

def main(global_config, **settings):
    # Setup the session factory and secret token key:
    timeout_seconds = 3 * 60 * 60
    secret_key = secrets.token_hex(32)
    session_factory = SignedCookieSessionFactory(secret_key)
    with Configurator(settings=settings, root_factory='.resources.Root') as config:
        config.set_security_policy(
            security.SecurityPolicy(
                secret=settings['security.secret'],
                timeout=timeout_seconds
            ),
        )
        config.set_session_factory(session_factory)
        config.include('pyramid_jinja2')
        config.include('.routes')
        config.scan()
    return config.make_wsgi_app()

####################################################################
