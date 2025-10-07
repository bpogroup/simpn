import os
import unittest

from simpn.bpmn_parser import BPMNParser, BPMNParseException


class TestBPMNParser(unittest.TestCase):

    # '00 unacceptable elements.bpmn': "The BPMN Model contains the following error(s):\n- The model contains an illegal model element: dataObject.\n- The model contains an illegal model element: ioSpecification.\n- The model contains an illegal model element: dataOutput.\n- The model contains an illegal model element: inputSet.\n- The model contains an illegal model element: outputSetRefs.\n- The model contains an illegal model element: outputSet.\n- The model contains an illegal model element: dataOutputRefs.\n- The model contains an illegal model element: inputSetRefs.\n- The model contains an illegal model element: dataOutputAssociation.\n- The model contains an illegal model element: sourceRef.\n- The model contains an illegal model element: targetRef.\n- The model contains an illegal model element: dataObjectReference.",
    def test_unacceptable_elements_errors(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '00 unacceptable elements.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model contains an illegal model element: dataObject", str(e))
            self.assertIn("The model contains an illegal model element: ioSpecification", str(e))
            self.assertIn("The model contains an illegal model element: dataOutput", str(e))
            self.assertIn("The model contains an illegal model element: inputSet", str(e))
            self.assertIn("The model contains an illegal model element: outputSetRefs", str(e))
            self.assertIn("The model contains an illegal model element: outputSet", str(e))
            self.assertIn("The model contains an illegal model element: dataOutputRefs", str(e))
            self.assertIn("The model contains an illegal model element: inputSetRefs", str(e))
            self.assertIn("The model contains an illegal model element: dataOutputAssociation", str(e))
            self.assertIn("The model contains an illegal model element: sourceRef", str(e))
            self.assertIn("The model contains an illegal model element: targetRef", str(e))
            self.assertIn("The model contains an illegal model element: dataObjectReference", str(e))

    # '01 unconnected arc.bpmn': "Unexpected error: an arc contains the identifier of a node that cannot be found. This may be caused by the following errors:\n- The model contains an arc that is not connected at the beginning or at the end.",
    def test_unconnected_arc_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '01 unconnected arc.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model contains an arc that is not connected at the beginning or at the end.", str(e))

    # '02 label appears twice.bpmn': "The BPMN Model contains the following error(s):\n- There are two elements in the model that have the name 'Duplicate Task'.",
    def test_duplicate_label_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '02 label appears twice.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("There are two elements in the model that have the name 'Duplicate Task'.", str(e))

    # '10 no lane.bpmn': "The BPMN Model contains the following error(s):\n- The model has no roles.\n- There is a node that is not contained in a lane.\n- The task 'Task' is not contained in a lane.\n- There is a node that is not contained in a lane.",
    def test_no_lane_errors(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '10 no lane.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model has no roles.", str(e))
            self.assertIn("There is a node that is not contained in a lane.", str(e))
            self.assertIn("The task 'Task' is not contained in a lane.", str(e))
            self.assertIn("There is a node that is not contained in a lane.", str(e))

    # '11 unlabeled lane.bpmn': "The BPMN Model contains the following error(s):\n- The model contains a lane that has no name.",
    def test_unlabeled_lane_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '11 unlabeled lane.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model contains a lane that has no name.", str(e))

    # '12 out of lane.bpmn': "The BPMN Model contains the following error(s):\n- The task 'Task' is not contained in a lane.",
    def test_out_of_lane_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '12 out of lane.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The task 'Task' is not contained in a lane.", str(e))

    # '21 multiple start events.bpmn': "The BPMN Model contains the following error(s):\n- The model contains multiple start events.",
    def test_multiple_start_events_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '21 multiple start events.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model contains multiple start events.", str(e))

    # '22 unlabeled start event.bpmn': "The BPMN Model contains the following error(s):\n- The model contains a start event that has no name.",
    def test_unlabeled_start_event_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '22 unlabeled start event.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model contains a start event that has no name.", str(e))

    # '23 start multiple outgoing.bpmn': "The BPMN Model contains the following error(s):\n- Start event 'Start' does not have exactly one outgoing arc and zero incoming arcs.",
    def test_start_multiple_outgoing_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '23 start multiple outgoing.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("Start event 'Start' does not have exactly one outgoing arc and zero incoming arcs.", str(e))

    # '24 no start.bpmn': "The BPMN Model contains the following error(s):\n- Task 'Task' has no incoming arc.\n- The model has no start event.",
    def test_no_start_errors(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '24 no start.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("Task 'Task' has no incoming arc.", str(e))
            self.assertIn("The model has no start event.", str(e))

    # '25 start no outgoing.bpmn': "The BPMN Model contains the following error(s):\n- Start event 'Start' does not have exactly one outgoing arc and zero incoming arcs.",
    def test_start_no_outgoing_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '25 start no outgoing.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("Start event 'Start' does not have exactly one outgoing arc and zero incoming arcs.", str(e))

    # '31 unlabeled task.bpmn': "The BPMN Model contains the following error(s):\n- The model contains a task that has no name.",
    def test_unlabeled_task_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '31 unlabeled task.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model contains a task that has no name.", str(e))

    # '32 task multiple incoming outgoing.bpmn': "The BPMN Model contains the following error(s):\n- Task 'Problematic Task' does not have exactly one outgoig arc.",
    def test_task_multiple_incoming_outgoing_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '32 task multiple incoming outgoing.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("Task 'Problematic Task' does not have exactly one outgoig arc.", str(e))

    # '33 task no incoming outgoing.bpmn': "The BPMN Model contains the following error(s):\n- Task 'Problematic Task' has no incoming arc.\n- Task 'Problematic Task' does not have exactly one outgoig arc.",
    def test_task_no_incoming_outgoing_errors(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '33 task no incoming outgoing.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("Task 'Problematic Task' has no incoming arc.", str(e))
            self.assertIn("Task 'Problematic Task' does not have exactly one outgoig arc.", str(e))

    # '41 unlabeled intermediate.bpmn': "The BPMN Model contains the following error(s):\n- The model contains an intermediate event that has no name.",
    def test_unlabeled_intermediate_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '41 unlabeled intermediate.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model contains an intermediate event that has no name.", str(e))

    # '42 intermediate multiple incoming outgoing.bpmn': "The BPMN Model contains the following error(s):\n- Intermediate event 'Problematic Event' has multiple incoming arcs.\n- Intermediate event 'Problematic Event' does not have exactly one outgoig arc.",
    def test_intermediate_multiple_incoming_outgoing_errors(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '42 intermediate multiple incoming outgoing.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            print(str(e))

    # '43 intermediate no incoming outgoing.bpmn': "The BPMN Model contains the following error(s):\n- Intermediate event 'Problematic Event' has no incoming arc.\n- Intermediate event 'Problematic Event' does not have exactly one outgoig arc.",
    def test_intermediate_no_incoming_outgoing_errors(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '43 intermediate no incoming outgoing.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("Intermediate event 'Problematic Event' has no incoming arc.", str(e))
            self.assertIn("Intermediate event 'Problematic Event' does not have exactly one outgoig arc.", str(e))
            
    # '51 unlabeled end.bpmn': "The BPMN Model contains the following error(s):\n- The model contains an end event that has no name.",
    def test_unlabeled_end_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '51 unlabeled end.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model contains an end event that has no name.", str(e))
    
    # '52 end multiple incoming.bpmn': "The BPMN Model contains the following error(s):\n- End event 'End' does not have exactly one incoming arc and zero outgoing arcs.",
    def test_end_multiple_incoming_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '52 end multiple incoming.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("End event 'End' does not have exactly one incoming arc and zero outgoing arcs.", str(e))
    
    # '53 end no incoming.bpmn': "The BPMN Model contains the following error(s):\n- End event 'Problematic End' does not have exactly one incoming arc and zero outgoing arcs.",
    def test_end_no_incoming_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '53 end no incoming.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("End event 'Problematic End' does not have exactly one incoming arc and zero outgoing arcs.", str(e))
    
    # '61 choice multiple incoming outgoing.bpmn': "The BPMN Model contains the following error(s):\n- The model contains an exclusive gateway with multiple incoming and outgoing arcs.",
    def test_choice_multiple_incoming_outgoing_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '61 choice multiple incoming outgoing.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model contains an exclusive gateway with multiple incoming and outgoing arcs.", str(e))
    
    # '62 parallel multiple incoming outgoing.bpmn': "The BPMN Model contains the following error(s):\n- The model contains a parallel gateway with multiple incoming and outgoing arcs.",
    def test_parallel_multiple_incoming_outgoing_error(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '62 parallel multiple incoming outgoing.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model contains a parallel gateway with multiple incoming and outgoing arcs.", str(e))

    # 70 is valid
    def test_valid_file_parsing(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '70 all valid elements.bpmn'))
        parser = BPMNParser()
        try:
            process = parser.parse_file(test_file)
            self.assertIsNotNone(process)  # Ensure that a process is returned
            self.assertTrue(hasattr(process, 'nodes'))  # Check if the process has nodes attribute
            self.assertTrue(len(process.nodes) > 0)  # Ensure that there are nodes in the process
        except BPMNParseException as e:
            self.fail(f"Parsing valid BPMN file raised an exception: {e}")