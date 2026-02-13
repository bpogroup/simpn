import unittest
from simpn.simulator import SimProblem, SimToken, SimVarQueue
from simpn.reporters import Reporter, OutputReporter
import simpn.prototypes as prototype
from random import randint


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

        self.assertEqual(len(a.marking), 4, "added 4 tokens to a")
        self.assertEqual(a.marking[3], SimToken(1, 1), "last token is 1@1")
        self.assertEqual(a.marking.count(SimToken(1, 1)), 1, "added 1 token with value 1 at time 1 to a")
        self.assertEqual(a.marking.count(SimToken(1, 0)), 1, "added 1 token with value 1 at time 0 to a")
        self.assertEqual(a.marking.count(SimToken("a", 0)), 2, "added 1 token with value a at time 0 to a")
        self.assertEqual(len(b.marking), 1, "added 1 token to b")
        self.assertEqual(b.marking, [SimToken(1)], "token is 1@0")

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

        self.assertEqual(len(a.marking), 4, "4 tokens left on a")
        self.assertEqual(a.marking[3], SimToken(1, 2), "last token is 1@2")
        self.assertEqual(a.marking[2], SimToken("a", 1), "before-last token is a@1")
        self.assertEqual(a.marking.count(SimToken(1, 0)), 1, "1 token with value 1 at time 0")
        self.assertEqual(a.marking.count(SimToken(1, 2)), 1, "1 token with value 1 at time 2")
        self.assertEqual(a.marking.count(SimToken("a", 0)), 1, "1 token with value a at time 0")
        self.assertEqual(a.marking.count(SimToken("a", 1)), 1, "1 token with value a at time 1")

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

    def test_transition_exceptions(self):
        # if a transition function has an incorrect number of parameters, an exception is raised.
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        b = test_problem.add_var("b")
        with self.assertRaises(Exception):
            test_problem.add_event([a, b], [], lambda c: 1)

    def test_transition_bindings_guard(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1")
        a.put("a2")
        b = test_problem.add_var("b")
        b.put("a1")
        b.put("a2")
        ta = test_problem.add_event([a, b], [], lambda c, d: [], name="ta", guard=lambda c, d: c == d)
        self.assertEqual(test_problem.bindings(), [([(a, SimToken("a1", 0)), (b, SimToken("a1", 0))], 0, ta)], "correct token combinations")

    def test_bindings_timing(self):
        # starting at time 0, with four possible token combinations a1, b1; a1, b2; a2, b1; a2, b2
        # no token combination is possible at time 0, because neither a1 nor a2 is available at time 0
        # the earliest possible time is 1, this should then become the enabling time of the transition
        # at time 1, only a2 is available, so only the combinations a2, b1 and a2, b2 are possible
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1", 2)
        a.put("a2", 1)
        b = test_problem.add_var("b")
        b.put("b1", 0)
        b.put("b2", 1)
        ta = test_problem.add_event([a, b], [], lambda c, d: [], name="ta")
        self.assertEqual(test_problem.bindings(), [([(a, SimToken("a2", 1)), (b, SimToken("b1", 0))], 1, ta)], "correct token combinations")

    def test_bindings_timing_complex(self):
        # just for completeness, a more complex example with 3 places
        # earliest time is 5 because of c1, at this time there are four possible combinations: a1, b1, c1; a1, b2, c1; a2, b1, c1; a2, b2, c1
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1", 1)
        a.put("a2", 2)
        b = test_problem.add_var("b")
        b.put("b2", 4)
        b.put("b1", 3)
        c = test_problem.add_var("c")
        c.put("c1", 5)
        c.put("c2", 6)
        ta = test_problem.add_event([a, b, c], [], lambda d, e, f: [], name="ta")            
        self.assertEqual(test_problem.bindings(), [([(a, SimToken("a1", 1)), (b, SimToken("b1", 3)), (c, SimToken("c1", 5))], 5, ta)])
        
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
        self.assertEqual(len(a.marking), 0, "fire consumes tokens")
        self.assertEqual(len(b.marking), 0, "fire consumes tokens")
        self.assertEqual(e.marking.count(SimToken(3, 1)), 1, "fire produces token")

    def test_fire_delay_function(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1, 1)
        b = test_problem.add_var("b")
        b.put(2, 1)
        e = test_problem.add_var("e")
        test_problem.add_event([a, b], [e], lambda c, d: [SimToken(c + d, delay=1)], name="ta")
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(e.marking.count(SimToken(3, 2)), 1, "fire produces token with delay")

    def test_fire_delay_list(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1, 1)
        b = test_problem.add_var("b")
        b.put(2, 1)
        e = test_problem.add_var("e")
        test_problem.add_event([a, b], [e], lambda c, d: [SimToken(c + d, delay=2)], name="ta")
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(e.marking.count(SimToken(3, 3)), 1, "fire produces token with delay")

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

    def test_binding_time_earlier_token(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1", 3)
        a.put("a2", 2)
        test_problem.add_event([a], [], lambda _: [], name="ta")
        test_problem.clock = 4
        bindings = test_problem.bindings()
        for binding in bindings:
            self.assertEqual(binding[1], test_problem.clock, "the enabling time of a binding must be equal to the current clock time")
        # the binding time must be at the current clock, because things cannot happen in the past
        self.assertEqual(bindings[0][1], test_problem.clock, "the enabling time of a binding must be equal to the current clock time")
        test_problem.fire(bindings[0])
        self.assertEqual(test_problem.clock, 4, "firing a binding does not change the clock time")

    def test_binding_time_later_token(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1", 5)
        a.put("a2", 6)
        test_problem.add_event([a], [], lambda _: [], name="ta")
        test_problem.clock = 4
        bindings = test_problem.bindings()
        self.assertEqual(len(bindings), 1, "only one binding is possible, which is the one that happens at soon as possible after the current time")
        self.assertEqual(test_problem.clock, 5, "since a binding can only be enabled if the clock time changes, the clock time is now 5")
        self.assertEqual(bindings[0][1], test_problem.clock, "the enabling time of a binding must be equal to the current clock time")

    def test_binding_time_guarded_token(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1", 3)
        a.put("a2", 2)
        self.assertEqual(a.marking[0].value, "a2", "a2 is earlier than a1")
        test_problem.add_event([a], [], lambda _: [], name="ta", guard=lambda x: x == "a1")
        test_problem.clock = 4
        bindings = test_problem.bindings()
        self.assertEqual(len(bindings), 1, "only one binding is possible, which is the one that satisfies the guard")
        # it is the binding with a1 (even though a2 is earlier), because a1 is the only one that satisfies the guard
        self.assertEqual(bindings[0][0][0][1].value, "a1", "the only binding is the one with a1")
        # the clock must still be 4
        self.assertEqual(test_problem.clock, 4, "the clock time is still 4")
        # the enabling time of the binding is 4, because a1 is available at time 3, and the clock is at time 4
        self.assertEqual(bindings[0][1], test_problem.clock, "the enabling time of a binding must be equal to the current clock time")        
        test_problem.fire(bindings[0])
        self.assertEqual(test_problem.clock, 4, "firing a binding does not change the clock time")
    
    def test_binding_time_prioritized_token(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a", priority=lambda x: int(x.value[1]))
        a.put("a1", 3)
        a.put("a2", 2)
        self.assertEqual(a.marking[0].value, "a1", "a1 has priority over a2")
        self.assertEqual(a.marking[1].value, "a2", "a1 has priority over a2")
        test_problem.add_event([a], [], lambda _: [], name="ta")
        test_problem.clock = 4
        bindings = test_problem.bindings()
        binding = test_problem.binding_priority(bindings)
        self.assertEqual(binding[0][0][1].value, "a1", "the binding with a1 has priority and must therefore be selected, even if it has a later time")
        self.assertEqual(test_problem.clock, 4, "the clock time is still 4")
        self.assertEqual(binding[1], test_problem.clock, "the enabling time of a binding must be equal to the current clock time")
        test_problem.fire(binding)
        self.assertEqual(test_problem.clock, 4, "firing a binding does not change the clock time")

    def test_binding_time_later_token_guarded(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a1", 7)
        a.put("a2", 6)
        self.assertEqual(a.marking[0].value, "a2", "a2 is earlier than a1")
        test_problem.add_event([a], [], lambda _: [], name="ta", guard=lambda x: x == "a1")
        test_problem.clock = 4
        bindings = test_problem.bindings()
        self.assertEqual(len(bindings), 1, "only one binding is possible, which is the one that satisfies the guard")
        # it is the binding with a1 (even though a2 is earlier), because a1 is the only one that satisfies the guard
        self.assertEqual(bindings[0][0][0][1].value, "a1", "the only binding is the one with a1")
        # the clock must now be 7, because a1 is only available at time 7
        self.assertEqual(test_problem.clock, 7, "the clock time is now 7")
        # the enabling time of the binding is 7, because a1 is available at time 7, and the clock is at time 7
        self.assertEqual(bindings[0][1], test_problem.clock, "the enabling time of a binding must be equal to the current clock time")
        test_problem.fire(bindings[0])
        self.assertEqual(test_problem.clock, 7, "firing a binding does not change the clock time")

    def test_binding_time_later_token_guarded_between_events(self):
        test_problem = SimProblem()

        a = test_problem.add_var("a")
        a.put("a1", 7)
        a.put("a2", 6)

        b = test_problem.add_var("b")
        b.put("b1", 7)
        b.put("b2", 3)
        b.put("b3", 6)

        self.assertEqual(
            a.marking[0].value, 
            "a2", 
            "a2 is earlier than a1"
        )
        self.assertEqual(
            b.marking[0].value, 
            "b2", 
            "b2 is the earliest"
        )
        test_problem.add_event(
            [a], [], 
            lambda _: [], 
            name="ta", guard=lambda x: x == "a1"
        )
        test_problem.add_event(
            [b], [], 
            lambda _: [], 
            name="tb", guard=lambda x: x == "b1" or x =="b2"
        )
        test_problem.clock = 4

        bindings = test_problem.bindings()
        self.assertEqual(len(bindings), 
            1, "only one binding is possible, which is the b2")
        # it is the binding with b2 as it is ealier than the clock and allowed
        # by the guard
        self.assertEqual(
            bindings[0][0][0][1].value, 
            "b2", 
            "the only binding is the one with b2"
        )
        # the clock must now be 4, because b2 before the clock
        self.assertEqual(test_problem.clock, 4, "the clock time is now 4")
        # the enabling time of the binding is 4, because b2 is available at 
        # time 3, and the clock is at time 4, thus the clock must be used
        self.assertEqual(
            bindings[0][1], 
            test_problem.clock, 
            "the enabling time of a binding must be equal to the current clock time"
        )
        test_problem.fire(bindings[0])
        self.assertEqual(
            test_problem.clock, 
            4, 
            "firing a binding does not change the clock time"
        )

        bindings = test_problem.bindings()
        self.assertEqual(len(bindings), 
            2, "two bindings are possible, one from e1 and e2 (a1, b1)")
        self.assertEqual(
            bindings[0][0][0][1].value, 
            "a1", 
            "the first binding is a1"
        )
        self.assertEqual(
            bindings[1][0][0][1].value, 
            "b1", 
            "the second binding is b1"
        )

        # the clock must now be 7, because both a1 and b1 are timed at 7
        self.assertEqual(test_problem.clock, 7, "the clock time must now be 7")
        self.assertEqual(
            bindings[0][1], 
            test_problem.clock, 
            "the enabling time of a binding must be equal to the current clock time"
        )
        self.assertEqual(
            bindings[1][1], 
            test_problem.clock, 
            "the enabling time of a binding must be equal to the current clock time"
        )
        test_problem.fire(bindings[0])
        self.assertEqual(
            test_problem.clock, 
            7, 
            "firing a binding does not change the clock time"
        )

        bindings = test_problem.bindings()
        self.assertEqual(len(bindings), 
            1, "only one binding is possible, b1")
        self.assertEqual(
            bindings[0][0][0][1].value, 
            "b1", 
            "the binding is b1"
        )
         # the clock must now be 7, because both a1 and b1 are timed at 7
        self.assertEqual(test_problem.clock, 7, "the clock time must now be 7")
        self.assertEqual(
            bindings[0][1], 
            test_problem.clock, 
            "the enabling time of a binding must be equal to the current clock time"
        )
        test_problem.fire(bindings[0])
        self.assertEqual(
            test_problem.clock, 
            7, 
            "firing a binding does not change the clock time"
        )

        bindings = test_problem.bindings()
        self.assertEqual(len(bindings), 
            0, "the problem shoud be deadlocked")


class TestSimVarQueue(unittest.TestCase):

    def test_simvarqueue_creation(self):
        # tests that a queue is created for a variable
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        self.assertIsInstance(a.queue, SimVarQueue, "counter is created")

    def test_simvarqueue_exception(self):
        # tests that a variable is not created for an id that ends with .queue
        test_problem = SimProblem()
        with self.assertRaises(Exception):
            test_problem.var("a.queue")
       
    def test_simvarqueue_add_token(self):
        # tests if putting a token is visible in the queue
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1)
        self.assertEqual(len(a.queue.marking), 1, "The queue var only has one token")
        self.assertEqual(a.queue.marking[0].value, [SimToken(1)], "The queue holds one token with value 1")

    def test_simvarqueue_add_token_2(self):
        # tests if putting an additional token is visible in the queue
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1)
        a.put(1)
        self.assertEqual(len(a.queue.marking), 1, "The queue var only has one token")
        self.assertEqual(a.queue.marking[0].value, [SimToken(1), SimToken(1)], "The queue holds one token with value 1")

    def test_simvarqueue_time(self):
        # tests if putting a token changes the time of the queue
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1,1)
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")
        a.put(1,2)
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")
        a.put(1,1)
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")

    def test_simvarqueue_add_token_function(self):
        # tests if the add_token function works
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.add_token(SimToken(1,1))
        self.assertEqual(a.queue.marking[0].value, [SimToken(1,1)], "Tokens are put in the queue in the correct order")
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")
        a.add_token(SimToken(1,2))
        self.assertEqual(a.queue.marking[0].value, [SimToken(1,1), SimToken(1,2)], "Tokens are put in the queue in the correct order")
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")
        a.add_token(SimToken(1,1))
        self.assertEqual(a.queue.marking[0].value, [SimToken(1,1), SimToken(1,1), SimToken(1,2)], "Tokens are put in the queue in the correct order")
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")

    def test_simvarqueue_remove_token_function(self):
        # tests if the remove_token function works
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.add_token(SimToken(1,1))
        a.add_token(SimToken(1,2))
        a.add_token(SimToken(1,1))
        a.remove_token(SimToken(1,1))
        self.assertEqual(a.queue.marking[0].value, [SimToken(1,1), SimToken(1,2)], "Tokens are put in the queue in the correct order")
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")
        a.remove_token(SimToken(1,2))
        self.assertEqual(a.queue.marking[0].value, [SimToken(1,1)], "Tokens are put in the queue in the correct order")
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")

    def test_simvarqueue_add_remove_through_firing(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        to_add = test_problem.add_var("to_add")
        to_remove = test_problem.add_var("to_remove")        
        test_problem.add_event([to_add], [a], lambda x: [SimToken(x)], name="add")
        test_problem.add_event([to_remove, a], [], lambda x, y: [], name="remove", guard = lambda x, y: x == y)

        to_add.put(1, 1)
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(a.queue.marking[0].value, [SimToken(1,1)], "Tokens are put in the queue in the correct order")
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")

        to_add.put(2, 2)
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(a.queue.marking[0].value, [SimToken(1,1), SimToken(2,2)], "Tokens are put in the queue in the correct order")
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")

        to_add.put(2, 2)
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(a.queue.marking[0].value, [SimToken(1,1), SimToken(2,2), SimToken(2,2)], "Tokens are put in the queue in the correct order")
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")

        to_remove.put(1)
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(a.queue.marking[0].value, [SimToken(2,2), SimToken(2,2)], "Tokens are put in the queue in the correct order")
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")

        to_remove.put(2)
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(a.queue.marking[0].value, [SimToken(2,2)], "Tokens are put in the queue in the correct order")
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")

        to_remove.put(2)
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(a.queue.marking[0].value, [], "Tokens are put in the queue in the correct order")
        self.assertEqual(a.queue.marking[0].time, 0, "Time is always 0")

    def test_simvarqueue_can_get_from_queue(self):
        # tests if we can get an item from the queue
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1,1)
        a.put(2,2)

        result = test_problem.add_var("result")

        # a queue manipulation event gets a queue.
        # the first token in the queue is put in the result variable.
        # Note that we should only put the value of the token back, not the time, because that will be interpreted as a delay.
        test_problem.add_event([a.queue], [result], name="get_queue", behavior=lambda q: [SimToken(q[0].value)])
        test_problem.fire(test_problem.bindings()[0])
        # the transition fires at the time of the queue, which is 0
        self.assertEqual(result.marking, [SimToken(1,0)], "Token value is obtained from the queue.")

    def test_simvarqueue_can_put_queue_back(self):
        # tests if we can get an item from the queue
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1,1)
        a.put(2,2)
        a.put(2,3)

        test_problem.add_event([a.queue], [a.queue], name="put_queue", behavior=lambda q: [q[1:]])
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(a.marking, [SimToken(2,2), SimToken(2,3)], "The manipulated queue is put back.")

    def test_simvarqueue_can_put_guard_on_queue(self):
        # tests if we can get an item from the queue
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1,1)
        a.put(2,2)
        a.put(2,3)

        test_problem.add_event([a.queue], [a.queue], name="put_queue", behavior=lambda q: [[]], guard=lambda q: len(q) > 0)
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(a.marking, [], "The manipulated queue is put back.")
        self.assertEqual(len(test_problem.bindings()), 0, "An empty queue does not fire.")


class TestTimeVariable(unittest.TestCase):

    def test_available(self):
        test_problem = SimProblem()

        time_var = test_problem.var("time")

        self.assertEqual(time_var.marking, [SimToken(0)], "There is one token with value 0")

    def test_updating(self):
        # tests if firing updates the time
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(1, 2)
        test_problem.add_event([a], [], lambda x: [], name="ta")
        test_problem.fire(test_problem.bindings()[0])

        time_var = test_problem.var("time")

        self.assertEqual(time_var.marking, [SimToken(2)], "There is one token with value 2")
    
    def test_time_at_firing(self):
        # tests if the time variable reflects the time at which a transition fires        
        test_problem = SimProblem()
        time_var = test_problem.var("time")
        a = test_problem.add_var("a")
        a.put(1, 2)
        e = test_problem.add_var("e")
        def f(x, t):
            print()
            print(test_problem.clock)
            print()
            return [SimToken(t)]
        test_problem.add_event([a, time_var], [e], f, name="ta")
        binding = test_problem.bindings()[0]
        test_problem.fire(binding)

        self.assertEqual(e.marking[0].value, 2, "The transition fired at time 2, so the time variable had value 2 at the moment of firing.")


class TestPriorities(unittest.TestCase):

    def test_basic_time_driven_prio(self):
        # this is a version of the test_bindings_timing test, but just double checking that the priority function returns the correct binding.
        # we have one place a with time-driven priority (lowest time first) with tokens with times 1, 2, 3, ... (in the place in random order)
        # and one place b without priority (random) with times 3, 6, 9 (in the place in random order)
        # current time is 0, so earliest possible time is 3
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a7", 7); a.put("a2", 2); a.put("a9", 9); a.put("a4", 4); a.put("a1", 1); a.put("a6", 6); a.put("a3", 3); a.put("a8", 8); a.put("a5", 5)
        b = test_problem.add_var("b") # the default queue priority is time-driven, lowest time first
        b.put("b9", 9)
        b.put("b6", 6)
        b.put("b3", 3)
        ta = test_problem.add_event([a, b], [], lambda c, d: [], name="ta")
        # on a single queue, the tokens are always in time order
        self.assertEqual(test_problem.bindings(), 
                         [([(a, SimToken("a1", 1)), (b, SimToken("b3", 3))], 3, ta)],
                         "correct token combinations")
        
        # if the SimProblem is set to use priority-based binding, the first binding must be the one with the lowest time
        test_problem.binding_priority = SimProblem.PRIORITY_QUEUE_BINDING
        binding = test_problem.binding_priority(test_problem.bindings())
        self.assertEqual(binding, ([(a, SimToken("a1", 1)), (b, SimToken("b3", 3))], 3, ta), "the binding must be fired for the first item in the queue, which is a1")

    def test_basic_time_driven_prio_multiple_transitions(self):
        # if there are two queues, by default tokens within a single queue are always in time order
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put("a7", 7); a.put("a2", 2); a.put("a9", 9); a.put("a4", 4); a.put("a1", 1); a.put("a6", 6); a.put("a3", 3); a.put("a8", 8); a.put("a5", 5)
        b = test_problem.add_var("b") # the default queue priority is time-driven, lowest time first
        b.put("b9", 9); b.put("b6", 6); b.put("b3", 3)
        ta = test_problem.add_event([a, b], [], lambda c, d: [], name="ta")
        c = test_problem.add_var("c")
        c.put("c7", 7); c.put("c2", 2); c.put("c9", 9); c.put("c4", 4); c.put("c1", 1); c.put("c6", 6); c.put("c3", 3); c.put("c8", 8); c.put("c5", 5)
        d = test_problem.add_var("d") # the default queue priority is time-driven, lowest time first
        d.put("d9", 9); d.put("d6", 6); d.put("d3", 3)
        tb = test_problem.add_event([c, d], [], lambda e, f: [], name="tb")

        # on a single queue, the tokens are always in time order
        self.assertEqual([(binding_vals, binding_time, binding_event) for (binding_vals, binding_time, binding_event) in test_problem.bindings() if binding_event == ta], 
                         [([(a, SimToken("a1", 1)), (b, SimToken("b3", 3))], 3, ta)                         ],
                         "correct token combinations on ta")
        self.assertEqual([(binding_vals, binding_time, binding_event) for (binding_vals, binding_time, binding_event) in test_problem.bindings() if binding_event == tb], 
                         [([(c, SimToken("c1", 1)), (d, SimToken("d3", 3))], 3, tb)
                          ],
                         "correct token combinations on tb")

    def test_basic_time_driven_prio_random_transition(self):
        test_problem = SimProblem(binding_priority=SimProblem.PRIORITY_QUEUE_BINDING)
        a = test_problem.add_var("a")
        a.put("a7", 7); a.put("a2", 2); a.put("a9", 9); a.put("a4", 4); a.put("a1", 1); a.put("a6", 6); a.put("a3", 3); a.put("a8", 8); a.put("a5", 5)
        b = test_problem.add_var("b") # the default queue priority is time-driven, lowest time first
        b.put("b9", 9); b.put("b6", 6); b.put("b3", 3)
        ta = test_problem.add_event([a, b], [], lambda c, d: [], name="ta")
        c = test_problem.add_var("c")
        c.put("c7", 7); c.put("c2", 2); c.put("c9", 9); c.put("c4", 4); c.put("c1", 1); c.put("c6", 6); c.put("c3", 3); c.put("c8", 8); c.put("c5", 5)
        d = test_problem.add_var("d") # the default queue priority is time-driven, lowest time first
        d.put("d9", 9); d.put("d6", 6); d.put("d3", 3)
        tb = test_problem.add_event([c, d], [], lambda e, f: [], name="tb")

        # we do this 20 times to account for randomness
        count_ta = 0
        count_tb = 0
        for _ in range(20):
            binding = test_problem.binding_priority(test_problem.bindings())
            if binding[2] == ta:
                count_ta += 1
                # the binding must be fired for the first item in the queue, which is a1
                self.assertEqual(binding[0], [(a, SimToken("a1", 1)), (b, SimToken("b3", 3))], "the binding must be fired for the first item in the queue, which is a1")
            elif binding[2] == tb:
                count_tb += 1
                # the binding must be fired for the first item in the queue, which is c1
                self.assertEqual(binding[0], [(c, SimToken("c1", 1)), (d, SimToken("d3", 3))], "the binding must be fired for the first item in the queue, which is c1")
            else:
                self.fail("binding must be for either ta or tb")
        # because of randomness, each of the two transitions should be chosen at least once
        self.assertGreater(count_ta, 0, "ta must be chosen at least once, it is possible - though unlikely - that this test fails due to randomness")
        self.assertGreater(count_tb, 0, "tb must be chosen at least once, it is possible - though unlikely - that this test fails due to randomness")

    def test_bpmn_time_driven_prio(self):
        test_problem = SimProblem()

        task1_queue = test_problem.add_var("task1_queue")
        task2_queue = test_problem.add_var("task2_queue")
        done = test_problem.add_var("done")

        resource = test_problem.add_var("resource")
        resource.put("r1")
        resource.put("r2")

        prototype.BPMNStartEvent(test_problem, [], [task1_queue], "", 1)

        prototype.BPMNTask(test_problem, [task2_queue, resource], [done, resource], "task2", lambda c, r: [SimToken((c, r), delay=1.25)])

        prototype.BPMNTask(test_problem, [task1_queue, resource], [task2_queue, resource], "task1", lambda c, r: [SimToken((c, r), delay=1.25)])

        last_completion = None
        completion_count = 0
        while test_problem.clock <= 20:
            bindings = test_problem.bindings()
            (binding, time, event) = test_problem.binding_priority(bindings)
            test_problem.fire((binding, time, event))

            # we check if the tokens in the queues always have time <= the global clock
            # this is an important assumption for the correctness of the simulation
            for token in task1_queue.marking:
                self.assertLessEqual(token.time, test_problem.clock, "tokens in the queues always have time <= the global clock")
            for token in task2_queue.marking:
                self.assertLessEqual(token.time, test_problem.clock, "tokens in the queues always have time <= the global clock")

            # we check if the jobs are completed in the order of their arrival
            #   this must be true, because they are started in the order of their arrival, and the processing time is deterministic
            if event._id == "task2<task:complete>":
                completion_count += 1
                completion = int(binding[0][1].value[0][0])
                if last_completion is not None:
                    self.assertGreaterEqual(completion, last_completion, "jobs are completed in the order of their arrival")
                last_completion = completion
            
        self.assertGreater(completion_count, 8, "there are at least 8 completions")

    def test_priority_driven_prio_before_current_time(self):
        test_problem = SimProblem()

        a = test_problem.add_var("a", priority=lambda token: -token.value)
        a.put(9, 15); a.put(10, 20); a.put(1, 5); a.put(5, 10)

        test_problem.clock = 15
        test_problem.add_event([a], [], lambda _: [], name="ta")
        bindings = test_problem.bindings()

        # because of the priority, the binding must be for the token with value 10
        self.assertEqual(len(bindings), 1, "there must be one binding")
        self.assertEqual(bindings[0][0][0][1].value, 10, "the first binding must be for the token with value 10")
        # the enabling time of the binding must be equal to the current clock time
        self.assertEqual(bindings[0][1], test_problem.clock, "the enabling time of a binding must be equal to the current clock time")
        # and the clock must be shifted to 20, because the token with value 10 is only available at time 20
        self.assertEqual(test_problem.clock, 20, "the clock time is now 20")

    def test_priority_driven_prio_between_simvars_before_current_time(self):
        test_problem = SimProblem()

        a = test_problem.add_var("a", priority=lambda token: -token.value)
        a.put(9, 15); a.put(10, 20); a.put(1, 5); a.put(5, 10)
        b = test_problem.add_var("b", priority=lambda token: token.value)
        b.put(8, 15); b.put(3, 20); b.put(4, 5); b.put(6, 10)

        test_problem.clock = 15
        test_problem.add_event([a, b], [], lambda x, y: [], name="tab")
        bindings = test_problem.bindings()
        self.assertEqual(len(bindings), 1, "there must be one binding")
        # according to priority the binding must be for the token with value 10 and 3
        self.assertEqual(bindings[0][0][0][1].value, 10, "the first binding must be for the token with value 10")
        self.assertEqual(bindings[0][0][1][1].value, 3, "the first binding must be for the token with value 3")
        # the enabling time of the binding must be equal to the current clock time
        self.assertEqual(bindings[0][1], test_problem.clock, "the enabling time of a binding must be equal to the current clock time")
        # and the clock must be shifted to 20, because the token with value 10 is only available at time 20
        self.assertEqual(test_problem.clock, 20, "the clock time is now 20")

    def test_priority_driven_prio_after_current_time(self):
        test_problem = SimProblem()

        a = test_problem.add_var("a", priority=lambda token: -token.value)
        a.put(9, 25); a.put(10, 20); a.put(1, 35); a.put(5, 30)

        test_problem.clock = 15
        test_problem.add_event([a], [], lambda _: [], name="ta")
        bindings = test_problem.bindings()

        # according to priority and the current time, only the token with value 10 is available
        self.assertEqual(len(bindings), 1, "there must be one binding")
        self.assertEqual(bindings[0][0][0][1].value, 10, "the first binding must be for the token with value 10")

    def test_time_driven_prio_with_two_simevents_before_current_time(self):
        test_problem = SimProblem()

        a = test_problem.add_var("a")
        a.put(9, 15); a.put(10, 20); a.put(1, 5); a.put(5, 10)
        b = test_problem.add_var("b")
        b.put(8, 15); b.put(3, 20); b.put(4, 5); b.put(6, 10)

        test_problem.clock = 15
        test_problem.add_event([a], [], lambda x: [], name="ta")
        test_problem.add_event([b], [], lambda x: [], name="tb")
        bindings = test_problem.bindings()
        self.assertEqual(len(bindings), 2, "there must be two bindings")
        # according to priority the binding must be for the token with value 1 and 8
        self.assertEqual(bindings[0][0][0][1].value, 1, "the first binding must be for the token with value 1")
        self.assertEqual(bindings[1][0][0][1].value, 4, "the second binding must be for the token with value 8")
        # the enabling time of the bindings must be equal to the current clock time
        self.assertEqual(bindings[0][1], test_problem.clock, "the enabling time of a binding must be equal to the current clock time")
        self.assertEqual(bindings[1][1], test_problem.clock, "the enabling time of a binding must be equal to the current clock time")

    def test_time_driven_prio_with_two_simevents_one_after_current_time(self):
        test_problem = SimProblem()

        a = test_problem.add_var("a")
        a.put(9, 25); a.put(10, 20); a.put(1, 30); a.put(5, 35)
        b = test_problem.add_var("b")
        b.put(8, 25); b.put(3, 20); b.put(4, 5); b.put(6, 10)

        test_problem.clock = 15
        test_problem.add_event([a], [], lambda x: [], name="ta")
        test_problem.add_event([b], [], lambda x: [], name="tb")
        bindings = test_problem.bindings()
        self.assertEqual(len(bindings), 1, "there must be one binding")
        # according to priority the binding must be for the token with value 4
        self.assertEqual(bindings[0][0][0][1].value, 4, "the first binding must be for the token with value 4")
        # the enabling time of the bindings must be equal to the current clock time
        self.assertEqual(bindings[0][1], test_problem.clock, "the enabling time of a binding must be equal to the current clock time")

    def test_time_driven_prio_with_two_simevents_after_current_time(self):
        test_problem = SimProblem()

        a = test_problem.add_var("a")
        a.put(9, 25); a.put(10, 20); a.put(1, 30); a.put(5, 35)
        b = test_problem.add_var("b")
        b.put(8, 25); b.put(3, 20); b.put(4, 30); b.put(6, 35)

        test_problem.clock = 15
        test_problem.add_event([a], [], lambda x: [], name="ta")
        test_problem.add_event([b], [], lambda x: [], name="tb")
        bindings = test_problem.bindings()
        self.assertEqual(len(bindings), 2, "there must be two bindings")
        # according to priority the binding must be for the token with value 10 and 3
        # there is no order between these bindings, so either the first is 10 and the second 3, or vice versa
        self.assertIn(bindings[0][0][0][1].value, [10, 3], "the first binding must be for the token with value 10 or 3")
        self.assertIn(bindings[1][0][0][1].value, [10, 3], "the second binding must be for the token with value 10 or 3")
        # the enabling time of the bindings must be equal to the time of the tokens
        self.assertEqual(bindings[0][1], 20, "the enabling time of a binding must be equal to the time of the token")
        self.assertEqual(bindings[1][1], 20, "the enabling time of a binding must be equal to the time of the token")

    def test_bpmn_priority_driven_prio(self):
        test_problem = SimProblem()

        def priority(token):
            return token.value[1]
        task1_queue = test_problem.add_var("task1_queue", priority=priority)
        task2_queue = test_problem.add_var("task2_queue", priority=priority)
        done = test_problem.add_var("done")

        resource = test_problem.add_var("resource")
        resource.put("r1")
        resource.put("r2")
        resource.put("r3")

        prototype.BPMNStartEvent(
            test_problem, [], [task1_queue], "", 1, 
            behavior=lambda id: SimToken((id, randint(1, 2)))
        )

        prototype.BPMNTask(test_problem, [task2_queue, resource], [done, resource], "task2", lambda c, r: [SimToken((c, r), delay=2)])

        prototype.BPMNTask(test_problem, [task1_queue, resource], [task2_queue, resource], "task1", lambda c, r: [SimToken((c, r), delay=2)])

        start1_count = 0
        start2_count = 0
        while test_problem.clock <= 50:
            bindings = test_problem.bindings()
            (binding, time, event) = test_problem.binding_priority(bindings)
            test_problem.fire((binding, time, event))

            # tokens with higher priority must always start first
            if event._id == "task1<task:start>":
                start1_count += 1
                prio = binding[0][1].value[1]
                for token in task1_queue.marking:
                    self.assertGreaterEqual(token.value[1], prio, "tokens with higher priority must always start first")

            if event._id == "task2<task:start>":
                start2_count += 2
                prio = binding[0][1].value[1]
                for token in task2_queue.marking:
                    self.assertGreaterEqual(token.value[1], prio, "tokens with higher priority must always start first")

        self.assertGreater(start1_count, 10, "there are at least 10 starts of task 1")
        self.assertGreater(start2_count, 10, "there are at least 10 starts of task 2")


class TestReporters(unittest.TestCase):
    
    def test_reporter_callback(self):

        class TestReporter(Reporter):
            def __init__(self):
                self.reported = []
            def callback(self, timed_binding):
                self.reported.append(timed_binding)

        test_problem = SimProblem()
        a = test_problem.add_var("a")
        b = test_problem.add_var("b")
        a.put("a1", 1)
        test_problem.add_event([a], [b], lambda x: [SimToken("b1", delay=1)], name="a_to_b")
        reporter = TestReporter()
        test_problem.simulate(10, reporter=reporter)

        # the reporter should have been called once with the binding for the event a_to_b, at time 1
        self.assertEqual(len(reporter.reported), 1, "the reporter should have been called once")
        (binding, time, event) = reporter.reported[0]
        self.assertEqual(binding[0][1].value, "a1", "the binding should be for the token with value a1")
        self.assertEqual(time, 1, "the time should be 1")
        self.assertEqual(event._id, "a_to_b", "the event should be a_to_b")

    def test_outputreporter_callback(self):

        class TestReporter(OutputReporter):
            def __init__(self):
                self.reported = []
            def callback(self, input_binding, time, event, output_binding):
                self.reported.append((input_binding, time, event, output_binding))

        test_problem = SimProblem()
        a = test_problem.add_var("a")
        b = test_problem.add_var("b")
        a.put("a1", 1)
        test_problem.add_event([a], [b], lambda x: [SimToken("b1", delay=1)], name="a_to_b")
        output_reporter = TestReporter()
        test_problem.simulate(10, reporter=output_reporter)

        # the output reporter should have printed the binding for the event a_to_b, at time 1
        self.assertEqual(len(output_reporter.reported), 1, "the output reporter should have been called once")
        (input_binding, time, event, output_binding) = output_reporter.reported[0]
        self.assertEqual(input_binding[0][1].value, "a1", "the input binding should be for the token with value a1")
        self.assertEqual(time, 1, "the time should be 1")
        self.assertEqual(event._id, "a_to_b", "the event should be a_to_b")
        self.assertEqual(output_binding[0][1].value, "b1", "the output binding should be for the token with value b1")

    def test_list_of_reporters(self):
        class TestReporter(Reporter):
            def __init__(self):
                self.reported = []
            def callback(self, timed_binding):
                self.reported.append(timed_binding)

        class TestOutputReporter(OutputReporter):
            def __init__(self):
                self.reported = []
            def callback(self, input_binding, time, event, output_binding):
                self.reported.append((input_binding, time, event, output_binding))

        test_problem = SimProblem()
        a = test_problem.add_var("a")
        b = test_problem.add_var("b")
        a.put("a1", 1)
        test_problem.add_event([a], [b], lambda x: [SimToken("b1", delay=1)], name="a_to_b")
        reporter = TestReporter()
        output_reporter = TestOutputReporter()
        test_problem.simulate(10, reporter=[reporter, output_reporter])

        # both reporters should have been called once with the binding for the event a_to_b, at time 1
        self.assertEqual(len(reporter.reported), 1, "the reporter should have been called once")
        self.assertEqual(len(output_reporter.reported), 1, "the output reporter should have been called once")


if __name__ == '__main__':
    unittest.main()
