from simpn.simulator import SimProblem, SimToken

P = SimProblem()

clock = P.add_var("clock")
places=[clock]
N=5 #<--- changing the PetriNet topology
for i in range(N):
    places.append( P.add_var("S"+str(i)) )

def behavior(clock, *stores):
    out=[SimToken(clock+1, delay=1)]
    for store in stores:
        out.append( SimToken(store+1, delay=1) )
    return out

def guard(clock, *stores):
    return sum(stores)<100

# init 0
for p in places:
    p.put(0,time=0)

P.add_event(inflow=places, outflow=places, behavior=behavior, guard=guard)

# Running
from simpn.reporters import SimpleReporter
P.simulate(10, SimpleReporter())
from simpn.visualisation import Visualisation
v = Visualisation(P)
v.show()