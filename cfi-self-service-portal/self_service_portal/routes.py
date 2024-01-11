def includeme(config):

    config.add_static_view('static', 'assets', cache_max_age=3600)

    config.add_route('home', '/')

    config.add_route('env-dashboard', '/env/')
    config.add_route('env-new-request', '/env/request/new/')
    config.add_route('env-request', '/env/request/{id}')

    config.add_route('env-admin-control-panel', '/env/admin/{id}')
