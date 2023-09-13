from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform as uniform
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
scan_queue = shop.add_var("scan queue")
to_choose = shop.add_var("to choose")
chosen = shop.add_var("chosen")
atm_queue = shop.add_var("atm queue")
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")
atm = shop.add_var("atm")

cassier.put("r1")
atm.put("a1")

# Define events.
def start_scan_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [scan_queue, cassier], [to_choose, cassier], "scan_groceries", start_scan_groceries)

def choose(c):
  return [SimToken((c[0], uniform(1,100)))]
shop.add_event([to_choose], [chosen], choose)

def pass_customer(c):
  return [SimToken(c)]

shop.add_event([chosen], [atm_queue], pass_customer, name="choose_use_atm", guard=lambda c: c[1] < 25)
shop.add_event([chosen], [done], pass_customer, name="choose_go_home", guard=lambda c: c[1] >= 25)

def start_use_atm(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [atm_queue, atm], [done, atm], "use_atm", start_use_atm)

def interarrival_time():
  return exp(1/10)
start_event(shop, [], [scan_queue], "arrive", interarrival_time)

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_choice.csv")
shop.simulate(24*60, reporter)
reporter.close()

# Show the whole thing in Petri nets
# Just show the choice construct in code
# Explain the lambda function (it is just a function without a name)
# Note that the choice is in two parts: first generating the random value, then checking the percentage.
# This cannot be done in one go, because then the choice would be sampled separately for both events.