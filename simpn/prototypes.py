import inspect
import pygame
from simpn.simulator import SimToken, SimVar, SimEvent, SimProblem, Describable
import simpn.visualisation as vis
import math
import re

# matplotlib set1 colormap
TASK_TOKEN_SHOW_COLOURS = [
    pygame.Color("#E41A1C"),
    pygame.Color("#377EB8"),
    pygame.Color("#4DAF4A"),
    pygame.Color("#984EA3"),
    pygame.Color("#FF7F00"),
    pygame.Color("#FFFF33"),
    pygame.Color("#A65628"),
    pygame.Color("#F781BF"),
    pygame.Color("#999999"),
]

class Prototype(Describable):
    """
    Superclass for all prototypes. Contains the basic structure of a prototype, which is a composition of SimVar and SimEvent.
    A prototype must subclass this class.
    Each event and variable that the prototype creates must both be added to the model and to the prototype itself.
    The prototype must finally be added to the model, using the model.add_prototype() method.
    """

    def __init__(self, model, incoming, outgoing, name):
        self.model = model
        self.incoming = incoming
        self.outgoing = outgoing
        self.name = name
        self.places = []
        self.events = []
        self.visualize = True
        self.visualize_edges = True
        self.visualization_of_edges = None

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

    def set_invisible_edges(self):
        self.visualize_edges = False       

    def set_visualization_of_edges(self, edges):
        """
        Sets the specific edges to visualize. Only the specified edges will be visualized.
        Edges must be specified as either (a: SimVar, self) or (self, b: SimVar).
        Precondition: for each edge (a, self), a must be in self.incoming; for each edge (self, b), b must be in self.outgoing.

        :param edges: a list of edges to visualize.
        """
        for (a, b) in edges:
            if a == self and b not in self.outgoing:
                raise ValueError("Edge (" + str(a) + ", " + str(b) + ") is not a valid outgoing edge for event " + str(self) + ".")
            if b == self and a not in self.incoming:
                raise ValueError("Edge (" + str(a) + ", " + str(b) + ") is not a valid incoming edge for event " + str(self) + ".")

        self.visualization_of_edges = edges


class TaskTokenShower(vis.Node):
    """
    A helper drawer that captures the in-flights tokens that are being 
    processed by a BPMN prototype. The shower creates a group of tokens 
    above the task, colouring them by the prefix of the tokens to highlight
    what tokens are being processed in the groups.
    """

    def __init__(self, model_node):
        super().__init__(model_node)
        self._task = None 
        self._token_radius = 3
        self._token_dia = self._token_radius * 2
        self._seen_token_types = {}
        self._next_tok_colour = 0
        self._max_rows = 3

    def set_task(self, task) -> 'TaskTokenShower':
        self._task = task 
        return self 
    
    def set_pos(self, pos) -> 'TaskTokenShower':
        self._pos = pos 
        return self 
    
    def set_rows(self, rows:int) -> 'TaskTokenShower':
        self._max_rows = rows 
        return self
    
    def set_time(self, clock:float) -> 'TaskTokenShower':
        self._curr_time = clock
        return self 
    
    def get_token_colour(self, token):
        # handle the token
        if isinstance(token, tuple):
            name = token[0]
        else:
            if not isinstance(token, str):
                name = str(token)
            else:
                name = token
        # it would be nice if we did not have to do this to find the general
        # family that the token comes from
        cut = re.compile("[0-9]").search(name).span()[0]
        name = name[:cut]
        # find a colour
        if name not in self._seen_token_types:
            colour = TASK_TOKEN_SHOW_COLOURS[self._next_tok_colour]
            self._next_tok_colour += 1 
            if (self._next_tok_colour >= len(TASK_TOKEN_SHOW_COLOURS)):
                self._next_tok_colour = 0 
            self._seen_token_types[name] = colour 
        else:
            colour = self._seen_token_types[name]
        return colour
    
    def draw(self, screen:pygame.Surface):
        """
        Draws the groups of tokens being processed above the current task
        """
        if (self._task is not None):
            tokens = []
            node = self._task._model_node
            if hasattr(node, '_busyvar'):
                tokens = node._busyvar.marking
            elif hasattr(node, '_marking'):
                tokens = node._marking
            else:
                raise ValueError(f"Could not identify the in-flight tokens for the given task :: {self._task=}")

            # start from the top left of the node
            group_height = self._token_dia * 2
            curr_x = self._pos[0] - self._task._half_width 
            padding_x = self._token_radius
            curr_y = self._pos[1] \
                - self._task._half_height - group_height - self._token_radius
            padding_y = self._token_radius
            start_x = curr_x
            row_end_x = start_x + self._task._width 
            rows = 1

            # loop through token groups
            for group in tokens:
                group_width = self._token_dia * (len(group.value) + 1)
                
                group_rect = pygame.Rect(
                    curr_x, curr_y,
                    group_width, group_height
                )

                pygame.draw.rect(
                    screen, vis.TUE_LIGHTBLUE, group_rect, vis.LINE_WIDTH,
                    int(group_width * 0.25)
                )

                tok_x = curr_x + self._token_radius
                tok_y = curr_y + self._token_radius
                # loop through values of the group
                for tok in group.value:
                    tok_circle = pygame.draw.circle(
                        screen, self.get_token_colour(tok),
                        (tok_x + self._token_radius, 
                         tok_y + self._token_radius),
                        self._token_radius,
                    )
                    tok_x += self._token_dia

                # handle moving to a new row
                curr_x += padding_x + group_width
                if (curr_x >= row_end_x):
                    curr_x = start_x
                    curr_y -= padding_y + group_height
                    rows += 1 
                
                # to prevent drawing a million groups
                if (rows >= self._max_rows):
                    break


