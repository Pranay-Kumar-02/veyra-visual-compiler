"""
Unified Compiler Pipeline Driver for Veyra Visual Compiler.
Coordinates:
Source -> Lexer -> Tokens -> Parser -> AST -> Semantic Analyzer -> Symbol Table
-> 3AC IR Generation -> Control Flow Graph -> 3AC Optimization -> Traced Interpreter -> Diagnostics
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
from backend.ir import IRGenerator, IRProgram
from backend.cfg import CFGBuilder
from backend.optimizer import OptimizationPipeline
from backend.codegen import CodeGenerator, AssemblyProgram
from backend.debugger import TracedInterpreter
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
    ir: Optional[Dict[str, Any]] = None
    ir_code: str = ""
    cfg: Optional[Dict[str, Any]] = None
    optimized_ir: Optional[Dict[str, Any]] = None
    optimized_ir_code: str = ""
    optimization_report: Optional[Dict[str, Any]] = None
    assembly: Optional[Dict[str, Any]] = None
    assembly_code: str = ""
    debug_trace: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "tokens": self.tokens,
            "ast": self.ast,
            "symbol_table": self.symbol_table,
            "ir": self.ir,
            "ir_code": self.ir_code,
            "cfg": self.cfg,
            "optimized_ir": self.optimized_ir,
            "optimized_ir_code": self.optimized_ir_code,
            "optimization_report": self.optimization_report,
            "assembly": self.assembly,
            "assembly_code": self.assembly_code,
            "debug_trace": self.debug_trace,
            "diagnostics": self.diagnostics,
            "output": self.output,
            "output_lines": self.output_lines,
            "stages_executed": self.stages_executed,
            "metrics": self.metrics,
        }


class VeyraCompiler:
    """
    Main compiler pipeline driver that coordinates all analysis, synthesis,
    optimization, graph generation, and runtime tracing stages.
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

            has_errors = any(d.severity == DiagnosticSeverity.ERROR for d in diagnostics)
            if has_errors:
                return self._build_result(
                    success=False,
                    tokens=tokens_data,
                    ast=ast_data,
                    symbol_table=symbol_table_data,
                    ir=None,
                    ir_code="",
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
                ir=None,
                ir_code="",
                diagnostics=diagnostics,
                output_lines=[],
                stages_executed=stages_executed,
                start_time=start_time,
            )

        # ---------------------------------------------------------------------
        # STAGE 4: Three-Address Code (3AC) Intermediate Representation
        # ---------------------------------------------------------------------
        ir_data: Optional[Dict[str, Any]] = None
        ir_code: str = ""
        ir_program: Optional[IRProgram] = None
        try:
            ir_gen = IRGenerator()
            ir_program = ir_gen.generate(program_ast)
            ir_data = ir_program.to_dict()
            ir_code = ir_program.to_text()
            stages_executed.append("IR Generation")
        except Exception as e:
            diagnostics.append(
                Diagnostic(
                    stage=DiagnosticStage.SEMANTIC,
                    message=f"Internal IR generator error: {str(e)}",
                    line=1,
                    column=1,
                )
            )
            return self._build_result(
                success=False,
                tokens=tokens_data,
                ast=ast_data,
                symbol_table=symbol_table_data,
                ir=None,
                ir_code="",
                diagnostics=diagnostics,
                output_lines=[],
                stages_executed=stages_executed,
                start_time=start_time,
            )

        # ---------------------------------------------------------------------
        # STAGE 4.1: Control Flow Graph (CFG) Construction & Analysis
        # ---------------------------------------------------------------------
        cfg_data: Optional[Dict[str, Any]] = None
        try:
            cfg_builder = CFGBuilder()
            cfg_obj = cfg_builder.build(ir_program)
            cfg_data = cfg_obj.to_dict()
        except Exception as e:
            diagnostics.append(
                Diagnostic(
                    stage=DiagnosticStage.SEMANTIC,
                    message=f"Internal CFG construction error: {str(e)}",
                    line=1,
                    column=1,
                )
            )

        # ---------------------------------------------------------------------
        # STAGE 4.2: 3AC Optimization Pipeline
        # ---------------------------------------------------------------------
        optimized_ir_data: Optional[Dict[str, Any]] = None
        optimized_ir_code: str = ""
        optimization_report: Optional[Dict[str, Any]] = None
        opt_result = None
        try:
            optimizer = OptimizationPipeline()
            opt_result = optimizer.optimize(ir_program)
            optimized_ir_data = opt_result.optimized_ir.to_dict()
            optimized_ir_code = opt_result.optimized_ir.to_text()
            optimization_report = opt_result.to_dict()
        except Exception as e:
            diagnostics.append(
                Diagnostic(
                    stage=DiagnosticStage.SEMANTIC,
                    message=f"Internal optimizer error: {str(e)}",
                    line=1,
                    column=1,
                )
            )

        # ---------------------------------------------------------------------
        # STAGE 4.3: Target Code Generation (x86-64 NASM Assembly)
        # ---------------------------------------------------------------------
        assembly_data: Optional[Dict[str, Any]] = None
        assembly_code: str = ""
        try:
            target_ir = opt_result.optimized_ir if opt_result is not None else ir_program
            codegen = CodeGenerator()
            asm_prog = codegen.generate(target_ir)
            assembly_data = asm_prog.to_dict()
            assembly_code = asm_prog.code
            stages_executed.append("Target Code Generation")
            if not asm_prog.is_valid:
                for diag_dict in asm_prog.diagnostics:
                    diagnostics.append(
                        Diagnostic(
                            stage=DiagnosticStage.SEMANTIC,
                            message=diag_dict.get("message", "Target code generation issue"),
                            line=diag_dict.get("line", 1),
                            column=diag_dict.get("column", 1),
                            severity=DiagnosticSeverity.WARNING,
                        )
                    )
        except Exception as e:
            diagnostics.append(
                Diagnostic(
                    stage=DiagnosticStage.SEMANTIC,
                    message=f"Internal target code generator error: {str(e)}",
                    line=1,
                    column=1,
                )
            )

        # ---------------------------------------------------------------------
        # STAGE 5: AST Traced Interpreter Execution
        # ---------------------------------------------------------------------
        debug_trace_data: Optional[Dict[str, Any]] = None
        if run_interpreter:
            interpreter = TracedInterpreter(symbol_table)
            try:
                output_lines, updated_symbols, trace = interpreter.interpret_with_trace(program_ast)
                debug_trace_data = trace.to_dict()
                symbol_table_data = updated_symbols.to_list()
                stages_executed.append("Interpreter")
            except VeyraCompilerException as e:
                diagnostics.append(e.to_diagnostic())
                debug_trace_data = {
                    "events": [ev.to_dict() for ev in interpreter.trace_events],
                    "total_steps": len(interpreter.trace_events),
                    "completed_normally": False,
                    "final_output": list(interpreter.output),
                    "runtime_error": e.message,
                }
                return self._build_result(
                    success=False,
                    tokens=tokens_data,
                    ast=ast_data,
                    symbol_table=symbol_table_data,
                    ir=ir_data,
                    ir_code=ir_code,
                    cfg=cfg_data,
                    optimized_ir=optimized_ir_data,
                    optimized_ir_code=optimized_ir_code,
                    optimization_report=optimization_report,
                    assembly=assembly_data,
                    assembly_code=assembly_code,
                    debug_trace=debug_trace_data,
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
                    ir=ir_data,
                    ir_code=ir_code,
                    cfg=cfg_data,
                    optimized_ir=optimized_ir_data,
                    optimized_ir_code=optimized_ir_code,
                    optimization_report=optimization_report,
                    assembly=assembly_data,
                    assembly_code=assembly_code,
                    debug_trace=debug_trace_data,
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
            ir=ir_data,
            ir_code=ir_code,
            cfg=cfg_data,
            optimized_ir=optimized_ir_data,
            optimized_ir_code=optimized_ir_code,
            optimization_report=optimization_report,
            assembly=assembly_data,
            assembly_code=assembly_code,
            debug_trace=debug_trace_data,
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
        ir: Optional[Dict[str, Any]] = None,
        ir_code: str = "",
        cfg: Optional[Dict[str, Any]] = None,
        optimized_ir: Optional[Dict[str, Any]] = None,
        optimized_ir_code: str = "",
        optimization_report: Optional[Dict[str, Any]] = None,
        assembly: Optional[Dict[str, Any]] = None,
        assembly_code: str = "",
        debug_trace: Optional[Dict[str, Any]] = None,
    ) -> CompilationResult:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        metrics = {
            "token_count": len(tokens),
            "symbol_count": len(symbol_table),
            "ir_instruction_count": ir.get("instruction_count", 0) if ir else 0,
            "optimized_instruction_count": optimized_ir.get("instruction_count", 0) if optimized_ir else 0,
            "assembly_instruction_count": assembly.get("instruction_count", 0) if assembly else 0,
            "cfg_block_count": cfg.get("block_count", 0) if cfg else 0,
            "cfg_edge_count": cfg.get("edge_count", 0) if cfg else 0,
            "debug_step_count": debug_trace.get("total_steps", 0) if debug_trace else 0,
            "diagnostic_count": len(diagnostics),
            "output_line_count": len(output_lines),
            "diagnostic_pipeline_duration_ms": elapsed_ms,
        }
        return CompilationResult(
            success=success,
            tokens=tokens,
            ast=ast,
            symbol_table=symbol_table,
            ir=ir,
            ir_code=ir_code,
            cfg=cfg,
            optimized_ir=optimized_ir,
            optimized_ir_code=optimized_ir_code,
            optimization_report=optimization_report,
            assembly=assembly,
            assembly_code=assembly_code,
            debug_trace=debug_trace,
            diagnostics=[d.to_dict() for d in diagnostics],
            output="\n".join(output_lines),
            output_lines=output_lines,
            stages_executed=stages_executed,
            metrics=metrics,
        )
