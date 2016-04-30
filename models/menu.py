# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.logo = A(B(myconf.take('app.title')),XML('&trade;&nbsp;'),
                  _class="navbar-brand",_href=URL('default','index'))
response.title = myconf.take('app.title')
response.subtitle = myconf.take('app.subtitle')

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = myconf.take('meta.author')
response.meta.description = myconf.take('meta.description')
response.meta.keywords = myconf.take('meta.keywords')

## your http://google.com/analytics id
response.google_analytics_id = myconf.take('app.google_analytics_id')

#########################################################################
## this is the main application menu add/remove items as required
#########################################################################

response.menu = [
    (T('EVote'), False, URL('default', 'index')),
    (T('Elections'), False, URL('default', 'elections')),
    (T('Features'), False, URL('default', 'features')),
    (T('Support'), False, URL('default', 'support')),
    (T('Source Code'), False, 'https://github.com/mdipierro/evote'),
]

