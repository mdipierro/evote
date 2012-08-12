debug_mode = True

from ballot import ballot2form, form2ballot, sign, \
    uuid, regex_email, SAMPLE, unpack_results

def index():
    return dict()

@auth.requires_login()
def elections():
    response.subtitle = 'My Elections'
    elections = db(db.election.created_by==auth.user.id).select(
        orderby=~db.election.created_on)
    return dict(elections=elections)

@auth.requires_login()
def edit():
    response.subtitle = "Edit Ballot"
    db.election.title.default = 'Election title (edit this)'
    db.election.ballot.default = SAMPLE
    db.election.voters.default = auth.user.email
    db.election.managers.default = auth.user.email
    db.election.secret.default = 'secret-'+uuid()
    election = db.election(request.args(0,cast=int,default=0))
    if election and not election.created_by==auth.user_id:
        redirect(URL('not_authorized'))
    form = SQLFORM(db.election,election).process()
    if form.accepted: redirect(URL('start',args=form.vars.id))
    return dict(form=form)

def start():    
    election = db.election(request.args(0,cast=int)) or redirect('index')
    response.subtitle = election.title+' / Start'
    demo = ballot2form(election.ballot)
    form = FORM(INPUT(_type='submit',_value='Email Voters and Start Election Now!'))
    failures = []
    if form.process().accepted:
        for email in regex_email.findall(election.voters):
            voter = db(db.voter.election_id==election.id)\
                (db.voter.email==email).select().first()
            voter_uuid = voter.voter_uuid if voter else 'voter-'+uuid()
            message = VOTE_MESSAGE % dict(
                title = election.title,
                link = URL('vote',args=voter_uuid,scheme='https'))
            if mail.send(to=email,subject=election.title,message=message):
                if not voter:
                    db.voter.insert(election_id=election.id,
                                    voter_uuid=voter_uuid,voted=False,
                                    email=email,invited_on=request.now)
                    token_uuid = 'token-'+sign(uuid(),election.secret)
                    db.token.insert(election_id=election.id,token_uuid=token_uuid)
            else:
                failures.append(email)
        if not failures:
            session.flash = 'Emails sent successfully'
            redirect(URL('elections'))
    return dict(demo=demo,form=form,failures=failures)

def results():
    id = request.args(0,cast=int) or redirect(URL('index'))
    election = db.election(id) or redirect(URL('index'))
    if auth.user_id!=election.created_by and not(election.deadline \
            and request.now>election.deadline):
        session.flash = 'Results not yet available'
        redirect(URL('index'))
    receipts = db(db.receipt.election_id==election.id).select()
    response.subtitle = election.title + ' / Results'
    counters = {}
    for receipt in receipts:
        results = unpack_results(receipt.results)
        for key in results:
            counters[key] = counters.get(key,0) + results[key]
    form = ballot2form(election.ballot,counters=counters)
    return dict(form=form,receipts=receipts,election=election)

def tokens():
    election = db.election(request.args(0,cast=int)) or \
        redirect(URL('invalid_link'))
    response.subtitle = election.title + ' / Tokens'
    tokens = db(db.token.election_id==election.id).select(
        orderby=db.token.token_uuid)
    return dict(tokens=tokens,election=election)

def receipt():
    receipt = db.receipt(receipt_uuid=request.args(0)) \
        or redirect(URL('invalid_link'))
    election = db.election(receipt.election_id)
    response.subtitle = election.title + ' / Receipt'
    return dict(receipt=receipt)


def vote():    
    import pickle, hashlib, cStringIO
    voter_uuid = request.args(0) or redirect('index')
    voter = db.voter(voter_uuid=voter_uuid)
    if not voter:
        redirect(URL('invalid_link'))
    if not debug_mode and voter.voted:
        redirect(URL('voted_already'))
    election = db.election(voter.election_id)    
    if election.deadline and request.now>election.deadline:
        session.flash = 'Election is closed'
        redirect(URL('results',args=election.id))
    response.subtitle = election.title + ' / Vote'
    form = ballot2form(election.ballot,readonly=False)
    if form.accepted:
        results = {}
        token = db(db.token.receipt_uuid==None).select(orderby='<random>',
                                                       limitby=(0,1)).first()
        if not token: redirect(URL('no_more_tokens'))
        ballot = form2ballot(election.ballot,token=token.token_uuid,
                             vars=request.vars,results=results)
        receipt_uuid = 'receipt-'+\
            sign(hashlib.sha1(ballot).hexdigest(),election.secret)
        db.receipt.insert(election_id=election.id,results=str(results),
                          filled_ballot=ballot,receipt_uuid=receipt_uuid)
        token.update_record(receipt_uuid=receipt_uuid, voted_on=request.now)
        voter.update_record(voted=True)
        message = VOTED_MESSAGE % dict(            
            title=election.title,
            receipt=URL('receipt',args=receipt_uuid,scheme='http'))
        attachment = mail.Attachment(filename=receipt_uuid+'.html',
                                     payload=cStringIO.StringIO(ballot))
        for email in regex_email.findall(election.managers):
            mail.send(to=email,
                      subject='Copy of Receipt for %s' % election.title,
                      message=message,attachments=[attachment])
        if mail.send(to=voter.email,
                     subject='Receipt for %s' % election.title,
                     message=message,attachments=[attachment]):
            session.flash = 'Your vote was recored and we sent you an email'
        else:
            session.flash = 'Your vote was recored but we failed to email you'
        redirect(URL('receipt',args=receipt_uuid))
    return dict(form=form)

def user():
    return dict(form=auth())

def invalid_link():
    return dict(message='Invalid Link')

def voted_already():
    return dict(message='You already voted')

def not_authorized():
    return dict(message='Not Authorized')

def no_more_tokens():
    return dict(message='No More Tokens / Vote Not recorded')
