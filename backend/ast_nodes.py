"""
Typed Abstract Syntax Tree (AST) node hierarchy for VCL.
Each node preserves source coordinates and provides a rich to_dict() structure
for visual tree rendering in the frontend.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ASTNode(ABC):
    """Abstract base class for all AST nodes in VCL."""

    def __init__(self, line: int, column: int):
        self.line = line
        self.column = column

    @abstractmethod
    def accept(self, visitor: Any) -> Any:
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serializes the AST node into a hierarchical structure for the visualizer."""
        pass


class Program(ASTNode):
    """Root node containing the list of statements in a VCL program."""

    def __init__(self, statements: List[ASTNode], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.statements: List[ASTNode] = statements

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_program(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Program",
            "label": "Program",
            "line": self.line,
            "column": self.column,
            "details": f"{len(self.statements)} statement(s)",
            "children": [stmt.to_dict() for stmt in self.statements],
        }


class VarDeclaration(ASTNode):
    """Variable declaration statement: let <name> = <initializer>;"""

    def __init__(self, name: str, initializer: ASTNode, line: int, column: int):
        super().__init__(line, column)
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_var_declaration(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "VarDeclaration",
            "label": f"let {self.name}",
            "name": self.name,
            "line": self.line,
            "column": self.column,
            "details": f"Identifier: {self.name}",
            "children": [self.initializer.to_dict()],
        }


class Assignment(ASTNode):
    """Variable reassignment statement: <target> = <value>;"""

    def __init__(self, target: str, value: ASTNode, line: int, column: int):
        super().__init__(line, column)
        self.target = target
        self.value = value

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_assignment(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Assignment",
            "label": f"{self.target} =",
            "target": self.target,
            "line": self.line,
            "column": self.column,
            "details": f"Target: {self.target}",
            "children": [self.value.to_dict()],
        }


class PrintStatement(ASTNode):
    """Print statement: print(<expression>);"""

    def __init__(self, expression: ASTNode, line: int, column: int):
        super().__init__(line, column)
        self.expression = expression

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_print_statement(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "PrintStatement",
            "label": "print()",
            "line": self.line,
            "column": self.column,
            "details": "Print expression to output",
            "children": [self.expression.to_dict()],
        }


class BlockStatement(ASTNode):
    """Block of statements enclosed in braces: { <statements> }"""

    def __init__(self, statements: List[ASTNode], line: int, column: int):
        super().__init__(line, column)
        self.statements = statements

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_block_statement(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "BlockStatement",
            "label": "Block { }",
            "line": self.line,
            "column": self.column,
            "details": f"{len(self.statements)} statement(s)",
            "children": [s.to_dict() for s in self.statements],
        }


class IfStatement(ASTNode):
    """Conditional statement: if (<condition>) <then_branch> [else <else_branch>]"""

    def __init__(
        self,
        condition: ASTNode,
        then_branch: ASTNode,
        else_branch: Optional[ASTNode],
        line: int,
        column: int,
    ):
        super().__init__(line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_if_statement(self)

    def to_dict(self) -> Dict[str, Any]:
        children = [
            {"node_type": "ConditionBranch", "label": "Condition", "line": self.line, "column": self.column, "children": [self.condition.to_dict()]},
            {"node_type": "ThenBranch", "label": "Then", "line": self.then_branch.line, "column": self.then_branch.column, "children": [self.then_branch.to_dict()]},
        ]
        if self.else_branch:
            children.append(
                {"node_type": "ElseBranch", "label": "Else", "line": self.else_branch.line, "column": self.else_branch.column, "children": [self.else_branch.to_dict()]}
            )
        return {
            "node_type": "IfStatement",
            "label": "if (...) ",
            "line": self.line,
            "column": self.column,
            "details": "Conditional branching",
            "children": children,
        }


class BinaryExpression(ASTNode):
    """Binary operations: +, -, *, /, %, ==, !=, <, >, <=, >=, &&, ||"""

    def __init__(
        self,
        left: ASTNode,
        operator: str,
        right: ASTNode,
        line: int,
        column: int,
    ):
        super().__init__(line, column)
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_binary_expression(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "BinaryExpression",
            "label": f"Op: {self.operator}",
            "operator": self.operator,
            "line": self.line,
            "column": self.column,
            "details": f"Operator: '{self.operator}'",
            "children": [self.left.to_dict(), self.right.to_dict()],
        }


class UnaryExpression(ASTNode):
    """Unary operations: -, !"""

    def __init__(self, operator: str, operand: ASTNode, line: int, column: int):
        super().__init__(line, column)
        self.operator = operator
        self.operand = operand

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_unary_expression(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "UnaryExpression",
            "label": f"Unary: {self.operator}",
            "operator": self.operator,
            "line": self.line,
            "column": self.column,
            "details": f"Operator: '{self.operator}'",
            "children": [self.operand.to_dict()],
        }


class Literal(ASTNode):
    """Literal values: Integer, Float, Boolean"""

    def __init__(self, value: Any, raw_type: str, line: int, column: int):
        super().__init__(line, column)
        self.value = value
        self.raw_type = raw_type

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_literal(self)

    def to_dict(self) -> Dict[str, Any]:
        val_str = str(self.value)
        if isinstance(self.value, bool):
            val_str = "true" if self.value else "false"
        return {
            "node_type": "Literal",
            "label": val_str,
            "value": self.value,
            "raw_type": self.raw_type,
            "line": self.line,
            "column": self.column,
            "details": f"Type: {self.raw_type}, Val: {val_str}",
            "children": [],
        }


class Identifier(ASTNode):
    """Variable reference: <name>"""

    def __init__(self, name: str, line: int, column: int):
        super().__init__(line, column)
        self.name = name

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_identifier(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Identifier",
            "label": self.name,
            "name": self.name,
            "line": self.line,
            "column": self.column,
            "details": f"Identifier '{self.name}'",
            "children": [],
        }
