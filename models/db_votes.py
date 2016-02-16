not_empty = IS_NOT_EMPTY()

db.define_table(
    'election',
    Field('title',requires=not_empty),
    Field('ballot_model','text',requires=not_empty), # empty ballot
    Field('voters','text',requires=not_empty),
    Field('managers','text',requires=not_empty),
    Field('deadline','datetime'),
    Field('vote_email','text'),
    Field('voted_email','text'),
    Field('email_sender',requires=IS_EMAIL(),default=mail.settings.sender,writable=False),
    Field('not_voted_email','text'),
    Field('public_key','text',writable=False,readable=False),                
    Field('private_key','text',writable=False,readable=False),                
    Field('counters','text',writable=False,readable=False),                
    Field('closed','boolean',writable=False,readable=False),
    auth.signature,
    format='%(title)s')

db.define_table(
    'voter',
    Field('voter_uuid',writable=False,readable=False),
    Field('election_id',db.election,writable=False),
    Field('email',requires=IS_EMAIL()),
    Field('voted','boolean',default=False),
    Field('invited_on','datetime'))

db.define_table(
    'ballot',
    Field('election_id',db.election),
    Field('ballot_content','text'),  # voted or blank ballot
    Field('assigned','boolean',default=False),
    Field('voted','boolean',default=False),
    Field('voted_on','datetime',default=None),
    Field('results','text',default='{}'),
    Field('ballot_uuid'), # uuid embedded in ballot
    Field('signature')) # signature of ballot (voted or blank)


# if resticted to some users get the list of users
def load_users_emails(filename=myconf.take('app.users_filename')):
    import urllib, os
    if not filename:
        return None
    elif filename.startswith('http://') or filename.startswith('https://'):
        emails = urllib.urlopen(filename).read().split('\n')
    else:
        if not filename.startswith('/'):
            filename = os.path.join(request.folder, filename)
        emails = open(filename).read().split('\n')
    emails = [email.strip() for email in emails if email.strip()]
    return emails
users_emails = cache.ram('users_emails',load_users_emails,3600)
