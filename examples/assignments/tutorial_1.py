from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from random import uniform
from simpn.reporters import SimpleReporter

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
arrival = agency.add_var("arrival")
waiting = agency.add_var("waiting")
busy = agency.add_var("busy")

arrival.put(1)

# Define resources.
employee = agency.add_var("emplpyee")
employee.put("e1")

# Define events.

def start(c, r):
  return [SimToken((c, r), delay=uniform(10, 15))]

agency.add_event([waiting, employee], [busy], start)

def complete(b):
  return [SimToken(b[1])]

agency.add_event([busy], [employee], complete)

def arrive(a):
  return [SimToken(a+1, delay=exp(4)*60), SimToken('c' + str(a))]

agency.add_event([arrival], [arrival, waiting], arrive)

# Run the simulation.
agency.simulate(60, SimpleReporter())
