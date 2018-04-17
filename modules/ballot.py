from gluon import *
import re, hashlib, base64
import rsa
import json
import random
import cPickle as pickle
from uuid import uuid4
try:
    import ast
    have_ast=True
except:
    have_ast=False

regex_field = re.compile('{{(\w+)(\:\w+)?\!?}}')
regex_email = re.compile('[^\s<>"\',;]+\@[^\s<>"\',;]+',re.IGNORECASE)


def uuid():
    return str(uuid4()).replace('-','').upper()

def rsakeys():
    (pubkey,privkey) = rsa.newkeys(1024)
    return (pubkey.save_pkcs1(), privkey.save_pkcs1())

def sign(text,privkey_pem):
    privkey = rsa.PrivateKey.load_pkcs1(privkey_pem)
    signature = base64.b16encode(rsa.sign(text,privkey,'SHA-1'))
    return signature

def ballot2form(ballot_model, readonly=False, vars=None, counters=None):
    """If counters is passed this counts the results in the ballot.
    If readonly is False, then the voter has not yet voted; if readonly
    is True, then they have just voted."""    
    ballot_structure = json.loads(ballot_model)
    ballot = FORM()
    for question in ballot_structure:
        div =DIV(_class="question")
        ballot.append(div)
        html = MARKMIN(question['preamble'])
        div.append(html)
        table = TABLE()
        div.append(table)        
        name = question['name']
        if counters:
            options = []
            for answer in question['answers']:
                key = name+'/simple-majority/'+answer
                options.append((counters.get(key,0), answer))
            options.sort(reverse=True)
            options = map(lambda a: a[1], options)
        else:
            options = question['answers']
            if question['randomize']:
                random.shuffle(options)
        for answer in options:
            key = name + '/simple-majority/' + answer
            if not counters:
                if question['algorithm'] == 'simple-majority':
                    inp = INPUT(_name=question['name'], _type="radio", _value=answer)
                if vars and vars.get(name) == answer:
                    inp['_checked'] = True
                if readonly:
                    inp['_disabled'] = True
            else:
                inp = STRONG(counters.get(key, 0))
            table.append(TR(TD(inp),TD(answer)))
        if question['comments']:        
            value = readonly and vars.get(question['name']+'_comments') or ''
            textarea =  TEXTAREA(value, _disabled=readonly, _name=question['name']+'_comments')
            ballot.append(DIV(H4('Comments'), textarea))
    if not readonly and not counters: 
        ballot.append(INPUT(_type='submit', _value="Submit Your Ballot!"))
    return ballot

def form2ballot(ballot_model, token, vars, results):    
    ballot_content = ballot2form(ballot_model, readonly=True, vars=vars).xml()
    if token: ballot_content += '<pre>\n%s\n</pre>' % token
    return '<div class="ballot">%s</div>' % ballot_content.strip()

def blank_ballot(token):
    ballot_content = '<h2>Blank</h2>'
    if token: ballot_content += '<pre>\n%s\n</pre>' % token
    return '<div class="ballot">%s</div>' % ballot_content

