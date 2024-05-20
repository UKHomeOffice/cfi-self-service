
import secrets
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory

def main(global_config, **settings):

    """
    Summary:
        This function is the main entry point for configuring and creating a Pyramid WSGI application.
        It sets up the Pyramid configuration with specified settings, includes necessary components
        such as templating engine (Jinja2), application routes, and scans the project for additional configuration.
    Args:
        global_config (dict): The global configuration settings from the PasteDeploy ini file.
        **settings: Additional configuration settings passed to the application.
    Returns:
        callable: A callable representing the Pyramid WSGI application.
    Note:
        - The function creates a Configurator instance to configure the Pyramid application.
        - It sets up the session factory using SignedCookieSessionFactory with a randomly generated secret key.
        - It includes necessary components such as the Jinja2 engine and application routes.
        - The config.scan() method scans the project for additional configuration and views.
    """

    # Generate a random secret key for session encryption:
    secret_key = secrets.token_hex(32)
    # Setup the session factory with the generated secret key:
    session_factory = SignedCookieSessionFactory(secret_key)
    # Initialize the Configurator to configure the Pyramid application:
    with Configurator(settings=settings) as config:
        # Set the session factory for the application:
        config.set_session_factory(session_factory)
        # Include the Jinja2 templating engine:
        config.include('pyramid_jinja2')
        # Include application routes:
        config.include('.routes')
        # Scan the project for additional configuration and views:
        config.scan()
    # Create and return the WSGI application:
    return config.make_wsgi_app()
