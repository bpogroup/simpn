# Jockeying is a situation in which customers switch queues when a certain condition is satisfied
# Example. Customers arrive at a checkout according to an exponential distribution of 5 min.

# There are two checkouts,
# checkout 1: a skilled employee serves at EXPO(5) minutes,
# checkout 2: an unskilled employee serves at EXPO(12) minutes.

# Customers are split equally over the two checkouts

# When customers are in the queue of checkout 2 and this queue is more than 2 persons longer than the queue at checkout 1, 
# customers will switch to queue 1.

# Customers at checkout 1 cannot switch queues



from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform
from simpn.reporters import SimpleReporter
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation


shop = SimProblem()

to_choose = shop.add_var("to choose")
waiting_1 = shop.add_var("cassier 1 queue")
waiting_2 = shop.add_var("cassier 2 queue")
cassier_1 = shop.add_var("cassier 1")
cassier_2 = shop.add_var("cassier 2")

cassier_1.put("c1")
cassier_2.put("c2")

done = shop.add_var("done")

prototype.BPMNStartEvent(shop, [], [to_choose], "arrive", lambda: exp(5))

def choose(c):
    percentage = uniform(1,100)
    if percentage <= 51:
        print("first queue")
        return [SimToken(c), None]
    else:
        print("second queue")
        return [None, SimToken(c)]
    return [None, SimToken(c)]

def switch_condition(c,c1_queue, c2_queue):
    return len(c1_queue)>len(c2_queue)+1

def switch_queue(c,c1_queue, c2_queue):
    last_token=c1_queue.pop()
    c2_queue.append(last_token)
    return [c1_queue, c2_queue]

shop.add_event([to_choose],[waiting_1, waiting_2], choose)
shop.add_event([waiting_1, waiting_1.queue, waiting_2.queue],[waiting_1.queue, waiting_2.queue], switch_queue,guard=switch_condition)

prototype.BPMNTask(shop, [waiting_1, cassier_1], [done, cassier_1],"scan_groceries_1", lambda c, r: [SimToken((c, r), delay=exp(5))])
prototype.BPMNTask(shop, [waiting_2, cassier_2], [done, cassier_2], "scan_groceries_2", lambda c, r: [SimToken((c, r), delay=exp(12))])
prototype.BPMNEndEvent(shop, [done], [], "leave")

shop.store_checkpoint("initial state")

shop.simulate(120, SimpleReporter())
m = Visualisation(shop, "./layout2.txt")
m.show()
m.save_layout("./layout2.txt")