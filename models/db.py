# -*- coding: utf-8 -*-
request.now = request.utcnow

# require an HTTP session
if SCHEME == 'https': session.secure()

# connect to database
db = DAL(DBURI)

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
auth.settings.extra_fields['auth_user'] = [
    Field('is_manager','boolean',default=AS_SERVICE or DEVELOPMENT,
          writable=False,readable=False)]
auth.define_tables(username=False, signature=False)

## configure email
mail=auth.settings.mailer

#mail.settings.server='smtp.gmail.com:587'
mail.settings.server = 'logging' if DEVELOPMENT else EMAIL_SERVER
mail.settings.sender = EMAIL_SENDER
mail.settings.login = EMAIL_LOGIN

## configure auth policy
auth.settings.registration_requires_verification = not (DEVELOPMENT or USERS_FILENAME)
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth,filename='private/janrain.key')
auth.settings.actions_disabled.append('profile')

# if resticted to some users
def load_users_emails(filename=USERS_FILENAME):
    import urllib, os
    if not filename:
        emails = []
    elif filename.startswith('http://') or filename.startswith('https://'):
        emails = urllib.urlopen(filename).read().split('\n')
    elif os.path.exists(filename):
        emails = open(filename).read().split('\n')
    else:
        emails = []
    emails = [email.strip() for email in emails if email.strip()]
    return emails
users_emails = cache.ram('users_emails',load_users_emails,3600)
