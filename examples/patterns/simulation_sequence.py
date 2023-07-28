from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import SimpleReporter

shop = SimProblem()

arrival = shop.add_var("arrival")
done = shop.add_var("done")

to_scan_groceries_groceries = shop.add_var("to_scan_groceries_groceries")
cassier = shop.add_var("cassier")
busy_scan_groceries = shop.add_var("busy_scan_groceries")

to_bag_groceries = shop.add_var("to_bag_groceries")
bagger = shop.add_var("bagger")
busy_bag_groceries = shop.add_var("busy_bag_groceries")

bagger.put("b1")
cassier.put("r1")
arrival.put(1)

def start_scan_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]

shop.add_event([to_scan_groceries_groceries, cassier], [busy_scan_groceries], start_scan_groceries)

def complete_scan_groceries(b):
  return [SimToken(b[1]), SimToken(b[0])]

shop.add_event([busy_scan_groceries], [cassier, to_bag_groceries], complete_scan_groceries)

def start_bag_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]

shop.add_event([to_bag_groceries, bagger], [busy_bag_groceries], start_bag_groceries)

def complete_bag_groceries(b):
  return [SimToken(b[1]), SimToken(b[0])]

shop.add_event([busy_bag_groceries], [bagger, done], complete_bag_groceries)

def customer_arrived(a):
  return [SimToken(a+1, exp(1/10)), SimToken('c' + str(a))]

shop.add_event([arrival], [arrival, to_scan_groceries_groceries], customer_arrived)

shop.simulate(10, SimpleReporter())