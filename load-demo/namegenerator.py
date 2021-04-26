import random
import re

with open ("adjusted-name-combinations-list.csv") as f:
  namelines = f.readlines()

names = []
namere = re.compile('^.*,.*,.*,.*,\"(.*)\s(.*)\",')
for n in namelines:
  name = namere.match(n)
  names.append(name.group(1)+name.group(2))

orignames = names.copy()

for n in orignames:
  names.append(n+"Jr")
  names.append(n+"Sr")

names = names[:1000]
random.shuffle(names)


pairs = []

for _ in range(100):
  pairs.append(("megacorp", names.pop()))
for _ in range(50):
  pairs.append(("mediumcorp", names.pop()))

companyi = 0

while(names):
  tenantname = "contoso-"+str(companyi)
  companyi += 1
  tenantsize = min(len(names), random.randint(0,10))
  for _ in range(tenantsize):
    pairs.append((tenantname, names.pop()))


random.shuffle(pairs)

for entry in pairs:
  print('%s,%s' % entry)

  
