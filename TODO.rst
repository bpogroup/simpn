TODO
====

Code:

- Make a visualization.
- Do a stress test for performance.
- Implement replications, warm-up time.
- Have others make assignments with the library, get input on: what is (not) possible, ask to send each error message with how long it took them to fix it.

Nice to have:

- currently bindings are reconstructed after each firing, it is (much) more efficient to keep a record of the bindings and add/ remove only changed ones.
- some constructs are hard to follow and can be simplified, e.g.:
  o it may make sense to return event output variables instead of including them as arguments to the function.
  o it may make sense to separate a list of input/ output variables from a single input/ output variable, so you don't always have to use a list. 