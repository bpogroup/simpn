from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event

shop = SimProblem()

to_create_offer = shop.add_var("to_create_offer")
to_wait_for_response = shop.add_var("to_wait_for_response")
to_process_response = shop.add_var("to_process_response")
done = shop.add_var("done")

administrator = shop.add_var("administrator")

administrator.put("a1")

def interarrival_time():
  return exp(1/10)
start_event(shop, [], [to_create_offer], "customer_arrived", interarrival_time)

def start_create_offer(c, r):
  return [SimToken((c, r), exp(1/4))]
task(shop, [to_create_offer, administrator], [to_wait_for_response, administrator], "create_offer", start_create_offer)

shop.add_event([to_wait_for_response], [to_process_response], lambda c: [SimToken(c, exp(1/4))], name="wait_for_response")

def start_process_response(c, r):
  return [SimToken((c, r), exp(1/4))]
task(shop, [to_process_response, administrator], [done, administrator], "process_response", start_process_response)

reporter = EventLogReporter("./temp/simulation_intermediate_event.csv")
shop.simulate(24*60, reporter)
reporter.close()
