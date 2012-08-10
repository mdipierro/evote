debug_mode = False

from ballot import ballot2form, form2ballot, sign, uuid, regex_email, SAMPLE

def index():
    return dict()

@auth.requires_login()
def elections():
    POLICY = {'election':True, 'voter':False}
    db.election.secret.default = 'secret-'+uuid()
    db.election.title.default = 'Election title (edit this)'
    db.election.ballot.default = SAMPLE
    db.election.voters.default = auth.user.email
    db.election.emails.default = auth.user.email
    db.election.secret.default = 'secret-'+uuid()
    grid = SQLFORM.smartgrid(
        db.election,
        constraints = {'election':db.election.created_by==auth.user.id},
        linked_tables = ['voter'],
        details=False, create = POLICY, editable = POLICY, deletable = POLICY,
        links = {'election': [
                lambda row:A('View',_href=URL('start',args=row.id)),
                lambda row:A('Tokens',_href=URL('tokens',args=row.id)),
                lambda row:A('Results',_href=URL('results',args=row.id))]})
    return dict(grid=grid)

def results():
    try:
        import ast
        have_ast=True
    except:
        have_ast=False
    id = request.args(0,cast=int) or redirect(URL('index'))
    election = db.election(id) or redirect(URL('index'))
    if auth.user_id!=election.created_by and not(election.deadline \
            and request.now>election.deadline):
        session.flash = 'Results not yet available'
        redirect(URL('index'))
    receipts = db(db.receipt.election==election.id).select()
    response.subtitle = election.title
    counters = {}
    for receipt in receipts:
        results = ast.literal_eval(receipt.results) if have_ast else eval(receipt.results)
        for key in results:
            counters[key] = counters.get(key,0) + results[key]
    form = ballot2form(election.ballot,counters=counters)
    return dict(form=form,receipts=receipts)

def tokens():
    id = request.args(0,cast=int) or redirect(URL('index'))
    election = db.election(id) or redirect(URL('index'))
    response.subtitle = election.title
    tokens_unused = db(db.voter.election==election.id)(db.voter.token!=None)\
        .select(db.voter.token,orderby=db.voter.token)
    tokens_used = db(db.receipt.election==election.id)(db.receipt.token!=None)\
        .select(db.receipt.token,orderby=db.receipt.token)
    return dict(tokens_used=tokens_used, tokens_unused=tokens_unused,
                election=election)

def receipt():
    receipt = db.receipt(signature=request.args(0)) \
        or redirect(URL('invalid_link'))
    election = db.election(receipt.election)
    response.subtitle = election.title
    return dict(receipt=receipt)

def start():
    election = db.election(request.args(0,cast=int)) or redirect('index')
    response.subtitle = election.title
    demo = ballot2form(election.ballot,readonly=True)
    form = FORM(INPUT(_type='submit',_value='Email voters to start election'))
    failures = []
    if form.process().accepted:
        for email in regex_email.findall(election.voters):
            voter = db(db.voter.election==election.id)\
                (db.voter.email==email).select().first()
            voter_uuid = voter.uuid if voter else 'voter-'+uuid()
            token_uuid = voter.token if voter else \
                'token-'+sign(uuid(),election.secret)
            message = VOTE_MESSAGE % dict(
                title = election.title,
                link = URL('vote',args=voter_uuid,scheme='https'))
            if mail.send(to=email,subject=election.title,message=message):
                if not voter:
                    db.voter.insert(election=election.id,
                                    uuid=voter_uuid,token=token_uuid,
                                        email=email,invited_on=request.now)
            else:
                failures.append(email)
        if not failures:
            session.flash = 'Emails sent successfully'
            redirect(URL('index'))
    return dict(demo=demo,form=form,failures=failures)

def invalid_link():
    return dict(message='Invalid Link')

def voted_already():
    return dict(message='You already voted')

def vote():    
    import pickle, hashlib, cStringIO
    voter_uuid = request.args(0) or redirect('index')
    voter = db.voter(uuid=voter_uuid)
    if not voter:
        redirect(URL('invalid_link'))
    if not debug_mode and voter.voted_on!=None:
        redirect(URL('voted_already'))
    election = db.election(voter.election)    
    if election.deadline and request.now>election.deadline:
        session.flash = 'Election is closed'
        redirect(URL('results',args=election.id))
    response.subtitle = election.title
    form = ballot2form(election.ballot,readonly=False)
    signature = None
    if form.accepted:
        results = {}
        ballot = form2ballot(election.ballot,voter.token,
                             vars=request.vars,results=results)
        signature = 'receipt-'+\
            sign(hashlib.sha1(ballot).hexdigest(),election.secret)
        db.receipt.insert(election=election.id,results=str(results),
                          ballot=ballot,signature=signature,
                          token=voter.token)
        voter.update_record(voted_on=request.now,token=None)
        message = VOTED_MESSAGE % dict(            
            title=election.title,
            receipt=URL('receipt',args=signature,scheme='http'))
        attachment = mail.Attachment(filename=signature+'.ballot',
                                     payload=cStringIO.StringIO(ballot))
        for email in regex_email.findall(election.emails):
            mail.send(to=email,
                      subject='Copy of Receipt for %s' % election.title,
                      message=message,attachments=[attachment])
        if mail.send(to=voter.email,
                     subject='Receipt for %s' % election.title,
                     message=message,attachments=[attachment]):
            session.flash = 'Your vote was recored and we sent you an email'
        else:
            session.flash = 'Your vote was recored but we failed to email you'
        redirect(URL('receipt',args=signature))
    return dict(form=form,signature=signature)

def user():
    return dict(form=auth())
