"""
Three-Address Code (3AC) Intermediate Representation (IR) for VCL.
Translates a validated AST into a linear stream of intermediate instructions
with explicit temporaries, labels, jumps, and operator operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

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


@dataclass
class IRInstruction(ABC):
    """Abstract base class for all 3AC intermediate instructions."""

    line: int = 0
    column: int = 0

    @abstractmethod
    def to_text(self) -> str:
        """Human-readable 3AC instruction format."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Structured dictionary serialization for API and UI rendering."""
        pass

    def __str__(self) -> str:
        return self.to_text()


@dataclass
class CopyInstruction(IRInstruction):
    """Variable or temp assignment: result = source"""

    result: str = ""
    source: str = ""

    def to_text(self) -> str:
        return f"{self.result} = {self.source}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "copy",
            "op": "=",
            "result": self.result,
            "arg1": self.source,
            "arg2": None,
            "formatted": self.to_text(),
            "line": self.line,
            "column": self.column,
        }


@dataclass
class BinaryOpInstruction(IRInstruction):
    """Binary operation: result = left op right"""

    result: str = ""
    op: str = ""
    left: str = ""
    right: str = ""

    def to_text(self) -> str:
        return f"{self.result} = {self.left} {self.op} {self.right}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "binary",
            "op": self.op,
            "result": self.result,
            "arg1": self.left,
            "arg2": self.right,
            "formatted": self.to_text(),
            "line": self.line,
            "column": self.column,
        }


@dataclass
class UnaryOpInstruction(IRInstruction):
    """Unary operation: result = op operand"""

    result: str = ""
    op: str = ""
    operand: str = ""

    def to_text(self) -> str:
        return f"{self.result} = {self.op}{self.operand}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "unary",
            "op": self.op,
            "result": self.result,
            "arg1": self.operand,
            "arg2": None,
            "formatted": self.to_text(),
            "line": self.line,
            "column": self.column,
        }


@dataclass
class LabelInstruction(IRInstruction):
    """Branch label target: name:"""

    name: str = ""

    def to_text(self) -> str:
        return f"{self.name}:"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "label",
            "op": "label",
            "result": self.name,
            "arg1": None,
            "arg2": None,
            "formatted": self.to_text(),
            "line": self.line,
            "column": self.column,
        }


@dataclass
class JumpInstruction(IRInstruction):
    """Unconditional jump: goto target"""

    target: str = ""

    def to_text(self) -> str:
        return f"goto {self.target}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "jump",
            "op": "goto",
            "result": self.target,
            "arg1": None,
            "arg2": None,
            "formatted": self.to_text(),
            "line": self.line,
            "column": self.column,
        }


@dataclass
class JumpIfFalseInstruction(IRInstruction):
    """Conditional jump when condition is false: if_false condition goto target"""

    condition: str = ""
    target: str = ""

    def to_text(self) -> str:
        return f"if_false {self.condition} goto {self.target}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "cond_jump_false",
            "op": "if_false",
            "result": self.target,
            "arg1": self.condition,
            "arg2": None,
            "formatted": self.to_text(),
            "line": self.line,
            "column": self.column,
        }


@dataclass
class JumpIfTrueInstruction(IRInstruction):
    """Conditional jump when condition is true: if_true condition goto target"""

    condition: str = ""
    target: str = ""

    def to_text(self) -> str:
        return f"if_true {self.condition} goto {self.target}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "cond_jump_true",
            "op": "if_true",
            "result": self.target,
            "arg1": self.condition,
            "arg2": None,
            "formatted": self.to_text(),
            "line": self.line,
            "column": self.column,
        }


@dataclass
class PrintInstruction(IRInstruction):
    """Standard output emission: print value"""

    value: str = ""

    def to_text(self) -> str:
        return f"print {self.value}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "print",
            "op": "print",
            "result": None,
            "arg1": self.value,
            "arg2": None,
            "formatted": self.to_text(),
            "line": self.line,
            "column": self.column,
        }


