from io import StringIO
import re
import xml.etree.ElementTree as ET
from enum import Enum
import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
import random


class BPMNParseException(Exception):
    pass


class NodeType(Enum):
    StartEvent = "StartEvent"
    EndEvent = "EndEvent"
    IntermediateEvent = "IntermediateEvent"
    Task = "Task"
    ExclusiveSplit = "ExclusiveSplit"
    ExclusiveJoin = "ExclusiveJoin"
    EventBasedGateway = "EventBasedGateway"
    ParallelSplit = "ParallelSplit"
    ParallelJoin = "ParallelJoin"


class BPMNNode:
    def __init__(self, name: str, ntype: NodeType):
        self.name = name
        self.type = ntype
        self.properties = {}
        self.incoming = []  # list of BPMNArc
        self.outgoing = []  # list of BPMNArc

    def add_incoming(self, arc):
        self.incoming.append(arc)

    def add_outgoing(self, arc):
        self.outgoing.append(arc)

    def set_type(self, ntype: NodeType):
        self.type = ntype
    
    def set_property(self, key: str, value):
        self.properties[key] = value

    def get_incoming(self):
        return self.incoming

    def get_outgoing(self):
        return self.outgoing


class BPMNArc:
    def __init__(self, probability=None):
        self.probability = probability
        self.source = None
        self.target = None

    def set_source(self, node: BPMNNode):
        self.source = node

    def set_target(self, node: BPMNNode):
        self.target = node


class BPMNRole:
    def __init__(self, name: str, nr_resources: int = 0):
        self.name = name
        self.nr_resources = nr_resources
        self.contained_nodes = []

    def set_nr_resources(self, nr: int):
        self.nr_resources = nr

    def add_contained_node(self, node: BPMNNode):
        self.contained_nodes.append(node)

    def get_contained_nodes(self):
        return self.contained_nodes


class BPMNModel:
    def __init__(self):
        self.roles = []
        self.nodes = []
        self.arcs = []
        self.start_event = None

    def add_role(self, role: BPMNRole):
        self.roles.append(role)

    def add_node(self, node: BPMNNode):
        self.nodes.append(node)

    def add_arc(self, arc: BPMNArc):
        self.arcs.append(arc)

    def get_roles(self):
        return self.roles

    def get_nodes(self):
        return self.nodes


def _choice_behavior(case, stable_probabilities):
    # A behavior function for exclusive gateways that selects an outgoing flow based on stable probabilities.
    # This is used by the BPMNParser transform method. It is not meant to be called directly.
    pick = random.uniform(0, 1)
    picked = False
    cumulative = 0.0
    result = [None] * len(stable_probabilities)
    for i, prob in enumerate(stable_probabilities):
        cumulative += prob
        if pick <= cumulative:
            result[i] = SimToken(case)
            picked = True
            break
    if not picked:
        result[-1] = SimToken(case)
    return result

