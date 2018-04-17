# -*- coding: utf-8 -*-

from gluon.tools import Auth
from gluon.contrib.appconfig import AppConfig

myconf = AppConfig(reload=True)

DEVELOPMENT = myconf.take('app.development').lower()=='true'
AS_SERVICE = myconf.take('app.as_service').lower()=='true'
DEBUG_MODE = myconf.take('app.debug_mode').lower()=='true'
SCHEME = 'http' # if DEVELOPMENT else 'https'

db = DAL(myconf.take('db.uri'), pool_size=myconf.take('db.pool_size', cast=int), check_reserved=['all'])

response.generic_patterns = []
response.formstyle = myconf.take('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.take('forms.separator')

auth = Auth(db)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.take('smtp.server')
mail.settings.sender = myconf.take('smtp.sender')
mail.settings.login = myconf.take('smtp.login')

## configure auth policy
auth.settings.registration_requires_verification = not DEVELOPMENT
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True
