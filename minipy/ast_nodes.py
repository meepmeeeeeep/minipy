# AST node classes for miniPy (updated: StringNode added)
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Node:
    lineno: Optional[int] = None
    col: Optional[int] = None

@dataclass
class Program(Node):
    body: List[Node] = None

@dataclass
class NumberNode(Node):
    value: float = 0

@dataclass
class StringNode(Node):
    value: str = ""

@dataclass
class IdentifierNode(Node):
    name: str = ""

@dataclass
class BinaryOpNode(Node):
    left: Node = None
    operator: str = ""
    right: Node = None

@dataclass
class AssignmentNode(Node):
    name: str = ""
    value: Node = None

@dataclass
class IfNode(Node):
    condition: Node = None
    then_body: List[Node] = None
    elifs: List = None  # list of (condition, body)
    else_body: Optional[List[Node]] = None

@dataclass
class WhileNode(Node):
    condition: Node = None
    body: List[Node] = None

@dataclass
class FunctionDefNode(Node):
    name: str = ""
    params: List[str] = None
    body: List[Node] = None

@dataclass
class ReturnNode(Node):
    value: Optional[Node] = None

@dataclass
class CallNode(Node):
    func: Node = None   # IdentifierNode or expression
    args: List[Node] = None