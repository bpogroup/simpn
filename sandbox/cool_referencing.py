from simpn.simulator import SimProblem, SimToken, SimTokenValue
from simpn.reporters import SimpleReporter
from simpn.visualisation.base import Visualisation

m = SimProblem()

customers_waiting = m.add_var("customers_waiting")
customers_ready = m.add_var("customers_ready")

def process(state, customer):
    for customer in state.customers_waiting:
        print("Processing customer " + customer.name, customer.time) 
    return [SimToken(customer, delay=0.75)]

m.add_event([customers_waiting], [customers_ready], process, state_access=True)

customers_waiting.put({'name': 'c1'})
customers_waiting.put({'name': 'c2'})
customers_waiting.put({'name': 'c3'})

v = Visualisation(m)
v.show()
