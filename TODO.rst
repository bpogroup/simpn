TODO
====

Code:

- Create decorators for prototypes.
  Maybe decorators are not the best way to go and we can simply pass strings to inflow/ outflow variables. 
  It is clear that it is pretty easy to lose track of the information that is passed via the variables.
  We should do something to make that more insightful. One thing we could do is typechecking on the variables.
  Another thing we could do is relate the variables more clearly to (the figure of) the model.
  Also, we could encourage including print statements.
- Make a visualization.
- Do a stress test for performance.
- Implement replications, warm-up time.
- Have others make assignments with the library, get input on: what is (not) possible, ask to send each error message with how long it took them to fix it.

Documentation:

- Document the basic theory.
  Note in the documentation that 'mutable types' do not work. Consequently, must use the pn_list, rather than the traditional Python list.
- Document how each of the basic patterns can be implemented (priority queue, ...).

Nice to have:

- currently bindings are reconstructed after each firing, it is (much) more efficient to keep a record of the bindings and add/ remove only changed ones.