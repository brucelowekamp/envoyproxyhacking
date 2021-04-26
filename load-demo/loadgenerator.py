from collections import namedtuple
from concurrent.futures import as_completed
from pprint import pprint
from requests_futures.sessions import FuturesSession
import re


def loadtest(url, keyfunc):
  User = namedtuple('User', ['tenant', 'name'])
  with open("namelist") as f:
    users = [ User(x[0],x[1]) for x in [l.strip().split(',') for l in f.readlines()]]

  session = FuturesSession(max_workers=20)

  futures=[session.get(url,
                       headers={'X-tenant': u.tenant,
                                'X-user': u.name,
                                'X-key': keyfunc(u)}
                       ) for u in users]

  nodecount = {}
  instancere = re.compile('^instance:\s(\S*)\s') 
  for future in as_completed(futures):
      resp = future.result()
      m = instancere.match(resp.text)
      if m is None:
        print ("no match in %s" % (resp.text))
        next
      node = m.group(1)
      #print ("got node %s" % (node))
      if nodecount.get(node) is None:
        nodecount[node] = 1
      else:
        nodecount[node] += 1
      #print(resp.text)


  for node,count in sorted(nodecount.items(), key=lambda x: -x[1]):
    print ('Node %s: %s' % ( node, count ))


