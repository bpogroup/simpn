from simpn.simulator import SimProblem

shop = SimProblem()

arrival = shop.add_var("arrival")
waiting = shop.add_var("waiting")
resource = shop.add_var("resource")
busy = shop.add_var("busy")

resource.put("r1")
arrival.put(1)

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

from simpn.reporters import SimpleReporter

shop.simulate(2.5, SimpleReporter())