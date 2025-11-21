import unittest

from tests.dummy_problems import create_dummy_bpmn

from simpn.simulator import SimToken, SimTokenValue
from simpn.simulator import SimProblem
from simpn.priorities import FirstClassPriority
from simpn.priorities import WeightedFirstClassPriority


def construct_scenario(
    has_gold: bool = False,
    golds: int = 1,
    has_silver: bool = False,
    silvers: int = 1,
    has_bronze: bool = False,
    bronzes: int = 1,
    priority: callable = None,
) -> SimProblem:

    tokens = []
    id = 1

    if has_gold:
        for _ in range(golds):
            tokens.append(SimTokenValue(id, type="gold"))
            id += 1
    if has_silver:
        for _ in range(silvers):
            tokens.append(SimTokenValue(id, type="silver"))
            id += 1
    if has_bronze:
        for _ in range(bronzes):
            tokens.append(SimTokenValue(id, type="bronze"))
            id += 1

    problem = SimProblem()

    if priority:
        start = problem.add_place("start", priority=priority)
    else:
        start = problem.add_place("start")

    for tok in tokens:
        start.put(tok)

    end = problem.add_place("end")
    doing = problem.add_event(
        [start],
        [end],
        lambda c: [SimToken(c, delay=1)],
        name="doing",
    )

    return problem, tokens


def construct_scenario2(
    has_gold: bool = False,
    golds: int = 1,
    has_silver: bool = False,
    silvers: int = 1,
    has_bronze: bool = False,
    bronzes: int = 1,
    starts: int = 5,
) -> SimProblem:

    tokens = []
    id = 1

    problem = SimProblem()
    starts = [problem.add_place(f"start-{i+1}") for i in range(starts)]

    if has_gold:
        for _ in range(golds):
            tokens.append(SimTokenValue(id, type="gold"))
            starts[id % len(starts)].put(tokens[-1])
            id += 1
    if has_silver:
        for _ in range(silvers):
            tokens.append(SimTokenValue(id, type="silver"))
            starts[id % len(starts)].put(tokens[-1])
            id += 1
    if has_bronze:
        for _ in range(bronzes):
            tokens.append(SimTokenValue(id, type="bronze"))
            starts[id % len(starts)].put(tokens[-1])
            id += 1

    end = problem.add_place("end")
    for i, start in enumerate(starts):
        doing = problem.add_event(
            [start],
            [end],
            lambda c: [SimToken(c, delay=1)],
            name="doing_{}".format(i + 1),
        )

    return problem, tokens


class TestFirstClassPriority(unittest.TestCase):

    def setUp(self):
        self.problem = create_dummy_bpmn(structured=True)
        self.ideal_priority = FirstClassPriority(
            class_attr="type",
            priority_ordering=["gold", "silver", "bronze"],
        )
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_sim_works_without_attribute(self):

        priority = FirstClassPriority(class_attr="foobar", priority_ordering=[])
        self.problem.set_binding_priority(priority)

        try:
            self.problem.simulate(duration=25)
        except Exception as e:
            self.fail(f"Simulation failed when it should not have: {e}")

        priority = FirstClassPriority(
            class_attr="foobar", priority_ordering=["foo", "bar", "baz"]
        )
        self.problem.set_binding_priority(priority)

        try:
            self.problem.simulate(duration=25)
        except Exception as e:
            self.fail(f"Simulation failed when it should not have: {e}")

    def test_sim_works_with_attribute(self):
        priority = FirstClassPriority(class_attr="type", priority_ordering=["bronze"])
        self.problem.set_binding_priority(priority)

        try:
            self.problem.simulate(duration=25)
        except Exception as e:
            self.fail(f"Simulation failed when it should not have: {e}")

        priority = FirstClassPriority(
            class_attr="type", priority_ordering=["silver", "bronze"]
        )
        self.problem.set_binding_priority(priority)

        try:
            self.problem.simulate(duration=25)
        except Exception as e:
            self.fail(f"Simulation failed when it should not have: {e}")

        priority = FirstClassPriority(
            class_attr="type", priority_ordering=["foobar", "silver", "bronze"]
        )
        self.problem.set_binding_priority(priority)

        try:
            self.problem.simulate(duration=25)
        except Exception as e:
            self.fail(f"Simulation failed when it should not have: {e}")

    def test_prioritizes_correctly(self):

        problem, toks = construct_scenario2(
            has_gold=True,
            golds=2,
            has_silver=True,
            silvers=2,
            has_bronze=True,
            bronzes=2,
        )

        bindings = problem.bindings()
        selected_binding = self.ideal_priority(bindings)
        selected_token = selected_binding[0][0][1]
        self.assertEqual(selected_token.value.type, "gold")

        problem, toks = construct_scenario2(
            has_gold=False,
            golds=2,
            has_silver=True,
            silvers=2,
            has_bronze=True,
            bronzes=2,
        )

        bindings = problem.bindings()
        selected_binding = self.ideal_priority(bindings)
        selected_token = selected_binding[0][0][1]
        self.assertEqual(selected_token.value.type, "silver")

        problem, toks = construct_scenario2(
            has_gold=False,
            golds=2,
            has_silver=False,
            silvers=2,
            has_bronze=True,
            bronzes=2,
        )

        bindings = problem.bindings()
        selected_binding = self.ideal_priority(bindings)
        selected_token = selected_binding[0][0][1]
        self.assertEqual(selected_token.value.type, "bronze")

    def test_handles_ties_randomly(self):
        problem, toks = construct_scenario2(
            has_gold=True,
            golds=5,
        )
        seen = set()

        bindings = problem.bindings()
        for _ in range(25):
            selected_binding = self.ideal_priority(bindings)
            seen.add(selected_binding[0][0][1].value.id)

        self.assertGreaterEqual(len(seen), 2, "Ties not handled randomly.")

    def test_place_priority(self):

        problem, toks = construct_scenario(
            has_gold=True,
            golds=2,
            has_silver=True,
            silvers=2,
            has_bronze=True,
            bronzes=2,
            priority=self.ideal_priority.find_priority,
        )

        start = problem.var("start")
        marking = start.marking
        self.assertEqual(marking[0].value.type, "gold")

        problem, toks = construct_scenario(
            has_gold=False,
            golds=2,
            has_silver=True,
            silvers=2,
            has_bronze=True,
            bronzes=2,
            priority=self.ideal_priority.find_priority,
        )

        start = problem.var("start")
        marking = start.marking
        self.assertEqual(marking[0].value.type, "silver")

        problem, toks = construct_scenario(
            has_gold=False,
            golds=2,
            has_silver=False,
            silvers=2,
            has_bronze=True,
            bronzes=2,
            priority=self.ideal_priority.find_priority,
        )

        start = problem.var("start")
        marking = start.marking
        self.assertEqual(marking[0].value.type, "bronze")

    def test_visualisation_works(self):
        from tests.utils import run_visualisation_for

        self.problem.simulate(duration=100)

        try:
            run_visualisation_for(duration=1500, sim_problem=self.problem)
        except Exception as e:
            self.fail(f"Visualisation failed when it should not have: {e}")


