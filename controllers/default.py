from ballot import ballot2form, form2ballot, blank_ballot, \
    sign, uuid, regex_email, unpack_results, rsakeys, \
    pack_counters, unpack_counters
from ranking_algorithms import iro, borda, schulze
import re

def index():
    return dict()

@auth.requires_login()
def elections():
    response.subtitle = T('My Elections')
    elections = db(db.election.created_by==auth.user.id).select(
        orderby=~db.election.created_on)
    ballots = db(db.voter.email == auth.user.email)(
        db.voter.voted==False)(db.voter.election_id==db.election.id)(
        (db.election.deadline==None)|(db.election.deadline>request.now)).select()
    return dict(elections=elections,ballots=ballots)

@auth.requires(auth.user and auth.user.is_manager)
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

@auth.requires(auth.user and auth.user.is_manager)
def start():    
    election = db.election(request.args(0,cast=int)) or redirect(URL('index'))
    check_closed(election)
    response.subtitle = election.title+T(' / Start')
    demo = ballot2form(election.ballot_model)
    return dict(demo=demo,election=election)

@auth.requires(auth.user and auth.user.is_manager)
def start_callback():
    election = db.election(request.args(0,cast=int)) or redirect(URL('index'))
    check_closed(election)
    form = SQLFORM.factory(
        submit_button=T('Email Voters and Start Election Now!'))
    form.element(_type='submit').add_class('btn')
    failures = []
    emails = []
    owner_email = election.created_by.email
    if form.process().accepted:
        ballot_counter = db(db.ballot.election_id==election.id).count()
        for email in regex_email.findall(election.voters):
            email = email.lower()
            voter = db(db.voter.election_id==election.id)\
                (db.voter.email==email).select().first()
            if voter:
                voter_uuid = voter.voter_uuid
            else:
                # create a voter
                voter_uuid = 'voter-'+uuid()
                voter = db.voter.insert(
                    election_id=election.id,
                    voter_uuid=voter_uuid,
                    email=email,invited_on=None)
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
            link_vote = URL('vote',args=(election.id,voter_uuid),scheme=SCHEME)
            link_ballots = URL('ballots',args=election.id,scheme=SCHEME)
            link_results = URL('results',args=election.id,scheme=SCHEME)
            message = message_replace(election.vote_email,
                                      election_id = election.id,
                                      owner_email = owner_email,
                                      title=election.title,
                                      link=link_vote,
                                      link_ballots=link_ballots,
                                      link_results=link_results)
            subject = '%s [%s]' % (election.title, election.id)
            emails.append((voter,email,subject,message))
        db.commit()
        sender = election.email_sender or mail.settings.sender
        for voter, to, subject, message in emails:
            if meta_send2(to=to,subject=subject,message=message,
                          sender=sender, reply_to=sender):
                db(db.voter.id==voter).update(invited_on=request.now)
            else:
                failures.append(to)
        if not failures:
            session.flash = T('Emails sent successfully')
            redirect(URL('elections'),client_side=True)
    return dict(form=form,failures=failures,election=election)


@auth.requires(False) # for now this is disabled
def self_service():
    form = SQLFORM.factory(
        Field('election_id','integer',requires=IS_NOT_EMPTY()),
        Field('email',requires=IS_EMAIL()))
    if form.process.accepted():
        election = db.election(form.vars.id)
        if not election: form.errors['election_id'] = 'Invalid'
        voter = db.voter(election=election_id,email=form.vars.email)
        if not voter: form.errors['voter'] = 'Invalid'
        if voter.voted:
            response.flash = T('User has voted alreday')
        else:
            link_vote = URL('vote',args=(election.id,voter_uuid),scheme=SCHEME)
            link_ballots = URL('ballots',args=election.id,scheme=SCHEME)
            link_results = URL('results',args=election.id,scheme=SCHEME)
            message = message_replace(election.vote_email,
                                      election_id = election.id,
                                      owner_email = owner_email,
                                      title=election.title,
                                      link=link_vote,
                                      link_ballots=link_ballots,
                                      link_results=link_results)
            sender = election.email_sender or mail.settings.sender
            if meta_send2(to=voter.email,subject=election.title,
                          message=message,
                          sender=sender, reply_to=sender):
                response.flash = T('Email sent')
            else:
                response.flash = T('Unable to send email')
    return dict(form=form)
                                

