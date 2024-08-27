from simpn.simulator import SimProblem, SimToken
from simpn.reporters import SimpleReporter

shop = SimProblem()

resources = shop.add_place("resources")
customers = shop.add_place("customers")

def process(c, r):
    return [SimToken(r, delay=0.75)]
shop.add_transition([customers, resources], [resources], process)

resources.put("cassier")
customers.put("c1")
customers.put("c2")
customers.put("c3")

shop.simulate(10, SimpleReporter())