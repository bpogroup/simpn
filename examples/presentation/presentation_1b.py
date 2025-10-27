from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from simpn.helpers import Place, Transition
from random import expovariate as exp
from simpn.visualisation import Visualisation

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
class Arrival(Place):
  model=shop
  name="arrival"
shop.var("arrival").put(1)

class Waiting(Place):
  model=shop
  name="waiting"

class Busy(Place):
  model=shop
  name="busy"

# Define resources.
class Employees(Place):
  model=shop
  name="cassier"
  amount=1

# Define actions or 'transitions' in the process
class Arrive(Transition):
  name="arrive"
  model=shop 
  incoming=["arrival"]
  outgoing=["arrival", "waiting"]

  def behaviour(a):
    return [
      SimToken(a+1, delay=exp(1/9)), 
      SimToken('c' + str(a))
    ]

class Start(Transition):
  name="start"
  model=shop 
  incoming=["waiting", "cassier"]
  outgoing=["busy"]

  def behaviour(c, r):
    return [SimToken((c, r), delay=exp(1/10))]

class Complete(Transition):
  name="complete"
  model=shop
  incoming=["busy"]
  outgoing=["cassier"]

  def behaviour(b):
    return [SimToken(b[1])]
  
# Run the simulation.
visualisation = Visualisation(shop, "./temp/presentation_1.layout")
visualisation.show()
visualisation.save_layout("./temp/presentation_1.layout")