@auth.requires(auth.user and auth.user.is_manager)
def reminders():    
    election = db.election(request.args(0,cast=int)) or redirect(URL('index'))
    response.subtitle = election.title+T(' / Reminders')
    return dict(election=election)

@auth.requires(auth.user and auth.user.is_manager)
def reminders_callback():
    election = db.election(request.args(0,cast=int)) or redirect(URL('index'))
    owner_email = election.created_by.email
    failures = []
    emails = []
    fields = []
    for email in regex_email.findall(election.voters):
        voter = db(db.voter.election_id==election.id)\
            (db.voter.email==email).select().first()
        voter_uuid = voter.voter_uuid
        key = 'voter_%s' % voter.id
        fields.append(Field(key,'boolean',default=not voter.voted,
                            label = voter.email))
        if key in request.post_vars:            
            link = URL('vote',args=(election.id,voter_uuid),scheme=SCHEME)
            link_ballots = URL('ballots',args=election.id,scheme=SCHEME)
            link_results = URL('results',args=election.id,scheme=SCHEME)
            message = message_replace(election.vote_email,
                                      election_id = election.id,
                                      owner_email = owner_email,
                                      title=election.title,
                                      link=link,
                                      link_ballots=link_ballots,
                                      link_results=link_results)
            subject = '%s [%s]' % (election.title, election.id)
            emails.append((email,subject,message))
    form = SQLFORM.factory(*fields).process()
    if form.accepted:
        sender = election.email_sender or mail.settings.sender
        for to, subject, message in emails:
            if not meta_send2(to=to,subject=subject,message=message,
                              sender=sender, reply_to=sender):
                failures.append(email)
        if not failures:
            session.flash = T('Emails sent successfully')
            redirect(URL('elections'),client_side=True)
    return dict(form=form,failures=failures,election=election)

@auth.requires(auth.user and auth.user.is_manager)
def recompute_results():
    election = db.election(request.args(0,cast=int)) or redirect(URL('index'))
    compute_results(election)
    redirect(URL('results',args=election.id))

def compute_results(election):
    voted_ballots = db(db.ballot.election_id==election.id
                       )(db.ballot.voted==True).select()
    counters = {}
    rankers = {}
    for k,ballot in enumerate(voted_ballots):
        results = unpack_results(ballot.results)
        for key in results:
            # name is the name of a group as in {{name:ranking}}
            # scheme is "ranking" or "checkbox" (default)
            # value is the <input value="value"> assigned to this checkbox or input
            (name,scheme,value) = key 
            if scheme == 'checkbox':
                # counters[key] counts how many times this checkbox was checked
                counters[key] = counters.get(key,0) + (
                    1 if results[key] else 0)                
            elif scheme == 'ranking':
                # rankers[name] = [[2,1,3],[3,1,2],[1,2,3],...]
                #                 The sublists in rankers mean:
                #                 [[my first-preferred candidate is
                #                   the candidate whose identifying
                #                   number on the original ballot was
                #                   <the number given in this first
                #                   position here>],
                #                  [my second-preferred candidate is
                #                   the candidate whose identifying
                #                   number on the original ballot was
                #                   <the number given in this second
                #                   position here>],
                #                  [my third-preferred candidate is
                #                   the candidate whose identifying
                #                   number on the original ballot was
                #                   <the number given in this third
                #                   position here>], ...]
                #
                # len(rankers[name]) = len(voted_ballots)
                # rankers[name][i][0] = ...?
                if not name in rankers:
                    rankers[name] = []
                if len(rankers[name])<k+1:
                    rankers[name].append([])
                vote = rankers[name][-1]
                print "ballot id:",ballot.id, "key:",key, "results[key]:",results[key], "vote:",vote
                ranking = int(results[key])
                d = ranking-len(vote)
                if d>0:
                    print "vote before:", vote
                    vote+=[0]*d
                    print "vote after: ", vote
                vote[ranking-1] = value
            else:
                raise RuntimeError("Invalid Voting Scheme")    
    for name in rankers:
        votes = rankers[name]
        cmajority = borda(votes,mode='exponential')
        ciro = iro(votes)
        cschulze = schulze(votes)
        for (r,k) in cmajority:
            counters[(name,'ranking',k)] = 'M:%s' % r
        for (r,k) in ciro:
            counters[(name,'ranking',k)] += ' I:%s' % r
        for (r,k) in cschulze:
            counters[(name,'ranking',k)] += ' S:%s' % r
    election.update_record(counters=pack_counters(counters))

