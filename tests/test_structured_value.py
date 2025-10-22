import unittest
from time import time, sleep
import threading
import pygame
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit, QDockWidget, QToolBar, QSizePolicy, QApplication

from simpn.simulator import SimProblem, SimToken, SimTokenValue

from simpn.visualisation.events import create_event
from tests.dummy_problems import create_dummy_bpmn

class TestStructuredTokenValues(unittest.TestCase):

    def test_repr(self):
        value = SimTokenValue("foo")
        rep = value.__repr__()
        self.assertEqual(value, eval(rep))

        value = SimTokenValue("foo", 1, [1,2,3], {'baz' : 1})
        rep = value.__repr__()
        self.assertEqual(value, eval(rep))

        value = SimTokenValue("foo", 1, [1,2,3], {'baz' : 1}, joe=12, mary=13)
        rep = value.__repr__()
        self.assertEqual(value, eval(rep))

    def test_get(self):
        value = SimTokenValue("foo")
        self.assertEqual(value[0], "foo")
        self.assertEqual(value.id, "foo")

        value = SimTokenValue("foo", 1, [1,2,3], {'baz' : 1})
        self.assertEqual(value[1], 1)
        self.assertEqual(value[2], [1,2,3])
        self.assertEqual(value[3], {'baz' : 1})

        value = SimTokenValue("foo", 1, [1,2,3], {'baz' : 1}, joe=12, mary=13)
        self.assertEqual(value['mary'], 13)
        self.assertEqual(value[5], 13)
        self.assertEqual(value.mary, 13)
        self.assertEqual(value['joe'], 12)
        self.assertEqual(value[4], 12)
        self.assertEqual(value.joe, 12)

    def test_set(self):
        value = SimTokenValue("foo", 1, [1,2,3], {'baz' : 1}, joe=12, mary=13)

        value2 = value.clone()
        value2.joe = 14
        self.assertNotEqual(value.joe, value2.joe)
        self.assertEqual(value2['joe'], 14)
        self.assertEqual(value2[4], 14)

        value2['mary'] = 150
        self.assertNotEqual(value['mary'], value2['mary'])
        self.assertEqual(value2['mary'], 150)
        self.assertEqual(value2.mary, 150)
        self.assertEqual(value2, value2.clone())

        value2.mary = 13
        self.assertEqual(value2.mary, value2['mary'])
        self.assertEqual(value.mary, value2.mary)
        self.assertEqual(value2, value2.clone())

        value2[1] = 2
        self.assertEqual(value2[1], 2)
        self.assertEqual(value2.clone(), value2)

        value2[4] = 12
        self.assertEqual(value2.joe, value.joe)
        self.assertEqual(value2['joe'], 12)
        self.assertEqual(value2, value2.clone())

    def test_unpack(self):

        value = SimTokenValue("a", 2 , { 'mary' : 5 }, joe = 10)
        
        id, val, maries, joe = value 

        self.assertEqual(id, value[0])
        self.assertEqual(val, value[1])
        self.assertEqual(maries, value[2])
        self.assertEqual(joe, value[3])


    def test_len(self):

        value = SimTokenValue("a")
        self.assertEqual(len(value), 1)

        value = SimTokenValue("a", 2, 3)
        self.assertEqual(len(value), 3)

    def test_iter(self):

        value = SimTokenValue("b", 5, {'foo': 5})
        for idx,val in enumerate(value):
            self.assertEqual(val, value[idx])

        value2 = SimTokenValue(*value)
        self.assertEqual(value, value2)

        vals = list(value)
        self.assertEqual(value, tuple(vals))

    def test_slice(self):

        value = SimTokenValue("b", 5, {'foo': 5})

        vals = value[:2]
        self.assertEqual(vals, [ value[0], value[1]])

        vals = value[::-1]
        self.assertEqual(vals, [ value[2], value[1], value[0]])

    def test_create_simple(self):
        value = SimTokenValue("foo")
        value2 = SimTokenValue("baz")

        self.assertEqual(value, tuple(["foo"]))
        self.assertNotEqual(value, value2)
        self.assertEqual(value, value)
        self.assertEqual(value2, value2)
        self.assertEqual(value2, tuple(["baz"]))

    def test_put(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        b = test_problem.add_var("b")

        one = SimTokenValue(1)
        alpha = SimTokenValue("a")
        a.put(one)
        a.put(one.clone(), 1)
        a.put(alpha)
        a.put(alpha.clone())
        b.put(one.clone())

        self.assertEqual(len(a.marking), 4, "added 4 tokens to a")
        self.assertEqual(a.marking[3], SimToken(one, 1), "last token is 1@1")
        self.assertEqual(a.marking.count(SimToken(one, 1)), 1, "added 1 token with value 1 at time 1 to a")
        self.assertEqual(a.marking.count(SimToken(one, 0)), 1, "added 1 token with value 1 at time 0 to a")
        self.assertEqual(a.marking.count(SimToken(alpha, 0)), 2, "added 1 token with value a at time 0 to a")
        self.assertEqual(len(b.marking), 1, "added 1 token to b")
        self.assertEqual(b.marking, [SimToken(one)], "token is 1@0")

    def test_remove(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")

        one = SimTokenValue(1)
        alpha = SimTokenValue("a")

        a.put(one)
        a.put(one, 1)
        a.put(one, 2)
        a.put(alpha)
        a.put(alpha)
        a.put(alpha, 1)
        a.remove_token(SimToken(one, 1))
        a.remove_token(SimToken(alpha))

        self.assertEqual(len(a.marking), 4, "4 tokens left on a")
        self.assertEqual(a.marking[3], SimToken(one, 2), "last token is 1@2")
        self.assertEqual(a.marking[2], SimToken(alpha, 1), "before-last token is a@1")
        self.assertEqual(a.marking.count(SimToken(one, 0)), 1, "1 token with value 1 at time 0")
        self.assertEqual(a.marking.count(SimToken(one, 2)), 1, "1 token with value 1 at time 2")
        self.assertEqual(a.marking.count(SimToken(alpha, 0)), 1, "1 token with value a at time 0")
        self.assertEqual(a.marking.count(SimToken(alpha, 1)), 1, "1 token with value a at time 1")

    def test_add_stransition(self):
        one = SimTokenValue(1)

        def test_behavior(d, e):
            return [SimToken(one, 0)]

        def test_constraint(d, e):
            return True

        test_problem = SimProblem()
        a = test_problem.add_var("a")
        b = test_problem.add_var("b")
        c = test_problem.add_var("c")
        ta = test_problem.add_event([a, b], [c], test_behavior, guard=test_constraint)
        tb = test_problem.add_event([a, b], [c], lambda d, e: [SimToken(one, 0)], name="tb", guard=test_constraint)

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
        b.put(SimTokenValue("b1"))
        ta = test_problem.add_event([a, b], [], lambda c, d: 1, name="ta")
        self.assertEqual(test_problem.bindings(), [], "no token combinations")

    def test_tokens_combinations_one_to_one(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a1 = SimTokenValue("a1")
        a.put(a1)
        b = test_problem.add_var("b")
        b1 = SimTokenValue("b1")
        b.put(b1)
        ta = test_problem.add_event([a, b], [], lambda c, d: 1, name="ta")

        bindings = test_problem.bindings()

        self.assertEqual(bindings , 
            [([(a, SimToken(a1, 0)), (b, SimToken(b1, 0))], 0, ta)], 
            "one token combination"
        )

    def test_tokens_combinations_one_to_one_mixed(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a1 = ("a1")
        a.put(a1)
        b = test_problem.add_var("b")
        b1 = SimTokenValue("b1")
        b.put(b1)
        ta = test_problem.add_event([a, b], [], lambda c, d: 1, name="ta")

        bindings = test_problem.bindings()

        self.assertEqual(bindings , 
            [([(a, SimToken(a1, 0)), (b, SimToken(b1, 0))], 0, ta)], 
            "one token combination"
        )

    def test_fire_delay_function(self):
        test_problem = SimProblem()
        a = test_problem.add_var("a")
        a.put(SimTokenValue(1), 1)
        b = test_problem.add_var("b")
        b.put(SimTokenValue(2), 1)
        e = test_problem.add_var("e")
        test_problem.add_event(
            [a, b], 
            [e], 
            lambda c, d: [SimToken(SimTokenValue(c.id + d.id), delay=1)], 
            name="ta")
        test_problem.fire(test_problem.bindings()[0])
        self.assertEqual(
            e.marking.count(SimToken(SimTokenValue(3), 2)), 
            1, "fire produces token with delay")
        
    def test_binding_order(self):
        test_problem = SimProblem()
        test_problem.clock = 4
        a = test_problem.add_var("a")
        a.put(SimTokenValue("b"), 3)
        a.put(SimTokenValue("d"), 1)
        a.put(SimTokenValue("c"), 2)
        a.put(SimTokenValue("a"), 4)
        b = test_problem.add_var("b")
        b.put(SimTokenValue("b"), 3)
        b.put(SimTokenValue("a"), 4)
        b.put(SimTokenValue("d"), 1)
        b.put(SimTokenValue("c"), 2)
        test_problem.add_event([a, b], [], lambda c, d: [], name="ta")
        test_problem.clock = 4
        bindings = test_problem.bindings()
        # for two tokens that have the same time for place b, the first token on a must always have time <= the second token
        # for two tokens that have the same time for place a, the first token on b must always have time <= the second token
        for time in range(1, 5):
            for i in range(len(bindings)):
                for j in range(i+1, len(bindings)):
                    if bindings[i][0][1][1].time == time and bindings[j][0][1][1].time == time:
                        self.assertLessEqual(bindings[i][0][0][1].time, bindings[j][0][0][1].time, 
                            "two bindings with index i, j, i < j, with the same time for b, must have binding[i] time for a <=  binding[j] time for a")
                    if bindings[i][0][0][1].time == time and bindings[j][0][0][1].time == time:
                        self.assertLessEqual(bindings[i][0][1][1].time, bindings[j][0][1][1].time, 
                            "two bindings with index i, j, i < j, with the same time for a, must have binding[i] time for b <=  binding[j] time for b")
                        
    def test_can_run_sim(self):
        problem = create_dummy_bpmn(structured=True)
        problem.simulate(10)

    @staticmethod
    def quick_close(vis, wait_time=0.4):
        start = time()
        for _ in range(5):
            vis.main_window.pygame_widget.get_panel().action_faster()
        vis.main_window.pygame_widget.get_panel().action_play()
        pygame.event.post(
            pygame.event.Event(
                pygame.USEREVENT + 1,
                { "message" : "hello, world!"}
            )
        )

        while (time() - start) <= wait_time:
            sleep(0.02)

        # quit the PyQT main application
        QApplication.instance().quit()

    def test_can_run_vis(self):
        from simpn.visualisation import Visualisation
        problem = create_dummy_bpmn(structured=True)
        
        vis = Visualisation(problem, extra_modules=[])
        self.assertIsNotNone(vis)
        
        thread = threading.Thread(target=self.quick_close, args=[vis, 1.5])
        thread.start()
        vis.show()
        thread.join()

