from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.visualisation import Visualisation

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
arrival = shop.add_var("arrival")
waiting = shop.add_var("waiting")
busy = shop.add_var("busy")

arrival.put(1)

# Define resources.
employee = shop.add_var("cassier")
employee.put("r1")

# Define events.

def start(c, r):
  return [SimToken((c, r), delay=exp(1/10))]

shop.add_event([waiting, employee], [busy], start)

def complete(b):
  return [SimToken(b[1])]

shop.add_event([busy], [employee], complete)

def arrive(a):
  return [SimToken(a+1, delay=exp(1/9)), SimToken('c' + str(a))]

shop.add_event([arrival], [arrival, waiting], arrive)

# Run the simulation.
visualisation = Visualisation(shop, "./temp/presentation_1.layout")
visualisation.show()
visualisation.save_layout("./temp/presentation_1.layout")
