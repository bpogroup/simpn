from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from simpn.visualisation import Visualisation
from random import expovariate as exp, uniform as uniform
from simpn.prototypes import task, start_event, end_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
to_split = shop.add_var("to split")
scan_queue = shop.add_var("scan queue")
atm_queue = shop.add_var("atm queue")
wait_sync_w_atm = shop.add_var("waiting for synchronization with atm")
wait_sync_w_scan = shop.add_var("waiting for synchronization with scanning")
to_done = shop.add_var("to done")

# Define resources.
cassier = shop.add_var("cassier")
atm = shop.add_var("atm")

cassier.put("r1")
atm.put("a1")

# Define events.
def interarrival_time():
  return exp(1/10)
start_event(shop, [], [to_split], "arrive", interarrival_time)


shop.add_event([to_split], [scan_queue, atm_queue], lambda c: [SimToken(c), SimToken(c)], name="split")


def start_scan_groceries(c, r):
  return [SimToken((c, r), delay=exp(1/9))]
task(shop, [scan_queue, cassier], [wait_sync_w_atm, cassier], "scan_groceries", start_scan_groceries)

def start_use_atm(c, r):
  return [SimToken((c, r), delay=exp(1/9))]
task(shop, [atm_queue, atm], [wait_sync_w_scan, atm], "use_atm", start_use_atm)


shop.add_event([wait_sync_w_atm, wait_sync_w_scan], [to_done], lambda c1, c2: [SimToken(c1)], name="join", guard=lambda c1, c2: c1 == c2)


end_event(shop, [to_done], [], "done")


#m = Visualisation(shop, "./temp/layout.txt")
m = Visualisation(shop)
m.show()
m.save_layout("./temp/layout.txt")