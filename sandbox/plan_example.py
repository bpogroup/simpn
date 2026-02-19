import random

from simpn.simulator import SimProblem, SimToken
from simpn.reporters import SimpleReporter
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation

# The simulator

terminal = SimProblem()

cranes = prototype.BPMNLane(terminal, "cranes")
cranes.put("c1")
cranes.put("c2")

arrived = prototype.BPMNFlow(terminal, "arrived")
completed = prototype.BPMNFlow(terminal, "completed")

def load_container(truck, crane, assignment):
    truck_type = truck[1]
    processing_time = None
    if (truck_type, crane) == ("T1", "c1"):
        processing_time = random.uniform(2, 4)
    elif (truck_type, crane) == ("T1", "c2"):
        processing_time = random.uniform(3, 5)
    elif (truck_type, crane) == ("T2", "c1"):
        processing_time = random.uniform(4, 6)
    elif (truck_type, crane) == ("T2", "c2"):
        processing_time = random.uniform(5, 7)
    return [SimToken((truck, crane), delay=processing_time)]

# We introduce a state variable that keeps track of the assignments X_{t, c}, which indicate whether crane c is assigned to truck t.
assignments = terminal.add_var("assignments")
# A truck t can only be loaded by a crane c if X_{t, c} = 1. We can express this as a guard on the loading event.
def load_container_controller(truck, crane, assignment):
    return (truck, crane) == assignment

# Put the process together

prototype.BPMNStartEvent(terminal, [], [arrived], "truck_arrives", lambda: random.expovariate(1/10), behavior=lambda: [SimToken(random.choice(["T1","T2"]))])
prototype.BPMNTask(terminal, [arrived, cranes, assignments], [completed, cranes], "load_container", load_container, guard=load_container_controller)
prototype.BPMNEndEvent(terminal, [completed], [], name="done")


# Add the assignment decision making event
# The decision moment:
# there are waiting trucks and available cranes
# that are not assigned yet.
def assignment_decision_guard(state):
    assigned_trucks = set()
    assigned_cranes = set()
    for assigned_token in state.assignments:
        assigned_trucks.add(assigned_token.value[0])
        assigned_cranes.add(assigned_token.value[1])
    unassigned_waiting_trucks = set([token.value for token in state.arrived]) - assigned_trucks
    unassigned_available_cranes = set([token.value for token in state.cranes]) - assigned_cranes
    return len(unassigned_waiting_trucks) > 0 and len(unassigned_available_cranes) > 0
# The decision:
# Randomly assign one of the unassigned waiting trucks to one of the unassigned available cranes, and add this assignment to the assignment variable.
def assignment_decision_behavior(state):
    assigned_trucks = set()
    assigned_cranes = set()
    for assigned_token in state.assignments:
        assigned_trucks.add(assigned_token.value[0])
        assigned_cranes.add(assigned_token.value[1])
    unassigned_waiting_trucks = set([token.value for token in state.arrived]) - assigned_trucks
    unassigned_available_cranes = set([token.value for token in state.cranes]) - assigned_cranes
    truck = random.choice(list(unassigned_waiting_trucks))
    crane = random.choice(list(unassigned_available_cranes))
    state.assignments.add(SimToken((truck, crane)))
    return []
# Now add the decision event to the simulator as a global event
terminal.add_global_event(behavior=assignment_decision_behavior, guard=assignment_decision_guard)


# Run the thing

vis = Visualisation(terminal)
vis.show()