class TestWeightedFirstClassPriority(unittest.TestCase):

    def setUp(self):
        self.problem = create_dummy_bpmn(structured=True)
        self.ideal_priority = WeightedFirstClassPriority(
            class_attr="type",
            weights={"gold": 5, "silver": 2.5, "bronze": 0.5},
        )
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_sim_works_without_attribute(self):

        priority = WeightedFirstClassPriority(class_attr="foobar", weights={})
        self.problem.set_binding_priority(priority)

        try:
            self.problem.simulate(duration=25)
        except Exception as e:
            self.fail(f"Simulation failed when it should not have: {e}")

    def test_sim_works_with_attribute(self):
        self.problem.set_binding_priority(self.ideal_priority)

        try:
            self.problem.simulate(duration=25)
        except Exception as e:
            self.fail(f"Simulation failed when it should not have: {e}")

    def test_prioritizes_correctly(self):
        problem, toks = construct_scenario2(
            has_gold=True,
            golds=2,
            has_silver=True,
            silvers=2,
            has_bronze=True,
            bronzes=2,
        )

        bindings = problem.bindings()

        # on the large scale it should pick gold more often
        golds = 0
        silvers = 0
        bronzes = 0
        for _ in range(100):
            selected_binding = self.ideal_priority(bindings)
            selected_token = selected_binding[0][0][1]
            match selected_token.value.type:
                case "gold":
                    golds += 1
                case "silver":
                    silvers += 1
                case "bronze":
                    bronzes += 1
        self.assertEqual(golds + silvers + bronzes, 100)
        self.assertGreater(golds, max(silvers, bronzes))

        problem, toks = construct_scenario2(
            has_gold=False,
            golds=2,
            has_silver=True,
            silvers=2,
            has_bronze=True,
            bronzes=2,
        )

        bindings = problem.bindings()

        # on the large scale it should pick silvers more often
        golds = 0
        silvers = 0
        bronzes = 0
        for _ in range(100):
            selected_binding = self.ideal_priority(bindings)
            selected_token = selected_binding[0][0][1]
            match selected_token.value.type:
                case "gold":
                    golds += 1
                case "silver":
                    silvers += 1
                case "bronze":
                    bronzes += 1
        self.assertEqual(golds + silvers + bronzes, 100)
        self.assertGreater(silvers, max(bronzes, golds))

        problem, toks = construct_scenario2(
            has_gold=False,
            golds=2,
            has_silver=False,
            silvers=2,
            has_bronze=True,
            bronzes=2,
        )

        # now with only bronzes it should always pick bronze
        bindings = problem.bindings()
        selected_binding = self.ideal_priority(bindings)
        selected_token = selected_binding[0][0][1]
        self.assertEqual(selected_token.value.type, "bronze")

    def test_handles_ties_randomly(self):
        problem, toks = construct_scenario2(
            has_gold=True,
            golds=5,
        )
        seen = set()

        bindings = problem.bindings()
        for _ in range(25):
            selected_binding = self.ideal_priority(bindings)
            seen.add(selected_binding[0][0][1].value.id)

        self.assertGreaterEqual(len(seen), 2, "Ties not handled randomly.")

    def test_place_priority(self):
        problem, toks = construct_scenario(
            has_gold=True,
            golds=2,
            has_silver=True,
            silvers=2,
            has_bronze=True,
            bronzes=2,
            priority=self.ideal_priority.find_priority,
        )

        start = problem.var("start")

        marking = start.marking
        self.assertEqual(marking[0].value.type, "gold")

        problem, toks = construct_scenario(
            has_gold=False,
            has_silver=True,
            silvers=2,
            has_bronze=True,
            bronzes=2,
            priority=self.ideal_priority.find_priority,
        )

        start = problem.var("start")

        marking = start.marking
        self.assertEqual(marking[0].value.type, "silver")

        problem, toks = construct_scenario(
            has_gold=False,
            has_silver=False,
            has_bronze=True,
            bronzes=2,
            priority=self.ideal_priority.find_priority,
        )

        start = problem.var("start")

        marking = start.marking
        self.assertEqual(marking[0].value.type, "bronze")

    def test_visualisation_works(self):
        from tests.utils import run_visualisation_for

        self.problem.simulate(duration=100)

        try:
            run_visualisation_for(duration=1500, sim_problem=self.problem)
        except Exception as e:
            self.fail(f"Visualisation failed when it should not have: {e}")