#@cache(request.env.path_info,time_expire=300,cache_model=cache.ram)
def results():
    id = request.args(0,cast=int) or redirect(URL('index'))
    election = db.election(id) or redirect(URL('index'))
    if auth.user_id!=election.created_by and \
            not(election.deadline and request.now>election.deadline):
        session.flash = T('Results not yet available')
        redirect(URL('index'))
    response.subtitle = election.title + T(' / Results')
    if DEBUG_MODE or not election.counters:
        compute_results(election)
    form = ballot2form(election.ballot_model,
                       counters=unpack_counters(election.counters))
    return dict(form=form,election=election)

def hash_ballot(text):
    import re
    text = text.replace('checked="checked" ','')
    text = text.replace('disabled="disabled" ','')
    text = re.sub('value="\d+"','',text)
    text = re.sub('ballot\S+','',text)
    return hash(text)

def ballots():
    election = db.election(request.args(0,cast=int)) or \
        redirect(URL('invalid_link'))
    response.subtitle = election.title + T(' / Ballots')
    ballots = db(db.ballot.election_id==election.id).select(        
        orderby=db.ballot.ballot_uuid)
    tampered = len(set(hash_ballot(b.ballot_content) 
                       for b in ballots if b.voted))>1
    return dict(ballots=ballots,election=election, tampered=tampered)

# @auth.requires(auth.user and auth.user.is_manager)
def email_voter_and_managers(election,voter,ballot,message):
    import cStringIO
    attachment = mail.Attachment(
        filename=ballot.ballot_uuid+'.html',
        payload=cStringIO.StringIO(ballot.ballot_content))
    sender = election.email_sender or mail.settings.sender
    ret = meta_send(to=voter.email,
                    subject='Receipt for %s' % election.title,
                    message=message,attachments=[attachment],
                    sender=sender, reply_to=sender)
    meta_send(to=regex_email.findall(election.managers),
              subject='Copy of Receipt for %s' % election.title,
              message=message,attachments=[attachment],
              sender=sender, reply_to=sender)
    return ret

def check_closed(election):
    if election.closed:
        session.flash = T('Election already closed')
        redirect(URL('elections'))

