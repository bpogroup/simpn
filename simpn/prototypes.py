import inspect
import pygame
from simpn.simulator import SimToken, SimVar
import simpn.visualisation as vis


class Prototype:
    def __init__(self, model, incoming, outgoing, name):
        """
        Superclass for all prototypes. Contains the basic structure of a prototype, which is a composition of SimVar and SimEvent.
        A prototype must subclass this class.
        Each event and variable that the prototype creates must both be added to the model and to the prototype itself.
        The prototype must finally be added to the model, using the model.add_prototype() method.
        """
        self.model = model
        self.incoming = incoming
        self.outgoing = outgoing
        self.name = name
        self.places = []
        self.events = []
        self.visualize = True

    def add_var(self, var):
        self.places.append(var)

    def add_event(self, event):
        self.events.append(event)

    def get_id(self):
        return self.name
    
    def get_visualisation(self):
        raise NotImplementedError("Method get_visualisation must be implemented in subclass.")

    def set_invisible(self):
        self.visualize = False

class BPMNStartEvent(Prototype):  

    def __init__(self, model, incoming, outgoing, name, interarrival_time, behavior=None):
        """
        Generates a composition of SimVar and SimEvent that represents a BPMN start event.
        Adds it to the specified model. The start event generates new cases with the specified interarrival_time.
        Cases are places on the outgoing SimVar. The cases will be a tuple (unique_number, case_data).
        Case_data will be generated according to the specified behavior, or unspecified if behavior==None.

        :param model: the SimProblem to which the start event composition must be added.
        :param incoming: parameter is only here for consistency, must be [].
        :param outgoing: a list with a single SimVar in which the cases will be placed.
        :param name: the name of the start event.
        :param interarrival_time: the interarrival time with which events are generated. Can be a numeric value or a function that produces a numeric value, such as a sampling function from a random distribution.
        :param behavior: an optional behavior describing how case_data is produced.
        """
        super().__init__(model, incoming, outgoing, name)

        if len(incoming) != 0:
            raise TypeError("Start event " + name + ": cannot have any incoming.")
        if len(outgoing) != 1:
            raise TypeError("Start event " + name + ": must have exactly one outgoing.")
        if not callable(interarrival_time) and not type(interarrival_time) is int and not type(interarrival_time) is float:
            raise TypeError("Start event " + name + ": must either have a value or a function as interarrival_time.")
        interarrival_time_f = interarrival_time
        if type(interarrival_time) is int or type(interarrival_time) is float:
            interarrival_time_f = lambda: interarrival_time

        invar_name = name + "_timer"
        invar = model.add_var(invar_name)
        self.add_var(invar)
        if behavior is None:
            result = model.add_event([invar], [invar, outgoing[0]], lambda a: [SimToken(name + str(int(a[len(name):]) + 1), delay=interarrival_time_f()), SimToken((a,))], name=name + "<start_event>")
            self.add_event(result)
        else:
            if not callable(behavior):
                raise TypeError("Start event " + name + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
            if len(inspect.signature(behavior).parameters) != 0:
                raise TypeError("Start event " + name + ": the behavior function must not have many parameters.")
            result = model.add_event([invar], [invar, outgoing[0]], lambda a: [SimToken(name + str(int(a[len(name):]) + 1), delay=interarrival_time_f()), SimToken((a, behavior()[0].value))], name=name + "<start_event>")
            self.add_event(result)
        invar.put(name + "0")

        model.add_prototype(self)

    class BPMNStartEventViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            pygame.draw.circle(screen, vis.TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), self._width/2)
            pygame.draw.circle(screen, vis.TUE_BLUE, (self._pos[0], self._pos[1]), self._width/2, vis.LINE_WIDTH)    
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))

    def get_visualisation(self):
        return self.BPMNStartEventViz(self)
    

