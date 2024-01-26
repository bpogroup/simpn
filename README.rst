SimPN
=====

SimPN (Simulation with Petri Nets) is a package for discrete event simulation in Python.

SimPN provides a simple syntax that is based on Python functions and variables, making it familiar for people who already know Python. At the same time, it uses the power of and flexibility of `Colored Petri Nets (CPN)`_ for simulation. It also provides prototypes for easy modeling of frequently occurring simulation constructs, such as (customer) arrival, processing tasks, queues, choice, parallelism, etc.

.. _`Colored Petri Nets (CPN)`: http://dx.doi.org/10.1145/2663340

.. role:: python(code)
  :language: python
  :class: highlight

Installation
============

The SimPN package is available on PyPI and can simply be installed with pip.

.. code-block::

    python -m pip install simpn

A Basic Tutorial
================

To illustrate how SimPN works, let's consider a simulation model of a cash register at a small shop,
which we can initialize as follows. This imports parts from the SimPN library that we use here
and further on in the example.

.. code-block:: python

    from simpn.simulator import SimProblem, SimToken

    shop = SimProblem()

A discrete event simulation is defined by the *state* of the system that is simulated and the *events* that can happen
in the system.

Simulation State and Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In case of our shop, the state of the system consists of customers that are waiting in line at
the cash register, resources that are free to help the customer, and resources that are busy helping a customer.
Consequently, we can model the state of our simulation, by defining two *variables* as follows.

.. code-block:: python

    customers = shop.add_var("customers")
    resources = shop.add_var("resources")

A simulation variable is different from a regular Python variable in two important ways. First, a simulation variable
can contain multiple values, while a regular Python variable can only contain one value. Second, values of a simulation
variable are available from a specific moment in (simulation) time. More about that later.
So, with that in mind, let's give our variables a value.

.. code-block:: python

    resources.put("cassier")
    customers.put("c1")
    customers.put("c2")
    customers.put("c3")

We now gave the `resources` variable one value, the string `cassier`, but we gave the `customers` variable three values.
You can probably understand why we did that: we now have one cassier and three customers waiting. This is the
*initial state* of our simulation model.

Simulation Events
~~~~~~~~~~~~~~~~~

Simulation events define what can happen in the system and how the system (state variables) change when they do.
We define simulation events as Python functions that take a system state and return a new system state.
Remember that the system state is defined in terms of variables, so an event function takes (values of) state variables as
input and produces (values of) state variables as output.

.. code-block:: python

    def process(customer, resource):
        return [SimToken(resource, delay=0.75)]

    shop.add_event([customers, resources], [resources], process)

In our example we introduce a single event that represents a resource processing a waiting customer.
First, let's focus on `shop.add_event` in the code below. This tells the simulator that our event takes a value from the
`customers` variable and a value from the `resources` variable as input, produces a value for the `resources`
variable as output, and uses the `process` function to change the state variables.
Describing that in natural language: it takes a customer and a resource and, when it is done, returns a resource.

The `process` function defines how the event modifies the system state (variables).
Taking a value from the `customers` variable (and calling it `customer`) and a value from the `resources` variable
(and calling it `resource`), the function returns the `resource` again. This return value will be put into the
`resources` variable, as per the `shop.add_event` definition. However, as you can see, there are several things
going on in the return statement.

First, the function does not return a single resource value, but a list of values. This is simply a convention
that you have to remember: event functions return a list of values. The reason for this is that we defined the
simulation event in `shop.add_event` as taking a list of values (consisting of one value from customers and one value from
resources) as input and as producing a list of values (consisting of one value for resources) as output.
Accordingly, we must produce a list of values as output, even if there is only one value.

Second, the function does not return the `resource`, but returns a `SimToken` containing the resource.
That is because in simulation, values have a time from which they are available. A value with a time
is called a *token*. This represents that the value is only available at, or after, the specified time.
In this case, the resource value is made available after a delay of 0.75. You can consider this the time it takes the resource to
process the customer. Since it takes 0.75 to process a customer, the resource is only made available
again after a delay of 0.75. In the meantime no new `process` events can happen, because a value from `resources`,
which is needed as input for such an event, is not available.

Putting it all together
~~~~~~~~~~~~~~~~~~~~~~~

Now we have modeled the entire system and we can simulate it.
To do that, we call the `simulate` function on the model.
This function takes two parameters. One is the amount of time for which the simulation will be run.
The other is the reporter that will be used to report the results of the simulation.
In our example we will run the simulation for 10. (Since we only have 3 customers, and each customer
takes 0.75 to process, this should be more than enough.) We will use a `SimpleReporter` from the
reporters package to report the result. This reporter simply prints each event that happens
to the standard output.

.. code-block:: python

    from simpn.reporters import SimpleReporter

    shop.simulate(10, SimpleReporter())

As expected, running this code leads to the following output.
The event of (starting) processing customer c1 happens at time t=0.
It uses value `c2` for variable `customers` and value `cassier` for variable `resources`.
The event of (starting) processing customer c2 happens at time t=0.75.
This is logical, because our definition of the `process` event that the value `cassier` is only available
in the variable `resources` again after 0.75. Accordingly, processing of c3 happens at time t=1.5.

.. code-block::

    process{customers: c1, resources: cassier}@t=0
    process{customers: c2, resources: cassier}@t=0.75
    process{customers: c3, resources: cassier}@t=1.5

For completeness, the full code of the example is:

.. code-block:: python

    from simpn.simulator import SimProblem, SimToken

    shop = SimProblem()

    resources = shop.add_var("resources")
    customers = shop.add_var("customers")

    def process(customer, resource):
        return [SimToken(resource, delay=0.75)]

    shop.add_event([customers, resources], [resources], process)

    resources.put("cassier")
    customers.put("c1")
    customers.put("c2")
    customers.put("c3")

    from simpn.reporters import SimpleReporter

    shop.simulate(10, SimpleReporter())

Visualizing the Model
=====================

To help check whether the model is correct, it is possible to visualize it. To this end, there is a Visualisation class.
You can simply create an instance of this class and call the `show` method to show the model as follows.

.. code-block:: python

    from simpn.visualisation import Visualisation

    v = Visualisation(shop)
    v.show()

The model will now be shown as a Petri net in a separate window.
The newly opened window will block further execution of the program until it is closed.
You can interact with the model in the newly opened window. Pressing the space bar will advance the simulation by one step.
You can also change the layout of the model by dragging its elements around.
After the model window is closed, you can save the layout of the model to a file, so that you can open it later.
Use the method `save_layout` to save the model to do so.
You can load the layout of the model from the file later, by passing the saved layout as a parameter to the constructor.
If the layout file does not exist, the model will be shown with an automatically generated layout.

.. code-block:: python

    v = Visualisation(shop, "layout.txt")
    v.show()
    v.save_layout("layout.txt")