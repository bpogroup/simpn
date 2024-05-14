from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation
import simpn.prototypes as prototype
from random import expovariate as exp

shop = SimProblem()

batch = shop.add_var("batch")
customers = shop.add_var("customers")

time = shop.var("time")

prototype.BPMNStartEvent(shop, [], [batch], "batch_arrival", lambda: exp(1/2))

def batch_explosion(b, cs, t):
    for i in range(2): # each batch has two customers
        cs.append(SimToken((b, i), time=t))
    return [cs]

shop.add_event([batch, customers.queue, time], [customers.queue], batch_explosion)

v = Visualisation(shop, "./temp/layout_batch.txt")
v.show()
v.save_layout("./temp/layout_batch.txt")
