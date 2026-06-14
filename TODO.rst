TODO
====

The current way of modeling data in BPMN or in general is a bit difficult. Find a better way to do it.

Add location information to specialized data stores (for BPO purposes).

It should be easier to access the simulation time in guards or behavior functions.

Describe the ways in which decisions can relate to transitions in the process model:
1. decisions valuate variables (places) that are guards for transitions already in the process model
2. decisions directly change tokens on places (note that this cannot registered by a Reporter)
3. action transitions are created as part of the process model with an incoming place that is the decision variables (places) - like solution 1
4. specific action-transitions are made that can be fired with values from the decision variables - like solution 2, but actions can now be reported
Important for 1 and 3 is that decision variable places are emptied when a decision is made. This coincides with the idea that decision variables are 'special' variables.

Improve the performance of the simulator.