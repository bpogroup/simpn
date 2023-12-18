from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import SimpleReporter

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
arrival = shop.add_var("arrival")
done = shop.add_var("done")

scan_queue = shop.add_var("scan queue")
busy_scan = shop.add_var("busy scanning groceries")

bag_queue = shop.add_var("bag queue")
busy_bag = shop.add_var("busy bagging groceries")

arrival.put(1)

# Define resources.
cassier = shop.add_var("cassier")
bagger = shop.add_var("bagger")

bagger.put("b1")
cassier.put("r1")

# Define events.
def start_scan_groceries(c, r):
  return [SimToken((c, r), delay=exp(1/9))]
shop.add_event([scan_queue, cassier], [busy_scan], start_scan_groceries)

def complete_scan_groceries(b):
  return [SimToken(b[1]), SimToken(b[0])]
shop.add_event([busy_scan], [cassier, bag_queue], complete_scan_groceries)

def start_bag_groceries(c, r):
  return [SimToken((c, r), delay=exp(1/9))]
shop.add_event([bag_queue, bagger], [busy_bag], start_bag_groceries)

def complete_bag_groceries(b):
  return [SimToken(b[1]), SimToken(b[0])]
shop.add_event([busy_bag], [bagger, done], complete_bag_groceries)

def customer_arrived(a):
  return [SimToken(a+1, delay=exp(1/10)), SimToken('c' + str(a))]
shop.add_event([arrival], [arrival, scan_queue], customer_arrived)

# Run the simulation.
shop.simulate(10, SimpleReporter())