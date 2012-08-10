from gluon import *
import re, hashlib
from uuid import uuid4
regex = re.compile('\((\d+)\!?\)')
regex_email = re.compile('[\w_\-\.]+\@[\w_\-\.]+')

SAMPLE = """
## Election Title

This is a ballot!

Text can be **bold** or ''italic'' and contain links and tables:

-------
Candidate 1 | (0)
Candidate 2 | (0)
Candidate 3 | (0)
-------
(exclusive)

or 

-------
Candidate 1 | (1) yes | (1) no | (1!) abstain
Candidate 2 | (2) yes | (2) no | (2!) abstain
Candidate 3 | (3) yes | (3) no | (3!) abstain
-------
(not exclusive)

The ! identifies a default option between a set of exclusive choices.
"""


def uuid():
    return str(uuid4()).replace('-','')

def sign(text,secret):
    return text+'-'+hashlib.sha1(text+secret).hexdigest()

def ballot2form(ballot,readonly=False,counters=None,filled=False):
    """ if counters is passed this counts the results in the ballot """
    
    radioes = {}    
    if isinstance(counters,dict): readonly=True
    def radio(item):        
        k = int(item.group(1))        
        value = radioes[k] = radioes.get(k,0)+1        
        if isinstance(counters,dict):
            return INPUT(_type='text',_readonly=True,_value=counters.get((k,value),0),_style="width:3em").xml()
        if not counters is None and 'x' in item.group().lower():
            counters[k,value] = counters.get((k,value),0)+1            
        return INPUT(_type='radio',_name='ck%s'%k,_value=value,
                     _checked=('!' in item.group() or \
                                   'x' in item.group().lower()),
                     _disabled=readonly).xml()    
    body = regex.sub(radio,MARKMIN(ballot).xml())
    form = FORM(XML(body),not readonly and INPUT(_type='submit') or '')
    if not readonly: form.process()
    return form

def form2ballot(ballot,token=None,vars=None,counters=None,results=None):    
    k, radioes = 0, {}
    def check(item):
        k = int(item.group(1))
        value = radioes[k] = radioes.get(k,0)+1
        if counters:
            return '[%s]' % counters.get((k,value),0)
        else:
            x = vars.get('ck%s'%k,0)==str(value)
            if isinstance(results,dict): results[(k,value)] = 1 if x else 0
            return '[X]' if x else '[ ]'
    filled_ballot = regex.sub(check,ballot)
    if token: filled_ballot += '\n\n[%s]' % token
    return filled_ballot
