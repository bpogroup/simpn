# Balking is a situation in which an arriving customer does not join the queue but
# goes away or goes someplace else. Example: The owner of the petrol station has the
# feeling that some potential clients are leaving the station because there is no place 
# to wait for service. Assumption: one car arrives on average each 4 minutes
# (according to a Poisson process) and the service time is uniformly distributed between 1 and 6 minutes.
# The maximum queue capacity is 4.

from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform
from simpn.reporters import SimpleReporter
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation


# Instantiate a simulation problem.
station=SimProblem()

# Define queues and other 'places' in the process.
to_check_queue = station.add_var("to check queue")
waiting = station.add_var("queue")
done = station.add_var("done")
to_leave = station.add_var("to leave")

# Define resources.
pump = station.add_var("pump")
pump.put("p1")

# Define events.
def interarrival_time():
  return exp(4)

prototype.BPMNStartEvent(station, [], [to_check_queue], "start", interarrival_time)

# Check the queue length
def check_queue_length(customer, complete_queue):
    if len(complete_queue) < 4: # If it is less than 4 customers in the queue, the customer goes into the queue
        # we add the customer to the queue by actually manipulating the queue variable
        complete_queue.append(SimToken(customer))
        return [complete_queue, None]
    else: # If it is more than 4 customers in the queue, the customer leaves
        # note that this means that the queue is not changed, but we need to put it back.
        return [complete_queue, SimToken(customer)]

station.add_event([to_check_queue, waiting.queue], [waiting.queue, to_leave], check_queue_length)
prototype.BPMNTask(station, [waiting, pump], [done, pump], "refueling", lambda c, r: [SimToken((c, r), delay=uniform(1,6))])

prototype.BPMNEndEvent(station, [done], [], "complete")
prototype.BPMNEndEvent(station, [to_leave], [], "leave")


# Run the simulation.
station.simulate(100, SimpleReporter())
m = Visualisation(station, "./layout1.txt")
m.show()
m.save_layout("./layout1.txt")

