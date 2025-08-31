from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from random import uniform
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype
from simpn.helpers import BPMN
from simpn.visualisation import Visualisation

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
class Done(BPMN):
    type="flow"
    model=agency
    name="done"

class Waiting(BPMN):
    type="flow"
    model=agency
    name="waiting"

# Define helper classes to represent the process
class Employees(BPMN):
    type="resource-pool"
    model=agency
    name="employee"
    amount=3

class Start(BPMN):
    type="start"
    model=agency
    name="arrive"
    amount=1
    outgoing=["waiting"]

    def interarrival_time():
        return exp(1/10)
    
class Scan(BPMN):
    type="task"
    model=agency
    name="scan"
    incoming=["waiting", "employee"]
    outgoing=["done", "employee"]

    def behaviour(c, r):
        return [SimToken((c, r), delay=exp(1/9))]
    
class End(BPMN):
    type="end"
    model=agency
    name="complete"
    incoming=["done"]

# Simulate with an EventLogReporter.
reporter = EventLogReporter("./temp/presentation_3.csv")
agency.simulate(1000*60, reporter)
reporter.close()