class BPMNTask(Prototype):
    def __init__(self, model, incoming, outgoing, name, behavior, guard=None, outgoing_behavior=None):
        """
        Generates a composition of SimVar and SimEvent that represents a BPMN task.
        Adds it to the specified model. The task must have at least two incoming and two outgoing SimVar.
        The first SimVar represents the case that must be processed by the task and the second the resource.
        There can be additional SimVar that represent additional variables that the task may need or produce.
        The behavior specifies how the task may change the case data.
        It also specifies the processing time of the task in the form of a SimToken delay.
        The behavior must take input parameters according to the incoming variables and produces a single intermediate variable, which must be a tuple (case, resource [, <additional variable 1>, <additional variable 2>, ...])@delay.

        :param model: the SimProblem to which the task composition must be added.
        :param incoming: a list with at least two SimVar: a case SimVar, a resource SimVar, and optionally additional SimVar.
        :param outgoing: a list with at least two SimVar: a case SimVar, a resource SimVar, and optionally additional SimVar.
        :param name: the name of the task.
        :param behavior: the behavior function, which takes at least two input parameters according to the incoming variables and produces a single intermediate variable.
        :param guard: an optional guard that specifies which combination of case and resource is allowed. The guard must take at least two input parameters according to the incoming variables.
        :param outgoing_behavior: an optional behavior that specifies how the outgoing variables are produced from the single intermediate variable.
        """
        super().__init__(model, incoming, outgoing, name)

        if len(incoming) < 2:
            raise TypeError("Task event " + name + ": must have at least two input parameters; the first for cases and the second for resources.")
        if len(outgoing) < 2:
            raise TypeError("Task event " + name + ": must have at least two output parameters; the first for cases and the second for resources.")
        if not callable(behavior):
            raise TypeError("Task event " + name + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
        if len(inspect.signature(behavior).parameters) != len(incoming):
            raise TypeError("Task event " + name + ": the behavior function must have as many parameters as the number of incoming variables.")
        if outgoing_behavior is not None:
            if not callable(outgoing_behavior):
                raise TypeError("Task event " + name + ": the outgoing_behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
            if len(inspect.signature(outgoing_behavior).parameters) != 1:
                raise TypeError("Task event " + name + ": the outgoing_behavior function must have exactly one parameter.")
        if guard is not None:
            if not callable(guard):
                raise TypeError("Task event " + name + ": the guard must be a function. (Maybe you made it a function call, exclude the brackets.)")
            if len(inspect.signature(guard).parameters) != len(incoming):
                raise TypeError("Task event " + name + ": the guard function must have as many parameters as the number of incoming variables.")

        busyvar_name = name + "_busy"
        start_event_name = name + "<task:start>"
        complete_event_name = name + "<task:complete>"
        self._busyvar = model.add_var(busyvar_name)
        self.add_var(self._busyvar)
        start_event = model.add_event(incoming, [self._busyvar], behavior, name=start_event_name, guard=guard)
        self.add_event(start_event)
        if outgoing_behavior is None:
            complete_event = model.add_event([self._busyvar], outgoing, lambda b: [SimToken(b[i]) for i in range(len(b))], name=complete_event_name)
        else:
            complete_event = model.add_event([self._busyvar], outgoing, outgoing_behavior, name=complete_event_name)
        self.add_event(complete_event)

        model.add_prototype(self)

    class BPMNTaskViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
            self._width = 100
            self._height = vis.STANDARD_NODE_HEIGHT
            self._half_width =  self._width / 2
            self._half_height = self._height / 2

        def draw(self, screen):
            x_pos, y_pos = int(self._pos[0] - self._width/2), int(self._pos[1] - self._height/2)
            pygame.draw.rect(screen, vis.TUE_LIGHTBLUE, pygame.Rect(x_pos, y_pos, self._width, self._height), border_radius=int(0.075*self._width))
            pygame.draw.rect(screen, vis.TUE_BLUE, pygame.Rect(x_pos, y_pos, self._width, self._height),  vis.LINE_WIDTH, int(0.075*self._width))
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)
            bold_font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE, bold=True)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = int((self._width - label.get_width())/2) + x_pos
            text_y_pos = int((self._height - label.get_height())/2) + y_pos
            screen.blit(label, (text_x_pos, text_y_pos))

            # draw marking
            mstr = "["
            ti = 0
            for token in self._model_node._busyvar.marking:
                mstr += str(token.value) + "@" + str(round(token.time, 2))
                if ti < len(self._model_node._busyvar.marking) - 1:
                    mstr += ", "
                ti += 1
            mstr += "]"
            label = bold_font.render(mstr, True, vis.TUE_RED)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))        


    def get_visualisation(self):
        return self.BPMNTaskViz(self)


