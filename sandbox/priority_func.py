from simpn.helpers import BPMN
from simpn.simulator import SimProblem, SimToken, SimTokenValue
from simpn.visualisation import Visualisation

import random


CALLED = False


def priority(bindings):
    global CALLED
    CALLED = True
    print(f"Priority function called with binding: {bindings}")
    return bindings[0]


model = SimProblem(binding_priority=priority)


class Start(BPMN):
    model = model
    type = "start"
    name = "start"
    outgoing = ["considering"]

    def interarrival_time():
        return random.expovariate(4)


class Employees(BPMN):
    model = model
    name = "employees"
    type = "resource-pool"
    amount = 2


class Doing(BPMN):
    model = model
    type = "task"
    incoming = ["considering", "employees"]
    outgoing = ["done", "employees"]
    name = "Doing"

    def behaviour(val, res):

        return [SimToken((val, res))]


class Done(BPMN):
    model = model
    type = "end"
    incoming = ["done"]
    name = "Finished"


vis = Visualisation(model)
vis.show()

model.simulate(duration=10)

assert CALLED, "Priority function was not called during simulation."
