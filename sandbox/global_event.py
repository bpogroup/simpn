from simpn.simulator import SimProblem, SimToken
from simpn.reporters import SimpleReporter

"""
This example shows how to use global events.
Global events are enabled as usual (by a token and a guard).
However, instead of returning a list of tokens, they can directly access the state of the system and modify it.
To this end, the behavior function of a global event has an additional argument, which is the state of the system at the time the event is triggered.
"""

shop = SimProblem()

resources = shop.add_var("resources")
customers = shop.add_var("customers")
waiting_customers = shop.add_var("waiting_customers")

resources.put("cassier")
waiting_customers.put("c1")
waiting_customers.put("c2")
waiting_customers.put("c3")

def serve_customer(customer, resource):
    return [SimToken(resource, delay=0.75)]
shop.add_event([customers, resources], [resources], serve_customer)

def plan_customer_guard(state):
    return len(state.waiting_customers) > 0 and len(state.resources) > 0

def plan_customer_behavior(state):
    print("  Waiting: " + str(state.waiting_customers))
    print("  Resources: " + str(state.resources))
    print("  Planned customers: " + str(state.customers))
    customer = state.waiting_customers.pop(0)
    print("Planning customer " + str(customer))
    state.customers.add(SimToken(customer))
    return []
shop.add_global_event(behavior=plan_customer_behavior, guard=plan_customer_guard)

shop.simulate(10, SimpleReporter())