class BPMNStartEvent(Prototype):  
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

    def __init__(self, model, incoming, outgoing, name, interarrival_time, behavior=None):
        super().__init__(model, incoming, outgoing, name)
        model.set_binding_priority(SimProblem.PRIORITY_QUEUE_BINDING)  # We process tokens in BPMN models FCFS

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

    def get_description(self):
        description = [(super().get_id() + ": BPMNStartEvent", Describable.Style.HEADING)]
        return description

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

    def __init__(self, model, incoming, outgoing, name, behavior, guard=None, outgoing_behavior=None):
        super().__init__(model, incoming, outgoing, name)
        model.set_binding_priority(SimProblem.PRIORITY_QUEUE_BINDING)  # We process tokens in BPMN models FCFS

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

    def get_description(self):
        description = [(super().get_id() + ": BPMNTask", Describable.Style.HEADING)]
        description.append( (" ", Describable.Style.NORMAL) )
        description.append( ("Marking:", Describable.Style.NORMAL) )
        for token in self._busyvar.marking:
            description.append( (str(token), Describable.Style.BOXED) )
        return description

    class BPMNTaskViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
            self._width = 100
            self._height = vis.STANDARD_NODE_HEIGHT
            self._half_width =  self._width / 2
            self._half_height = self._height / 2
            self._token_shower = TaskTokenShower(None)

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

            # draw tokens above the task being processed
            self._token_shower \
                .set_task(self) \
                .set_pos(self.get_pos()) \
                .draw(screen)

    def get_visualisation(self):
        return self.BPMNTaskViz(self)


