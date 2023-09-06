import unittest
from simpn.simulator import SimProblem, SimToken


class TestBasics(unittest.TestCase):
    def test_add_svar(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        b = test_problem.add_var("b")
        self.assertEqual(len(test_problem.places), 2, "added 2 places")
        self.assertIn(a, test_problem.places, "a is in places")
        self.assertEqual(test_problem.id2node["a"], a, "a is stored by name")

    def test_put(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        b = test_problem.add_var("b")
        a.put(1)
        a.put(1, 1)
        a.put("a")
        a.put("a")
        b.put(1)

        self.assertEqual(len(a.marking_count), 3, "added 3 token types to a")
        self.assertEqual(len(a.marking_order), 3, "added 3 token types to a")
        self.assertEqual(a.marking_order[2], SimToken(1, 1), "last token is 1@1")
        self.assertEqual(a.marking_count[SimToken(1, 1)], 1, "added 1 token with value 1 at time 1 to a")
        self.assertEqual(a.marking_count[SimToken(1, 0)], 1, "added 1 token with value 1 at time 0 to a")
        self.assertEqual(a.marking_count[SimToken("a", 0)], 2, "added 1 token with value a at time 0 to a")
        self.assertEqual(len(b.marking_count), 1, "added 1 token types to b")
        self.assertEqual(len(b.marking_order), 1, "added 1 token types to b")
        self.assertEqual(b.marking_order[0], SimToken(1), "token is 1@0")

    def test_remove(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1)
        a.put(1, 1)
        a.put(1, 2)
        a.put("a")
        a.put("a")
        a.put("a", 1)
        a.remove_token(SimToken(1, 1))
        a.remove_token(SimToken("a"))

        self.assertEqual(len(a.marking_count), 4, "4 token types left on a")
        self.assertEqual(len(a.marking_order), 4, "4 token types left on a")
        self.assertEqual(a.marking_order[3], SimToken(1, 2), "last token is 1@2")
        self.assertEqual(a.marking_order[2], SimToken("a", 1), "before-last token is a@1")
        self.assertEqual(a.marking_count[SimToken(1, 0)], 1, "1 token with value 1 at time 0")
        self.assertEqual(a.marking_count[SimToken(1, 2)], 1, "1 token with value 1 at time 2")
        self.assertEqual(a.marking_count[SimToken("a", 0)], 1, "1 token with value a at time 0")
        self.assertEqual(a.marking_count[SimToken("a", 1)], 1, "1 token with value a at time 1")

    def test_add_stransition(self):
        def test_behavior(d, e):
            return [SimToken(1, 0)]

        def test_constraint(d, e):
            return True

        test_problem = SimProblem()
        a = test_problem.add_var("a")
        b = test_problem.add_var("b")
        c = test_problem.add_var("c")
        ta = test_problem.add_event([a, b], [c], test_behavior, guard=test_constraint)
        tb = test_problem.add_event([a, b], [c], lambda d, e: [SimToken(1, 0)], name="tb", guard=test_constraint)

        self.assertEqual(len(test_problem.events), 2, "added 2 transitions")
        self.assertIn(ta, test_problem.events, "test_behavior is in transitions")
        self.assertEqual(test_problem.id2node["test_behavior"], ta, "test_behavior is stored by name")
        self.assertEqual(test_problem.id2node["tb"], tb, "tb is stored by name")
        self.assertEqual(len(ta.incoming), 2, "added 2 incoming to ta")
        self.assertEqual(ta.incoming[0], a, "first incoming to ta is correct")
        self.assertEqual(ta.incoming[1], b, "second incoming to ta is correct")
        self.assertEqual(len(ta.outgoing), 1, "added 1 outgoing to ta")
        self.assertEqual(ta.outgoing[0], c, "outgoing of ta is correct")
        self.assertEqual(ta.behavior, test_behavior, "behavior of ta is correct")
        self.assertEqual(ta.guard, test_constraint, "constraint of ta is correct")

    def test_tokens_combinations_zero_to_one(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        b = test_problem.add_var("b")
        b.put("b1")
        ta = test_problem.add_event([a, b], [], lambda c, d: 1, name="ta")
        self.assertEqual(test_problem.tokens_combinations(ta), [], "no token combinations")

    def test_tokens_combinations_one_to_one(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1")
        b = test_problem.add_var("b")
        b.put("b1")
        ta = test_problem.add_event([a, b], [], lambda c, d: 1, name="ta")
        self.assertEqual(test_problem.tokens_combinations(ta), [[(a, SimToken("a1", 0)), (b, SimToken("b1", 0))]], "one token combination")

    def test_tokens_combinations_one_to_many(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1")
        b = test_problem.add_var("b")
        b.put("b1")
        b.put("b2")
        ta = test_problem.add_event([a, b], [], lambda c, d: 1, name="ta")
        self.assertEqual(test_problem.tokens_combinations(ta), [[(a, SimToken("a1", 0)), (b, SimToken("b1", 0))], [(a, SimToken("a1", 0)), (b, SimToken("b2", 0))]], "correct token combinations")

    def test_tokens_combinations_many_to_many(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1")
        a.put("a2")
        b = test_problem.add_var("b")
        b.put("b1")
        b.put("b2")
        ta = test_problem.add_event([a, b], [], lambda c, d: 1, name="ta")
        self.assertEqual(test_problem.tokens_combinations(ta), [[(a, SimToken("a1", 0)), (b, SimToken("b1", 0))], [(a, SimToken("a2", 0)), (b, SimToken("b1", 0))], [(a, SimToken("a1", 0)), (b, SimToken("b2", 0))], [(a, SimToken("a2", 0)), (b, SimToken("b2", 0))]], "correct token combinations")

    def test_transition_bindings_guard(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1")
        a.put("a2")
        b = test_problem.add_var("b")
        b.put("a1")
        b.put("a2")
        ta = test_problem.add_event([a, b], [], lambda c, d: 1, name="ta", guard=lambda c, d: c == d)
        self.assertEqual(test_problem.bindings(), [([(a, SimToken("a1", 0)), (b, SimToken("a1", 0))], 0, ta),  ([(a, SimToken("a2", 0)), (b, SimToken("a2", 0))], 0, ta)], "correct token combinations")

    def test_bindings_timing(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1", 2)
        a.put("a2", 1)
        b = test_problem.add_var("b")
        b.put("b1", 0)
        b.put("b2", 1)
        ta = test_problem.add_event([a, b], [], lambda c, d: [], name="ta")
        self.assertEqual(test_problem.bindings(), [([(a, SimToken("a2", 1)), (b, SimToken("b1", 0))], 1, ta),  ([(a, SimToken("a2", 1)), (b, SimToken("b2", 1))], 1, ta)], "correct token combinations")

    def test_fire_result(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1, 1)
        b = test_problem.add_var("b")
        b.put(2, 1)
        e = test_problem.add_var("e")
        ta = test_problem.add_event([a, b], [e], lambda c, d: [SimToken(c + d)], name="ta")
        self.assertEqual(test_problem.bindings(), [([(a, SimToken(1, 1)), (b, SimToken(2, 1))], 1, ta)], "correct token combinations")
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(len(a.marking_count), 0, "fire consumes tokens")
        self.assertEqual(len(b.marking_count), 0, "fire consumes tokens")
        self.assertEqual(e.marking_count[SimToken(3, 1)], 1, "fire produces token")

    def test_fire_delay_function(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1, 1)
        b = test_problem.add_var("b")
        b.put(2, 1)
        e = test_problem.add_var("e")
        test_problem.add_event([a, b], [e], lambda c, d: [SimToken(c + d, 1)], name="ta")
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(e.marking_count[SimToken(3, 2)], 1, "fire produces token with delay")

    def test_fire_delay_list(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1, 1)
        b = test_problem.add_var("b")
        b.put(2, 1)
        e = test_problem.add_var("e")
        test_problem.add_event([a, b], [e], lambda c, d: [SimToken(c + d, 2)], name="ta")
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(e.marking_count[SimToken(3, 3)], 1, "fire produces token with delay")

    def test_binding_order(self):
        test_problem = SimProblem()
        test_problem.clock = 4
        a = test_problem.add_var("a")
        a.put("b", 3)
        a.put("d", 1)
        a.put("c", 2)
        a.put("a", 4)
        b = test_problem.add_var("b")
        b.put("b", 3)
        b.put("a", 4)
        b.put("d", 1)
        b.put("c", 2)
        test_problem.add_event([a, b], [], lambda c, d: [], name="ta")
        test_problem.clock = 4
        bindings = test_problem.bindings()
        # for two tokens that have the same time for place b, the first token on a must always have time <= the second token
        # for two tokens that have the same time for place a, the first token on b must always have time <= the second token
        for time in range(1, 5):
            for i in range(len(bindings)):
                for j in range(i+1, len(bindings)):
                    if bindings[i][0][1][1].time == time and bindings[j][0][1][1].time == time:
                        self.assertLessEqual(bindings[i][0][0][1].time, bindings[j][0][0][1].time, "two bindings with index i, j, i < j, with the same time for b, must have binding[i] time for a <=  binding[j] time for a")
                    if bindings[i][0][0][1].time == time and bindings[j][0][0][1].time == time:
                        self.assertLessEqual(bindings[i][0][1][1].time, bindings[j][0][1][1].time, "two bindings with index i, j, i < j, with the same time for a, must have binding[i] time for b <=  binding[j] time for b")


class TestSimVarCounter(unittest.TestCase):

    def test_simvarcounter_simple(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1)
        b = test_problem.add_var("b")
        c = test_problem.add_var("c")
        ta = test_problem.add_event([a], [a, b, c], lambda x: [SimToken(x), SimToken(x), SimToken(x, 1)], name="ta")
        self.assertEqual(len(test_problem.bindings()), 1, "one binding")
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(len(test_problem.bindings()), 1, "one binding")
        test_problem.fire(test_problem.bindings()[0])
        self.assertTrue(len(a.marking_count) == 1 and a.marking_count[SimToken(1)] == 1, "two fires leave one token 1@0 in a")
        self.assertTrue(len(b.marking_count) == 1 and b.marking_count[SimToken(1)] == 2, "two fires produce two tokens 1@0 in b")
        self.assertTrue(len(c.marking_count) == 1 and c.marking_count[SimToken(1, 1)] == 2, "two fires produce two tokens 1@1 in c")

        a_counter = test_problem.var("a.count")
        self.assertTrue(len(a_counter.marking_count) == 1 and a_counter.marking_count[SimToken(1)] == 1, "counter also reflects that there is one token in a")
        self.assertTrue(len(a_counter.marking_order) == 1 and a_counter.marking_order[0] == SimToken(1), "counter also reflects that there is one token in a")

    #TODO: do more tests for finding the counter variable
    #TODO: do more tests for the counter counting correctly (also remove tokens - check what affects the total counter in simvar)
    #TODO: optionally, split up the test above into more fine-grained tests


if __name__ == '__main__':
    unittest.main()