class BPMNParser:
    """
    A parser for BPMN 2.0 XML files that can convert them into a simulatable SimProblem.
    This parser reads BPMN XML files, constructs an internal representation of the BPMN model,
    and provides a method to transform the model into a SimProblem using the simpn BPMN prototypes.
    The transformation includes: Lanes, Sequence Flows, Start Events, End Events, Tasks, Exclusive Gateways, and Parallel Gateways.
    TODO: Intermediate Events and Event-Based Gateways are not yet supported.

    **Example Usage**:
    ```python
    parser = BPMNParser()
    parser.parse_file("model.bpmn")
    sim_problem = parser.transform()
    ```
    """
    def __init__(self):
        self.result = BPMNModel()
        self.errors = []
        self.has_pool = False
        self.id2node = {}
        self.role2contained_ids = {}
        self.arc2source_id = {}
        self.arc2target_id = {}

    def _should_ignore(self, tag):
        # Exact match ignores
        if tag in ("definitions", "process", "extensionElements", "timerEventDefinition", 
                   "messageEventDefinition", "outgoing", "incoming", "collaboration", "laneSet",
                   "conditionExpression", "flowNodeRef", "documentation", "signavioMetaData",
                   "signavioDiagramMetaData", "property", "dataState"):
            return True
        
        # Prefix match ignores (case-insensitive for BPMN diagram elements)
        tag_lower = tag.lower()
        if (tag.startswith("signavio:") or tag.startswith("bpmndi:") or 
            tag.startswith("omgdi:") or tag.startswith("omgdc:") or
            tag_lower.startswith("bpmn")):  # BPMNDiagram, BPMNPlane, BPMNShape, BPMNEdge, etc.
            return True
        
        # Additional diagram-related elements
        if tag in ("Bounds", "waypoint", "Font"):
            return True
            
        return False

    def _parse_element(self, elem):
        # Parse a single XML element and update the BPMN model accordingly.
        tag = elem.tag
        
        # Ignore certain elements
        if self._should_ignore(tag):
            return

        if tag == "participant":
            if self.has_pool:
                self.errors.append("The model contains more than one pool.")
            else:
                self.has_pool = True
                
        elif tag == "lane":
            name = elem.get("name", "")
            nr_resources = 0
            if not name:
                self.errors.append("The model contains a lane that has no name.")
            # The name must have the form "role_name (nr_resources)"
            match = re.match(r"^(.*?)(?:\s*\((\d+)\))?$", name)
            if not match:
                self.errors.append(f"The lane name '{name}' is not valid. It must be of the form 'role_name (nr_resources)'.")
            else:
                role_name = match.group(1).strip()
                nr_resources_str = match.group(2)
                if nr_resources_str is not None:
                    try:
                        nr_resources = int(nr_resources_str)
                    except ValueError:
                        self.errors.append(f"The number of resources for lane '{name}' is not a valid integer.")
            role = BPMNRole(role_name, nr_resources)
            self.result.add_role(role)
            self.role2contained_ids[role] = []
            
            # Parse flowNodeRef children
            for child in elem:
                if child.tag == "flowNodeRef":
                    node_id = child.text.strip() if child.text else ""
                    if node_id:
                        self.role2contained_ids[role].append(node_id)
                        
        elif tag == "startEvent":
            name = elem.get("name", "")
            if not name:
                self.errors.append("The model contains a start event that has no name.")
            id_ = elem.get("id")
            if not id_:
                raise BPMNParseException("Unexpected error: the model contains an event that has no identifier.")
            if id_ in self.id2node:
                raise BPMNParseException("Unexpected error: the model contains two nodes with the same identifier.")
            # a start event must have a property child with name "interarrival_time"
            # this child must have a child dataState with a name which - when we call eval on it - evaluates to a number
            interarrival_time = elem.find("property[@name='interarrival_time']")
            data_state_name = ""
            if interarrival_time is None:
                self.errors.append(f"The model contains a start event '{name}' that has no property 'interarrival_time'.")
            else:
                data_state = interarrival_time.find("dataState")
                if data_state is None:
                    self.errors.append(f"The interarrival_time of start event '{name}' must have a 'dataState'.")
                else:
                    data_state_name = data_state.get("name", "")
                    # Check if the name evaluates to a number
                    try:
                        eval(data_state_name)
                    except:
                        self.errors.append(f"The interarrival_time of start event '{name}' does not evaluate to a number.")

            node = BPMNNode(name, NodeType.StartEvent)
            node.set_property("interarrival_time", data_state_name)
            self.result.add_node(node)
            self.id2node[id_] = node
            
        elif tag == "endEvent":
            name = elem.get("name", "")
            if not name:
                self.errors.append("The model contains an end event that has no name.")
            id_ = elem.get("id")
            if not id_:
                raise BPMNParseException("Unexpected error: the model contains an event that has no identifier.")
            if id_ in self.id2node:
                raise BPMNParseException("Unexpected error: the model contains two nodes with the same identifier.")
            node = BPMNNode(name, NodeType.EndEvent)
            self.result.add_node(node)
            self.id2node[id_] = node
            
        elif tag == "intermediateCatchEvent":
            name = elem.get("name", "")
            if not name:
                self.errors.append("The model contains an intermediate event that has no name.")
            id_ = elem.get("id")
            if not id_:
                raise BPMNParseException("Unexpected error: the model contains an event that has no identifier.")
            if id_ in self.id2node:
                raise BPMNParseException("Unexpected error: the model contains two nodes with the same identifier.")
            node = BPMNNode(name, NodeType.IntermediateEvent)
            self.result.add_node(node)
            self.id2node[id_] = node
            
        elif tag == "task":
            name = elem.get("name", "")
            if not name:
                self.errors.append("The model contains a task that has no name.")
            id_ = elem.get("id")
            if not id_:
                raise BPMNParseException("Unexpected error: the model contains an event that has no identifier.")
            if id_ in self.id2node:
                raise BPMNParseException("Unexpected error: the model contains two nodes with the same identifier.")
            # a task must have a property child with name "processing_time"
            # this child must have a child dataState with a name which - when we call eval on it - evaluates to a number
            processing_time = elem.find("property[@name='processing_time']")
            data_state_name = ""
            if processing_time is None:
                self.errors.append(f"The model contains a task '{name}' that has no property 'processing_time'.")
            else:
                data_state = processing_time.find("dataState")
                if data_state is None:
                    self.errors.append(f"The processing_time of task '{name}' must have a 'dataState'.")
                else:
                    data_state_name = data_state.get("name", "")
                    # Check if the name evaluates to a number
                    try:
                        eval(data_state_name)
                    except:
                        self.errors.append(f"The processing_time of task '{name}' does not evaluate to a number.")
            
            node = BPMNNode(name, NodeType.Task)
            node.set_property("processing_time", data_state_name)
            self.result.add_node(node)
            self.id2node[id_] = node
            
        elif tag == "exclusiveGateway":
            id_ = elem.get("id")
            if not id_:
                raise BPMNParseException("Unexpected error: the model contains an event that has no identifier.")
            if id_ in self.id2node:
                raise BPMNParseException("Unexpected error: the model contains two nodes with the same identifier.")
            node = BPMNNode("", NodeType.ExclusiveSplit)
            self.result.add_node(node)
            self.id2node[id_] = node
            
        elif tag == "eventBasedGateway":
            id_ = elem.get("id")
            if not id_:
                raise BPMNParseException("Unexpected error: the model contains an event that has no identifier.")
            if id_ in self.id2node:
                raise BPMNParseException("Unexpected error: the model contains two nodes with the same identifier.")
            node = BPMNNode("", NodeType.EventBasedGateway)
            self.result.add_node(node)
            self.id2node[id_] = node
            
        elif tag == "parallelGateway":
            id_ = elem.get("id")
            if not id_:
                raise BPMNParseException("Unexpected error: the model contains an event that has no identifier.")
            if id_ in self.id2node:
                raise BPMNParseException("Unexpected error: the model contains two nodes with the same identifier.")
            node = BPMNNode("", NodeType.ParallelSplit)
            self.result.add_node(node)
            self.id2node[id_] = node
            
        elif tag == "sequenceFlow":
            name = elem.get("name")
            probability = None
            if name is not None and len(name) > 0:
                # The name should be of the form "number%"
                if not re.match(r"^\d+%$", name):
                    self.errors.append(f"Invalid probability format for arc: {name}. Expected format is 'number%'.")
                else:
                    probability = int(name[:-1]) / 100.0
                    if probability < 0.0 or probability > 1.0:
                        self.errors.append(f"The probability for arc '{name}' must be between 0% and 100%.")
            arc = BPMNArc(probability)
            self.result.add_arc(arc)
            source_ref = elem.get("sourceRef")
            target_ref = elem.get("targetRef")
            if not source_ref or not target_ref:
                self.errors.append("The model contains an arc that is not connected at the beginning or at the end.")
            self.arc2source_id[arc] = source_ref
            self.arc2target_id[arc] = target_ref
        else:
            # Report error for unrecognized/illegal elements
            self.errors.append(f"The model contains an illegal model element: {tag}.")

    def _traverse_tree(self, elem):
        """Recursively traverse the XML tree."""
        self._parse_element(elem)
        for child in elem:
            self._traverse_tree(child)

    def _connect_elements(self):
        # connect nodes to roles
        for role, ids in self.role2contained_ids.items():
            for cid in ids:
                node = self.id2node.get(cid)
                if node is None:
                    self.result = None
                    raise BPMNParseException(f"Unexpected error: lane '{role.name}' contains the identifier '{cid}' of a node that cannot be found." + ("" if not self.errors else " This may be caused by the following errors:\n" + self._errors_to_string()))
                role.add_contained_node(node)

        # connect arcs
        for arc, sid in self.arc2source_id.items():
            node = self.id2node.get(sid)
            if node is None:
                self.result = None
                raise BPMNParseException("Unexpected error: an arc contains the identifier of a node that cannot be found." + ("" if not self.errors else " This may be caused by the following errors:\n" + self._errors_to_string()))
            node.add_outgoing(arc)
            arc.set_source(node)

        for arc, tid in self.arc2target_id.items():
            node = self.id2node.get(tid)
            if node is None:
                self.result = None
                raise BPMNParseException("Unexpected error: an arc contains the identifier of a node that cannot be found." + ("" if not self.errors else " This may be caused by the following errors:\n" + self._errors_to_string()))
            node.add_incoming(arc)
            arc.set_target(node)

        # classify gateways as join or split
        for node in self.result.get_nodes():
            if node.type in (NodeType.ExclusiveSplit, NodeType.ParallelSplit):
                if len(node.get_incoming()) > 1 and len(node.get_outgoing()) == 1:
                    if node.type == NodeType.ParallelSplit:
                        node.set_type(NodeType.ParallelJoin)
                    else:
                        node.set_type(NodeType.ExclusiveJoin)

    def _check_semantics(self):
        if len(self.result.get_roles()) == 0:
            self.errors.append("The model has no roles.")

        role_names = set()
        for role in self.result.get_roles():
            if role.name in role_names:
                self.errors.append(f"There are two roles that have the name '{role.name}'.")
            role_names.add(role.name)

        element_names = set()
        for node in self.result.get_nodes():
            if node.type in (NodeType.Task, NodeType.StartEvent, NodeType.IntermediateEvent):
                if node.name in element_names:
                    self.errors.append(f"There are two elements in the model that have the name '{node.name}'.")
                element_names.add(node.name)

        for node in self.result.get_nodes():
            in_role = False
            for role in self.result.get_roles():
                if node in role.get_contained_nodes():
                    in_role = True
                    break
            if not in_role:
                if node.type == NodeType.Task:
                    self.errors.append(f"The task '{node.name}' is not contained in a lane.")
                else:
                    self.errors.append("There is a node that is not contained in a lane.")

        for node in self.result.get_nodes():
            inc = len(node.get_incoming())
            out = len(node.get_outgoing())
            if node.type == NodeType.Task:
                if inc == 0:
                    self.errors.append(f"Task '{node.name}' has no incoming arc.")
                if out != 1:
                    self.errors.append(f"Task '{node.name}' does not have exactly one outgoig arc.")
            elif node.type == NodeType.IntermediateEvent:
                if inc == 0:
                    self.errors.append(f"Intermediate event '{node.name}' has no incoming arc.")
                elif inc > 1:
                    self.errors.append(f"Intermediate event '{node.name}' has multiple incoming arcs.")
                if out != 1:
                    self.errors.append(f"Intermediate event '{node.name}' does not have exactly one outgoig arc.")
            elif node.type == NodeType.StartEvent:
                if inc != 0 or out != 1:
                    self.errors.append(f"Start event '{node.name}' does not have exactly one outgoing arc and zero incoming arcs.")
            elif node.type == NodeType.EndEvent:
                if inc != 1 or out != 0:
                    self.errors.append(f"End event '{node.name}' does not have exactly one incoming arc and zero outgoing arcs.")
            elif node.type == NodeType.EventBasedGateway:
                if inc == 0:
                    self.errors.append("The model contains an event based gateway that has no incoming arc.")
                if out < 2:
                    self.errors.append("The model contains an event based gateway that has les than two outgoing arcs.")
            elif node.type in (NodeType.ParallelJoin, NodeType.ParallelSplit):
                if inc == 0:
                    self.errors.append("The model contains a parallel gateway without incoming arcs.")
                if out == 0:
                    self.errors.append("The model contains a parallel gateway without outgoing arcs.")
                if inc == 1 and out == 1:
                    self.errors.append("The model contains a parallel gateway with only one incoming and one outgoing arc.")
                if inc > 1 and out > 1:
                    self.errors.append("The model contains a parallel gateway with multiple incoming and outgoing arcs.")
            elif node.type in (NodeType.ExclusiveJoin, NodeType.ExclusiveSplit):
                if inc == 0:
                    self.errors.append("The model contains an exclusive gateway without incoming arcs.")
                if out == 0:
                    self.errors.append("The model contains an exclusive gateway without outgoing arcs.")
                if inc == 1 and out == 1:
                    self.errors.append("The model contains an exclusive gateway with only one incoming and one outgoing arc.")
                if inc > 1 and out > 1:
                    self.errors.append("The model contains an exclusive gateway with multiple incoming and outgoing arcs.")

        if len([node for node in self.result.get_nodes() if node.type == NodeType.StartEvent]) == 0:
            self.errors.append("The model has no start event.")

    def _errors_to_string(self):
        return "\n".join([f"- {e}" for e in self.errors])

    def parse_file(self, file_name: str):
        """
        Parse a BPMN 2.0 XML file and construct the internal BPMN model representation.

        :param file_name: The path to the BPMN XML file.
        :raises BPMNParseException: If an error occurs during parsing or if the model is invalid.
        """
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                xml = f.read()
        except IOError as e:
            self.result = None
            raise BPMNParseException(f"An unexpected error occurred while reading the BPMN file '{file_name}'.") from e

        # Reset state
        self.result = BPMNModel()
        self.errors = []
        self.id2node = {}
        self.role2contained_ids = {}
        self.arc2source_id = {}
        self.arc2target_id = {}
        self.has_pool = False

        # Parse XML using ElementTree
        try:
            it = ET.iterparse(StringIO(xml))
            for _, el in it:
                _, _, el.tag = el.tag.rpartition('}') # strip ns
            root = it.root
        except ET.ParseError as e:
            self.result = None
            raise BPMNParseException(f"An unexpected error occurred while reading the BPMN XML: {str(e)}") from e

        # Traverse the XML tree
        self._traverse_tree(root)

        # Connect and check
        self._connect_elements()
        self._check_semantics()
        if self.errors:
            self.result = None
            raise BPMNParseException("The BPMN Model contains the following error(s):\n" + self._errors_to_string())

        return self.result

    def transform(self):
        """
        Transform the parsed BPMN model into a simulation model (SimProblem).
        
        :return: A SimProblem instance representing the executable simulation model.
        :raises BPMNParseException: If no BPMN model has been parsed, or if a task/event is not contained in any role/lane.
        """        
        if self.result is None:
            raise BPMNParseException("No BPMN model has been parsed yet. Call parse() or parse_file() first.")
        
        # Create the simulation problem
        sim_problem = SimProblem()
        
        # Create resources for each role (lane)
        role_resources = {}
        for role in self.result.get_roles():
            resource = sim_problem.add_var(role.name)
            # Add resource tokens based on nr_resources (default to 1 if not set)
            nr_resources = role.nr_resources if role.nr_resources > 0 else 1
            for i in range(1, nr_resources + 1):
                resource.put(i)
            role_resources[role] = resource
        
        # Create flows for each arc
        arc_flows = {}
        arc_counter = 0
        for arc in self.result.arcs:
            # Generate a unique flow name based on source and target
            source_name = arc.source.name if arc.source and arc.source.name else "unknown"
            target_name = arc.target.name if arc.target and arc.target.name else "unknown"
            flow_name = f"{source_name}_to_{target_name}_{arc_counter}"
            arc_counter += 1
            flow = prototype.BPMNFlow(sim_problem, flow_name)
            arc_flows[arc] = flow
        
        # Helper function to find the role containing a node
        def get_node_role(node):
            for role in self.result.get_roles():
                if node in role.get_contained_nodes():
                    return role
            return None
        
        # Create BPMN elements for each node
        for node in self.result.get_nodes():
            incoming_flows = [arc_flows[arc] for arc in node.get_incoming()]
            outgoing_flows = [arc_flows[arc] for arc in node.get_outgoing()]
            
            if node.type == NodeType.StartEvent:
                def interarrival_time_factory(duration):
                    return eval("lambda: " + duration)
                interarrival_time_expression = node.properties.get("interarrival_time")
                prototype.BPMNStartEvent(
                    sim_problem, 
                    [], 
                    outgoing_flows, 
                    node.name, 
                    interarrival_time_factory(interarrival_time_expression)
                )
            
            elif node.type == NodeType.EndEvent:
                prototype.BPMNEndEvent(
                    sim_problem, 
                    incoming_flows, 
                    [], 
                    name=node.name
                )
            
            elif node.type == NodeType.Task:
                # Get the resource for this task's role
                role = get_node_role(node)
                if role is None:
                    raise BPMNParseException(f"Task '{node.name}' is not in any role/lane.")
                resource = role_resources[role]

                def processing_time_factory(duration):
                    return eval("lambda: " + duration)
                processing_time_expression = node.properties.get("processing_time")
                default_behavior = lambda case, res: [SimToken((case, res), delay=processing_time_factory(processing_time_expression)())]

                prototype.BPMNTask(
                    sim_problem,
                    [incoming_flows[0], resource],
                    [outgoing_flows[0], resource],
                    node.name,
                    default_behavior
                )
            
            elif node.type == NodeType.IntermediateEvent:
                raise BPMNParseException("Intermediate events are not yet supported in the transformation.")
            
            elif node.type == NodeType.ExclusiveSplit:
                def choice_factory(outgoing_probabilities):
                    # A factory for the choice behavior based on arc probabilities.
                    # Takes a list of probabilities corresponding to outgoing flows.
                    # Returns a function that takes a case as input and returns a list of SimToken(case)
                    # of len(outgoing_probabilities), with only one SimToken for the chosen flow the rest None.
                    return eval("lambda case: _choice_behavior(case, " + str(outgoing_probabilities) + ")")
                
                outgoing_flow_probabilities = []
                for arc in node.get_outgoing():
                    prob = arc.probability if arc.probability is not None else 0.0
                    outgoing_flow_probabilities.append(prob)

                prototype.BPMNExclusiveSplitGateway(
                    sim_problem,
                    incoming_flows,
                    outgoing_flows,
                    node.name if node.name else "xor split",
                    behavior=choice_factory(outgoing_flow_probabilities)
                )
            
            elif node.type == NodeType.ExclusiveJoin:
                prototype.BPMNExclusiveJoinGateway(
                    sim_problem,
                    incoming_flows,
                    outgoing_flows,
                    node.name if node.name else "xor join"
                )
            
            elif node.type == NodeType.ParallelSplit:
                prototype.BPMNParallelSplitGateway(
                    sim_problem,
                    incoming_flows,
                    outgoing_flows,
                    node.name if node.name else "and split"
                )
            
            elif node.type == NodeType.ParallelJoin:
                prototype.BPMNParallelJoinGateway(
                    sim_problem,
                    incoming_flows,
                    outgoing_flows,
                    node.name if node.name else "and join"
                )
            
            elif node.type == NodeType.EventBasedGateway:
                raise BPMNParseException("Event-based gateways are not yet supported in the transformation.")
        
        return sim_problem