class BPMNIntermediateEvent(Prototype):
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

    def __init__(self, model, incoming, outgoing, name, behavior, guard=None):
        super().__init__(model, incoming, outgoing, name)
        model.set_binding_priority(SimProblem.PRIORITY_QUEUE_BINDING)  # We process tokens in BPMN models FCFS

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

    def get_description(self):
        description = [(super().get_id() + ": BPMNIntermediateEvent", Describable.Style.HEADING)]
        return description

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
    """
    Generates a composition of SimVar and SimEvent that represents a BPMN end event.

    :param model: the SimProblem to which the event composition must be added.
    :param incoming: a list with one SimVar: a case SimVar.
    :param outgoing: parameter is only here for consistency, must be [].
    :param name: the name of the event.
    """

    def __init__(self, model, incoming, outgoing, name):
        super().__init__(model, incoming, outgoing, name)
        model.set_binding_priority(SimProblem.PRIORITY_QUEUE_BINDING)  # We process tokens in BPMN models FCFS

        if len(incoming) != 1:
            raise TypeError("Event " + name + ": must have one input parameter for cases.")
        if len(outgoing) != 0:
            raise TypeError("Event " + name + ": must not have output parameters.")

        self._marking = []
        result = model.add_event(incoming, outgoing, lambda c: self.behaviour(c), name=name + "<end_event>")
        self.add_event(result)

        model.add_prototype(self)

    def behaviour(self, c):
        """
        wrapper to count tokens that made it to the end event.
        """
        self._marking.append(SimToken(c))
        return []

    def get_description(self):
        description = [(super().get_id() + ": BPMNEndEvent", Describable.Style.HEADING)]
        description.append( (" ", Describable.Style.NORMAL) )
        description.append( ("Marking:", Describable.Style.NORMAL) )
        for token in self._marking:
            description.append( (str(token), Describable.Style.BOXED) )
        return description
    
    class BPMNEndEventViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            pygame.draw.circle(screen, vis.TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), self._width/2)
            pygame.draw.circle(screen, vis.TUE_BLUE, (self._pos[0], self._pos[1]), self._width/2, vis.LINE_WIDTH*2)
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)

            # draw tokens
            vis.TokenShower(self._model_node._marking) \
                .set_pos(self._pos) \
                .show_token_count(True) \
                .set_time(self._curr_time) \
                .draw(screen)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))

    def get_visualisation(self):
        return self.BPMNEndEventViz(self)


class BPMNFlow(SimVar):
    """
    A SimVar that represents a BPMN Flow.
    It is just a SimVar with a different visualisation.
    The flow can have a priority, which makes sense if the flow is the single flow into a BPMN task,
    the priority then determines the order in which cases are processed by the task. Default is FCFS.

    :param model: the SimProblem to which the event composition must be added.
    :param _id: the id of the flow.
    :param priority: the priority with which tokens on the flow are processed, defaults to FCFS.
    """

    def __init__(self, model, _id, priority=None):
        super().__init__(_id, priority=priority)
        model.set_binding_priority(SimProblem.PRIORITY_QUEUE_BINDING)  # We process tokens in BPMN models FCFS

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

            # draw tokens 
            vis.TokenShower(self._model_node.marking) \
                .show_token_count() \
                .set_pos(self._pos) \
                .set_time(self._curr_time) \
                .draw(screen)    

    def get_visualisation(self):
        return self.BPMNFlowViz(self)


