def includeme(config):

    config.add_static_view('static', 'assets', cache_max_age=3600)

    # Login Screen:
    config.add_route('login', '/')

    # Login Screen - Force Change Password:
    config.add_route('change-password-force', '/login/change-password/force/')

    # Login Screen - Forgotten Password:
    config.add_route('change-password-reset-request', '/login/change-password/request/')
    config.add_route('change-password', '/login/change-password/')

    # Login Screen - MFA:
    config.add_route('mfa-setup', '/login/mfa/setup/')
    config.add_route('mfa-request', '/login/mfa/request/')

    # Logout:
    config.add_route('logout', '/logout/')

    # Home Screen:
    config.add_route('home', '/home/')

    # Envrionment Access:
    config.add_route('env-dashboard', '/env/')
    config.add_route('env-new-request', '/env/request/new/')
    config.add_route('env-request', '/env/request/{id}')

    config.add_route('env-admin-control-panel', '/env/admin/{id}')
    config.add_route('env-export-data', '/env/admin/export/')

    # Environment URL's:
    config.add_route('env-generate', '/env/generate/')
    config.add_route('env-update', '/env/update/')
