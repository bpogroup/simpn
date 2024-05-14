from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import SimpleReporter
import simpn.prototypes as prototype

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
def start_scan(c, r):
  return [SimToken((c, r), delay=exp(1/9))]
prototype.BPMNTask(shop, [scan_queue, cassier], [bag_queue, cassier], "scan_groceries", start_scan)

def start_bag(c, r):
  return [SimToken((c, r), delay=exp(1/9))]
prototype.BPMNTask(shop, [bag_queue, bagger], [done, bagger], "bag_groceries", start_bag)

def interarrival_time():
  return exp(1/10)
prototype.BPMNStartEvent(shop, [], [scan_queue], "customer_arrived", interarrival_time)

# Run the simulation.
shop.simulate(60, SimpleReporter())