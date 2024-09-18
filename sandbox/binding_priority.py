from simpn.simulator import SimProblem, SimToken
from simpn.reporters import SimpleReporter

shop = SimProblem()

resources = shop.add_var("resources")
customers = shop.add_var("customers")
busy_cases = shop.add_var("busy cases")

def start(customer, resource):
    return [SimToken((customer, resource), delay=0.75)]

def complete(busy_case):
    return [SimToken(busy_case[1])]

shop.add_event([customers, resources], [busy_cases], start)
shop.add_event([busy_cases], [resources], complete)

resources.put("cassier1")
resources.put("cassier2")
customers.put("c1")
customers.put("c2")
customers.put("c3")

shop.store_checkpoint("start")

# By default, it prefers to execute start events over complete events.
print("Execution trace with default binding priority:")
shop.simulate(10, SimpleReporter())

shop.restore_checkpoint("start")

# But you can change the binding priority.
def binding_priority_function(bindings):
    # A binding is a triple (list(variable_binding), time, event),
    # where a variable binding is a pair (variable, token).
    # From the list of bindings, this function must return the binding to execute.
    # Note that this function is called each time an event is fired, so it must be implemented efficiently.
    # In this case, we will iterate over the list and return the binding for the event with the name we like the most.
    start_binding = None
    complete_binding = None
    if len(bindings) == 1:  # for efficiency purposes: if there is just one binding, return it.
        return bindings[0]
    for binding in bindings:  # Iterate over the bindings and store the first binding with a particular event name.
        if binding[2].get_id() == "start" and start_binding is None:
            start_binding = binding
        elif binding[2].get_id() == "complete" and complete_binding is None:
            complete_binding = binding
    if complete_binding is not None:  # Now return the binding with the event name we like the most.
        return complete_binding
    elif start_binding is not None:
        return start_binding
  
shop.set_binding_priority(binding_priority_function)

print()
print("Execution trace where we prefer complete events:")
shop.simulate(10, SimpleReporter())