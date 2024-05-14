from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
offer_queue = shop.add_var("offer queue")
to_response = shop.add_var("to response")
to_choose = shop.add_var("to choose")
simple_response_queue = shop.add_var("simple response queue")
complex_response_queue = shop.add_var("complex response queue")
to_done = shop.add_var("to done")

# Define resources.
administrator = shop.add_var("administrator")

administrator.put("a1")

# Define events.
prototype.BPMNStartEvent(shop, [], [offer_queue], "simple_customer_arrived", lambda: exp(1/15), lambda: [SimToken("simple")])
prototype.BPMNStartEvent(shop, [], [offer_queue], "complex_customer_arrived", lambda: exp(1/30), lambda: [SimToken("complex")])

prototype.BPMNTask(shop, [offer_queue, administrator], [to_response, administrator], "create_offer", lambda c, r: [SimToken((c, r), delay=exp(1/4))])

shop.add_event([to_response], [to_choose], lambda c: [SimToken(c, delay=exp(1/4))], name="wait_for_response")

def choose(c):
    if c[1] == "simple":
        return [SimToken(c), None]
    else:
        return [None, SimToken(c)]
shop.add_event([to_choose], [simple_response_queue, complex_response_queue], choose)

prototype.BPMNTask(shop, [simple_response_queue, administrator], [to_done, administrator], "process_simple_response", lambda c,r: [SimToken((c, r), delay=exp(1/3))])

prototype.BPMNTask(shop, [complex_response_queue, administrator], [to_done, administrator], "process_complex_response", lambda c,r : [SimToken((c, r), delay=exp(1/6))])

prototype.BPMNEndEvent(shop, [to_done], [], "done")

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_different_case_types.csv")
shop.simulate(24*60, reporter)
reporter.close()
