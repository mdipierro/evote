from gluon import *
import re, hashlib
from uuid import uuid4
try:
    import ast
    have_ast=True
except:
    have_ast=False

regex = re.compile('{{(\w+)\!?}}')
regex_email = re.compile('[\w_\-\.]+\@[\w_\-\.]+')


SAMPLE = """
<h2>Election Title</h2>

<p>This is a ballot!</p>

<table>
<tr><td>Candidate 1</td><td>{{0}}</td></tr>
<tr><td>Candidate 2</td><td>{{0}}</td></tr>
<tr><td>Candidate 3</td><td>{{0}}</td></tr>
</table>

<p>or</p>

<table>
<tr><td>Candidate 1</td><td>{{1}} yes</td><td>{{1}} no</td><td>{{1!}} abstain</td></tr>
<tr><td>Candidate 2</td><td>{{2}} yes</td><td>{{2}} no</td><td>{{2!}} abstain</td></tr>
<tr><td>Candidate 3</td><td>{{3}} yes</td><td>{{3}} no</td><td>{{3!}} abstain</td></tr>
</table>
"""


def uuid():
    return str(uuid4()).replace('-','')

def sign(text,secret):
    return text+'-'+hashlib.sha1(text+secret).hexdigest()

def unpack_results(results):
    return ast.literal_eval(results) if have_ast else eval(results)

def ballot2form(ballot,readonly=False,counters=None,filled=False):
    """ if counters is passed this counts the results in the ballot """    
    radioes = {}    
    if isinstance(counters,dict): readonly=True
    def radio(item):        
        name = "ck_"+item.group(1)       
        value = radioes[name] = radioes.get(name,0)+1        
        if isinstance(counters,dict):
            return INPUT(_type='text',_readonly=True,
                         _value=counters.get((name,value),0),
                         _style="width:3em").xml()
        if not counters is None and 'x' in item.group().lower():
            counters[name,value] = counters.get((name,value),0)+1            
        return INPUT(_type='radio',_name=name,_value=value,
                     _checked=('!' in item.group()),
                     _disabled=readonly).xml()    
    body = regex.sub(radio,ballot)
    form = FORM(XML(body),not readonly and INPUT(_type='submit', _value="Vote!") or '',_class="ballot")
    if not readonly: form.process(formname="ballot")
    return form

def form2ballot(ballot,token,vars,results):    
    radioes = {}
    def check(item):
        name = 'ck_'+item.group(1)
        value = radioes[name] = radioes.get(name,0)+1
        checked = vars.get(name,0)==str(value)
        if isinstance(results,dict): results[(name,value)] = checked
        return INPUT(_type="radio",_name=name,_value=value,
                     _disabled=True,_checked=checked).xml()
    ballot_content = regex.sub(check,ballot)
    if token: ballot_content += '<hr/><pre>\n%s\n</pre><hr/>' % token
    return '<div class="ballot">%s</div>' % ballot_content.strip()

def blank_ballot(token):
    ballot_content = '<h2>Blank</h2>'
    if token: ballot_content += '<hr/><pre>\n%s\n</pre><hr/>' % token
    return '<div class="ballot">%s</div>' % ballot_content
