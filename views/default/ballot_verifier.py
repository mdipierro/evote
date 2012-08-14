import base64, rsa # install module with "pip install rsa".
ballot = """
{{=XML(ballot.ballot_content)}}
""".strip()

signature = base64.b16decode("{{=ballot.signature.split('-')[1]}}")

pk_pem = """
{{=election.public_key.strip()}}
"""

public_key = rsa.PublicKey.load_pkcs1(pk_pem)
if rsa.verify(ballot, signature, public_key)==None: print 'success'
