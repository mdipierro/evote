not_empty = IS_NOT_EMPTY()

db.define_table('election',
                Field('title',requires=not_empty),
                Field('ballot','text',requires=not_empty),
                Field('voters','text',requires=not_empty),
                Field('managers','text',requires=not_empty),
                Field('deadline','datetime'),
                Field('secret',writable=False,readable=False),                
                auth.signature,
                format='%(title)s')

db.define_table('token',
                Field('election_id',db.election,writable=False),
                Field('token_uuid'),
                Field('receipt_uuid'),
                Field('voted_on'))

db.define_table('voter',
                Field('voter_uuid',writable=False,readable=False),
                Field('election_id',db.election,writable=False),
                Field('email',requires=IS_EMAIL()),
                Field('voted','boolean'),
                Field('invited_on','datetime'))

db.define_table('receipt',
                Field('election_id',db.election),
                Field('filled_ballot','text'),
                Field('results','text'),
                Field('receipt_uuid','text'))

                
