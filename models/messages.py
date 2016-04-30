db.election.title.default = 'Election title'

db.election.ballot_model.default = """
<h2>Election Title</h2>

<p>This is a sample ballot!  You can replace this text with anything you want.  The explanations and examples here are just to help you.  You should replace the explanations with whatever explanations you think will be most useful to your voters, and replace the examples with your actual candidate groups.</p>

<p>This first group places three candidates in a ranked-choice election.  The identifier surrounded by curly braces, <tt>&#123;&#123;group_one&#125;&#125;</tt>, is what tells E-Vote that these candidates are to be ranked against each other but not against other candidates in other labeled groups on this ballot.  Note that the voter will be able to drag these candidates into her preferred order, using the mouse:</p>

<ul>
<li>{{group_one:ranking}} Candidate A in a ranked-choice group</li>
<li>{{group_one:ranking}} Candidate B in a ranked-choice group</li>
<li>{{group_one:ranking}} Candidate C in a ranked-choice group</li>
</ul>

<p>The second group, identified by the <tt>&#123;&#123;group_two&#125;&#125;</tt>, involves four candidates, from whom the voter must choose exactly one (since browser radio buttons don't have a way to do "uncheck all" once one has been selected, it is typical to offer an "Abstain" option here):</p>

<table>
<tr><td>Candidate 1</td><td>{{group_two}}</td></tr>
<tr><td>Candidate 2</td><td>{{group_two}}</td></tr>
<tr><td>Candidate 3</td><td>{{group_two}}</td></tr>
<tr><td>Candidate 4</td><td>{{group_two}}</td></tr>
<tr><td>Abstain</td><td>{{group_two}}</td></tr>
</table>

<p>The next section lists a set of five candidates among whom voters are asked to do <em>approval voting</em>, that is, to vote "yes" for those candidates they approve of, "no" for those they don't approve, or to vote "abstain" if they have no opinion.  The way we specify that here is a little tricky: each candidate is its <em>own</em> group&nbsp;&mdash;&nbsp;we use labels like <tt>&#123;&#123;candidate_1&#125;&#125;</tt>, <tt>&#123;&#123;candidate_2&#125;&#125;</tt>, etc here for clarity, but they could as easily be <tt>&#123;&#123;snufflewhump&#125;&#125;</tt>, <tt>&#123;&#123;firenze&#125;&#125;</tt>, etc.  It doesn't matter what the labels are, so long as they are consistent across the target candidate and different from any other candidate on this page:</p>

<table>
<tr><td>Candidate 1</td><td>{{candidate_1}} yes</td><td>{{candidate_1}} no</td><td>{{candidate_1!}} abstain</td></tr>
<tr><td>Candidate 2</td><td>{{candidate_2}} yes</td><td>{{candidate_2}} no</td><td>{{candidate_2!}} abstain</td></tr>
<tr><td>Candidate 3</td><td>{{candidate_3}} yes</td><td>{{candidate_3}} no</td><td>{{candidate_3!}} abstain</td></tr>
<tr><td>Candidate 4</td><td>{{candidate_4}} yes</td><td>{{candidate_4}} no</td><td>{{candidate_4!}} abstain</td></tr>
<tr><td>Candidate 5</td><td>{{candidate_5}} yes</td><td>{{candidate_5}} no</td><td>{{candidate_5!}} abstain</td></tr>
</table>
"""

db.election.vote_email.default = """
{{=title}}

Link to vote: {{=link}}
Link to ballots: {{=link_ballots}}
Link to results: {{=link_results}}
"""

db.election.voted_email.default = """
{{=title}}

You have voted and your vote has been registered. Thank you!
Here is your ballot.

Your ballot: {{=link}}
A copy is also attached.

Please keep it to verify the integrity of the election.
"""

db.election.not_voted_email.default = """
{{=title}}

Your ballot: {{=link}}

{{=signature}}
(you did not vote, your BLANK ballot is also attached)
"""

def message_replace(message,**vars):
    message = 'Election N.{{=election_id}} by {{=owner_email}}\n\n' + message
    for key in vars:
        message = message.replace('{{=%s}}' % key, str(vars[key]))
    return message

def meta_send(*args, **kwargs):
    if kwargs.get('sender') == myconf.take('smtp.sender'):
        mail.settings.server = myconf.take('smtp.server')
        mail.settings.login = myconf.take('smtp.login')
    return mail.send(*args, **kwargs)

def meta_send2(to,message,reply_to,subject,sender=None):
    import smtplib
    fromaddr = mail.settings.sender
    msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nReply-to: %s\r\n\r\n%s" \
        % (fromaddr, to, subject, reply_to, message)
    try:
        server = None
        server = smtplib.SMTP(mail.settings.server,timeout=5)
        server.ehlo(mail.settings.hostname)
        server.starttls()
        server.ehlo(mail.settings.hostname)
        if mail.settings.login:
            server.login(*mail.settings.login.split(':', 1))
        server.sendmail(fromaddr, [to], msg)
        return True
    except:
        return False
    finally:
        if server:
            server.quit()

