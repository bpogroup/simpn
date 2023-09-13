from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
offer_queue = shop.add_var("offer queue")
to_response = shop.add_var("to response")
processing_queue = shop.add_var("processing queue")
done = shop.add_var("done")

# Define resources.
administrator = shop.add_var("administrator")

administrator.put("a1")

# Define events.
def interarrival_time():
  return exp(1/10)
start_event(shop, [], [offer_queue], "customer_arrived", interarrival_time)

def start_create_offer(c, r):
  return [SimToken((c, r), exp(1/4))]
task(shop, [offer_queue, administrator], [to_response, administrator], "create_offer", start_create_offer)

shop.add_event([to_response], [processing_queue], lambda c: [SimToken(c, exp(1/4))], name="wait_for_response")

def start_process_response(c, r):
  return [SimToken((c, r), exp(1/4))]
task(shop, [processing_queue, administrator], [done, administrator], "process_response", start_process_response)

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_intermediate_event.csv")
shop.simulate(24*60, reporter)
reporter.close()
