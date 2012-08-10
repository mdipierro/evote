VOTE_MESSAGE = """
%(title)s

Link to vote: %(link)s

"""

VOTED_MESSAGE = """
%(title)s

Voting receipt: %(receipt)s

"""

BALLOT_EXAMPLE = """
## Ballot title

text can be **bold** or ''italic'' and contain links and tables:

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
