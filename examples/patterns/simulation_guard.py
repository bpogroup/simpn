from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
customers = shop.add_var("customers")
customers.put(("c1", 90))
customers.put(("c2", 110))

accepted_customers = shop.add_var("accepted customers")

# Define events.

def accept(c):
  return [SimToken(c)]

def acceptance_condition(c):
    return c[1] > 100

shop.add_event([customers], [accepted_customers], accept, guard=acceptance_condition)

# Run the simulation.
from simpn.reporters import SimpleReporter

shop.simulate(100, SimpleReporter())
