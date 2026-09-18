"""
Semantic Analyzer for VCL.
Performs symbol resolution, scope analysis, duplicate/undeclared variable checks,
and basic type checking across the AST.
"""

from typing import List, Optional, Tuple
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
from backend.symbol_table import Symbol, SymbolTable
from backend.errors import Diagnostic, DiagnosticStage, DiagnosticSeverity, SemanticError


class SemanticAnalyzer:
    """
    Validates AST semantics, resolves identifiers to scopes, and infers types.
    """

    def __init__(self, symbol_table: Optional[SymbolTable] = None):
        self.symbol_table: SymbolTable = symbol_table or SymbolTable()
        self.diagnostics: List[Diagnostic] = []

    def analyze(self, program: Program) -> Tuple[SymbolTable, List[Diagnostic]]:
        """Runs full semantic analysis over the program AST."""
        self.diagnostics = []
        self.symbol_table.reset()
        self.visit(program)
        return self.symbol_table, self.diagnostics

    def _add_error(self, message: str, line: int, column: int, hint: Optional[str] = None) -> None:
        self.diagnostics.append(
            Diagnostic(
                stage=DiagnosticStage.SEMANTIC,
                message=message,
                line=line,
                column=column,
                severity=DiagnosticSeverity.ERROR,
                hint=hint,
            )
        )

    def visit(self, node: ASTNode) -> str:
        """Dispatches node visiting and returns the inferred type string ('int', 'float', 'bool', 'unknown')."""
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> str:
        return "unknown"

    def visit_Program(self, node: Program) -> str:
        for stmt in node.statements:
            self.visit(stmt)
        return "void"

    def visit_VarDeclaration(self, node: VarDeclaration) -> str:
        # Check for duplicate declaration in the current scope
        existing = self.symbol_table.lookup(node.name, current_only=True)
        if existing is not None:
            self._add_error(
                message=f"Duplicate declaration of identifier '{node.name}' in the same scope.",
                line=node.line,
                column=node.column,
                hint=f"Identifier '{node.name}' was already declared at line {existing.line}.",
            )

        inferred_type = self.visit(node.initializer)

        # Register symbol in symbol table
        symbol = Symbol(
            name=node.name,
            type_name=inferred_type,
            value=None,  # Value is populated during interpretation
            line=node.line,
            column=node.column,
        )
        self.symbol_table.define(symbol)
        return "void"

    def visit_Assignment(self, node: Assignment) -> str:
        symbol = self.symbol_table.lookup(node.target)
        if symbol is None:
            self._add_error(
                message=f"Cannot assign to undeclared identifier '{node.target}'.",
                line=node.line,
                column=node.column,
                hint=f"Declare '{node.target}' using 'let {node.target} = ...;' before assignment.",
            )
            val_type = self.visit(node.value)
            return "void"

        val_type = self.visit(node.value)
        # Type compatibility check (allow int/float coercion, but flag bool <-> number mismatch)
        if symbol.type_name != "unknown" and val_type != "unknown":
            if symbol.type_name == "bool" and val_type in ("int", "float"):
                self._add_error(
                    message=f"Type mismatch: cannot assign numeric type '{val_type}' to boolean variable '{node.target}'.",
                    line=node.line,
                    column=node.column,
                )
            elif symbol.type_name in ("int", "float") and val_type == "bool":
                self._add_error(
                    message=f"Type mismatch: cannot assign boolean to numeric variable '{node.target}'.",
                    line=node.line,
                    column=node.column,
                )
            elif symbol.type_name == "int" and val_type == "float":
                # In strict or educational typing, we can update or note
                symbol.type_name = "float"
        return "void"

    def visit_PrintStatement(self, node: PrintStatement) -> str:
        self.visit(node.expression)
        return "void"

    def visit_BlockStatement(self, node: BlockStatement) -> str:
        self.symbol_table.enter_scope(prefix="block")
        for stmt in node.statements:
            self.visit(stmt)
        self.symbol_table.exit_scope()
        return "void"

    def visit_IfStatement(self, node: IfStatement) -> str:
        cond_type = self.visit(node.condition)
        if cond_type != "bool" and cond_type != "unknown":
            self._add_error(
                message=f"Condition in 'if' statement must evaluate to a boolean, got '{cond_type}'.",
                line=node.condition.line,
                column=node.condition.column,
                hint="Use relational operators (e.g. '>', '==') or a boolean literal.",
            )
        self.visit(node.then_branch)
        if node.else_branch is not None:
            self.visit(node.else_branch)
        return "void"

    def visit_BinaryExpression(self, node: BinaryExpression) -> str:
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        op = node.operator

        # Arithmetic operators
        if op in ("+", "-", "*", "/", "%"):
            if left_type == "bool" or right_type == "bool":
                self._add_error(
                    message=f"Operator '{op}' cannot be applied to boolean operands.",
                    line=node.line,
                    column=node.column,
                    hint="Arithmetic operations are only valid for integers and floats.",
                )
                return "unknown"
            if left_type == "float" or right_type == "float":
                return "float"
            if left_type == "int" and right_type == "int":
                return "int"
            return "unknown"

        # Relational operators
        if op in ("<", ">", "<=", ">="):
            if left_type == "bool" or right_type == "bool":
                self._add_error(
                    message=f"Relational operator '{op}' cannot be applied to boolean operands.",
                    line=node.line,
                    column=node.column,
                )
            return "bool"

        # Equality operators
        if op in ("==", "!="):
            if (left_type == "bool" and right_type in ("int", "float")) or (
                right_type == "bool" and left_type in ("int", "float")
            ):
                self._add_error(
                    message=f"Cannot compare boolean with numeric type using '{op}'.",
                    line=node.line,
                    column=node.column,
                )
            return "bool"

        # Logical operators
        if op in ("&&", "||"):
            if (left_type != "bool" and left_type != "unknown") or (
                right_type != "bool" and right_type != "unknown"
            ):
                self._add_error(
                    message=f"Logical operator '{op}' requires boolean operands, got '{left_type}' and '{right_type}'.",
                    line=node.line,
                    column=node.column,
                )
            return "bool"

        return "unknown"

    def visit_UnaryExpression(self, node: UnaryExpression) -> str:
        operand_type = self.visit(node.operand)
        op = node.operator

        if op == "!":
            if operand_type != "bool" and operand_type != "unknown":
                self._add_error(
                    message=f"Logical NOT operator '!' requires boolean operand, got '{operand_type}'.",
                    line=node.line,
                    column=node.column,
                )
            return "bool"
        if op == "-":
            if operand_type == "bool":
                self._add_error(
                    message="Unary minus '-' cannot be applied to boolean operand.",
                    line=node.line,
                    column=node.column,
                )
                return "unknown"
            return operand_type

        return operand_type

    def visit_Literal(self, node: Literal) -> str:
        return node.raw_type

    def visit_Identifier(self, node: Identifier) -> str:
        symbol = self.symbol_table.lookup(node.name)
        if symbol is None:
            self._add_error(
                message=f"Undeclared identifier '{node.name}'.",
                line=node.line,
                column=node.column,
                hint=f"Ensure '{node.name}' is declared with 'let' before use.",
            )
            return "unknown"
        return symbol.type_name
