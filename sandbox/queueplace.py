from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation

shop = SimProblem()

resources = shop.add_var("resources")
customers = shop.add_var("customers")
busy = shop.add_var("busy")
done = shop.add_var("done")

def start(customerqueue, resource):
    customer = customerqueue[0]
    resultqueue = customerqueue[1:]
    return [resultqueue, SimToken((customer, resource), delay=0.75)]

shop.add_event([customers.queue, resources], [customers.queue, busy], start, guard = lambda q, r: len(q) > 0)

def complete(busy):
    return [SimToken(busy[0]), SimToken(busy[1])]

shop.add_event([busy], [done, resources], complete)

resources.put("cassier")
customers.put("c1")
customers.put("c2")
customers.put("c3")

v = Visualisation(shop, "./temp/layoutqueue.txt")
v.show()
v.save_layout("./temp/layoutqueue.txt")
