import inspect
import pygame
from simpn.simulator import SimToken, SimVar
import random
import simpn.prototypes as prototypes
import simpn.visualisation as vis

class QueueingGenerator(prototypes.Prototype):

    def __init__(self, model, incoming, outgoing, name, interarrival_time, behavior=None):
        """
        Generates a composition of SimVar and SimEvent that represents a queueing system generator.
        Adds it to the specified model. The generator generates new cases with the specified interarrival_time.
        Cases are places on the outgoing SimVar (which can be a queue). The cases will be a tuple (unique_number, case_data).
        Case_data will be generated according to the specified behavior, or unspecified if behavior==None.
        The arrival of a new case will be signalled as a 'start event', so it can be used for process mining.

        :param model: the SimProblem to which the generator must be added.
        :param incoming: parameter is only here for consistency, must be [].
        :param outgoing: a list with a single SimVar in which the generated cases will be placed.
        :param name: the name of the generator.
        :param interarrival_time: the interarrival time with which events are generated. Can be a numeric value or a function that produces a numeric value, such as a sampling function from a random distribution.
        :param behavior: an optional behavior describing how case_data is produced.
        """
        super().__init__(model, incoming, outgoing, name)

        if len(incoming) != 0:
            raise TypeError("Generator " + name + ": cannot have any incoming.")
        if len(outgoing) != 1:
            raise TypeError("Generator " + name + ": must have exactly one outgoing.")
        if not callable(interarrival_time) and not type(interarrival_time) is int and not type(interarrival_time) is float:
            raise TypeError("Generator " + name + ": must either have a value or a function as interarrival_time.")
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
                raise TypeError("Generator " + name + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
            if len(inspect.signature(behavior).parameters) != 0:
                raise TypeError("Generator " + name + ": the behavior function must not have many parameters.")
            result = model.add_event([invar], [invar, outgoing[0]], lambda a: [SimToken(name + str(int(a[len(name):]) + 1), delay=interarrival_time_f()), SimToken((a, behavior()[0].value))], name=name + "<start_event>")
            self.add_event(result)
        invar.put(name + "0")

        model.add_prototype(self)

    class QueueingGeneratorViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            x, y = self._pos
            hw, hh = self._half_width, self._half_height
            pygame.draw.polygon(screen, vis.TUE_LIGHTBLUE, [(x-hw, y-hh), (x+hw, y), (x-hw, y+hh), (x-hw, y-hh)])
            pygame.draw.polygon(screen, vis.TUE_BLUE, [(x-hw, y-hh), (x+hw, y), (x-hw, y+hh), (x-hw, y-hh)], vis.LINE_WIDTH)
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))

    def get_visualisation(self):
        return self.QueueingGeneratorViz(self)


class QueueingQueue(SimVar):
    def __init__(self, model, _id, priority=lambda token: token.time):
        """
        A SimVar that represents a queue in a queueing system.
        It is just a SimVar with a different visualisation.
        """
        super().__init__(_id, priority)

        model.add_prototype_var(self)

    class QueueingQueueViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            x, y = self._pos
            hw, hh = self._half_width, self._half_height
            pygame.draw.rect(screen, vis.TUE_LIGHTBLUE, pygame.Rect(x-hw, y-hh, self._width, self._height))
            pygame.draw.line(screen, vis.TUE_BLUE, (x-hw, y-hh), (x+hw, y-hh), vis.LINE_WIDTH)
            pygame.draw.line(screen, vis.TUE_BLUE, (x+hw, y-hh), (x+hw, y+hh), vis.LINE_WIDTH)
            pygame.draw.line(screen, vis.TUE_BLUE, (x+hw, y+hh), (x-hw, y+hh), vis.LINE_WIDTH)

            pygame.draw.line(screen, vis.TUE_BLUE, (x-int(hw/2), y-hw), (x-int(hw/2), y+hw), vis.LINE_WIDTH)
            pygame.draw.line(screen, vis.TUE_BLUE, (x, y-hw), (x, y+hw), vis.LINE_WIDTH)
            pygame.draw.line(screen, vis.TUE_BLUE, (x+int(hw/2), y-hw), (x+int(hw/2), y+hw), vis.LINE_WIDTH)

            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)
            bold_font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE, bold=True)
            
            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))

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
        return self.QueueingQueueViz(self)


