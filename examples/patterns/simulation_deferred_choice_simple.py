from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event, choice, end_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
offer_qeue = shop.add_var("offer queue")
to_choose = shop.add_var("to choose")
waiting_response = shop.add_var("waiting for response")
processing_queue = shop.add_var("processing queue")
to_leave = shop.add_var("to leave")
done = shop.add_var("done")

# Define resources.
administrator = shop.add_var("administrator")

administrator.put("a1")

# Define events.
def interarrival_time():
  return exp(1/10)
start_event(shop, [], [offer_qeue], "customer_arrived", interarrival_time)

def start_create_offer(c, r):
  return [SimToken((c, r), exp(1/4))]
task(shop, [offer_qeue, administrator], [to_choose, administrator], "create_offer", start_create_offer)

def choose(c):
  waiting_time = exp(1/4)
  if waiting_time < 5:
    return [SimToken((c[0], waiting_time))]
  else:
    return [SimToken((c[0], 5))]

choice(shop, [to_choose], [processing_queue, to_leave], "choose", choose, [lambda c: c[1] < 5, lambda c: c[1] >= 5])

shop.add_event([waiting_response], [processing_queue], lambda c: [SimToken(c, c[1])], name="wait_for_response")

def start_process_response(c, r):
  return [SimToken((c, r), exp(1/4))]
task(shop, [processing_queue, administrator], [done, administrator], "process_response", start_process_response)

end_event(shop, [done], [], "done")

end_event(shop, [to_leave], [], "left")

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_deferred_simple.csv")
shop.simulate(24*60, reporter)
reporter.close()