class BPMNIntermediateEvent(Prototype):
    def __init__(self, model, incoming, outgoing, name, behavior, guard=None):
        """
        Generates a composition of SimVar and SimEvent that represents a BPMN intermediate event.
        The intermediate event can make changes to the data of a case and can generate waiting time for the case.

        :param model: the SimProblem to which the event composition must be added.
        :param incoming: a list with at least one SimVar: a case SimVar.
        :param outgoing: a list with at least one SimVar: a case SimVar.
        :param name: the name of the event.
        :param behavior: specifies the changes that the intermediate event makes to the data and the delay that the intermediate event may lead to.
        :param guard: an optional guard that specifies under which condition the intermediate event can happen.
        """
        super().__init__(model, incoming, outgoing, name)

        if len(incoming) < 1:
            raise TypeError("Event " + name + ": must have at least one input parameter for cases.")
        if len(outgoing) < 1:
            raise TypeError("Event " + name + ": must have at least one output parameter for cases.")
        if not callable(behavior):
            raise TypeError("Event " + name + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
        if len(inspect.signature(behavior).parameters) != len(incoming):
            raise TypeError("Event " + name + ": the behavior function must have as many parameters as the number of incoming variables.")
        if guard is not None:
            if not callable(guard):
                raise TypeError("Event " + name + ": the guard must be a function. (Maybe you made it a function call, exclude the brackets.)")
            if len(inspect.signature(guard).parameters) != len(incoming):
                raise TypeError("Event " + name + ": the guard function must have as many parameters as the number of incoming variables.")

        result = model.add_event(incoming, outgoing, behavior, name=name + "<intermediate_event>", guard=guard)
        self.add_event(result)

        model.add_prototype(self)

    class BPMNIntermediateEventViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            pygame.draw.circle(screen, vis.TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), self._width/2)
            pygame.draw.circle(screen, vis.TUE_BLUE, (self._pos[0], self._pos[1]), self._width/2, vis.LINE_WIDTH)   
            pygame.draw.circle(screen, vis.TUE_BLUE, (self._pos[0], self._pos[1]), self._width/2-3, vis.LINE_WIDTH)   
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))

    def get_visualisation(self):
        return self.BPMNIntermediateEventViz(self)


class BPMNEndEvent(Prototype):
    def __init__(self, model, incoming, outgoing, name):
        """
        Generates a composition of SimVar and SimEvent that represents a BPMN end event.

        :param model: the SimProblem to which the event composition must be added.
        :param incoming: a list with one SimVar: a case SimVar.
        :param outgoing: parameter is only here for consistency, must be [].
        :param name: the name of the event.
        """
        super().__init__(model, incoming, outgoing, name)

        if len(incoming) != 1:
            raise TypeError("Event " + name + ": must have one input parameter for cases.")
        if len(outgoing) != 0:
            raise TypeError("Event " + name + ": must not have output parameters.")

        result = model.add_event(incoming, outgoing, lambda c: [], name=name + "<end_event>")
        self.add_event(result)

        model.add_prototype(self)

    class BPMNEndEventViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            pygame.draw.circle(screen, vis.TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), self._width/2)
            pygame.draw.circle(screen, vis.TUE_BLUE, (self._pos[0], self._pos[1]), self._width/2, vis.LINE_WIDTH*2)
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))

    def get_visualisation(self):
        return self.BPMNEndEventViz(self)


class BPMNFlow(SimVar):
    def __init__(self, model, _id):
        """
        A SimVar that represents a BPMN Flow.
        It is just a SimVar with a different visualisation.
        """
        super().__init__(_id)

        model.add_prototype_var(self)

    class BPMNFlowViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
            self._width = 3
            self._height = 3
            self._half_width =  self._width / 2
            self._half_height = self._height / 2
            self._show_arrowheads = False
        
        def draw(self, screen):
            x, y = self._pos
            pygame.draw.circle(screen, vis.TUE_BLUE, (x, y), self._width)

            bold_font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE, bold=True)
            
            # draw marking
            mstr = "["
            ti = 0
            for token in self._model_node.marking:
                mstr += str(token.value) + "@" + str(round(token.time, 2))
                if ti < len(self._model_node.marking) - 1:
                    mstr += ", "
                ti += 1
            mstr += "]"
            label = bold_font.render(mstr, True, vis.TUE_RED)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH + int(label.get_height())
            screen.blit(label, (text_x_pos, text_y_pos))        

    def get_visualisation(self):
        return self.BPMNFlowViz(self)
