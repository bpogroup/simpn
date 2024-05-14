from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter, TimeUnit
import simpn.prototypes as prototype

# Instantiate a simulation problem.
sales = SimProblem()

# Define queues and other 'places' in the process.
offer_queue = sales.add_var("offer queue")
to_response = sales.add_var("to response")
processing_queue = sales.add_var("processing queue")
done = sales.add_var("done")

# Define resources.
administrator = sales.add_var("administrator")
administrator.put("a1")

# Define events.
prototype.BPMNStartEvent(sales, [], [offer_queue], "customer_arrived", lambda: exp(1/10))

prototype.BPMNTask(sales, [offer_queue, administrator], [to_response, administrator], "create_offer", lambda c, r: [SimToken((c, r), delay=exp(1/4))])

sales.add_event([to_response], [processing_queue], lambda c: [SimToken(c, delay=exp(1/4))], name="wait_for_response")

prototype.BPMNTask(sales, [processing_queue, administrator], [done, administrator], "process_response", lambda c, r: [SimToken((c, r), delay=exp(1/4))])

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_intermediate_event.csv", timeunit=TimeUnit.DAYS)
sales.simulate(24*60, reporter)
reporter.close()
