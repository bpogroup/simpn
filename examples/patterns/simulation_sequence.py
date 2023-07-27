from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import SimpleReporter

shop = SimProblem()

arrival = shop.add_var("arrival")
done = shop.add_var("done")

to_scan = shop.add_var("to_scan")
cashier = shop.add_var("cashier")
busy_scan = shop.add_var("busy_scan")

to_bag = shop.add_var("to_bag")
bagger = shop.add_var("bagger")
busy_bag = shop.add_var("busy_bag")

bagger.put("b1")
cashier.put("r1")
arrival.put(1)

def start_scan(c, r):
  return [SimToken((c, r), exp(1/9))]

shop.add_event([to_scan, cashier], [busy_scan], start_scan)

def complete_scan(b):
  return [SimToken(b[1]), SimToken(b[0])]

shop.add_event([busy_scan], [cashier, to_bag], complete_scan)

def start_bag(c, r):
  return [SimToken((c, r), exp(1/9))]

shop.add_event([to_bag, bagger], [busy_bag], start_bag)

def complete_bag(b):
  return [SimToken(b[1]), SimToken(b[0])]

shop.add_event([busy_bag], [bagger, done], complete_bag)

def arrive(a):
  return [SimToken(a+1, exp(1/10)), SimToken('c' + str(a))]

shop.add_event([arrival], [arrival, to_scan], arrive)

shop.simulate(10, SimpleReporter())