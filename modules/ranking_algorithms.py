import random, copy

__all__ = ['makeup_votes','iro','borda', 'schulze']

def makeup_votes(nvotes=100, candidates=['A','B','C','D']):
    """ generate random votes for testing """
    votes = []
    for k in range(nvotes):
        vote = copy.copy(candidates)
        random.shuffle(vote)
        votes.append(vote)
    return votes

def is_valid(vote):
    """ check no repeated candidate names in vote """
    return len(vote)==len(set(vote))

def iro(votes):
    """ instant run-off voting """
    # winners is a list of (v,k) = (number of preferences, option number)
    # ordered from the candidate with the least preferences to the highest
    winners = []
    losers = set()    
    allowed_options = reduce(lambda a,b:a|b,[set(vote) for vote in votes])
    n = len(allowed_options)
    while len(winners)<n:
        # options maps candidates to count of ballots
        # who voted for that candidate in first place
        # after ignoring some candidates
        options = {}
        # important! options must be initialized to that all options
        # are present, even nobody choose them as their first option
        # else 0 counts would not be present
        for item in allowed_options:
            if not item in losers:
                options[item] = 0
        # for every ballot
        for vote in votes: 
            # if the vote for the ballot is valid
            if is_valid(vote):
                # for each voting option in this balloe
                for item in vote:
                    # if the option(candidate) have not been
                    # alreday discurded
                    if not item in losers:
                        # count how many ballot have this option 
                        # as first option
                        options[item] += 1
                        break
                    
        # find the option(candidate) with the least number of
        # top preferences                    
        options_list = [(v,k) for (k,v) in options.items()]
        options_list.sort()
        minv = options_list[0][0]
        # discard this option and count again
        for (v,k) in options_list:
            if v==minv:
                losers.add(k)
                winners.append((v,k))
    return winners

def borda(votes, ignored=set(), mode='linear'):
    """ borda voting when mode="linear" """
    if not mode in ('linear','fractional','exponential'):
        raise RuntimeError("mode not supported")
    winners = {}
    n = len(votes[0])
    for vote in votes:
        if is_valid(vote):
            if len(vote)!=len(set(vote)):
                raise InvalidVote
            for k,item in enumerate(vote):
                if not item in ignored:
                    if mode == 'linear':
                        delta = linear*(n-k)
                    elif mode == 'fractional':
                        delta = 1.0/(k+1)
                    elif mode == 'exponential':
                        delta = n**(n-k-1)
                    winners[item] = winners.get(item,0) + delta
    winners = [(v,k) for (k,v) in winners.items()]
    winners.sort()
    return winners

def schulze(votes):
    """ schulze voting algorithm """
    d = {}
    p = {}
    candidates = list(reduce(lambda a,b:a&b,[set(vote) for vote in votes]))
    map_candid = dict((k,i) for (i,k) in enumerate(candidates))
    n = len(candidates)
    for i in range(n):
        for j in range(n):
            d[i,j] = p[i,j] = 0
    for vote in votes:
        if is_valid(vote):
            for i in range(0,n-1):
                for j in range(i+1,n):
                    key = (map_candid[vote[i]],map_candid[vote[j]])
                    d[key] += 1
    for i in range(n):
        for j in range(n):
            if i!=j:
                p[i,j] = d[i,j] if d[i,j] > d[j,i] else 0
    for i in range(n):
        for j in range(n):
            if i!=j:
                for k in range(n):
                    if k!=i and k!=j:
                        p[j,k] = max(p[j,k], min(p[j,i], p[i,k]))
    winners = range(n)
    winners.sort(lambda i,j: cmp(p[i,j],p[j,i]))
    return [(i,candidates[k]) for (i,k) in enumerate(winners)]
    
    

def test(nsamples=10):
    diff_iro_borda = 0
    diff_iro_schulze = 0
    diff_borda_schulze = 0
    for k in range(nsamples):
        votes = makeup_votes(10)            
        a = iro(votes)
        b = borda(votes,mode="exponential")
        c = schulze(votes)
        if a[-1][1]!=b[-1][1]:
            diff_iro_borda+=1
        if a[-1][1]!=c[-1][1]:
            diff_iro_schulze+=1
        if b[-1][1]!=c[-1][1]:
            diff_borda_schulze+=1

    print diff_iro_borda, diff_iro_schulze, diff_borda_schulze

def test_schulze():
    votes = []
    for i in range(5): votes.append('ACBED')
    for i in range(5): votes.append('ADECB')
    for i in range(8): votes.append('BEDAC')
    for i in range(3): votes.append('CABED')
    for i in range(7): votes.append('CAEBD')
    for i in range(2): votes.append('CBADE')
    for i in range(7): votes.append('DCEBA')
    for i in range(8): votes.append('EBADC')
    assert schulze(votes) == [(0, 'D'), (1, 'B'), (2, 'C'), (3, 'A'), (4, 'E')]

if __name__ == '__main__':
    test()
    test_schulze()
    votes = makeup_votes(10)
    print borda(votes,mode="exponential")
    print iro(votes)
    print schulze(votes)
