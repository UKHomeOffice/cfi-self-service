
from pyramid.config import Configurator

def main(global_config, **settings):

    """
    Pyramid application setup.

    This function is the main entry point for configuring and creating a Pyramid
    WSGI application. It sets up the Pyramid configuration with specified settings,
    includes necessary components such as templating engine (Jinja2), application routes,
    and scans the project for additional configuration.

    Args:
        global_config (dict): The global configuration settings from the PasteDeploy ini file.
        **settings: Additional configuration settings passed to the application.
    Returns:
        callable: A callable representing the Pyramid WSGI application.1§
    Example:
        This function is typically called to create a WSGI application for running a Pyramid web server.
        It is invoked during application startup, often from a `__init__.py` file in the project directory.
    Note:
        - The function creates a `Configurator` instance to configure the Pyramid application.
        - It includes necessary components such as the Jinja2 templating engine and application routes.
        - The `config.scan()` method scans the project for additional configuration and views.
    """

    with Configurator(settings=settings) as config:
        config.include('pyramid_jinja2')
        config.include('.routes')
        config.scan()
    return config.make_wsgi_app()
