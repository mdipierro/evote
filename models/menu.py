# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.logo = None
response.title = request.application.replace('_',' ').title()
response.subtitle = T('Electornic Voting Service')

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'Your Name <you@example.com>'
response.meta.description = 'a cool new app'
response.meta.keywords = 'web2py, python, framework'
response.meta.generator = 'Web2py Web Framework'

## your http://google.com/analytics id
response.google_analytics_id = None

#########################################################################
## this is the main application menu add/remove items as required
#########################################################################

response.menu = [
    (T('Home'), False, URL('default', 'index')),
    (T('Elections'), False, URL('default', 'elections')),
    (T('Features'), False, URL('default', 'features')),
    (T('Support'), False, URL('default', 'support')),
]

