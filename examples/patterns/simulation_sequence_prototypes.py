from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import SimpleReporter
from simpn.prototypes import task, start_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
scan_queue = shop.add_var("scan queue")
bag_queue = shop.add_var("bag queue")
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")
bagger = shop.add_var("bagger")

bagger.put("b1")
cassier.put("r1")

# Define events.
def start_scan_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]

scan_groceries = task(shop, [scan_queue, cassier], [bag_queue, cassier], "scan_groceries", start_scan_groceries)

def start_bag_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]

bag_groceries = task(shop, [bag_queue, bagger], [done, bagger], "bag_groceries", start_bag_groceries)

def interarrival_time():
  return exp(1/10)

customer_arrived = start_event(shop, [], [scan_queue], "customer_arrived", interarrival_time)

# Run the simulation.
shop.simulate(60, SimpleReporter())