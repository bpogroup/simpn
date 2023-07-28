from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import SimpleReporter
from simpn.prototypes import task, start_event

shop = SimProblem()

to_scan_groceries = shop.add_var("to_scan_groceries")
cassier = shop.add_var("cassier")

to_bag_groceries = shop.add_var("to_bag_groceries")
bagger = shop.add_var("bagger")

done = shop.add_var("done")

bagger.put("b1")
cassier.put("r1")

def start_scan_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]

scan_groceries = task(shop, [to_scan_groceries, cassier], [to_bag_groceries, cassier], "scan_groceries", start_scan_groceries)

def start_bag_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]

bag_groceries = task(shop, [to_bag_groceries, bagger], [done, bagger], "bag_groceries", start_bag_groceries)

def interarrival_time():
  return exp(1/10)

customer_arrived = start_event(shop, [], [to_scan_groceries], "customer_arrived", interarrival_time)

shop.simulate(60, SimpleReporter())