class QueueingServer(prototypes.Prototype):
    def __init__(self, model, incoming, outgoing, name, processing_time, behavior=None, c=1):
        """
        Generates a composition of SimVar and SimEvent that represents a queue server with c resources.
        Adds it to the specified model. The server must have one incoming (queue) SimVar and one outgoing SimVar.
        The behavior specifies how the server may change the case data.
        By default the behavior is None, which means that the case data is not changed.
        It also specifies the processing time of the task in the form of a SimToken delay.

        :param model: the SimProblem to which the task composition must be added.
        :param incoming: a list with one SimVar.
        :param outgoing: a list with one SimVar.
        :param name: the name of the server.
        :param processing_time: the processing time of the server, which can either be a deterministic number or a function that is invoked to sample the processing time.
        :param behavior: the behavior function, which takes one input parameters according to the incoming and produces a single outgoing, which is a tuple (case, resource)@delay.
        :param c: the number of resources of the server.
        """
        super().__init__(model, incoming, outgoing, name)

        if len(incoming) != 1:
            raise TypeError("Server " + name + ": must have one input parameter for the case taken from the queue.")
        if len(outgoing) != 1:
            raise TypeError("Server " + name + ": must have one output parameter.")
        if behavior is not None and not callable(behavior):
            raise TypeError("Server " + name + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
        if behavior is not None and len(inspect.signature(behavior).parameters) != 1:
            raise TypeError("Server " + name + ": the behavior function must have one parameter for the case taken from the queue.")
        if not callable(processing_time) and not type(processing_time) is int and not type(processing_time) is float:
            raise TypeError("Server " + name + ": must either have a value or a function as processing_time.")
        processing_time_f = processing_time
        if type(processing_time) is int or type(processing_time) is float:
            processing_time_f = lambda: processing_time

        resource_name = name + "_resource"
        busyvar_name = name + "_busy"
        start_event_name = name + "<task:start>"
        complete_event_name = name + "<task:complete>"
        self._busyvar = model.add_var(busyvar_name)
        self.add_var(self._busyvar)
        self._resourcevar = model.add_var(resource_name)
        self.add_var(self._resourcevar)
        for i in range(c):
            self._resourcevar.put("r"+str(i))
        if behavior is None:
            behavior_f = lambda a, r: [SimToken((a, r), delay=processing_time_f())]
        else:
            behavior_f = lambda a, r: [SimToken((behavior(a), r), delay=processing_time_f())]
        start_event = model.add_event([incoming[0], self._resourcevar], [self._busyvar], behavior_f, name=start_event_name)
        self.add_event(start_event)
        complete_event = model.add_event([self._busyvar], [outgoing[0], self._resourcevar], lambda b: [SimToken(b[0]), SimToken(b[1])], name=complete_event_name)
        self.add_event(complete_event)

        model.add_prototype(self)

    class QueueingServerViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            pygame.draw.circle(screen, vis.TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), self._half_height)
            pygame.draw.circle(screen, vis.TUE_BLUE, (self._pos[0], self._pos[1]), self._half_height, vis.LINE_WIDTH)    
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)
            bold_font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE, bold=True)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
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
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH + int(label.get_height())
            screen.blit(label, (text_x_pos, text_y_pos))        

            # draw free servers
            label = bold_font.render("free: " + str(len(self._model_node._resourcevar.marking)), True, vis.TUE_RED)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] - self._half_height - vis.LINE_WIDTH - int(label.get_height())
            screen.blit(label, (text_x_pos, text_y_pos))        

    def get_visualisation(self):
        return self.QueueingServerViz(self)


class QueueingSink(SimVar):
    def __init__(self, model, _id, priority=lambda token: token.time):
        """
        A SimVar that represents a sink.
        It is just a SimVar with a different visualisation.
        """
        super().__init__(_id, priority)

        model.add_prototype_var(self)

    class QueueingSinkViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            x, y = self._pos
            hw, hh = self._half_width, self._half_height
            pygame.draw.polygon(screen, vis.TUE_LIGHTBLUE, [(x-hw, y), (x+hw, y-hw), (x+hw, y+hh), (x-hw, y)])
            pygame.draw.polygon(screen, vis.TUE_BLUE, [(x-hw, y), (x+hw, y-hw), (x+hw, y+hh), (x-hw, y)], vis.LINE_WIDTH)

            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)
            bold_font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE, bold=True)
            
            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))

            # draw marking
            label = bold_font.render(str(len(self._model_node.marking)), True, vis.TUE_RED)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH + int(label.get_height())
            screen.blit(label, (text_x_pos, text_y_pos))        

    def get_visualisation(self):
        return self.QueueingSinkViz(self)


class QueueingChoice(prototypes.Prototype):

    def __init__(self, model, incoming, outgoing, name, weights):
        """
        Generates a composition of SimVar and SimEvent that represents a choice of which queue to go in.
        Adds it to the specified model. The choice is made according to the weights.
        Cases are taken from the (single) incoming SimVar and placed in one of the outgoing SimVars according to specified the weights.

        :param model: the SimProblem to which the generator must be added.
        :param incoming: parameter is only here for consistency, must be [].
        :param outgoing: a list with a single SimVar in which the generated cases will be placed.
        :param name: the name of the generator.
        :param weights: a list of weights that sum up to 1.0.
        """
        super().__init__(model, incoming, outgoing, name)

        if len(incoming) != 1:
            raise TypeError("Choice " + name + ": must have exacly one incoming SimVar.")
        if len(outgoing) < 2:
            raise TypeError("Choice " + name + ": must have at least two outgoing SimVar.")
        if len(outgoing) != len(weights):
            raise TypeError("Choice " + name + ": the number of outgoing SimVars must be equal to the number of weights.")
        for w in weights:
            if type(w) is not int and type(w) is not float:
                raise TypeError("Choice " + name + ": the weights must be numeric values. " + str(w) + " is not.")

        def choose(c):
            chosen = random.choices(list(range(len(outgoing))), weights)[0]
            result = [None] * len(outgoing)
            result[chosen] = SimToken(c)
            return result
        choice_event = model.add_event(incoming, outgoing, choose)
        self.add_event(choice_event)

        model.add_prototype(self)

    class QueueingChoiceViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            x, y = self._pos
            hw, hh = self._half_width, self._half_height
            pygame.draw.polygon(screen, vis.TUE_LIGHTBLUE, [(x-hw, y), (x, y-hw), (x+hw, y), (x, y+hh), (x-hw, y)])
            pygame.draw.polygon(screen, vis.TUE_BLUE, [(x-hw, y), (x, y-hw), (x+hw, y), (x, y+hh), (x-hw, y)], vis.LINE_WIDTH)
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))

    def get_visualisation(self):
        return self.QueueingChoiceViz(self)
