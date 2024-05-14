from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
to_check_queue = shop.add_var("to check queue")
waiting = shop.add_var("queue")
done = shop.add_var("done")
to_leave = shop.add_var("to leave")

# Define resources.
cassier = shop.add_var("cassier")
cassier.put("r1")

# Define events.
prototype.BPMNStartEvent(shop, [], [to_check_queue], "start", lambda: exp(1/9))

# Check the queue length
def check_queue_length(customer, complete_queue):
    if len(complete_queue) < 5: # If it is less than 5 customers in the queue, the customer goes into the queue
        # we add the customer to the queue by actually manipulating the queue variable
        complete_queue.append(SimToken(customer))
        return [complete_queue, None]
    else: # If it is more than 5 customers in the queue, the customer leaves
        # note that this means that the queue is not changed, but we need to put it back.
        return [complete_queue, SimToken(customer)]
shop.add_event([to_check_queue, waiting.queue], [waiting.queue, to_leave], check_queue_length)

prototype.BPMNTask(shop, [waiting, cassier], [done, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), delay=exp(1/9))])

prototype.BPMNEndEvent(shop, [done], [], "complete")
prototype.BPMNEndEvent(shop, [to_leave], [], "leave")


# Run the simulation.
reporter = EventLogReporter("./temp/simulation_limited_queue_space.csv")
shop.simulate(24*60, reporter)
reporter.close()
