
from pyramid.session import SignedCookieSessionFactory
from pyramid.config import Configurator

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application. """
    session_factory = SignedCookieSessionFactory('your_secret_key')
    with Configurator(settings=settings) as config:
        config.set_session_factory(session_factory)
        config.include('pyramid_jinja2')
        config.include('.routes')
        config.scan()
    return config.make_wsgi_app()