@dataclass
class IRProgram:
    """Complete Three-Address Code program representation."""

    instructions: List[IRInstruction]
    temp_count: int
    label_count: int

    def to_text(self) -> str:
        """Returns formatted, readable 3AC source text."""
        lines: List[str] = []
        for inst in self.instructions:
            if isinstance(inst, LabelInstruction):
                lines.append(inst.to_text())
            else:
                lines.append(f"  {inst.to_text()}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the IR program for API response and UI visualization."""
        return {
            "instructions": [inst.to_dict() for inst in self.instructions],
            "code": self.to_text(),
            "instruction_count": len(self.instructions),
            "temp_count": self.temp_count,
            "label_count": self.label_count,
        }


class IRGenerator:
    """
    Translates a validated VCL Abstract Syntax Tree into Three-Address Code (3AC).
    Guarantees deterministic temporary variable naming (t1, t2, ...) and
    labels (L1, L2, ...). AST is never mutated.
    """

    def __init__(self):
        self.instructions: List[IRInstruction] = []
        self._temp_counter: int = 0
        self._label_counter: int = 0

    def generate(self, program: Program) -> IRProgram:
        """Translates the AST Program into an IRProgram."""
        self.instructions = []
        self._temp_counter = 0
        self._label_counter = 0

        if not isinstance(program, Program):
            return IRProgram(instructions=[], temp_count=0, label_count=0)

        for stmt in program.statements:
            self._generate_statement(stmt)

        return IRProgram(
            instructions=list(self.instructions),
            temp_count=self._temp_counter,
            label_count=self._label_counter,
        )

    def _new_temp(self) -> str:
        self._temp_counter += 1
        return f"t{self._temp_counter}"

    def _new_label(self) -> str:
        self._label_counter += 1
        return f"L{self._label_counter}"

    def _emit(self, instruction: IRInstruction) -> None:
        self.instructions.append(instruction)

    # -------------------------------------------------------------------------
    # Statement Translation
    # -------------------------------------------------------------------------

    def _generate_statement(self, stmt: ASTNode) -> None:
        if isinstance(stmt, VarDeclaration):
            val = self._generate_expression(stmt.initializer)
            self._emit(
                CopyInstruction(
                    result=stmt.name,
                    source=val,
                    line=stmt.line,
                    column=stmt.column,
                )
            )

        elif isinstance(stmt, Assignment):
            val = self._generate_expression(stmt.value)
            self._emit(
                CopyInstruction(
                    result=stmt.target,
                    source=val,
                    line=stmt.line,
                    column=stmt.column,
                )
            )

        elif isinstance(stmt, PrintStatement):
            val = self._generate_expression(stmt.expression)
            self._emit(
                PrintInstruction(
                    value=val,
                    line=stmt.line,
                    column=stmt.column,
                )
            )

        elif isinstance(stmt, BlockStatement):
            for inner_stmt in stmt.statements:
                self._generate_statement(inner_stmt)

        elif isinstance(stmt, IfStatement):
            cond_val = self._generate_expression(stmt.condition)

            if stmt.else_branch is not None:
                label_else = self._new_label()
                label_end = self._new_label()

                # If condition evaluates false, branch to else
                self._emit(
                    JumpIfFalseInstruction(
                        condition=cond_val,
                        target=label_else,
                        line=stmt.line,
                        column=stmt.column,
                    )
                )

                # Then branch
                self._generate_statement(stmt.then_branch)
                self._emit(
                    JumpInstruction(
                        target=label_end,
                        line=stmt.line,
                        column=stmt.column,
                    )
                )

                # Else branch
                self._emit(
                    LabelInstruction(
                        name=label_else,
                        line=stmt.else_branch.line,
                        column=stmt.else_branch.column,
                    )
                )
                self._generate_statement(stmt.else_branch)

                # End label
                self._emit(
                    LabelInstruction(
                        name=label_end,
                        line=stmt.line,
                        column=stmt.column,
                    )
                )
            else:
                label_end = self._new_label()

                # If condition evaluates false, skip then branch
                self._emit(
                    JumpIfFalseInstruction(
                        condition=cond_val,
                        target=label_end,
                        line=stmt.line,
                        column=stmt.column,
                    )
                )

                # Then branch
                self._generate_statement(stmt.then_branch)

                # End label
                self._emit(
                    LabelInstruction(
                        name=label_end,
                        line=stmt.line,
                        column=stmt.column,
                    )
                )

    # -------------------------------------------------------------------------
    # Expression Translation
    # -------------------------------------------------------------------------

    def _generate_expression(self, expr: ASTNode) -> str:
        """
        Recursively translates an expression into 3AC.
        Returns the variable name, temporary name, or literal representation.
        """
        if isinstance(expr, Literal):
            if isinstance(expr.value, bool):
                return "true" if expr.value else "false"
            return str(expr.value)

        elif isinstance(expr, Identifier):
            return expr.name

        elif isinstance(expr, BinaryExpression):
            left_val = self._generate_expression(expr.left)
            right_val = self._generate_expression(expr.right)
            temp = self._new_temp()
            self._emit(
                BinaryOpInstruction(
                    result=temp,
                    op=expr.operator,
                    left=left_val,
                    right=right_val,
                    line=expr.line,
                    column=expr.column,
                )
            )
            return temp

        elif isinstance(expr, UnaryExpression):
            operand_val = self._generate_expression(expr.operand)
            temp = self._new_temp()
            self._emit(
                UnaryOpInstruction(
                    result=temp,
                    op=expr.operator,
                    operand=operand_val,
                    line=expr.line,
                    column=expr.column,
                )
            )
            return temp

        # Fallback for unknown or malformed node
        return "unknown"
