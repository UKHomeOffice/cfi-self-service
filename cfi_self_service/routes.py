def includeme(config):

    """
    Pyramid config hook.
    This function is a Pyramid config hook used to include configuration settings
    for routes and static views in the Pyramid application. It sets up routes for various
    endpoints of the application and configures static views for serving static assets.

    Args:
        config (pyramid.config.Configurator): The Pyramid configurator object.
    Example:
        This function is called during Pyramid application startup to configure routes
        and static views. It is usually invoked in the main application setup file.
    Note:
        - The function sets up routes for different endpoints of the application using 
          the 'add_route' method.
        - It also configures a static view to serve static assets (e.g., CSS, JavaScript 
          files).
        - Route names and paths are specified for each route to define the mapping 
          between URLs and view functions.
    """

    # Static Asset Setup:
    config.add_static_view(name='static', path='frontend/assets', cache_max_age=3600)
    # Main Dashbord / Home Route:
    config.add_route(name='home', path='/')
    # Access Requests Routes:
    config.add_route(name='access-requests-dashboard', path='/access_requests/')
    config.add_route(name='access-requests-existing', path='/access_requests/{id}')
    config.add_route(name='access-requests-export', path='/access_requests/export/')
    config.add_route(name='access-requests-admin', path='/access_requests/admin/{id}')
    config.add_route(name='access-requests-new', path='/access_requests/new/')
    # Environment URL Routes:
    config.add_route(name='environment-urls-generate', path='/environment-urls/')
    config.add_route(name='environment-urls-update', path='/environment-urls/update/')
    # VPN Profile Routes:
    config.add_route(name='vpn-profiles', path='/vpn-profiles/')
