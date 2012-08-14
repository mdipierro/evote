debug_mode = False

from ballot import ballot2form, form2ballot, blank_ballot, \
    sign, uuid, regex_email, SAMPLE, unpack_results, rsakeys

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
    election = db.election(request.args(0,cast=int,default=0))
    if election and not election.created_by==auth.user_id:
        redirect(URL('not_authorized'))
    if not election:
        (pubkey, privkey) = rsakeys()
        db.election.title.default = 'Election title (edit this)'
        db.election.ballot_model.default = SAMPLE
        db.election.voters.default = auth.user.email
        db.election.managers.default = auth.user.email
        db.election.public_key.default = pubkey
        db.election.private_key.default = privkey        
    form = SQLFORM(db.election,election,
                   submit_button="Save and Preview").process()
    if form.accepted: redirect(URL('start',args=form.vars.id))
    return dict(form=form)

@auth.requires_login()
def start():    
    import hashlib
    election = db.election(request.args(0,cast=int)) or redirect(URL('index'))
    response.subtitle = election.title+' / Start'
    demo = ballot2form(election.ballot_model)
    return dict(demo=demo,election=election)

@auth.requires_login()
def start_callback():
    import hashlib
    election = db.election(request.args(0,cast=int)) or redirect(URL('index'))
    response.subtitle = election.title+' / Start'
    form = FORM(INPUT(_type='submit',_value='Email Voters and Start Election Now!'))
    failures = []
    if form.process().accepted:
        ballot_counter = db(db.ballot.election_id==election.id).count()
        for email in regex_email.findall(election.voters):
            voter = db(db.voter.election_id==election.id)\
                (db.voter.email==email).select().first()
            voter_uuid = voter.voter_uuid if voter else 'voter-'+uuid()
            message = VOTE_MESSAGE % dict(
                title = election.title,
                link = URL('vote',args=voter_uuid,scheme='https'))
            if mail.send(to=email,subject=election.title,message=message):
                if not voter:
                    ballot_counter+=1
                    ballot_uuid = '%i-%i' % (election.id,ballot_counter)
                    blank_ballot_content = blank_ballot(ballot_uuid)
                    signature = sign(blank_ballot_content,election.private_key)
                    db.voter.insert(
                        election_id=election.id,
                        voter_uuid=voter_uuid,
                        email=email,invited_on=request.now)
                    db.ballot.insert(
                        election_id=election.id,
                        ballot_content = blank_ballot_content,
                        ballot_uuid=ballot_uuid,
                        signature = signature)
            else:
                failures.append(email)
        if not failures:
            session.flash = 'Emails sent successfully'
            redirect(URL('elections'),client_side=True)
    return dict(form=form,failures=failures,election=election)

def results():
    id = request.args(0,cast=int) or redirect(URL('index'))
    election = db.election(id) or redirect(URL('index'))
    if auth.user_id!=election.created_by and not(election.deadline \
            and request.now>election.deadline):
        session.flash = 'Results not yet available'
        redirect(URL('index'))
    voted_ballots = db(db.ballot.election_id==election.id)\
        (db.ballot.voted==True).select()
    response.subtitle = election.title + ' / Results'
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
    response.subtitle = election.title + ' / Ballots'
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
            session.flash = 'Voted corrupted ballots/voter mismatch'
            redirect(URL('elections'))
        for i in range(len(voters)):
            voter, ballot = voters[i], ballots[i]
            message = NOT_VOTED_MESSAGE % dict(            
                title=election.title,signature=ballot.signature,
                ballot=URL('ballot',args=ballot.ballot_uuid,scheme='http'))
            email_voter_and_managers(election,voter,ballot,message)
            ballot.update_record(assigned=True)
        session.flash = 'Election Closed!'
        redirect(URL('results',args=election.id))
    return dict(dialog=dialog,election=election)

def ballot():
    ballot_uuid = request.args(0)
    election_id = int(ballot_uuid.split('-')[0])
    election = db.election(election_id)  
    ballot = db.ballot(election_id=election.id,ballot_uuid=ballot_uuid) \
        or redirect(URL('invalid_link'))
    response.subtitle = election.title + ' / Ballot'
    return dict(ballot=ballot,election=election)

def vote():    
    import hashlib
    voter_uuid = request.args(0) or redirect(URL('index'))
    voter = db.voter(voter_uuid=voter_uuid)
    if not voter:
        redirect(URL('invalid_link'))
    if not debug_mode and voter.voted:
        redirect(URL('voted_already'))
    election = db.election(voter.election_id)    
    if election.deadline and request.now>election.deadline:
        session.flash = 'Election is closed. '
        if voter.voted:
            session.flash += 'Your vote was recorded'
        else:
            session.flash += 'Your vote was NOT recorded'
        redirect(URL('results',args=election.id))
    response.subtitle = election.title + ' / Vote'
    form = ballot2form(election.ballot_model,readonly=False)
    if form.accepted:
        results = {}
        ballot = db(db.ballot.voted==False).select(
            orderby='<random>',limitby=(0,1)).first()
        if not ballot:
            redirect(URL('no_more_ballots'))
        ballot_content = form2ballot(election.ballot_model,
                                     token=ballot.ballot_uuid,
                                    vars=request.vars,results=results)
        signature = sign(ballot_content,election.private_key)
        ballot.update_record(results=str(results),
                             ballot_content=ballot_content,
                             signature=signature,
                             voted=True,assigned=True,voted_on=request.now)
        voter.update_record(voted=True)
        message = VOTED_MESSAGE % dict(            
            title=election.title,signature=signature,
            ballot=URL('ballot',args=ballot.ballot_uuid,scheme='http'))
        if email_voter_and_managers(election,voter,ballot,message):
            session.flash = 'Your vote was recorded and we sent you an email'
        else:
            session.flash = 'Your vote was recorded but we failed to email you'
        redirect(URL('ballot',args=ballot.ballot_uuid))
    return dict(form=form)

def user():
    return dict(form=auth())

def invalid_link():
    return dict(message='Invalid Link')

def voted_already():
    return dict(message='You already voted')

def not_authorized():
    return dict(message='Not Authorized')

def no_more_ballots():
    return dict(message='Run out of ballots. Your vote was not recorded')
