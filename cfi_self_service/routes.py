

def includeme(config):

    """
    Summary:
      Pyramid config hook.
      This function is a Pyramid config hook used to include configuration settings
      for routes and static views in the Pyramid application. It sets up routes for various
      endpoints of the application and configures static views for serving static assets.
    Args:
      config (pyramid.config.Configurator): The Pyramid configurator object.
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
    config.add_route(name='home', path='/home/')

    # Login Routes:
    config.add_route('login', '/')

    # Password Routes:
    config.add_route('password-reset-request', '/login/password/reset-request/')
    config.add_route('password-reset', '/login/password/reset/')
    config.add_route('change-password-force', '/login/password/reset/force/')

    # MFA Routes:
    config.add_route('mfa-setup', '/login/mfa/setup/')
    config.add_route('mfa-request', '/login/mfa/request/')

    # Access Requests Routes:
    config.add_route(name='access-requests-dashboard', path='/access-requests/')
    config.add_route(name='access-requests-existing', path='/access-requests/{id}')
    config.add_route(name='access-requests-export', path='/access-requests/export/')
    config.add_route(name='access-requests-admin', path='/access-requests/admin/{id}')
    config.add_route(name='access-requests-new', path='/access-requests/new/')

    # Environment URL & VPN Profile Routes:
    config.add_route(name='environment-urls-vpn-generate', path='/environment-urls-vpn/')
    config.add_route(name='environment-urls-vpn-update', path='/environment-urls-vpn/update/')

    # Logout Route:
    config.add_route('logout', '/logout/')
