from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation

shop = SimProblem()

v_resources = shop.add_var("resources")
v_customers = shop.add_var("customers")

def process(customer, resource):
    return [SimToken(resource, delay=0.75)]

e_process = shop.add_event([v_customers, v_resources], [v_resources], process)

v_resources.put("cassier")
v_customers.put("c1")
v_customers.put("c2")
v_customers.put("c3")

v = Visualisation(shop, layout_algorithm="sugiyama", grid_spacing=100, node_spacing=200, layout_file="./temp/layout.txt")
v.show()
v.save_layout("./temp/layout.txt")