class BPMNExclusiveSplitGateway(Prototype):
    """
    Generates a composition of SimVar and SimEvent that represents a BPMN exclusive split gateway.
    A choice has a single incoming flow (SimVar) and multiple outgoing flows (SimVar) to choose from.
    A behavior function must be specified that determines which outgoing flow is chosen.
    The behavior function must take a single input parameter, which is the incoming flow.
    The behavior function must return a list of SimToken, which are put on the outgoing flows. For outgoing flows that are not chosen, the behavior function must None. Exactly one SimToken must be returned for each outgoing flow.
    
    
    :param model: the SimProblem to which the event composition must be added.
    :param incoming: a list with exactly one SimVar: a case SimVar.
    :param outgoing: a list with at least two SimVar: a case SimVar.
    :param label: the label on the gateway.
    :param behavior: specifies the choice behavior of the gateway.
    """

    def __init__(self, model, incoming, outgoing, label, behavior):
        super().__init__(model, incoming, outgoing, label)
        model.set_binding_priority(SimProblem.PRIORITY_QUEUE_BINDING)  # We process tokens in BPMN models FCFS

        if len(incoming) != 1:
            raise TypeError("Gateway " + label + ": must have at exactly one input parameter for cases.")
        if len(outgoing) < 2:
            raise TypeError("Gateway " + label + ": must have at least two output parameter for cases.")
        if not callable(behavior):
            raise TypeError("Gateway " + label + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
        if len(inspect.signature(behavior).parameters) != 1:
            raise TypeError("Gateway " + label + ": the behavior function must have at exactly one input parameter for cases.")

        def behavior_encapsulation(c):
            # encapsulates the behavior to check if the behavior function returns a list of SimToken with the same length as the number of outgoing flows.
            result = behavior(c)
            if len(result) != len(outgoing):
                raise TypeError("Gateway " + label + ": the behavior function must return a list of SimToken with the same length as the number of outgoing flows.")
            count_tokens = 0
            for i in range(len(result)):
                if result[i] is not None:
                    if not isinstance(result[i], SimToken):
                        raise TypeError("Gateway " + label + ": the behavior function must return a list of SimToken. However, element " + str(i) + " is not a SimToken.")
                    count_tokens += 1
            if count_tokens != 1:
                raise TypeError("Gateway " + label + ": the behavior function must return a list of SimToken with exactly one SimToken. However, " + str(count_tokens) + " SimTokens were returned.")
            return result
        result = model.add_event(incoming, outgoing, behavior_encapsulation, name=label + "<xor_split>")
        self.add_event(result)

        model.add_prototype(self)

    def get_description(self):
        description = [(super().get_id() + ": BPMNExclusiveSplitGateway", Describable.Style.HEADING)]
        return description

    class BPMNExclusiveSplitGatewayViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            # draw a pygame diamond shape with TUE_BLUE outline and TUE_LIGHTBLUE fill
            x_pos, y_pos = int(self._pos[0] - self._width/2), int(self._pos[1] - self._height/2)
            pygame.draw.polygon(screen, vis.TUE_LIGHTBLUE, [(x_pos, y_pos + self._half_height), (x_pos + self._half_width, y_pos), (x_pos + self._width, y_pos + self._half_height), (x_pos + self._half_width, y_pos + self._height)])
            pygame.draw.polygon(screen, vis.TUE_BLUE, [(x_pos, y_pos + self._half_height), (x_pos + self._half_width, y_pos), (x_pos + self._width, y_pos + self._half_height), (x_pos + self._half_width, y_pos + self._height)], vis.LINE_WIDTH)
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)

            # # draw a big X inside the diamond
            pygame.draw.line(screen, vis.TUE_BLUE, (x_pos + 0.35*self._width, y_pos + 0.3*self._height), (x_pos + 0.65*self._width, y_pos + 0.7*self._height), 4*vis.LINE_WIDTH)
            pygame.draw.line(screen, vis.TUE_BLUE, (x_pos + 0.35*self._width, y_pos + 0.7*self._height), (x_pos + 0.65*self._width, y_pos + 0.3*self._height), 4*vis.LINE_WIDTH)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))

    def get_visualisation(self):
        return self.BPMNExclusiveSplitGatewayViz(self)


