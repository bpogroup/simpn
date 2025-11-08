import pygame
from pygame.event import Event
from simpn.visualisation import Node, Visualisation
from simpn.visualisation.events import EventType
from threading import Thread


class DummyEventHandler:
    """
    A test event handler that tracks which event types have been fired.
    Can be registered with the main window's event dispatcher for testing purposes.
    """

    def __init__(self):
        """Initialize the event handler with all event tracking flags set to False."""
        self._event_dispatcher = None
        self.visualization_created = False
        self.pre_event_loop_called = False
        self.post_event_loop_called = False
        self.binding_fired_called = False
        self.render_sim_called = False
        self.render_ui_called = False
        self.node_clicked_called = False
        self.selection_clear_called = False

    def handle_event(self, event: Event) -> bool:
        """
        Handle an event and track that it was received.

        :param event: The pygame event to handle
        :return: True to allow event propagation to continue
        """
        event_type = getattr(event, "event_type", None)

        if event_type == EventType.VISUALIZATION_CREATED:
            self.visualization_created = True
        elif event_type == EventType.PRE_EVENT_LOOP:
            self.pre_event_loop_called = True
        elif event_type == EventType.POST_EVENT_LOOP:
            self.post_event_loop_called = True
        elif event_type == EventType.BINDING_FIRED:
            self.binding_fired_called = True
        elif event_type == EventType.RENDER_SIM:
            self.render_sim_called = True
        elif event_type == EventType.RENDER_UI:
            self.render_ui_called = True
        elif event_type == EventType.NODE_CLICKED:
            self.node_clicked_called = True
        elif event_type == EventType.SELECTION_CLEAR:
            self.selection_clear_called = True

        return True  # Allow event to propagate to other handlers


def run_visualisation_for(duration: int, **kwargs):
    """
    Runs the visualisation class with the supplied kwargs for a
    total of `duration` milliseconds.

    :param sim_problem: the sim problem for the vis
    :param extra_modules: the modules being tested
    :param include_default_modules: whether to include the default mods
    """
    vis = Visualisation(**kwargs)

    vis.main_window.simulation_panel.start_simulation()

    for _ in range(5):
        vis.main_window.simulation_panel.faster_simulation()

    def stop(duration):
        from time import sleep

        sleep(duration / 1000.0)
        vis.app.exit()

    thread = Thread(target=stop, args=[duration])
    thread.start()

    vis.show()
    thread.join()
