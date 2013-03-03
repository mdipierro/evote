# -*- coding: utf-8 -*-

DEVELOPMENT = False

# connect to database
db = DAL('sqlite://storage.sqlite')

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail=auth.settings.mailer

#mail.settings.server='smtp.gmail.com:587'
mail.settings.server = 'logging' if DEVELOPMENT else 'localhost'
mail.settings.sender = 'i.vote.secure@gmail.com'
mail.settings.login = None

## configure auth policy
auth.settings.registration_requires_verification = True
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth,filename='private/janrain.key')
auth.settings.actions_disabled.append('profile')
