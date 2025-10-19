"""
Test script to verify the BPMN parser transform function.
"""
import os
from simpn.bpmn_parser import BPMNParser
from simpn.visualisation import Visualisation

# Parse a BPMN file
test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '80 correct numbers.bpmn'))

parser = BPMNParser()
bpmn_model = parser.parse_file(test_file)

print("BPMN Model parsed successfully!")
print(f"Number of roles: {len(bpmn_model.get_roles())}")
print(f"Number of nodes: {len(bpmn_model.get_nodes())}")

# Transform to simulation model
print("\nTransforming to simulation model...")
sim_problem = parser.transform()

print("Simulation model created successfully!")
print(f"Number of prototypes: {len(sim_problem.prototypes)}")
print(f"Number of places (variables): {len(sim_problem.places)}")
print(f"Number of events: {len(sim_problem.events)}")

# Visualize the model
print("\nVisualizing the model...")
vis = Visualisation(sim_problem, "./temp/transformed_bpmn_layout.txt")
vis.show()
vis.save_layout("./temp/transformed_bpmn_layout.txt")
