import unittest

from simpn.simulator import SimProblem, SimTokenValue
import simpn.prototypes as prototype


class TestDataStore(unittest.TestCase):

    def test_constructor_treats_third_type_arg_as_schema(self):
        test_problem = SimProblem()
        store = prototype.DataStore(test_problem, "staff", str)

        store.update_data("s1", "Alice")

        self.assertEqual(store.read_data("s1")[1], "Alice")

    def test_update_data_with_raw_values_checks_types(self):
        test_problem = SimProblem()
        store = prototype.DataStore(test_problem, "items", None, int, str, status=str)

        store.update_data("row1", 5, "alice", status="active")

        self.assertEqual(store.read_data("row1").id, "row1")
        self.assertEqual(store.read_data("row1")[1], 5)
        self.assertEqual(store.read_data("row1")[2], "alice")
        self.assertEqual(store.read_data("row1")["status"], "active")

    def test_update_data_with_raw_values_raises_on_type_mismatch(self):
        test_problem = SimProblem()
        store = prototype.DataStore(test_problem, "items", None, int, str, status=str)

        with self.assertRaises(TypeError):
            store.update_data("row1", "not_an_int", "alice", status="active")

    def test_update_data_allows_int_for_float_field(self):
        test_problem = SimProblem()
        store = prototype.DataStore(test_problem, "patients", has_appointment=bool, appointment_time=float)

        store.update_data("arrives0", has_appointment=False, appointment_time=1)

        self.assertEqual(store.read_data("arrives0")["appointment_time"], 1)

    def test_update_data_allows_partial_named_update_for_existing_row(self):
        test_problem = SimProblem()
        store = prototype.DataStore(test_problem, "patients", has_appointment=bool, appointment_time=float)

        store.update_data("arrives0", has_appointment=False, appointment_time=1)
        store.update_data("arrives0", appointment_time=3)

        self.assertEqual(store.read_data("arrives0")["has_appointment"], False)
        self.assertEqual(store.read_data("arrives0")["appointment_time"], 3)

    def test_update_data_partial_named_update_fails_for_new_row(self):
        test_problem = SimProblem()
        store = prototype.DataStore(test_problem, "patients", has_appointment=bool, appointment_time=float)

        with self.assertRaises(TypeError):
            store.update_data("arrives0", appointment_time=3)

    def test_update_data_with_simtokenvalue_checks_types(self):
        test_problem = SimProblem()
        store = prototype.DataStore(test_problem, "items", None, int, str, status=str)

        token_value = SimTokenValue("row1", 5, "alice", status="active")
        store.update_data("row1", token_value)

        self.assertEqual(store.read_data("row1"), token_value)

    def test_update_data_with_simtokenvalue_raises_on_id_or_type_mismatch(self):
        test_problem = SimProblem()
        store = prototype.DataStore(test_problem, "items", None, int, str, status=str)

        with self.assertRaises(ValueError):
            store.update_data("row1", SimTokenValue("row2", 5, "alice", status="active"))

        with self.assertRaises(TypeError):
            store.update_data("row1", SimTokenValue("row1", 5, "alice", status=3))

    def test_update_data_with_simtokenvalue_does_not_allow_partial_named(self):
        test_problem = SimProblem()
        store = prototype.DataStore(test_problem, "patients", has_appointment=bool, appointment_time=float)

        with self.assertRaises(TypeError):
            store.update_data("arrives0", SimTokenValue("arrives0", appointment_time=3))
