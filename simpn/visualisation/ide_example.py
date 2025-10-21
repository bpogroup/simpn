from simpn.visualisation.ide import Visualisation
from simpn.simulator import SimProblem, SimToken


def create_simple_example():
    shop = SimProblem()

    resources = shop.add_var("resources")
    customers = shop.add_var("customers")

    def process(customer, resource):
        return [SimToken(resource, delay=0.75)]

    shop.add_event([customers, resources], [resources], process)

    resources.put("cassier")
    customers.put("c1")
    customers.put("c2")
    customers.put("c3")

    return shop


v = Visualisation(create_simple_example(), layout_algorithm="sugiyama", grid_spacing=100, node_spacing=200, layout_file="./temp/layout.txt")
v.show()
v.save_layout("./temp/layout.txt")
