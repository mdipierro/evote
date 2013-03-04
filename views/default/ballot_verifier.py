####################################################################
# This is a python program that allows you to verify your ballot   #
# using the RSA algorithm. It requires the Python interpreter from #
#   http://python.org                                              #
# it also requires the RSA module which you can install with       #
#   pip install rsa                                                #
# Save this program with a name like "verify.py" and run it        #
# The output of this program "valid" or "invalid"                  #
####################################################################

# import required libraries
import base64, rsa # install module with "pip install rsa".

# this is the ballot to verify
ballot = """
{{=XML(ballot.ballot_content)}}
""".strip()

# this is the ballot RSA signature
signature = base64.b16decode("{{=ballot.signature.split('-')[1]}}")

# this is the election public key
pk_pem = """
{{=election.public_key.strip()}}
"""

# this is the code that verifies the signature
public_key = rsa.PublicKey.load_pkcs1(pk_pem)
if rsa.verify(ballot, signature, public_key)==None:
    print 'valid'
else:
    print 'invalid'
