"""
Veyra Visual Compiler - Backend Package
Interactive Visual Compiler with Step-by-Step AST and Symbol Table Visualization
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
    "VeyraCompiler",
    "CompilationResult",
]
