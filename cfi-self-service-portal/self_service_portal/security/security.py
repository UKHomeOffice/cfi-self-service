
import bcrypt
import configparser
from pyramid.authentication import AuthTktCookieHelper
from pyramid.authorization import (
    ACLHelper,
    Authenticated,
    Everyone,
)

def hash_password(pw):
    pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')

def check_password(pw, hashed_pw):
    expected_hash = hashed_pw.encode('utf8')
    return bcrypt.checkpw(pw.encode('utf8'), expected_hash)

######################################################################################

GROUPS_FILE = 'development.ini'

def load_groups_from_file():
    config = configparser.ConfigParser()
    config.read(GROUPS_FILE)
    groups = {}
    if 'groups' in config:
        for user, group_list in config['groups'].items():
            groups[user] = group_list.split(',')
    
    return groups

GROUPS = load_groups_from_file()

######################################################################################

class SecurityPolicy:

    def __init__(self, secret, timeout):
        self.authtkt = AuthTktCookieHelper(secret=secret, timeout=timeout)
        self.acl = ACLHelper()

    def identity(self, request):
        identity = self.authtkt.identify(request)
        if identity is not None:
            return identity

    def authenticated_userid(self, request):
        identity = self.identity(request)
        if identity is not None:
            return identity['userid']

    def remember(self, request, userid, **kw):
        return self.authtkt.remember(request, userid, **kw)

    def forget(self, request, **kw):
        return self.authtkt.forget(request, **kw)

    def permits(self, request, context, permission):
        principals = self.effective_principals(request)
        return self.acl.permits(context, principals, permission)

    def effective_principals(self, request):
        principals = [Everyone]
        userid = self.authenticated_userid(request)
        if userid is not None:
            principals += [Authenticated, 'u:' + userid]
            principals += GROUPS.get(userid, [])
        return principals
    
######################################################################################
