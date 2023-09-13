from simpn.simulator import SimProblem

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
arrival = shop.add_var("arrival")
waiting = shop.add_var("waiting")
busy = shop.add_var("busy")

arrival.put(1)

# Define resources.
resource = shop.add_var("resource")
resource.put("r1")

# Define events.
from simpn.simulator import SimToken
from random import expovariate as exp

def start(c, r):
  return [SimToken((c, r), exp(1/0.8))]

shop.add_event([waiting, resource], [busy], start)

def complete(b):
  return [SimToken(b[1], 0)]

shop.add_event([busy], [resource], complete)

def arrive(a):
  return [SimToken(a+1, exp(1)), SimToken('c' + str(a))]

shop.add_event([arrival], [arrival, waiting], arrive)

# Run the simulation.
from simpn.reporters import SimpleReporter

shop.simulate(2.5, SimpleReporter())

# also write down the model as a Petri net.
# cicles are variables. squares are events.
# variables have values at a moment in time (tokens).
# an event takes labeled variables and produces tokens for other variables.
# also note that here we have start and complete events.