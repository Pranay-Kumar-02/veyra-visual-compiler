"""
Step-by-Step Execution Debugger for Veyra Visual Compiler.
Instruments the AST interpreter to record deterministic execution trace events,
capturing variable state snapshots, branch decisions, source locations,
accumulated output, and runtime exceptions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

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
from backend.errors import RuntimeCompilerError, VeyraCompilerException
from backend.interpreter import Interpreter, Environment


@dataclass
class DebugEvent:
    """Snapshot of execution state at a discrete step."""
    step_index: int
    event_type: str  # 'start' | 'step' | 'var_declare' | 'assignment' | 'branch_decision' | 'print' | 'runtime_error' | 'completed'
    line: int
    column: int
    node_type: str
    description: str
    variables: Dict[str, Dict[str, Any]]  # { var_name: { "value": str/val, "type": type_name } }
    changed_variable: Optional[str] = None
    branch_info: Optional[Dict[str, Any]] = None  # { "condition": str, "result": bool, "branch_taken": str }
    output_so_far: List[str] = field(default_factory=list)
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "event_type": self.event_type,
            "line": self.line,
            "column": self.column,
            "node_type": self.node_type,
            "description": self.description,
            "variables": self.variables,
            "changed_variable": self.changed_variable,
            "branch_info": self.branch_info,
            "output_so_far": list(self.output_so_far),
            "error": self.error,
        }


@dataclass
class DebugTrace:
    """Complete recorded trace of an interpreter execution session."""
    events: List[DebugEvent]
    total_steps: int
    completed_normally: bool
    final_output: List[str]
    runtime_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "events": [e.to_dict() for e in self.events],
            "total_steps": self.total_steps,
            "completed_normally": self.completed_normally,
            "final_output": self.final_output,
            "runtime_error": self.runtime_error,
        }


class TracedInterpreter(Interpreter):
    """
    Subclasses Interpreter to record genuine execution events at each statement.
    Maintains complete variable snapshots for deterministic forward/backward inspection.
    """

    def __init__(self, symbol_table: Optional[SymbolTable] = None):
        super().__init__(symbol_table)
        self.trace_events: List[DebugEvent] = []
        self._step_counter: int = 0

    def _snapshot_variables(self) -> Dict[str, Dict[str, Any]]:
        """Collects all visible variables from active environment hierarchy."""
        vars_dict: Dict[str, Dict[str, Any]] = {}
        curr_env: Optional[Environment] = self.env
        while curr_env is not None:
            for k, v in curr_env.values.items():
                if k not in vars_dict:
                    val_type = "int" if isinstance(v, int) and not isinstance(v, bool) else (
                        "float" if isinstance(v, float) else ("bool" if isinstance(v, bool) else "unknown")
                    )
                    vars_dict[k] = {
                        "value": "true" if v is True else ("false" if v is False else v),
                        "type": val_type,
                    }
            curr_env = curr_env.parent
        return vars_dict

    def _record_event(
        self,
        event_type: str,
        line: int,
        column: int,
        node_type: str,
        description: str,
        changed_variable: Optional[str] = None,
        branch_info: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
    ) -> None:
        event = DebugEvent(
            step_index=self._step_counter,
            event_type=event_type,
            line=line,
            column=column,
            node_type=node_type,
            description=description,
            variables=self._snapshot_variables(),
            changed_variable=changed_variable,
            branch_info=branch_info,
            output_so_far=list(self.output),
            error=error,
        )
        self.trace_events.append(event)
        self._step_counter += 1

    def interpret_with_trace(self, program: Program) -> Tuple[List[str], SymbolTable, DebugTrace]:
        """Executes the program while recording a complete execution trace."""
        self.output = []
        self.trace_events = []
        self._step_counter = 0
        self.global_env = Environment()
        self.env = self.global_env

        # Initial entry event
        self._record_event(
            event_type="start",
            line=program.line,
            column=program.column,
            node_type="Program",
            description="Program execution started",
        )

        completed_normally = False
        runtime_err_msg: Optional[str] = None

        try:
            for stmt in program.statements:
                self.execute(stmt)
            completed_normally = True
            # Program completed event
            self._record_event(
                event_type="completed",
                line=program.line,
                column=program.column,
                node_type="Program",
                description=f"Program finished normally with {len(self.output)} output line(s)",
            )
        except RuntimeCompilerError as e:
            runtime_err_msg = e.message
            err_dict = {
                "message": e.message,
                "line": e.line,
                "column": e.column,
                "hint": e.hint,
            }
            self._record_event(
                event_type="runtime_error",
                line=e.line,
                column=e.column,
                node_type="RuntimeError",
                description=f"Runtime error: {e.message}",
                error=err_dict,
            )
            # Re-raise to let caller handle standard compiler diagnostic
            raise e

        trace = DebugTrace(
            events=self.trace_events,
            total_steps=len(self.trace_events),
            completed_normally=completed_normally,
            final_output=list(self.output),
            runtime_error=runtime_err_msg,
        )
        return self.output, self.symbol_table, trace

    def exec_VarDeclaration(self, node: VarDeclaration) -> None:
        value = self.evaluate(node.initializer)
        self.env.define(node.name, value)

        val_type = "int" if isinstance(value, int) and not isinstance(value, bool) else (
            "float" if isinstance(value, float) else ("bool" if isinstance(value, bool) else "unknown")
        )
        self.symbol_table.update(node.name, value, val_type)

        val_repr = "true" if value is True else ("false" if value is False else str(value))
        self._record_event(
            event_type="var_declare",
            line=node.line,
            column=node.column,
            node_type="VarDeclaration",
            description=f"Declared variable '{node.name}' = {val_repr}",
            changed_variable=node.name,
        )

    def exec_Assignment(self, node: Assignment) -> None:
        value = self.evaluate(node.value)
        assigned = self.env.assign(node.target, value)
        if not assigned:
            self.env.define(node.target, value)

        val_type = "int" if isinstance(value, int) and not isinstance(value, bool) else (
            "float" if isinstance(value, float) else ("bool" if isinstance(value, bool) else "unknown")
        )
        self.symbol_table.update(node.target, value, val_type)

        val_repr = "true" if value is True else ("false" if value is False else str(value))
        self._record_event(
            event_type="assignment",
            line=node.line,
            column=node.column,
            node_type="Assignment",
            description=f"Assigned '{node.target}' = {val_repr}",
            changed_variable=node.target,
        )

    def exec_PrintStatement(self, node: PrintStatement) -> None:
        value = self.evaluate(node.expression)
        if isinstance(value, bool):
            formatted = "true" if value else "false"
        elif isinstance(value, float):
            formatted = str(int(value)) if value.is_integer() else str(value)
        else:
            formatted = str(value)
        self.output.append(formatted)

        self._record_event(
            event_type="print",
            line=node.line,
            column=node.column,
            node_type="PrintStatement",
            description=f"Output printed: {formatted}",
        )

    def exec_IfStatement(self, node: IfStatement) -> None:
        condition_val = self.evaluate(node.condition)
        is_true = bool(condition_val is True)
        branch_taken = "Then" if is_true else ("Else" if node.else_branch else "None (Fall-through)")

        branch_info = {
            "condition_line": node.line,
            "evaluated_result": is_true,
            "branch_taken": branch_taken,
        }

        self._record_event(
            event_type="branch_decision",
            line=node.line,
            column=node.column,
            node_type="IfStatement",
            description=f"Condition evaluated to {is_true} -> Taking {branch_taken} branch",
            branch_info=branch_info,
        )

        if is_true:
            self.execute(node.then_branch)
        elif node.else_branch is not None:
            self.execute(node.else_branch)
