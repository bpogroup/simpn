from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import SimpleReporter
from simpn.prototypes import task, start_event

shop = SimProblem()

to_scan = shop.add_var("to_scan")
cashier = shop.add_var("cashier")

to_bag = shop.add_var("to_bag")
bagger = shop.add_var("bagger")

done = shop.add_var("done")

bagger.put("b1")
cashier.put("r1")

def start_scan(c, r):
  return [SimToken((c, r), exp(1/9))]

scan = task(shop, [to_scan, cashier], [to_bag, cashier], "scan", start_scan)

def start_bag(c, r):
  return [SimToken((c, r), exp(1/9))]

bag = task(shop, [to_bag, bagger], [done, bagger], "bag", start_bag)

def interarrival_time():
  return exp(1/10)

arrive = start_event(shop, [], [to_scan], "arrive", interarrival_time)

shop.simulate(60, SimpleReporter())