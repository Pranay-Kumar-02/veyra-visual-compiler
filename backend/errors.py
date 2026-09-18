"""
Diagnostics and structured error handling for Veyra Visual Compiler.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class DiagnosticStage(str, Enum):
    LEXICAL = "Lexical Error"
    SYNTAX = "Syntax Error"
    SEMANTIC = "Semantic Error"
    RUNTIME = "Runtime Error"


class DiagnosticSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Diagnostic:
    stage: DiagnosticStage
    message: str
    line: int
    column: int
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "hint": self.hint,
            "formatted": str(self),
        }

    def __str__(self) -> str:
        loc = f"Line {self.line}, Column {self.column}" if self.line > 0 else "Source Position Unknown"
        res = f"[{self.stage.value}] {self.message}\n  --> {loc}"
        if self.hint:
            res += f"\n  Hint: {self.hint}"
        return res


class VeyraCompilerException(Exception):
    """Base exception for all Veyra compiler stages."""

    def __init__(
        self,
        stage: DiagnosticStage,
        message: str,
        line: int = 1,
        column: int = 1,
        hint: Optional[str] = None,
    ):
        super().__init__(message)
        self.stage = stage
        self.message = message
        self.line = line
        self.column = column
        self.hint = hint

    def to_diagnostic(self) -> Diagnostic:
        return Diagnostic(
            stage=self.stage,
            message=self.message,
            line=self.line,
            column=self.column,
            severity=DiagnosticSeverity.ERROR,
            hint=self.hint,
        )


class LexicalError(VeyraCompilerException):
    def __init__(self, message: str, line: int = 1, column: int = 1, hint: Optional[str] = None):
        super().__init__(DiagnosticStage.LEXICAL, message, line, column, hint)


class SyntaxError(VeyraCompilerException):
    def __init__(self, message: str, line: int = 1, column: int = 1, hint: Optional[str] = None):
        super().__init__(DiagnosticStage.SYNTAX, message, line, column, hint)


class SemanticError(VeyraCompilerException):
    def __init__(self, message: str, line: int = 1, column: int = 1, hint: Optional[str] = None):
        super().__init__(DiagnosticStage.SEMANTIC, message, line, column, hint)


class RuntimeCompilerError(VeyraCompilerException):
    def __init__(self, message: str, line: int = 1, column: int = 1, hint: Optional[str] = None):
        super().__init__(DiagnosticStage.RUNTIME, message, line, column, hint)
