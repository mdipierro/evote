debug_mode = False

from ballot import ballot2form, form2ballot, blank_ballot, \
    sign, uuid, regex_email, unpack_results, rsakeys

def index():
    return dict()

@auth.requires_login()
def elections():
    response.subtitle = T('My Elections')
    elections = db(db.election.created_by==auth.user.id).select(
        orderby=~db.election.created_on)
    return dict(elections=elections)

@auth.requires_login()
def edit():
    response.subtitle = T('Edit Ballot')
    election = db.election(request.args(0,cast=int,default=0))
    if election and not election.created_by==auth.user_id:
        redirect(URL('not_authorized'))
    if not election:
        (pubkey, privkey) = rsakeys()
        db.election.voters.default = auth.user.email
        db.election.managers.default = auth.user.email
        db.election.public_key.default = pubkey
        db.election.private_key.default = privkey        
    form = SQLFORM(db.election,election,deletable=True,
                   submit_button="Save and Preview").process()
    if form.accepted: redirect(URL('start',args=form.vars.id))
    return dict(form=form)

@auth.requires_login()
def start():    
    import hashlib
    election = db.election(request.args(0,cast=int)) or redirect(URL('index'))
    response.subtitle = election.title+T(' / Start')
    demo = ballot2form(election.ballot_model)
    return dict(demo=demo,election=election)

@auth.requires_login()
def start_callback():
    import hashlib
    election = db.election(request.args(0,cast=int)) or redirect(URL('index'))
    form = FORM(INPUT(_type='submit',
                      _value=T('Email Voters and Start Election Now!')))
    failures = []
    if form.process().accepted:
        ballot_counter = db(db.ballot.election_id==election.id).count()
        for email in regex_email.findall(election.voters):
            voter = db(db.voter.election_id==election.id)\
                (db.voter.email==email).select().first()
            if voter:
                voter_uuid = voter.voter_uuid
            else:
                # create a voter
                voter_uuid = 'voter-'+uuid()
                db.voter.insert(
                    election_id=election.id,
                    voter_uuid=voter_uuid,
                    email=email,invited_on=request.now)
                # create a ballot
                ballot_counter+=1
                ballot_uuid = 'ballot-%i-%.6i' % (election.id,ballot_counter)
                blank_ballot_content = blank_ballot(ballot_uuid)
                signature = 'signature-'+sign(blank_ballot_content,
                                              election.private_key)
                db.ballot.insert(
                    election_id=election.id,
                    ballot_content = blank_ballot_content,
                    ballot_uuid=ballot_uuid,
                    signature = signature)
            link = URL('vote',args=(election.id,voter_uuid),scheme='https')
            message = message_replace(election.vote_email,
                              title=election.title,link=link)
            if not mail.send(to=email,subject=election.title,message=message):
                failures.append(email)
        if not failures:
            session.flash = T('Emails sent successfully')
            redirect(URL('elections'),client_side=True)
    return dict(form=form,failures=failures,election=election)

def results():
    id = request.args(0,cast=int) or redirect(URL('index'))
    election = db.election(id) or redirect(URL('index'))
    if auth.user_id!=election.created_by and \
            not(election.deadline and request.now>election.deadline):
        session.flash = T('Results not yet available')
        redirect(URL('index'))
    voted_ballots = db(db.ballot.election_id==election.id)\
        (db.ballot.voted==True).select()
    response.subtitle = election.title + T(' / Results')
    counters = {}
    for ballot in voted_ballots:
        results = unpack_results(ballot.results)
        for key in results:
            counters[key] = counters.get(key,0) + results[key]
    form = ballot2form(election.ballot_model,counters=counters)
    return dict(form=form,election=election)

def ballots():
    election = db.election(request.args(0,cast=int)) or \
        redirect(URL('invalid_link'))
    response.subtitle = election.title + T(' / Ballots')
    ballots = db(db.ballot.election_id==election.id).select(
        orderby=db.ballot.ballot_uuid)
    return dict(ballots=ballots,election=election)

def email_voter_and_managers(election,voter,ballot,message):
    import cStringIO
    attachment = mail.Attachment(
        filename=ballot.ballot_uuid+'.html',
        payload=cStringIO.StringIO(ballot.ballot_content))
    ret = mail.send(to=voter.email,
                    subject='Receipt for %s' % election.title,
                    message=message,attachments=[attachment])
    mail.send(to=regex_email.findall(election.managers),
              subject='Copy of Receipt for %s' % election.title,
              message=message,attachments=[attachment])
    return ret

