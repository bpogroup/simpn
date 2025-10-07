import io
from enum import Enum
from xml.sax import handler, make_parser, InputSource, SAXException
from xml.sax.handler import ContentHandler


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
        self.incoming = []  # list of BPMNArc
        self.outgoing = []  # list of BPMNArc

    def add_incoming(self, arc):
        self.incoming.append(arc)

    def add_outgoing(self, arc):
        self.outgoing.append(arc)

    def set_type(self, ntype: NodeType):
        self.type = ntype

    def get_incoming(self):
        return self.incoming

    def get_outgoing(self):
        return self.outgoing


class BPMNArc:
    def __init__(self, name=None):
        self.name = name
        self.source = None
        self.target = None

    def set_source(self, node: BPMNNode):
        self.source = node

    def set_target(self, node: BPMNNode):
        self.target = node


class BPMNRole:
    def __init__(self, name: str):
        self.name = name
        self.resources = []
        self.contained_nodes = []

    def add_resource(self, r: str):
        if r:
            self.resources.append(r)

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

    def set_start_event(self, node: BPMNNode):
        self.start_event = node


class XMLErrorHandler(handler.ErrorHandler):
    def __init__(self):
        self._errors = []

    def error(self, exception):
        self._errors.append(str(exception))

    def fatalError(self, exception):
        self._errors.append(str(exception))

    def warning(self, exception):
        # collect warnings but don't fail
        self._errors.append(str(exception))

    def has_errors(self):
        return len(self._errors) > 0

    def errors_as_string(self):
        return "\n".join(self._errors)


class ConditionEvaluator:
    """Stub that mirrors the Java ConditionEvaluator.getInstance().validate(name).
    For now it always returns an empty list (no validation errors)."""
    @staticmethod
    def validate(name: str):
        return []


