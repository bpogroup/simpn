import unittest
from simpn.simulator import SimProblem, SimToken, SimVarQueue
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


class TestPriorities(unittest.TestCase):

    def test_time_driven_prio(self):
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
            (binding, time, event) = bindings[0]
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
            
        self.assertGreater(completion_count, 10, "there are at least 10 completions")

    def test_priority_driven_prio(self):
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

        prototype.BPMNStartEvent(test_problem, [], [task1_queue], "", 1, behavior=lambda: [SimToken(randint(1, 2))])

        prototype.BPMNTask(test_problem, [task2_queue, resource], [done, resource], "task2", lambda c, r: [SimToken((c, r), delay=2)])

        prototype.BPMNTask(test_problem, [task1_queue, resource], [task2_queue, resource], "task1", lambda c, r: [SimToken((c, r), delay=2)])

        start1_count = 0
        start2_count = 0
        while test_problem.clock <= 50:
            bindings = test_problem.bindings()
            (binding, time, event) = bindings[0]
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


if __name__ == '__main__':
    unittest.main()