class BPMNExclusiveJoinGateway(Prototype):
    """
    Generates a composition of SimVar and SimEvent that represents a BPMN exclusive join gateway.
    A join gateway has multiple incoming flows and one outgoing flow.        
    
    :param model: the SimProblem to which the event composition must be added.
    :param incoming: a list with exactly one SimVar: a case SimVar.
    :param outgoing: a list with at least two SimVar: a case SimVar.
    :param label: the label on the gateway.
    """

    def __init__(self, model, incoming, outgoing, label):
        super().__init__(model, incoming, outgoing, label)
        model.set_binding_priority(SimProblem.PRIORITY_QUEUE_BINDING)  # We process tokens in BPMN models FCFS

        if len(incoming) < 2:
            raise TypeError("Gateway " + label + ": must have multiple input parameter for cases.")
        if len(outgoing) != 1:
            raise TypeError("Gateway " + label + ": must have exactly one output parameter for cases.")

        self._joiner = model.add_var(label + "_joiner")
        self.add_var(self._joiner)

        for i in range(len(incoming)):
            # create an event, connect it to the incoming flow and the joiner, add it to the model and to self
            result = model.add_event([incoming[i]], [self._joiner], lambda c: [SimToken(c)], name=label + "<joiner" + str(i) + ">")
            self.add_event(result)
        # create an event, connect it to the joiner and the outgoing flow, add it to the model and to self
        resutl = model.add_event([self._joiner], outgoing, lambda c: [SimToken(c)], name=label + "<joiner>")
        self.add_event(resutl)

        model.add_prototype(self)

    def get_description(self):
        description = [(super().get_id() + ": BPMNExclusiveJoinGateway", Describable.Style.HEADING)]
        return description
    
    class BPMNExclusiveJoinGatewayViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            # draw a pygame diamond shape with TUE_BLUE outline and TUE_LIGHTBLUE fill
            x_pos, y_pos = int(self._pos[0] - self._width/2), int(self._pos[1] - self._height/2)
            pygame.draw.polygon(screen, vis.TUE_LIGHTBLUE, [(x_pos, y_pos + self._half_height), (x_pos + self._half_width, y_pos), (x_pos + self._width, y_pos + self._half_height), (x_pos + self._half_width, y_pos + self._height)])
            pygame.draw.polygon(screen, vis.TUE_BLUE, [(x_pos, y_pos + self._half_height), (x_pos + self._half_width, y_pos), (x_pos + self._width, y_pos + self._half_height), (x_pos + self._half_width, y_pos + self._height)], vis.LINE_WIDTH)
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)
            bold_font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE, bold=True)

            # # draw a big X inside the diamond
            pygame.draw.line(screen, vis.TUE_BLUE, (x_pos + 0.35*self._width, y_pos + 0.3*self._height), (x_pos + 0.65*self._width, y_pos + 0.7*self._height), 4*vis.LINE_WIDTH)
            pygame.draw.line(screen, vis.TUE_BLUE, (x_pos + 0.35*self._width, y_pos + 0.7*self._height), (x_pos + 0.65*self._width, y_pos + 0.3*self._height), 4*vis.LINE_WIDTH)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))
            
            # draw marking
            mstr = "["
            ti = 0
            for token in self._model_node._joiner.marking:
                mstr += str(token.value) + "@" + str(round(token.time, 2))
                if ti < len(self._model_node._joiner.marking) - 1:
                    mstr += ", "
                ti += 1
            mstr += "]"
            label = bold_font.render(mstr, True, vis.TUE_RED)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH + int(label.get_height())
            screen.blit(label, (text_x_pos, text_y_pos))        

    def get_visualisation(self):
        return self.BPMNExclusiveJoinGatewayViz(self)


class BPMNParallelSplitGateway(SimEvent):
    """
    A SimVar that represents a parallel split gateway.
    It is just a SimEvent with a different visualisation.
    It must have a single incoming place and multiple outgoing places.
    Its behavior takes the data from the source place and passes it to each of its outgoing places.
    """

    def __init__(self, model, incoming, outgoing, label):
        super().__init__(label)
        model.set_binding_priority(SimProblem.PRIORITY_QUEUE_BINDING)  # We process tokens in BPMN models FCFS

        if len(incoming) != 1:
            raise TypeError("Gateway " + label + ": must have at exactly one input parameter for cases.")
        if len(outgoing) < 2:
            raise TypeError("Gateway " + label + ": must have at least two output parameter for cases.")

        self.set_inflow(incoming)
        self.set_outflow(outgoing)

        self.set_behavior(lambda c: [SimToken(c) for _ in range(len(outgoing))])

        model.add_prototype_event(self)

    def get_description(self):
        description = [(super().get_id() + ": BPMNParallelSplitGateway", Describable.Style.HEADING)]
        return description

    class BPMNParallelSplitGatewayViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            # draw a pygame diamond shape with TUE_BLUE outline and TUE_LIGHTBLUE fill
            x_pos, y_pos = int(self._pos[0] - self._width/2), int(self._pos[1] - self._height/2)
            pygame.draw.polygon(screen, vis.TUE_LIGHTBLUE, [(x_pos, y_pos + self._half_height), (x_pos + self._half_width, y_pos), (x_pos + self._width, y_pos + self._half_height), (x_pos + self._half_width, y_pos + self._height)])
            pygame.draw.polygon(screen, vis.TUE_BLUE, [(x_pos, y_pos + self._half_height), (x_pos + self._half_width, y_pos), (x_pos + self._width, y_pos + self._half_height), (x_pos + self._half_width, y_pos + self._height)], vis.LINE_WIDTH)
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)

            # # draw a big + inside the diamond
            pygame.draw.line(screen, vis.TUE_BLUE, (x_pos + self._half_width, y_pos + 0.2*self._height), (x_pos + self._half_width, y_pos + 0.8*self._height), 4*vis.LINE_WIDTH)
            pygame.draw.line(screen, vis.TUE_BLUE, (x_pos + 0.2*self._width, y_pos + self._half_height), (x_pos + 0.8*self._width, y_pos + self._half_height), 4*vis.LINE_WIDTH)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))
            
    def get_visualisation(self):
        return self.BPMNParallelSplitGatewayViz(self)
    

