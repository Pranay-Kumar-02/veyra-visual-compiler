"""
Unified Compiler Pipeline Driver for Veyra Visual Compiler.
Coordinates:
Source -> Lexer -> Tokens -> Parser -> AST -> Semantic Analyzer -> Symbol Table -> Interpreter -> Output & Diagnostics
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.tokens import TokenManager
from backend.lexer import Lexer
from backend.parser import Parser
from backend.ast_nodes import Program
from backend.symbol_table import SymbolTable
from backend.semantic import SemanticAnalyzer
from backend.interpreter import Interpreter
from backend.errors import (
    Diagnostic,
    DiagnosticStage,
    DiagnosticSeverity,
    VeyraCompilerException,
)


@dataclass
class CompilationResult:
    success: bool
    tokens: List[Dict[str, Any]]
    ast: Optional[Dict[str, Any]]
    symbol_table: List[Dict[str, Any]]
    diagnostics: List[Dict[str, Any]]
    output: str
    output_lines: List[str]
    stages_executed: List[str]
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "tokens": self.tokens,
            "ast": self.ast,
            "symbol_table": self.symbol_table,
            "diagnostics": self.diagnostics,
            "output": self.output,
            "output_lines": self.output_lines,
            "stages_executed": self.stages_executed,
            "metrics": self.metrics,
        }


class VeyraCompiler:
    """
    Main compiler pipeline driver that produces complete, structured visualization data.
    """

    def compile(self, source: str, run_interpreter: bool = True) -> CompilationResult:
        start_time = time.perf_counter()
        stages_executed: List[str] = []
        diagnostics: List[Diagnostic] = []
        tokens_data: List[Dict[str, Any]] = []
        ast_data: Optional[Dict[str, Any]] = None
        symbol_table_data: List[Dict[str, Any]] = []
        output_lines: List[str] = []

        # ---------------------------------------------------------------------
        # STAGE 1: Lexical Analysis
        # ---------------------------------------------------------------------
        try:
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            token_manager = TokenManager(tokens)
            tokens_data = token_manager.to_list()
            stages_executed.append("Lexer")
        except VeyraCompilerException as e:
            diagnostics.append(e.to_diagnostic())
            return self._build_result(
                success=False,
                tokens=tokens_data,
                ast=None,
                symbol_table=[],
                diagnostics=diagnostics,
                output_lines=[],
                stages_executed=stages_executed,
                start_time=start_time,
            )
        except Exception as e:
            # Fallback for unexpected internal errors
            diagnostics.append(
                Diagnostic(
                    stage=DiagnosticStage.LEXICAL,
                    message=f"Internal scanner error: {str(e)}",
                    line=1,
                    column=1,
                )
            )
            return self._build_result(
                success=False,
                tokens=tokens_data,
                ast=None,
                symbol_table=[],
                diagnostics=diagnostics,
                output_lines=[],
                stages_executed=stages_executed,
                start_time=start_time,
            )

        # ---------------------------------------------------------------------
        # STAGE 2: Syntactic Analysis (Parser)
        # ---------------------------------------------------------------------
        program_ast: Optional[Program] = None
        try:
            parser = Parser(tokens)
            program_ast = parser.parse()
            ast_data = program_ast.to_dict()
            stages_executed.append("Parser")
        except VeyraCompilerException as e:
            diagnostics.append(e.to_diagnostic())
            return self._build_result(
                success=False,
                tokens=tokens_data,
                ast=None,
                symbol_table=[],
                diagnostics=diagnostics,
                output_lines=[],
                stages_executed=stages_executed,
                start_time=start_time,
            )
        except Exception as e:
            diagnostics.append(
                Diagnostic(
                    stage=DiagnosticStage.SYNTAX,
                    message=f"Internal parser error: {str(e)}",
                    line=1,
                    column=1,
                )
            )
            return self._build_result(
                success=False,
                tokens=tokens_data,
                ast=None,
                symbol_table=[],
                diagnostics=diagnostics,
                output_lines=[],
                stages_executed=stages_executed,
                start_time=start_time,
            )

        # ---------------------------------------------------------------------
        # STAGE 3: Semantic Analysis & Symbol Table Generation
        # ---------------------------------------------------------------------
        symbol_table: SymbolTable = SymbolTable()
        try:
            analyzer = SemanticAnalyzer(symbol_table)
            symbol_table, sem_diagnostics = analyzer.analyze(program_ast)
            stages_executed.append("Semantic Analysis")
            diagnostics.extend(sem_diagnostics)
            symbol_table_data = symbol_table.to_list()

            # If semantic errors are present, stop before interpretation
            has_errors = any(d.severity == DiagnosticSeverity.ERROR for d in diagnostics)
            if has_errors:
                return self._build_result(
                    success=False,
                    tokens=tokens_data,
                    ast=ast_data,
                    symbol_table=symbol_table_data,
                    diagnostics=diagnostics,
                    output_lines=[],
                    stages_executed=stages_executed,
                    start_time=start_time,
                )
        except Exception as e:
            diagnostics.append(
                Diagnostic(
                    stage=DiagnosticStage.SEMANTIC,
                    message=f"Internal semantic analyzer error: {str(e)}",
                    line=1,
                    column=1,
                )
            )
            return self._build_result(
                success=False,
                tokens=tokens_data,
                ast=ast_data,
                symbol_table=symbol_table_data,
                diagnostics=diagnostics,
                output_lines=[],
                stages_executed=stages_executed,
                start_time=start_time,
            )

        # ---------------------------------------------------------------------
        # STAGE 4: AST Interpreter Execution
        # ---------------------------------------------------------------------
        if run_interpreter:
            try:
                interpreter = Interpreter(symbol_table)
                output_lines, updated_symbols = interpreter.interpret(program_ast)
                symbol_table_data = updated_symbols.to_list()
                stages_executed.append("Interpreter")
            except VeyraCompilerException as e:
                diagnostics.append(e.to_diagnostic())
                return self._build_result(
                    success=False,
                    tokens=tokens_data,
                    ast=ast_data,
                    symbol_table=symbol_table_data,
                    diagnostics=diagnostics,
                    output_lines=output_lines,
                    stages_executed=stages_executed,
                    start_time=start_time,
                )
            except Exception as e:
                diagnostics.append(
                    Diagnostic(
                        stage=DiagnosticStage.RUNTIME,
                        message=f"Internal runtime error: {str(e)}",
                        line=1,
                        column=1,
                    )
                )
                return self._build_result(
                    success=False,
                    tokens=tokens_data,
                    ast=ast_data,
                    symbol_table=symbol_table_data,
                    diagnostics=diagnostics,
                    output_lines=output_lines,
                    stages_executed=stages_executed,
                    start_time=start_time,
                )

        return self._build_result(
            success=True,
            tokens=tokens_data,
            ast=ast_data,
            symbol_table=symbol_table_data,
            diagnostics=diagnostics,
            output_lines=output_lines,
            stages_executed=stages_executed,
            start_time=start_time,
        )

    def _build_result(
        self,
        success: bool,
        tokens: List[Dict[str, Any]],
        ast: Optional[Dict[str, Any]],
        symbol_table: List[Dict[str, Any]],
        diagnostics: List[Diagnostic],
        output_lines: List[str],
        stages_executed: List[str],
        start_time: float,
    ) -> CompilationResult:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        metrics = {
            "token_count": len(tokens),
            "symbol_count": len(symbol_table),
            "diagnostic_count": len(diagnostics),
            "output_line_count": len(output_lines),
            "diagnostic_pipeline_duration_ms": elapsed_ms,
        }
        return CompilationResult(
            success=success,
            tokens=tokens,
            ast=ast,
            symbol_table=symbol_table,
            diagnostics=[d.to_dict() for d in diagnostics],
            output="\n".join(output_lines),
            output_lines=output_lines,
            stages_executed=stages_executed,
            metrics=metrics,
        )
