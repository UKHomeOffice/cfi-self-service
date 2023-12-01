def includeme(config):
    config.add_static_view('static', 'assets', cache_max_age=3600)
    config.add_route('home', '/')
