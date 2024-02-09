#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 14:53:49 2024

@author: lgenga
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 10:38:05 2023

@author: lgenga
"""

#Reneging is a situation in which arriving customers are willing to wait for only a limited period of time before they renege from the queue.
#Cars arrive at a carwash according to an exponential distribution of 10 min.
#Washing a car takes EXPO(7) minutes (1 server)
#Cars that are waiting for more than 10 minutes leave the system with a probability of 80%


from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform
from simpn.reporters import SimpleReporter
from simpn.prototypes import start_event, task, end_event, intermediate_event
from simpn.visualisation import Visualisation

carwash = SimProblem()

left=carwash.add_var("left")
waiting = carwash.add_var("waiting")
machine = carwash.add_var("machine")

machine.put("m1")

done = carwash.add_var("done")

time_var = carwash.var("time")


start_event(carwash, [], [waiting], "arrive", lambda: exp(100))


def leave_condition(t, c1_queue, left_queue):
    for c in c1_queue:
        if t - c.time > 0.5:
            return True
    return False



def leave_queue(t, c1_queue, left_queue):
    for c in c1_queue:
        if t - c.time > 0.5:
            percentage = uniform(1,100)
            if percentage >= 80:
                c1_queue.remove(c)
                left_queue.append(c)
    return [c1_queue, left_queue]


carwash.add_event([time_var, waiting.queue, left.queue],[waiting.queue, left.queue], leave_queue, guard=leave_condition)

task(carwash, [waiting, machine], [done, machine],"wash car", lambda c, r: [SimToken((c, r), delay=exp(1))])
end_event(carwash, [done], [], "leave after service")
end_event(carwash, [left], [], "leave without service")


#carwash.simulate(100, SimpleReporter())
m = Visualisation(carwash, "./layout4.txt")
m.show()
m.save_layout("./layout4.txt")
