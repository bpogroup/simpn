"""
Example of using the IDE with a simulation problem.

This script demonstrates how to load a simulation into the IDE.
"""

import sys
from PyQt6.QtWidgets import QApplication
from simpn.visualisation.ide import MainWindow
from simpn.simulator import SimProblem, SimToken


def create_simple_example():
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

    return shop


def main():
    """Run the IDE with a loaded simulation."""
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Create and load a simulation
    sim_problem = create_simple_example()
    window.load_simulation(sim_problem)
    
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
