import matplotlib.pyplot as plt 
from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import WarmupReporter, ProcessReporter
from simpn.helpers import BPMN

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
class Done(BPMN):
    type="flow"
    model=shop
    name="done"

class Waiting(BPMN):
    type="flow"
    model=shop
    name="waiting"

# Define helper classes for simulation
class Cassiers(BPMN):
    type="resource-pool"
    model = shop 
    name = "cassier"
    amount = 1

class Start(BPMN):
    type="start"
    model=shop
    name="arrive"
    amount=1
    outgoing=["waiting"]

    def interarrival_time():
        return exp(1/10)
    
class Scan(BPMN):
    type="task"
    model=shop
    name="scan_groceries"
    incoming=["waiting", "cassier"]
    outgoing=["done", "cassier"]

    def behaviour(c, r):
        return [SimToken((c, r), delay=exp(1/9))]
    
class End(BPMN):
    type="end"
    model=shop
    name="complete"
    incoming=["done"]

shop.store_checkpoint("initial state")

# Simulate once with a warmup reporter.
reporter = WarmupReporter()
shop.simulate(20000, reporter)

plt.plot(reporter.times, reporter.average_cycle_times, color="blue")
plt.xlabel("arrival time (min)")
plt.xticks(range(0, 20001, 5000))
plt.ylabel("cycle time (min)")
plt.show()
