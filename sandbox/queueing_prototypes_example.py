from simpn.simulator import SimProblem
from simpn.visualisation import Visualisation
from random import expovariate as exp
from simpn.prototypes_queueing import QueueingGenerator, QueueingQueue, QueueingServer

# Instantiate a simulation problem.
queueing_network = SimProblem()

q1 = QueueingQueue(queueing_network, "q1")
o1 = queueing_network.add_var("sink")

g1 = QueueingGenerator(queueing_network, [], [q1], "g1", exp(1/10))

s1 = QueueingServer(queueing_network, [q1], [o1], "s1", exp(1/9))

m = Visualisation(queueing_network)
m.show()