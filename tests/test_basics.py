import unittest
from simpn.simulator import SimProblem, SimToken


class TestBasics(unittest.TestCase):
    def test_add_svar(self):
        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        b = test_problem.add_svar("b")
        self.assertEqual(len(test_problem.places), 2, "added 2 places")
        self.assertIn(a, test_problem.places, "a is in places")
        self.assertEqual(test_problem.id2node["a"], a, "a is stored by name")

    def test_put(self):
        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        b = test_problem.add_svar("b")
        a.put(1)
        a.put(1, 1)
        a.put("a")
        a.put("a")
        b.put(1)

        self.assertEqual(len(a.marking), 3, "added 3 token types to a")
        self.assertEqual(a.marking[SimToken(1, 1)], 1, "added 1 token with value 1 at time 1 to a")
        self.assertEqual(a.marking[SimToken(1, 0)], 1, "added 1 token with value 1 at time 0 to a")
        self.assertEqual(a.marking[SimToken("a", 0)], 2, "added 1 token with value a at time 0 to a")
        self.assertEqual(len(b.marking), 1, "added 1 token types to b")

    def test_add_stransition(self):
        def test_behavior(d, e):
            return [1]

        def test_constraint(d, e):
            return True

        def test_delay(d, e):
            return [0]

        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        b = test_problem.add_svar("b")
        c = test_problem.add_svar("c")
        ta = test_problem.add_stransition([a, b], [c], test_behavior, constraint=test_constraint, delay=[0])
        tb = test_problem.add_stransition([a, b], [c], lambda d, e: 1, name="tb", constraint=test_constraint, delay=test_delay)

        self.assertEqual(len(test_problem.transitions), 2, "added 2 transitions")
        self.assertIn(ta, test_problem.transitions, "test_behavior is in transitions")
        self.assertEqual(test_problem.id2node["test_behavior"], ta, "test_behavior is stored by name")
        self.assertEqual(test_problem.id2node["tb"], tb, "tb is stored by name")
        self.assertEqual(len(ta.incoming), 2, "added 2 incoming to ta")
        self.assertEqual(ta.incoming[0], a, "first incoming to ta is correct")
        self.assertEqual(ta.incoming[1], b, "second incoming to ta is correct")
        self.assertEqual(len(ta.outgoing), 1, "added 1 outgoing to ta")
        self.assertEqual(ta.outgoing[0], c, "outgoing of ta is correct")
        self.assertEqual(ta.behavior, test_behavior, "behavior of ta is correct")
        self.assertEqual(ta.guard, test_constraint, "constraint of ta is correct")
        self.assertEqual(ta.delay, [0], "delay of ta is correct")
        self.assertEqual(tb.delay, test_delay, "delay of tb is correct")

    def test_tokens_combinations_zero_to_one(self):
        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        b = test_problem.add_svar("b")
        b.put("b1")
        ta = test_problem.add_stransition([a, b], [], lambda c, d: 1, name="ta")
        self.assertEqual(test_problem.tokens_combinations(ta), [], "no token combinations")

    def test_tokens_combinations_one_to_one(self):
        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        a.put("a1")
        b = test_problem.add_svar("b")
        b.put("b1")
        ta = test_problem.add_stransition([a, b], [], lambda c, d: 1, name="ta")
        self.assertEqual(test_problem.tokens_combinations(ta), [[(a, SimToken("a1", 0)), (b, SimToken("b1", 0))]], "one token combination")

    def test_tokens_combinations_one_to_many(self):
        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        a.put("a1")
        b = test_problem.add_svar("b")
        b.put("b1")
        b.put("b2")
        ta = test_problem.add_stransition([a, b], [], lambda c, d: 1, name="ta")
        self.assertEqual(test_problem.tokens_combinations(ta), [[(a, SimToken("a1", 0)), (b, SimToken("b1", 0))], [(a, SimToken("a1", 0)), (b, SimToken("b2", 0))]], "correct token combinations")

    def test_tokens_combinations_many_to_many(self):
        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        a.put("a1")
        a.put("a2")
        b = test_problem.add_svar("b")
        b.put("b1")
        b.put("b2")
        ta = test_problem.add_stransition([a, b], [], lambda c, d: 1, name="ta")
        self.assertEqual(test_problem.tokens_combinations(ta), [[(a, SimToken("a1", 0)), (b, SimToken("b1", 0))], [(a, SimToken("a2", 0)), (b, SimToken("b1", 0))], [(a, SimToken("a1", 0)), (b, SimToken("b2", 0))], [(a, SimToken("a2", 0)), (b, SimToken("b2", 0))]], "correct token combinations")

    def test_transition_bindings_guard(self):
        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        a.put("a1")
        a.put("a2")
        b = test_problem.add_svar("b")
        b.put("a1")
        b.put("a2")
        ta = test_problem.add_stransition([a, b], [], lambda c, d: 1, name="ta", constraint=lambda c, d: c == d)
        self.assertEqual(test_problem.bindings(), [([(a, SimToken("a1", 0)), (b, SimToken("a1", 0))], 0, ta),  ([(a, SimToken("a2", 0)), (b, SimToken("a2", 0))], 0, ta)], "correct token combinations")

    def test_bindings_timing(self):
        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        a.put("a1", 2)
        a.put("a2", 1)
        b = test_problem.add_svar("b")
        b.put("b1", 0)
        b.put("b2", 1)
        ta = test_problem.add_stransition([a, b], [], lambda c, d: 1, name="ta")
        self.assertEqual(test_problem.bindings(), [([(a, SimToken("a2", 1)), (b, SimToken("b1", 0))], 1, ta),  ([(a, SimToken("a2", 1)), (b, SimToken("b2", 1))], 1, ta)], "correct token combinations")

    def test_fire_result(self):
        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        a.put(1, 1)
        b = test_problem.add_svar("b")
        b.put(2, 1)
        e = test_problem.add_svar("e")
        ta = test_problem.add_stransition([a, b], [e], lambda c, d: [c + d], name="ta")
        self.assertEqual(test_problem.bindings(), [([(a, SimToken(1, 1)), (b, SimToken(2, 1))], 1, ta)], "correct token combinations")
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(len(a.marking), 0, "fire consumes tokens")
        self.assertEqual(len(b.marking), 0, "fire consumes tokens")
        self.assertEqual(e.marking[SimToken(3, 1)], 1, "fire produces token")

    def test_fire_delay_function(self):
        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        a.put(1, 1)
        b = test_problem.add_svar("b")
        b.put(2, 1)
        e = test_problem.add_svar("e")
        ta = test_problem.add_stransition([a, b], [e], lambda c, d: [c + d], name="ta", delay=lambda c, d: [1])
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(e.marking[SimToken(3, 2)], 1, "fire produces token with delay")

    def test_fire_delay_list(self):
        test_problem = SimProblem()
        a = test_problem.add_svar("a")
        a.put(1, 1)
        b = test_problem.add_svar("b")
        b.put(2, 1)
        e = test_problem.add_svar("e")
        ta = test_problem.add_stransition([a, b], [e], lambda c, d: [c + d], name="ta", delay=lambda c, d: [2])
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(e.marking[SimToken(3, 3)], 1, "fire produces token with delay")


if __name__ == '__main__':
    unittest.main()
