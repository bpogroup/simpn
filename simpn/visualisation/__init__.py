"""
Visualisation module for simpn.
==============================

This package provides classes and functions to create an interactive visual representation of a Petri net-based simulation.

The visualisation will show a MainWindow containing:
    - A toolbar at the top with buttons to control the simulation
    - A ModelPanel, wrapped in a PyGameWidget, in the center showing the simulation model
    - An AttributePanel on the right displaying properties of selected elements
    - A DebugPanel at the bottom for simulation control and status information

The application can run in two modes:
1. Embedded mode: by programmatically using the `Visualisation` class to create and manage the visual representation of a specific simulation.
2. Application mode: by starting the simpn.visualisation as main application, which provides a graphical user interface.

An example of the first method is as follows:
```python
    from simpn.simulator import SimProblem, SimToken
    from simpn.visualisation import Visualisation

    shop = SimProblem()

    v_resources = shop.add_var("resources")
    v_customers = shop.add_var("customers")

    e_process = shop.add_event([v_customers, v_resources], [v_resources], lambda c, r: [SimToken(r, delay=0.75)])

    v_resources.put("cassier")
    v_customers.put("c1"); v_customers.put("c2"); v_customers.put("c3")

    v = Visualisation(shop)
    v.show()

Modules
-------

- `base`: Contains the main `Visualisation` class, which can be called to activate the visualisation, as well as the `MainWindow`, `PyGameWidget`, `AttributePanel`, and `DebugPanel` GUI components.
- `model_panel`: Contains the `ModelPanel` class, which is responsible for creating and layouting the simulation model, as well as classes for visual representation of simulation elements, including `PlaceViz`, `TransitionViz`, and `TokenShower`.
- `model_panel_mods`: Contains extensions that can be placed on the `ModelPanel` for additional functionality.
- `constants`: Contains various constants used throughout the visualisation module.
- `events`: Contains event handling logic for the simulation, which allows the various classes to operate in a loosely coupled manner.

Workflow and Extensibility
---------------------------

The event handling system allows visual elements to respond to changes in the simulation model without tight coupling.
New visual elements or modifications can be added by creating new classes that listen for specific simulation events and respond accordingly.
They should implement the `events.IEventHandler` interface to register for and handle events.
The `listen_to` method specifies which event types an element is interested in, while the `handle_event` method contains the logic to respond to those events.

There are two main types of visual elements:
1. Main window components (e.g., `ModelPanel`, `AttributePanel`, `DebugPanel`).
   These should be instantiated by the __init__ method of the `MainWindow` class.
2. Mods of the `ModelPanel`, which provide additional display information on the `ModelPanel`.
   These should be instantiated after the simulation model has been created in `MainWindow.set_simulation`.
   These elements can respond to simulation events such as RENDER_UI, which carry a PyGame surface to draw on.

Visual elements should be deregistered from a simulation model and registered for a new simulation model with the event dispatcher when a simulation model is set in `MainWindow.set_simulation`.

"""

from .base import Visualisation
from .model_panel import PlaceViz, TransitionViz, TokenShower, Shape, Hook, Edge, Node
from .constants import *