@auth.requires(auth.user and auth.user.is_manager)
def close_election():
    import zipfile, os
    election = db.election(request.args(0,cast=int)) or \
        redirect(URL('invalid_link'))
    check_closed(election)
    response.subtitle = election.title
    dialog = FORM.confirm(T('Close'),
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
        owner_email = election.created_by.email
        for i in range(len(voters)):
            voter, ballot = voters[i], ballots[i]
            link = URL('ballot',args=ballot.ballot_uuid,scheme='http')
            message = message_replace(election.not_voted_email,
                                      election_id=election.id,
                                      owner_email = owner_email,
                                      title=election.title,
                                      signature=ballot.signature,link=link)
            email_voter_and_managers(election,voter,ballot,message)
            ballot.update_record(assigned=True)
        compute_results(election)
        zippath = os.path.join(request.folder,'static','zips')
        if not os.path.exists(zippath):
            os.mkdir(zippath)
        archive = zipfile.ZipFile(
            os.path.join(zippath,'%s.zip' % election.id),'w')
        dbset = db(db.ballot.election_id==election.id)
        ballots = dbset.select()
        for ballot in ballots:
            archive.writestr(ballot.ballot_uuid,ballot.ballot_content)
        ballots = dbset.select(
            db.ballot.election_id,
            db.ballot.ballot_uuid,
            db.ballot.assigned,
            db.ballot.voted,
            db.ballot.voted_on,
            db.ballot.signature,
            orderby=db.ballot.ballot_uuid)
        archive.writestr('ballots.csv',str(ballots))
        archive.close()
        election.update_record(closed=True)
        session.flash = 'Election Closed!'
        redirect(URL('results',args=election.id))
    return dict(dialog=dialog,election=election)

def ballot():
    ballot_uuid = request.args(0) or redirect(URL('index'))
    signature = request.args(1)
    election_id = int(ballot_uuid.split('-')[1])
    election = db.election(election_id) or redirect(URL('index'))
    ballot = db.ballot(election_id=election.id,ballot_uuid=ballot_uuid) \
        or redirect(URL('invalid_link'))
    if (not election.deadline or election.deadline>request.now) \
            and ballot.signature!=signature:
        session.flash = "your ballot is not visible until election is closed"
        redirect(URL('index'))
    response.subtitle = election.title + T(' / Ballot')
    return dict(ballot=ballot,election=election)

def recorded():
    return dict()

def ballot_verifier():
    response.headers['Content-Type'] = 'text/plain'
    return ballot()

def vote():    
    import hashlib
    response.menu = []
    election_id = request.args(0,cast=int)
    voter_uuid = request.args(1)
    election = db.election(election_id) or redirect(URL('invalid_link'))       
    voter = db(db.voter.election_id==election_id)\
        (db.voter.voter_uuid==voter_uuid).select().first() or \
        redirect(URL('invalid_link'))
    if not DEBUG_MODE and voter.voted:
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
        #if not for_update: db.executesql('begin immediate transaction;')
        ballot = db(db.ballot.election_id==election_id)\
            (db.ballot.voted==False).select(
            orderby='<random>',limitby=(0,1),for_update=for_update).first() \
            or redirect(URL('no_more_ballots'))
        ballot_content = form2ballot(election.ballot_model,
                                     token=ballot.ballot_uuid,
                                     vars=request.post_vars,results=results)
        signature = 'signature-'+sign(ballot_content,election.private_key)
        ballot.update_record(results=str(results),
                             ballot_content=ballot_content,
                             signature=signature,
                             voted=True,assigned=True,voted_on=request.now)
        voter.update_record(voted=True)
        link = URL('ballot',args=(ballot.ballot_uuid,ballot.signature),
                   scheme='http')

        message = message_replace(election.voted_email,link=link,
                                  election_id=election.id,
                                  owner_email = election.created_by.email,
                                  title=election.title,signature=signature)
        emailed = email_voter_and_managers(election,voter,ballot,message)
        session.flash = \
            T('Your vote was recorded and we sent you an email') \
            if emailed else \
            T('Your vote was recorded but we failed to email you')
        redirect(URL('recorded',vars=dict(link=link)))
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

@auth.requires(auth.user and auth.user.is_manager)
def voters_csv():
    election = db.election(request.args(0,cast=int,default=0),created_by=auth.user.id)
    return db(db.voter.election_id==election.id).select(
        db.voter.election_id,db.voter.email,db.voter.voted).as_csv()

def features():
    return locals()

def support():
    return locals()

def contactus():
    return locals()
