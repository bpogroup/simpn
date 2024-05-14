# Resources have different activities and may therefore be unavailable to the process for some time
# Cars arrive at a garage according to an exponential distribution of 20 min.
# Checking a car takes Uniform(15,20) minutes (1 mechanic)
# If the queue is empty the mechanic will take a coffee break of 10 minutes He will stay in his break unless
# more than 2 cars are waiting in the queue


from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform
from simpn.reporters import SimpleReporter
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation

# Instantiate a simulation problem.
garage = SimProblem()

# Define queues and other 'places' in the process.
check_queue = garage.add_var("check queue")
done = garage.add_var("done")

# Define resources and resource state variables.
mechanic = garage.add_var("mechanic") # the variable that contains available mechanics
mechanic.put("m1") # mechanic m1
mechanic_break = garage.add_var("mechanic_break") # the variable that contains mechanics who are on a break

# Define events.
prototype.BPMNStartEvent(garage, [], [check_queue], "start", lambda: 20)

# Note: after the task is done, we send mechanics for the 'break check'
prototype.BPMNTask(garage, [check_queue, mechanic], [done, mechanic], "check_cars", lambda c, r: [SimToken((c, r), delay=uniform(15,20))])

def start_break_condition(c,car_queue):
    if len(car_queue)==0:
        return True
    else:
        return False
# The break check is basically a choice
def start_break(c, car_queue):
        return [SimToken(c, delay=10), car_queue]


garage.add_event([mechanic, check_queue.queue], [mechanic_break, check_queue.queue], start_break, guard=start_break_condition)

#once the mechanic is on a break, it will be availble again only when two or more cars are waiting
def stay_in_break_condition(c, car_queue):
    if len(car_queue)<2:
        return True
    else:
        return False

def back_to_work_condition(c, car_queue):
    if len(car_queue)>=2:
        return True
    else:
        return False

def stay_in_break(c, car_queue):
    return [SimToken(c, delay=10),car_queue]

def back_to_work(c, car_queue):
    return [SimToken(c),car_queue]

garage.add_event([mechanic_break, check_queue.queue],[mechanic_break, check_queue.queue],stay_in_break, guard=stay_in_break_condition)
garage.add_event([mechanic_break, check_queue.queue],[mechanic, check_queue.queue],back_to_work, guard=back_to_work_condition)

prototype.BPMNEndEvent(garage, [done], [], "complete")

# Run the simulation.
# garage.simulate(100, SimpleReporter())

m = Visualisation(garage, "./layout6.txt")
m.show()
m.save_layout("./layout6.txt")