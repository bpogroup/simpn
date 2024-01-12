from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation
from random import expovariate as exp

shop = SimProblem()

arrival = shop.add_var("arrival")
customers = shop.add_var("customers")

time = shop.var("time")

arrival.put(1)

def batch_arrival(a, cs, t):
    for i in range(2): # each batch has two customers
        cs.append(SimToken((a, i), time=t))

    arrival_token = SimToken(a+1, delay=exp(1/2))

    return [arrival_token, cs]
            
shop.add_event([arrival, customers.queue, time], [arrival, customers.queue], batch_arrival)

v = Visualisation(shop, "./temp/layout_batch2.txt")
v.show()
v.save_layout("./temp/layout_batch2.txt")
