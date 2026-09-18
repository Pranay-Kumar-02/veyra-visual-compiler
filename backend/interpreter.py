"""
Tree-walking AST Interpreter for VCL.
Evaluates the Abstract Syntax Tree, updates the Symbol Table with runtime values,
captures program output, and detects runtime errors such as division by zero.
"""

from typing import Any, List, Optional, Tuple
from backend.ast_nodes import (
    ASTNode,
    Program,
    VarDeclaration,
    Assignment,
    PrintStatement,
    IfStatement,
    BlockStatement,
    BinaryExpression,
    UnaryExpression,
    Literal,
    Identifier,
)
from backend.symbol_table import SymbolTable
from backend.errors import RuntimeCompilerError


class Environment:
    """Runtime environment storing active variable bindings with scope hierarchy."""

    def __init__(self, parent: Optional["Environment"] = None):
        self.parent: Optional["Environment"] = parent
        self.values: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def assign(self, name: str, value: Any) -> bool:
        if name in self.values:
            self.values[name] = value
            return True
        if self.parent is not None:
            return self.parent.assign(name, value)
        return False

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        return None


class Interpreter:
    """
    Evaluates VCL AST nodes and maintains execution state.
    """

    def __init__(self, symbol_table: Optional[SymbolTable] = None):
        self.symbol_table: SymbolTable = symbol_table or SymbolTable()
        self.output: List[str] = []
        self.global_env = Environment()
        self.env = self.global_env

    def interpret(self, program: Program) -> Tuple[List[str], SymbolTable]:
        """Executes the program AST and returns (output_lines, updated_symbol_table)."""
        self.output = []
        self.global_env = Environment()
        self.env = self.global_env

        for stmt in program.statements:
            self.execute(stmt)

        return self.output, self.symbol_table

    def execute(self, node: ASTNode) -> Any:
        method_name = f"exec_{node.__class__.__name__}"
        executor = getattr(self, method_name, self.generic_exec)
        return executor(node)

    def generic_exec(self, node: ASTNode) -> Any:
        return None

    def exec_Program(self, node: Program) -> None:
        for stmt in node.statements:
            self.execute(stmt)

    def exec_VarDeclaration(self, node: VarDeclaration) -> None:
        value = self.evaluate(node.initializer)
        self.env.define(node.name, value)

        # Infer type name for the value
        val_type = "int" if isinstance(value, int) and not isinstance(value, bool) else (
            "float" if isinstance(value, float) else ("bool" if isinstance(value, bool) else "unknown")
        )
        self.symbol_table.update(node.name, value, val_type)

    def exec_Assignment(self, node: Assignment) -> None:
        value = self.evaluate(node.value)
        assigned = self.env.assign(node.target, value)
        if not assigned:
            # Fallback define if not present
            self.env.define(node.target, value)

        val_type = "int" if isinstance(value, int) and not isinstance(value, bool) else (
            "float" if isinstance(value, float) else ("bool" if isinstance(value, bool) else "unknown")
        )
        self.symbol_table.update(node.target, value, val_type)

    def exec_PrintStatement(self, node: PrintStatement) -> None:
        value = self.evaluate(node.expression)
        if isinstance(value, bool):
            formatted = "true" if value else "false"
        elif isinstance(value, float):
            # If float is an exact integer representation like 20.0, format cleanly
            formatted = str(int(value)) if value.is_integer() else str(value)
        else:
            formatted = str(value)
        self.output.append(formatted)

    def exec_BlockStatement(self, node: BlockStatement) -> None:
        previous_env = self.env
        try:
            self.env = Environment(parent=previous_env)
            for stmt in node.statements:
                self.execute(stmt)
        finally:
            self.env = previous_env

    def exec_IfStatement(self, node: IfStatement) -> None:
        condition_val = self.evaluate(node.condition)
        if condition_val is True:
            self.execute(node.then_branch)
        elif node.else_branch is not None:
            self.execute(node.else_branch)

    # -------------------------------------------------------------------------
    # Expression Evaluation
    # -------------------------------------------------------------------------

    def evaluate(self, node: ASTNode) -> Any:
        method_name = f"eval_{node.__class__.__name__}"
        evaluator = getattr(self, method_name, self.generic_eval)
        return evaluator(node)

    def generic_eval(self, node: ASTNode) -> Any:
        return None

    def eval_Literal(self, node: Literal) -> Any:
        return node.value

    def eval_Identifier(self, node: Identifier) -> Any:
        val = self.env.get(node.name)
        if val is None:
            # Check symbol table as fallback
            sym = self.symbol_table.lookup(node.name)
            if sym and sym.value is not None:
                return sym.value
            raise RuntimeCompilerError(
                message=f"Variable '{node.name}' has not been initialized.",
                line=node.line,
                column=node.column,
            )
        return val

    def eval_UnaryExpression(self, node: UnaryExpression) -> Any:
        operand = self.evaluate(node.operand)
        if node.operator == "-":
            return -operand
        if node.operator == "!":
            return not bool(operand)
        raise RuntimeCompilerError(
            message=f"Unsupported unary operator '{node.operator}'.",
            line=node.line,
            column=node.column,
        )

    def eval_BinaryExpression(self, node: BinaryExpression) -> Any:
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        op = node.operator

        # Arithmetic
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise RuntimeCompilerError(
                    message="Division by zero encountered during execution.",
                    line=node.line,
                    column=node.column,
                    hint="Ensure divisor expression does not evaluate to 0.",
                )
            # If both are int and evenly divisible, return int for clean VCL integer arithmetic
            res = left / right
            if isinstance(left, int) and isinstance(right, int) and left % right == 0:
                return int(res)
            return res
        if op == "%":
            if right == 0:
                raise RuntimeCompilerError(
                    message="Modulo by zero encountered during execution.",
                    line=node.line,
                    column=node.column,
                    hint="Ensure modulo divisor expression does not evaluate to 0.",
                )
            return left % right

        # Relational
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        if op == ">=":
            return left >= right

        # Logical
        if op == "&&":
            return bool(left) and bool(right)
        if op == "||":
            return bool(left) or bool(right)

        raise RuntimeCompilerError(
            message=f"Unknown binary operator '{op}'.",
            line=node.line,
            column=node.column,
        )