class BPMNParallelJoinGateway(SimEvent):
    """
    A SimVar that represents a parallel join gateway.
    It is just a SimEvent with a different visualisation.
    It must have multiple incoming places and a single outgoing place.
    Its behavior takes the data from one of the source places and passes it to the outgoing place.
    """

    def __init__(self, model, incoming, outgoing, label, behavior=None):
        super().__init__(label)
        model.set_binding_priority(SimProblem.PRIORITY_QUEUE_BINDING)  # We process tokens in BPMN models FCFS

        if len(incoming) < 2:
            raise TypeError("Gateway " + label + ": must have at least two input parameter for cases.")
        if len(outgoing) != 1:
            raise TypeError("Gateway " + label + ": must have at exactly one output parameter for cases.")

        self.set_inflow(incoming)
        self.set_outflow(outgoing)

        if behavior is not None:
            self.set_behavior(behavior)
        else:
            self.set_behavior(lambda *args: [SimToken(args[0])])
        
        # the transition must be fired for cases with the same case identifier
        self.set_guard(lambda *args: all([args[i][0] == args[0][0] for i in range(1,len(args))]))

        model.add_prototype_event(self)

    def get_description(self):
        description = [(super().get_id() + ": BPMNParallelJoinGateway", Describable.Style.HEADING)]
        return description

    class BPMNParallelJoinGatewayViz(vis.Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            # draw a pygame diamond shape with TUE_BLUE outline and TUE_LIGHTBLUE fill
            x_pos, y_pos = int(self._pos[0] - self._width/2), int(self._pos[1] - self._height/2)
            pygame.draw.polygon(screen, vis.TUE_LIGHTBLUE, [(x_pos, y_pos + self._half_height), (x_pos + self._half_width, y_pos), (x_pos + self._width, y_pos + self._half_height), (x_pos + self._half_width, y_pos + self._height)])
            pygame.draw.polygon(screen, vis.TUE_BLUE, [(x_pos, y_pos + self._half_height), (x_pos + self._half_width, y_pos), (x_pos + self._width, y_pos + self._half_height), (x_pos + self._half_width, y_pos + self._height)], vis.LINE_WIDTH)
            font = pygame.font.SysFont('Calibri', vis.TEXT_SIZE)

            # # draw a big + inside the diamond
            pygame.draw.line(screen, vis.TUE_BLUE, (x_pos + self._half_width, y_pos + 0.2*self._height), (x_pos + self._half_width, y_pos + 0.8*self._height), 4*vis.LINE_WIDTH)
            pygame.draw.line(screen, vis.TUE_BLUE, (x_pos + 0.2*self._width, y_pos + self._half_height), (x_pos + 0.8*self._width, y_pos + self._half_height), 4*vis.LINE_WIDTH)

            # draw label
            label = font.render(self._model_node.get_id(), True, vis.TUE_BLUE)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + vis.LINE_WIDTH
            screen.blit(label, (text_x_pos, text_y_pos))
            
    def get_visualisation(self):
        return self.BPMNParallelJoinGatewayViz(self)