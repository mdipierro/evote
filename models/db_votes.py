not_empty = IS_NOT_EMPTY()

db.define_table('election',
                Field('title',requires=not_empty),
                Field('ballot','text',requires=not_empty),
                Field('voters','text',requires=not_empty),
                Field('emails','text',requires=not_empty),
                Field('deadline','datetime'),
                Field('secret',writable=False,readable=False),                
                auth.signature,
                format='%(title)s')

db.define_table('voter',
                Field('uuid',writable=False,readable=False),
                Field('token',writable=False,readable=False),
                Field('election',db.election),
                Field('email',requires=IS_EMAIL()),
                Field('invited_on','datetime'),
                Field('voted_on','datetime'))

db.define_table('receipt',
                Field('election',db.election),
                Field('ballot','text'),
                Field('results','text'),
                Field('signature','text'),
                Field('token',writable=False,readable=False))

                
#for row in db(db.voter).select():
#    row.update_record(invited_on=row.voted_on,voted_on=None)
