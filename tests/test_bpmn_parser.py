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

    # 71 is valid
    def test_valid_elements_wrong_values_parsing(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '71 valid elements wrong values.bpmn'))
        parser = BPMNParser()
        try:
            process = parser.parse_file(test_file)
            # If no exception is raised, the test should fail
            self.fail("BPMNParseException was not raised")
        except BPMNParseException as e:
            self.assertIn("The model contains a start event 'start no time' that has no property 'interarrival_time'.", str(e))
            self.assertIn("The model contains a start event 'start wrong time' that has no property 'interarrival_time'.", str(e))
            self.assertIn("The interarrival_time of start event 'start no data' must have a 'dataState'.", str(e))
            self.assertIn("The interarrival_time of start event 'start wrong value' does not evaluate to a number.", str(e))
            self.assertIn("The model contains a task 'task no time' that has no property 'processing_time'.", str(e))
            self.assertIn("The model contains a task 'task wrong time' that has no property 'processing_time'.", str(e))
            self.assertIn("The processing_time of task 'task no data' must have a 'dataState'.", str(e))
            self.assertIn("The processing_time of task 'task wrong value' does not evaluate to a number.", str(e))
            self.assertIn("Invalid probability format for arc: variable < 1. Expected format is 'number%'.", str(e))
            self.assertIn("Invalid probability format for arc: variable >= 1. Expected format is 'number%'.", str(e))

    # 80 is a correct model that can also simulate
    def test_valid_simulation_model_parsing(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '80 correct numbers.bpmn'))
        parser = BPMNParser()
        try:
            process = parser.parse_file(test_file)
            self.assertIsNotNone(process)  # Ensure that a process is returned
            self.assertTrue(hasattr(process, 'nodes'))  # Check if the process has nodes attribute
            self.assertTrue(len(process.nodes) > 0)  # Ensure that there are nodes in the process
        except BPMNParseException as e:
            self.fail(f"Parsing valid BPMN file raised an exception: {e}")
    
    # Test transformation creates something
    def test_transformation_to_simulation_model(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '80 correct numbers.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            sim_problem = parser.transform()
            self.assertIsNotNone(sim_problem)  # Ensure that a simulation problem is returned
            self.assertTrue(len(sim_problem.prototypes) > 0)  # Ensure that there are prototypes in the simulation model
            self.assertTrue(len(sim_problem.places) > 0)  # Ensure that there are places (variables) in the simulation model
            self.assertTrue(len(sim_problem.events) > 0)  # Ensure that there are events in the simulation model
        except BPMNParseException as e:
            self.fail(f"Transformation to simulation model raised an exception: {e}")

    # Test transformation creates 1 lane ("employee"), 3 tasks ("Task A", "Task B", "Task C"), 1 start ("start"), 2 end ("end1", "end2"), 1 XOR gateway
    def test_transformation_nodes_correct(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '80 correct numbers.bpmn'))
        parser = BPMNParser()
        try:
            parser.parse_file(test_file)
            sim_problem = parser.transform()
            
            # Check for lane
            var_names = [var._id for var in sim_problem.places]
            self.assertIn("employee", var_names)

            # Check for tasks
            event_names = [event._id for event in sim_problem.events]
            self.assertIn("Task A<task:start>", event_names)
            self.assertIn("Task B<task:start>", event_names)
            self.assertIn("Task C<task:start>", event_names)
            self.assertIn("start<start_event>", event_names)
            self.assertIn("end1<end_event>", event_names)
            self.assertIn("end2<end_event>", event_names)
            self.assertIn("xor split<xor_split>", event_names)

        except BPMNParseException as e:
            self.fail(f"Transformation structure check raised an exception: {e}")
    
    # Test transformation creates correct connections: 
    # - "Task A" has incoming and outgoing connection to "employee"
    # - "Task A" has incoming connection from "start" and outgoing to "xor split"
    # - "xor split" has outgoing connections to "Task B" and "Task C"
    # - "Task B" and "Task C" have incoming connections from "xor split" and outgoing to "end1" and "end2" respectively
    def test_transformation_connections_correct(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '80 correct numbers.bpmn'))
        parser = BPMNParser()

        parser.parse_file(test_file)
        sim_problem = parser.transform()
        
        event_dict = {event._id: event for event in sim_problem.events}
        var_dict = {var._id: var for var in sim_problem.places}
        
        # Check "start" connections: start has two outgoing flows, the second must go to "Task A"
        # "Task A" has two incoming flows, the first must come from "start".
        start_event = event_dict["start<start_event>"]
        self.assertEqual(len(start_event.outgoing), 2)
        task_a = event_dict["Task A<task:start>"]
        self.assertEqual(len(task_a.incoming), 2)
        self.assertIs(start_event.outgoing[1], task_a.incoming[0])

        # Check "Task A" to employee connections
        task_a = event_dict["Task A<task:start>"]
        self.assertIn(var_dict["employee"], task_a.incoming)
        task_a = event_dict["Task A<task:complete>"]
        self.assertIn(var_dict["employee"], task_a.outgoing)

        # Check "Task A" to "xor split" connection
        xor_split = event_dict["xor split<xor_split>"]
        self.assertIs(task_a.outgoing[0], xor_split.incoming[0])

        # Check "xor split" to "Task B" and "Task C" connections
        task_b = event_dict["Task B<task:start>"]
        task_c = event_dict["Task C<task:start>"]
        self.assertIs(xor_split.outgoing[0], task_b.incoming[0])
        self.assertIs(xor_split.outgoing[1], task_c.incoming[0])

        # Check "Task B" to "end1" connection
        end1 = event_dict["end1<end_event>"]
        task_b_complete = event_dict["Task B<task:complete>"]
        self.assertIs(task_b_complete.outgoing[0], end1.incoming[0])

    # Test transformation creates correct: employee numbers, task processing times, start interarrival time, xor probabilities
    def test_transformation_properties_correct(self):
        test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ext', 'bpmn_test_files', '80 correct numbers.bpmn'))
        parser = BPMNParser()

        parser.parse_file(test_file)
        sim_problem = parser.transform()
        
        event_dict = {event._id: event for event in sim_problem.events}
        var_dict = {var._id: var for var in sim_problem.places}

        # Check employee amount
        self.assertEqual(len(var_dict["employee"].marking), 2)

        # Check interarrival times of start event, by sampling 1000 times and checking that the average is close to 10
        start_event = event_dict["start<start_event>"]
        interarrival_samples = [start_event.behavior("start1")[0].delay for _ in range(1000)]
        avg_interarrival = sum(interarrival_samples) / len(interarrival_samples)
        self.assertAlmostEqual(avg_interarrival, 10, delta=1)

        # Check processing times of tasks, by sampling 1000 times and checking that the averages are close to 4
        task_a = event_dict["Task A<task:start>"]
        processing_samples_a = [task_a.behavior("case1", "employee1")[0].delay for _ in range(1000)]
        avg_processing_a = sum(processing_samples_a) / len(processing_samples_a)
        self.assertAlmostEqual(avg_processing_a, 4, delta=0.5)

        # Check that the xor split samples the first and second path with approx. 50% probability each
        xor_split = event_dict["xor split<xor_split>"]
        path_counts = [0, 0]
        for _ in range(1000):
            result = xor_split.behavior("case1")
            if result[0] is not None:
                path_counts[0] += 1
            elif result[1] is not None:
                path_counts[1] += 1
        path1_ratio = path_counts[0] / 1000
        path2_ratio = path_counts[1] / 1000
        self.assertAlmostEqual(path1_ratio, 0.5, delta=0.1)
        self.assertAlmostEqual(path2_ratio, 0.5, delta=0.1)