class BPMNParser(ContentHandler):
    def __init__(self):
        super().__init__()
        self.error_handler = XMLErrorHandler()
        self.has_pool = False
        self.role_being_parsed = None
        self.node_ref_being_parsed = None
        self.documentation_being_parsed = None
        self.role2contained_ids = {}
        self.id2node = {}
        self.arc2source_id = {}
        self.arc2target_id = {}
        self.result = BPMNModel()
        self.errors = []
        self.node_being_parsed = None

    # ContentHandler callbacks
    def startElement(self, name, attrs):
        qName = name
        # ignore some qNames like the Java code
        if (qName in ("definitions", "process", "extensionElements", "timerEventDefinition", "messageEventDefinition") or
                qName in ("outgoing", "incoming", "collaboration", "laneSet") or
                qName.startswith("signavio:") or qName.startswith("bpmndi:") or qName.startswith("omgdi:") or qName.startswith("omgdc:") or qName.startswith("conditionExpression")):
            return

        id_ = None
        if qName in ("startEvent", "intermediateCatchEvent", "endEvent", "task", "exclusiveGateway", "eventBasedGateway", "parallelGateway"):
            id_ = attrs.get("id")
            if id_ is None:
                self.result = None
                raise SAXException("Unexpected error: the model contains an event that has no identifier.")
            if id_ in self.id2node:
                self.result = None
                raise SAXException("Unexpected error: the model contains a two nodes with the same identifier.")

        if qName == "participant":
            if self.has_pool:
                self.errors.append("The model contains more than one pool.")
            else:
                self.has_pool = True
        elif qName == "lane":
            name_attr = attrs.get("name")
            if not name_attr:
                self.errors.append("The model contains a lane that has no name.")
            role = BPMNRole(name_attr or "")
            self.result.add_role(role)
            self.role_being_parsed = role
            self.role2contained_ids[role] = []
        elif qName == "flowNodeRef":
            self.node_ref_being_parsed = ""
        elif qName == "documentation":
            self.documentation_being_parsed = ""
        elif qName in ("startEvent", "endEvent", "intermediateCatchEvent", "task"):
            name_attr = attrs.get("name") or ""
            if qName == "startEvent":
                if len(name_attr) == 0:
                    self.errors.append("The model contains a start event that has no name.")
                node = BPMNNode(name_attr, NodeType.StartEvent)
            elif qName == "endEvent":
                if len(name_attr) == 0:
                    self.errors.append("The model contains an end event that has no name.")
                node = BPMNNode(name_attr, NodeType.EndEvent)
            elif qName == "intermediateCatchEvent":
                if len(name_attr) == 0:
                    self.errors.append("The model contains an intermediate event that has no name.")
                node = BPMNNode(name_attr, NodeType.IntermediateEvent)
            else:  # task
                if len(name_attr) == 0:
                    self.errors.append("The model contains a task that has no name.")
                node = BPMNNode(name_attr, NodeType.Task)
            self.node_being_parsed = node
            self.result.add_node(node)
            self.id2node[id_] = node
        elif qName == "exclusiveGateway":
            node = BPMNNode("", NodeType.ExclusiveSplit)
            self.result.add_node(node)
            self.id2node[id_] = node
        elif qName == "eventBasedGateway":
            node = BPMNNode("", NodeType.EventBasedGateway)
            self.result.add_node(node)
            self.id2node[id_] = node
        elif qName == "parallelGateway":
            node = BPMNNode("", NodeType.ParallelSplit)
            self.result.add_node(node)
            self.id2node[id_] = node
        elif qName == "sequenceFlow":
            name_attr = attrs.get("name")
            name_attr = None if (name_attr is None or len(name_attr) == 0) else name_attr
            if name_attr is not None:
                self.errors.extend(ConditionEvaluator.validate(name_attr))
            arc = BPMNArc(name_attr)
            self.result.add_arc(arc)
            source_ref = attrs.get("sourceRef")
            target_ref = attrs.get("targetRef")
            if (not source_ref) or (not target_ref):
                self.errors.append("The model contains an arc that is not connected at the beginning or at the end.")
            self.arc2source_id[arc] = source_ref
            self.arc2target_id[arc] = target_ref
        else:
            self.errors.append(f"The model contains an illegal model element: {qName}.")

    def characters(self, content):
        if self.node_ref_being_parsed is not None:
            self.node_ref_being_parsed += content
        elif self.documentation_being_parsed is not None:
            self.documentation_being_parsed += content

    def endElement(self, name):
        qName = name
        if qName == "lane":
            self.role_being_parsed = None
        elif qName == "flowNodeRef":
            if self.role_being_parsed is not None:
                self.role2contained_ids[self.role_being_parsed].append(self.node_ref_being_parsed.strip())
            self.node_ref_being_parsed = None
        elif qName == "documentation":
            if self.documentation_being_parsed is not None:
                for resource in self.documentation_being_parsed.split(','):
                    if self.role_being_parsed is not None:
                        self.role_being_parsed.add_resource(resource.strip())
            self.documentation_being_parsed = None
        elif qName in ("startEvent", "endEvent", "intermediateCatchEvent", "task", "exclusiveGateway", "eventBasedGateway", "parallelGateway"):
            self.node_being_parsed = None

    def connect_elements(self):
        # connect nodes to roles
        for role, ids in self.role2contained_ids.items():
            for cid in ids:
                node = self.id2node.get(cid)
                if node is None:
                    self.result = None
                    raise BPMNParseException(f"Unexpected error: lane '{role.name}' contains the identifier '{cid}' of a node that cannot be found." + ("" if not self.errors else " This may be caused by the following errors:\n" + self.errors_to_string()))
                role.add_contained_node(node)

        # connect arcs
        for arc, sid in self.arc2source_id.items():
            node = self.id2node.get(sid)
            if node is None:
                self.result = None
                raise BPMNParseException("Unexpected error: an arc contains the identifier of a node that cannot be found." + ("" if not self.errors else " This may be caused by the following errors:\n" + self.errors_to_string()))
            node.add_outgoing(arc)
            arc.set_source(node)

        for arc, tid in self.arc2target_id.items():
            node = self.id2node.get(tid)
            if node is None:
                self.result = None
                raise BPMNParseException("Unexpected error: an arc contains the identifier of a node that cannot be found." + ("" if not self.errors else " This may be caused by the following errors:\n" + self.errors_to_string()))
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

    def check_semantics(self):
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

        has_start = False
        for node in self.result.get_nodes():
            if node.type == NodeType.StartEvent:
                if has_start:
                    self.errors.append("The model contains multiple start events.")
                self.result.set_start_event(node)
                has_start = True
        if not has_start:
            self.errors.append("The model has no start event.")

    def errors_to_string(self):
        return "\n".join([f"- {e}" for e in self.errors])

    def parse_file(self, file_name: str):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                xml = f.read()
        except IOError as e:
            self.result = None
            raise BPMNParseException(f"An unexpected error occurred while reading the BPMN file '{file_name}'.") from e
        return self.parse(xml)

    def parse(self, xml: str):
        # reset state
        self.result = BPMNModel()
        self.error_handler = XMLErrorHandler()
        self.errors = []
        self.id2node = {}
        self.role2contained_ids = {}
        self.arc2source_id = {}
        self.arc2target_id = {}

        # parse XML using SAX
        parser = make_parser()
        parser.setContentHandler(self)
        parser.setErrorHandler(self.error_handler)
        try:
            src = InputSource()
            src.setCharacterStream(io.StringIO(xml))
            parser.parse(src)
        except SAXException as e:
            self.result = None
            raise BPMNParseException("An unexpected error occurred while reading the BPMN XML.") from e

        if self.error_handler.has_errors():
            self.result = None
            raise BPMNParseException("The BPMN XML contains unexpected errors:\n" + self.error_handler.errors_as_string())

        # connect and check
        self.connect_elements()
        self.check_semantics()
        if self.errors:
            self.result = None
            raise BPMNParseException("The BPMN Model contains the following error(s):\n" + self.errors_to_string())

        return self.result

    def get_parsed_model(self):
        return self.result
