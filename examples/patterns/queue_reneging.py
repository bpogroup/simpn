#Reneging is a situation in which arriving customers are willing to wait for only a limited period of time before they renege from the queue.
#Cars arrive at a carwash according to an exponential distribution of 10 min.
#Washing a car takes EXPO(7) minutes (1 server)
#Cars that are waiting for more than 10 minutes leave the system with a probability of 80%


from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform
from simpn.reporters import SimpleReporter, ProcessReporter
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation

carwash = SimProblem()

left=carwash.add_var("left")
waiting = carwash.add_var("waiting")
machine = carwash.add_var("machine")

machine.put("m1")

done = carwash.add_var("done")

time_var = carwash.var("time")


prototype.BPMNStartEvent(carwash, [], [waiting], "arrive", lambda: exp(100), behavior=lambda : [SimToken({'tested': 0})]) #tokens enter the system with a flag set to false (meaning, they have not yet waited too long and decided whether to leave or not)


def leave_condition(t, c1_queue, left_queue):
    for c in c1_queue:
        if c.value[1]['tested'] == 0 and t - c.time > 0.5: #c[1] contains the value of the token (c[0] is the token ID, used internally) and in this case it is a dictionary with a single key 'tested'
            return True
    return False



def leave_queue(t, c1_queue, left_queue):
    for c in c1_queue:
        if c.value[1]['tested'] == 0 and t - c.time > 0.5:
            c.value[1]['tested'] = 1
            percentage = uniform(1,100)
            if percentage >= 80:
                c1_queue.remove(c)
                left_queue.append(c)
    return [c1_queue, left_queue]


carwash.add_event([time_var, waiting.queue, left.queue],[waiting.queue, left.queue], leave_queue, guard=leave_condition)

prototype.BPMNTask(carwash, [waiting, machine], [done, machine],"wash car", lambda c, r: [SimToken((c, r), delay=exp(1))])
prototype.BPMNEndEvent(carwash, [done], [], "leave after service")
prototype.BPMNEndEvent(carwash, [left], [], "leave without service")

reporter = ProcessReporter()
carwash.simulate(10, reporter)

reporter.print_result()
#m = Visualisation(carwash, "./layout4.txt")
#m.show()
#m.save_layout("./layout4.txt")