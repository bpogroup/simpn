# Defect products arrive at a repair shop according to an exponential distribution of 10 min.
# One part of the product needs cleaning EXPO(5) while the other half needs repairing EXPO(10) minutes. Both activities can be done in parallel.
# After repairing & cleaning the product parts are assembled and packed (packing takes 3 minutes) for distribution.
# There are two workers in the repair shop which can be used to clean, repair or pack the products.
# If more than 3 products are waiting for packing and less than 5 parts are waiting at the repair or clean queue, packing gets the highest priority. When packing is empty, its priority is set back to low.

from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from simpn.visualisation import Visualisation
from random import expovariate as exp, uniform as uniform
import simpn.prototypes as prototype
from simpn.reporters import SimpleReporter

shop=SimProblem()

to_split = shop.add_var("to split")
clean_queue=shop.add_var("clean queue", priority=lambda token: token.value[1])
busy_clean=shop.add_var("busy clean")
repair_queue=shop.add_var("repair queue", priority=lambda token: token.value[1])
busy_repair=shop.add_var("busy repair")
packing_queue=shop.add_var("packing queue", priority=lambda token: token.value[1])


wait_sync_w_rep = shop.add_var("waiting for synchronization with repair")
wait_sync_w_clean = shop.add_var("waiting for synchronization with clean")
to_done = shop.add_var("to done")

worker=shop.add_var("worker")
worker.put("w1")
worker.put("w2")
worker.put("w3")

prototype.BPMNStartEvent(shop, [], [to_split], "customer_arrived", lambda: exp(1/8), behavior=lambda: [SimToken(2)])


shop.add_event([to_split], [clean_queue, repair_queue], lambda c: [SimToken(c), SimToken(c)], name="split")

def priority_condition(c, r, packing_queue_q):
    return all(t.value[1]>c[1] for t in packing_queue_q)

def complete_clean(b):
    return [SimToken(b[1]),SimToken(b[0])]

def complete_repair(b):
    return [SimToken(b[1]),SimToken(b[0])]

def start_repair(c, r, packing_queue_q):
  return [SimToken((c, r), delay=exp(1/12)), packing_queue_q]
#prototype.BPMNTask(shop, [repair_queue, worker, packing_queue.queue], [wait_sync_w_clean, worker,packing_queue.queue], "repair", start_repair, guard=priority_condition)
shop.add_event([repair_queue, worker, packing_queue.queue], [busy_repair,packing_queue.queue], start_repair, guard=priority_condition)
shop.add_event([busy_repair], [worker, wait_sync_w_rep], complete_repair)


def start_cleaning(c, r, packing_queue_q):
  return [SimToken((c, r), delay=exp(1/8)), packing_queue_q]
#prototype.BPMNTask(shop, [clean_queue, worker, packing_queue.queue], [wait_sync_w_rep, worker, packing_queue.queue], "clean", start_cleaning, guard=priority_condition)
shop.add_event([clean_queue, worker, packing_queue.queue], [busy_clean,packing_queue.queue], start_cleaning, guard=priority_condition)
shop.add_event([busy_clean], [worker, wait_sync_w_clean], complete_clean)


shop.add_event([wait_sync_w_rep, wait_sync_w_clean], [packing_queue], lambda c1, c2: [SimToken(c1)], name="join", guard=lambda c1, c2: c1 == c2)

def start_packing(c,r):
    return [SimToken((c,r), delay=exp(1/2))]
prototype.BPMNTask(shop, [packing_queue, worker],[to_done, worker], "packing", start_packing)



def packing_priority_condition(c,clean_queue_q, repair_queue_q, packing_queue_q):
    #return len(packing_queue_q)>3 and (len(repair_queue_q)<5 or len(clean_queue_q)<5)
    return (len(packing_queue_q)>0 and any(t.value[1] != 1 for t in packing_queue_q))


def prioritize_packing(c,clean_queue_q, repair_queue_q, packing_queue_q):
    for t in packing_queue_q:
        t.value=(t.value[0],1)
    return [clean_queue_q, repair_queue_q,packing_queue_q]


shop.add_event([packing_queue, clean_queue.queue, repair_queue.queue,  packing_queue.queue],[clean_queue.queue, repair_queue.queue,packing_queue.queue],prioritize_packing, guard=packing_priority_condition)
#shop.add_event([packing_queue, clean_queue.queue, repair_queue.queue,  packing_queue.queue],[clean_queue.queue, repair_queue.queue,packing_queue.queue],deprioritize_packing, guard=packing_priority_lower_condition)


prototype.BPMNEndEvent(shop, [to_done], [], "done")

# Run the simulation.
# shop.simulate(500, SimpleReporter())
m = Visualisation(shop, "./layout7.txt")
m.show()
m.save_layout("./layout7.txt")
#reporter = EventLogReporter("./temp/simulation_parallellism.csv")
#shop.simulate(24*60, reporter)
#reporter.close()