from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event, choice, end_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
offer_queue = shop.add_var("offer queue")
to_response = shop.add_var("to response")
to_choose = shop.add_var("to choose")
simple_response_queue = shop.add_var("simple response queue")
complex_response_queue = shop.add_var("complex response queue")
done = shop.add_var("done")

# Define resources.
administrator = shop.add_var("administrator")

administrator.put("a1")

# Define events.
start_event(shop, [], [offer_queue], "simple_customer_arrived", lambda: exp(1/15), lambda: [SimToken("simple")])
start_event(shop, [], [offer_queue], "complex_customer_arrived", lambda: exp(1/30), lambda: [SimToken("complex")])

def start_create_offer(c, r):
  return [SimToken((c, r), exp(1/4))]
task(shop, [offer_queue, administrator], [to_response, administrator], "create_offer", start_create_offer)

shop.add_event([to_response], [to_choose], lambda c: [SimToken(c, exp(1/4))], name="wait_for_response")

shop.add_event([to_choose], [simple_response_queue], lambda c: [SimToken(c)], name="choose_simple", guard=lambda c: c[1] == "simple")
shop.add_event([to_choose], [complex_response_queue], lambda c: [SimToken(c)], name="choose_complex", guard=lambda c: c[1] == "complex")

def start_process_simple_response(c, r):
  return [SimToken((c, r), exp(1/3))]
task(shop, [simple_response_queue, administrator], [done, administrator], "process_simple_response", start_process_simple_response)

def start_process_complex_response(c, r):
  return [SimToken((c, r), exp(1/6))]
task(shop, [complex_response_queue, administrator], [done, administrator], "process_complex_response", start_process_complex_response)

end_event(shop, [done], [], "done")

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_different_case_types.csv")
shop.simulate(24*60, reporter)
reporter.close()
