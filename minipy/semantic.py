# Very small semantic analyzer: checks simple undefined variable usage.
from .ast_nodes import *
class CompilerError(Exception):
    pass

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]

    def enter(self):
        self.scopes.append({})

    def exit(self):
        self.scopes.pop()

    def insert(self, name):
        self.scopes[-1][name] = True

    def lookup(self, name):
        for s in reversed(self.scopes):
            if name in s:
                return True
        return False

class SemanticAnalyzer:
    def __init__(self):
        self.symtab = SymbolTable()
        # some builtins we allow by default
        self.symtab.insert("print")

    def analyze(self, node):
        try:
            self.visit(node)
            return True
        except CompilerError as e:
            print(f"Semantic error: {e}")
            return False

    def visit(self, node):
        method = getattr(self, f'visit_{type(node).__name__}', None)
        if method:
            return method(node)
        # default traversal
        for attr in getattr(node, "__dict__", {}):
            val = getattr(node, attr)
            if isinstance(val, list):
                for child in val:
                    if hasattr(child, "__dict__"):
                        self.visit(child)
            elif hasattr(val, "__dict__"):
                self.visit(val)

    def visit_Program(self, node: Program):
        for s in node.body:
            self.visit(s)

    def visit_AssignmentNode(self, node: AssignmentNode):
        # analyze RHS first
        self.visit(node.value)
        # declare LHS in current scope (no block-scoped shadowing)
        self.symtab.insert(node.name)

    def visit_IdentifierNode(self, node: IdentifierNode):
        if not self.symtab.lookup(node.name):
            raise CompilerError(f"Use of undeclared variable '{node.name}' at line {node.lineno}")

    def visit_FunctionDefNode(self, node: FunctionDefNode):
        # register function name in current scope
        self.symtab.insert(node.name)
        # enter function scope (function bodies are new lexical scopes)
        self.symtab.enter()
        for p in node.params or []:
            self.symtab.insert(p)
        for s in node.body or []:
            self.visit(s)
        self.symtab.exit()

    def visit_CallNode(self, node: CallNode):
        # allow calling functions; visit args
        if isinstance(node.func, IdentifierNode):
            # allow forward function calls; do not require function declared before use
            pass
        else:
            self.visit(node.func)
        for a in node.args or []:
            self.visit(a)

    def visit_IfNode(self, node: IfNode):
        # DO NOT create a new scope for if/elif/else blocks: assignments inside blocks
        # should be visible in the enclosing function/module scope (like Python).
        self.visit(node.condition)
        for s in node.then_body or []:
            self.visit(s)
        for cond, body in node.elifs or []:
            self.visit(cond)
            for s in body:
                self.visit(s)
        if node.else_body:
            for s in node.else_body:
                self.visit(s)

    def visit_WhileNode(self, node: WhileNode):
        # DO NOT create a new scope for while bodies for same reason as if
        self.visit(node.condition)
        for s in node.body or []:
            self.visit(s)

    def visit_ReturnNode(self, node: ReturnNode):
        if node.value:
            self.visit(node.value)

    def visit_BinaryOpNode(self, node: BinaryOpNode):
        self.visit(node.left)
        self.visit(node.right)

    def visit_NumberNode(self, node: NumberNode):
        pass

    def visit_StringNode(self, node: 'StringNode'):
        pass