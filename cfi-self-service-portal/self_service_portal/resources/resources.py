
from pyramid.authorization import Allow, Everyone

class Root:

    __acl__ = [
                ( Allow, Everyone, 'view' ),
                ( Allow, 'group:Testers', 'protected' ),
                ( Allow, 'group:Users', 'protected' ),
                ( Allow, 'group:DevOps', 'admin' ),
                ( Allow, 'group:DevOps', 'protected' )
            ]

    def __init__(self, request):
        pass

