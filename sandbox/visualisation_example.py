from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation

shop = SimProblem()

resources = shop.add_var("resources")
resources.set_invisible_edges()

customers = shop.add_var("customers")

def process(customer, resource):
    return [SimToken(resource, delay=0.75)]

process = shop.add_event([customers, resources], [resources], process)

resources.put("cassier")
customers.put("c1")
customers.put("c2")
customers.put("c3")

v = Visualisation(shop, layout_algorithm="sugiyama", grid_spacing=100, node_spacing=200)
v.show()
v.save_layout("./temp/layout.txt")
