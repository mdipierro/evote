from gluon import *
import re, hashlib, base64
import rsa
import cPickle as pickle
from uuid import uuid4
try:
    import ast
    have_ast=True
except:
    have_ast=False

regex_field = re.compile('{{(\w+)(\:\w+)?\!?}}')
regex_email = re.compile('[^\s<>"\',;]+\@[^\s<>"\',;\+',re.IGNORECASE)

def uuid():
    return str(uuid4()).replace('-','').upper()

def rsakeys():
    (pubkey,privkey) = rsa.newkeys(1024)
    return (pubkey.save_pkcs1(), privkey.save_pkcs1())

def sign(text,privkey_pem):
    privkey = rsa.PrivateKey.load_pkcs1(privkey_pem)
    signature = base64.b16encode(rsa.sign(text,privkey,'SHA-1'))
    return signature

def unpack_results(results):
    return ast.literal_eval(results) if have_ast else eval(results)

def ballot2form(ballot,readonly=False,counters=None,filled=False):
    """If counters is passed this counts the results in the ballot.
    If readonly is False, then the voter has not yet voted; if readonly
    is True, then they have just voted."""    
    radioes = {}    
    if isinstance(counters,dict): readonly=True
    def radio(item):     
        name = "ck_"+item.group(1)       
        value = radioes[name] = radioes.get(name,0)+1        
        if item.group(2):
            scheme = 'ranking'
        else:
            scheme = 'checkbox'
        key = (name,scheme,value)
        if isinstance(counters,dict):
            return INPUT(_type='text',_readonly=True,
                         _value=counters.get(key,0),
                         _class='model-'+scheme,
                         _style="width:3em").xml()
        ### CHECK THIS!
        #if counters is not None and 'x' in item.group().lower():
        #    counters[key] = counters.get(key,0)+1
        ### CHECK THIS!
        if scheme == 'checkbox':
            return INPUT(_type='radio',_name=name,_value=value,
                         _checked=('!' in item.group()),
                         _class='model-'+scheme,
                         _disabled=readonly).xml()
        elif scheme == 'ranking':
            name = name+'-%s-%s' % (item.group(2)[1:], value)
            return INPUT(_type='input',_name=name,_value=value,
                         _checked=('!' in item.group()),
                         _class='model-'+scheme,
                         _disabled=readonly,
                         ).xml()   
    body = regex_field.sub(radio,ballot.replace('\r',''))
    form = FORM(XML(body),not readonly and INPUT(_type='submit', _value="Submit Your Ballot!") or '',_class="ballot")
    if not readonly: form.process(formname="ballot")
    return form

def form2ballot(ballot,token,vars,results):    
    radioes = {}
    def check(item):        
        name = 'ck_'+item.group(1)
        value = radioes[name] = radioes.get(name,0)+1
        if item.group(2):
            scheme = item.group(2)[1:]
            name2 = name+'-%s-%s' % (scheme, value)
            rank = vars.get(name2,0)            
            if isinstance(results,dict):
                results[(name,scheme,value)] = int(rank)
            return INPUT(_type="input",_name=name2,_value=rank,
                         _disabled=True).xml()
        else:
            scheme = 'checkbox'
            checked = vars.get(name,0)==str(value)
            if isinstance(results,dict):
                results[(name,scheme,value)] = checked
            return INPUT(_type="radio",_name=name,_value=value,
                         _disabled=True,_checked=checked).xml()
    ballot_content = regex_field.sub(check,ballot.replace('\r',''))
    if token: ballot_content += '<pre>\n%s\n</pre>' % token
    return '<div class="ballot">%s</div>' % ballot_content.strip()

def blank_ballot(token):
    ballot_content = '<h2>Blank</h2>'
    if token: ballot_content += '<pre>\n%s\n</pre>' % token
    return '<div class="ballot">%s</div>' % ballot_content

def pack_counters(counters):
    return pickle.dumps(counters)

def unpack_counters(counters):
    return pickle.loads(counters)
