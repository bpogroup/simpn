from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation

shop = SimProblem()

resources = shop.add_var("resources")
customers = shop.add_var("customers")
busy = shop.add_var("busy")
done = shop.add_var("done")

def start(ws, r):
    c = ws[0].value
    resultqueue = ws[1:]
    return [resultqueue, SimToken((c, r), delay=0.75)]

def start_condition(ws, r):
    return len(ws) > 0

shop.add_event([customers.queue, resources], [customers.queue, busy], start, guard = start_condition)

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
