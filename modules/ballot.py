from gluon import *
import re, hashlib, base64
import rsa
from uuid import uuid4
try:
    import ast
    have_ast=True
except:
    have_ast=False

regex = re.compile('{{(\w+)\!?}}')
regex_email = re.compile('[\w_\-\.]+\@[\w_\-\.]+')

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
    body = regex.sub(radio,ballot.replace('\r',''))
    form = FORM(XML(body),not readonly and INPUT(_type='submit', _value="Submit You Ballot!") or '',_class="ballot")
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
    ballot_content = regex.sub(check,ballot.replace('\r',''))
    if token: ballot_content += '<pre>\n%s\n</pre>' % token
    return '<div class="ballot">%s</div>' % ballot_content.strip()

def blank_ballot(token):
    ballot_content = '<h2>Blank</h2>'
    if token: ballot_content += '<pre>\n%s\n</pre>' % token
    return '<div class="ballot">%s</div>' % ballot_content
