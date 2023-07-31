from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event, choice, end_event

shop = SimProblem()

to_create_offer = shop.add_var("to_create_offer")
to_wait_for_response = shop.add_var("to_wait_for_response")
to_choose = shop.add_var("to_choose")
to_process_simple_response = shop.add_var("to_process_simple_response")
to_process_complex_response = shop.add_var("to_process_complex_response")
done = shop.add_var("done")

administrator = shop.add_var("administrator")

administrator.put("a1")

start_event(shop, [], [to_create_offer], "simple_customer_arrived", lambda: exp(1/15), lambda: [SimToken("simple")])
start_event(shop, [], [to_create_offer], "complex_customer_arrived", lambda: exp(1/30), lambda: [SimToken("complex")])

def start_create_offer(c, r):
  return [SimToken((c, r), exp(1/4))]
task(shop, [to_create_offer, administrator], [to_wait_for_response, administrator], "create_offer", start_create_offer)

shop.add_event([to_wait_for_response], [to_choose], lambda c: [SimToken(c, exp(1/4))], name="wait_for_response")

shop.add_event([to_choose], [to_process_simple_response], lambda c: [SimToken(c)], name="choose_simple", guard=lambda c: c[1] == "simple")
shop.add_event([to_choose], [to_process_complex_response], lambda c: [SimToken(c)], name="choose_complex", guard=lambda c: c[1] == "complex")

def start_process_simple_response(c, r):
  return [SimToken((c, r), exp(1/3))]
task(shop, [to_process_simple_response, administrator], [done, administrator], "process_simple_response", start_process_simple_response)

def start_process_complex_response(c, r):
  return [SimToken((c, r), exp(1/6))]
task(shop, [to_process_complex_response, administrator], [done, administrator], "process_complex_response", start_process_complex_response)

end_event(shop, [done], [], "done")

reporter = EventLogReporter("./temp/simulation_different_case_types.csv")
shop.simulate(24*60, reporter)
reporter.close()
