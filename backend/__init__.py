"""
Veyra Visual Compiler - Backend Package
Interactive Visual Compiler with Step-by-Step AST, Symbol Table,
CFG Visualization, 3AC Optimization, and Runtime Debugger.
"""

from backend.tokens import Token, TokenType, TokenManager
from backend.errors import (
    Diagnostic,
    DiagnosticStage,
    DiagnosticSeverity,
    VeyraCompilerException,
    LexicalError,
    SyntaxError,
    SemanticError,
    RuntimeCompilerError,
)
from backend.lexer import Lexer
from backend.ast_nodes import ASTNode
from backend.parser import Parser
from backend.symbol_table import Symbol, SymbolTable
from backend.semantic import SemanticAnalyzer
from backend.interpreter import Interpreter
from backend.ir import IRGenerator, IRProgram, IRInstruction
from backend.cfg import CFGBuilder, ControlFlowGraph, BasicBlock, CFGEdge
from backend.optimizer import OptimizationPipeline, OptimizationResult, TransformationRecord
from backend.debugger import TracedInterpreter, DebugTrace, DebugEvent
from backend.compiler import VeyraCompiler, CompilationResult

__all__ = [
    "Token",
    "TokenType",
    "TokenManager",
    "Diagnostic",
    "DiagnosticStage",
    "DiagnosticSeverity",
    "VeyraCompilerException",
    "LexicalError",
    "SyntaxError",
    "SemanticError",
    "RuntimeCompilerError",
    "Lexer",
    "ASTNode",
    "Parser",
    "Symbol",
    "SymbolTable",
    "SemanticAnalyzer",
    "IRGenerator",
    "IRProgram",
    "IRInstruction",
    "Interpreter",
    "CFGBuilder",
    "ControlFlowGraph",
    "BasicBlock",
    "CFGEdge",
    "OptimizationPipeline",
    "OptimizationResult",
    "TransformationRecord",
    "TracedInterpreter",
    "DebugTrace",
    "DebugEvent",
    "VeyraCompiler",
    "CompilationResult",
]