def close_election():
    election = db.election(request.args(0,cast=int)) or \
        redirect(URL('invalid_link'))
    response.subtitle = election.title
    dialog = FORM.confim(T('Close'),
                         {T('Cancel'):URL('elections')})
    if dialog.accepted:
        election.update_record(deadline=request.now)
        voters = db(db.voter.election_id==election.id)\
            (db.voter.voted==False).select()
        ballots = db(db.ballot.election_id==election.id)\
            (db.ballot.voted==False)(db.ballot.assigned==False).select()
        if ballots and len(voters)!=len(ballots):
            session.flash = T('Voted corrupted ballots/voter mismatch')
            redirect(URL('elections'))
        for i in range(len(voters)):
            voter, ballot = voters[i], ballots[i]
            link = URL('ballot',args=ballot.ballot_uuid,scheme='http')
            message = message_replace(election.not_voted_message,
                                      title=election.title,
                                      signature=ballot.signature,link=link)
            email_voter_and_managers(election,voter,ballot,message)
            ballot.update_record(assigned=True)
        session.flash = 'Election Closed!'
        redirect(URL('results',args=election.id))
    return dict(dialog=dialog,election=election)

def ballot():
    ballot_uuid = request.args(0) or redirect(URL('index'))
    election_id = int(ballot_uuid.split('-')[1])
    election = db.election(election_id) or redirect(URL('index'))
    ballot = db.ballot(election_id=election.id,ballot_uuid=ballot_uuid) \
        or redirect(URL('invalid_link'))
    response.subtitle = election.title + T(' / Ballot')
    return dict(ballot=ballot,election=election)

def ballot_verifier():
    response.headers['Content-Type'] = 'text/plain'
    return ballot()

def vote():    
    import hashlib
    election_id = request.args(0,cast=int)
    voter_uuid = request.args(1)
    election = db.election(election_id) or redirect(URL('invalid_link'))       
    voter = db(db.voter.election_id==election_id)\
        (db.voter.voter_uuid==voter_uuid).select().first() or \
        redirect(URL('invalid_link'))
    if not debug_mode and voter.voted:
        redirect(URL('voted_already'))
    
    if election.deadline and request.now>election.deadline:
        session.flash = T('Election is closed')
        if voter.voted:
            session.flash += T('Your vote was recorded')
        else:
            session.flash += T('Your vote was NOT recorded')
        redirect(URL('results',args=election.id))
    response.subtitle = election.title + ' / Vote'
    form = ballot2form(election.ballot_model,readonly=False)
    if form.accepted:
        results = {}
        for_update = not db._uri.startswith('sqlite') # not suported by sqlite
        if not for_update: db.executesql('begin immediate transaction;')
        ballot = db(db.ballot.election_id==election_id)\
            (db.ballot.voted==False).select(
            orderby='<random>',limitby=(0,1),for_update=for_update).first() \
            or redirect(URL('no_more_ballots'))
        ballot_content = form2ballot(election.ballot_model,
                                     token=ballot.ballot_uuid,
                                     vars=request.vars,results=results)        
        signature = 'signature-'+sign(ballot_content,election.private_key)
        ballot.update_record(results=str(results),
                             ballot_content=ballot_content,
                             signature=signature,
                             voted=True,assigned=True,voted_on=request.now)
        voter.update_record(voted=True)
        link = URL('ballot',args=ballot.ballot_uuid,scheme='http')
        message = message_replace(election.voted_email,link=link,
                                  title=election.title,signature=signature)
        emailed = email_voter_and_managers(election,voter,ballot,message)
        session.flash = \
            T('Your vote was recorded and we sent you an email') \
            if emailed else \
            T('Your vote was recorded but we failed to email you')
        redirect(URL('ballot',args=ballot.ballot_uuid))
    return dict(form=form)

def user():
    return dict(form=auth())

def invalid_link():
    return dict(message=T('Invalid Link'))

def voted_already():
    return dict(message=T('You already voted'))

def not_authorized():
    return dict(message=T('Not Authorized'))

def no_more_ballots():
    return dict(message=T('Run out of ballots. Your vote was not recorded'))
