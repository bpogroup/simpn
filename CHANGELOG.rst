Changelog
=========

Version 1.0.1 (2024-03-21)
---------------------------

- [Bugfix] store-checkpoint did not work correctly for SimVarTime.

Version 1.1.0 (2024-05-14)
---------------------------

- [Feature] improved visualization of prototypes.

Version 1.2.0 (2024-05-20)
---------------------------

- [Feature] added queueing network prototypes.

Version 1.2.1 (2024-05-29)
---------------------------

- [Bugfix] if a layout contains a node not in the model anymore, it does not generate an exception.

Version 1.2.2 (2024-05-29)
---------------------------

- [Change] changed the semantics of queue tokens: now they are always available instead of at the time of the last token in the queue.

Version 1.2.3 (2024-06-22)
---------------------------

- [Minor feature] added configurable separator to EventLogReporter.
- [Minor feature] added BPMNFlow prototype.
- [Minor feature] BPMN tasks can now have multiple inflows and outflows.
- [Minor feature] BPMN intermediate events can now have multiple inflows and outflows.

Version 1.2.4 (2024-08-27)
--------------------------

- [Minor feature] added ability to include images in package, used to add logo.
- [Minor feature] added synonymous methods for adding places and transitions, rather than variables and events, to the simulation model.

Version 1.2.5 (2024-09-08)
--------------------------

- [Minor feature] added variadic parameters for events.

Version 1.2.6 (2024-09-18)
--------------------------

- [Minor feature] added the option to prioritize bindings.

Version 1.2.7 (2024-11-06)
--------------------------

- [Minor feature] added the option to make nodes invisible in the visualization.

Version 1.2.8 (2024-11-06)
--------------------------

- [Bugfix] visualization of time variable did not work correctly.

Version 1.2.9 (2024-12-04)
--------------------------

- [Bugfix] solved package dependency problems.

Version 1.2.10 (2025-05-09)
--------------------------

- [Minor feature] added BPMN exclusive split and join gateways.

Version 1.2.11 (2025-06-25)
--------------------------

- [Bugfix] tokens now have a dedicated less than operator that takes different datatypes into account properly.

Version 1.2.12 (2025-06-28)
---------------------------

- [Bugfix] fixed problem with the API documentation of prototypes.
- [Minor feature] data can now be exported to the log using the EventLogReporter
- [Minor feature] added BPMN parallel split and join gateways.

Version 1.3.0 (2025-07-07)
---------------------------

- [Major feature] added conformance checking functionality to the analysis module.