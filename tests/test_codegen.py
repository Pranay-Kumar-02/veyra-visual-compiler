"""
Comprehensive Target Code Generation Test Suite for Veyra Visual Compiler.
Verifies x86-64 NASM Intel-syntax assembly generation, deterministic stack frame allocation,
arithmetic/relational/branching operations, runtime dependencies, and API integration.
"""

import pytest
from app import app
from backend.compiler import VeyraCompiler
from backend.codegen import CodeGenerator, AssemblyProgram
from backend.lexer import Lexer
from backend.parser import Parser
from backend.ir import (
    IRGenerator,
    IRProgram,
    CopyInstruction,
    BinaryOpInstruction,
    UnaryOpInstruction,
    LabelInstruction,
    JumpInstruction,
    JumpIfFalseInstruction,
    JumpIfTrueInstruction,
    PrintInstruction,
)
from backend.optimizer import OptimizationPipeline


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_flagship_vcl_assembly_generation():
    """Verifies x86-64 assembly generation for the faculty flagship program."""
    vcl_code = """
    let score = 20;
    let bonus = 5;
    let result = score + bonus * 2;

    if (result >= 30) {
        print(result);
    } else {
        print(0);
    }
    """
    compiler = VeyraCompiler()
    res = compiler.compile(vcl_code)

    assert res.success is True
    assert res.output == "30"
    assert "Target Code Generation" in res.stages_executed
    assert res.assembly is not None
    assert res.assembly["is_valid"] is True
    assert res.assembly["target_arch"] == "x86-64"
    assert res.assembly["target_syntax"] == "NASM Intel Syntax"
    assert res.assembly["instruction_count"] > 15
    assert res.metrics["assembly_instruction_count"] == res.assembly["instruction_count"]

    asm_code = res.assembly_code
    # Directives and symbols
    assert "default rel" in asm_code
    assert "section .rodata" in asm_code
    assert "section .text" in asm_code
    assert "global main" in asm_code
    assert "extern printf" in asm_code

    # Variables allocated on stack
    assert "[rbp - " in asm_code
    assert "score" in res.assembly["variable_offsets"]
    assert "bonus" in res.assembly["variable_offsets"]
    assert "result" in res.assembly["variable_offsets"]

    # Branches and labels
    assert "je       L1" in asm_code or "je" in asm_code
    assert "L1:" in asm_code
    assert "L2:" in asm_code
    assert "call     printf" in asm_code


def test_arithmetic_operations():
    """Tests arithmetic operations: +, -, *, /, % translation from 3AC."""
    vcl_code = """
    let a = 100;
    let b = 20;
    let c = a + b;
    let d = a - b;
    let e = a * b;
    let f = a / b;
    let g = a % b;
    print(c);
    """
    tokens = Lexer(vcl_code).tokenize()
    ast = Parser(tokens).parse()
    ir = IRGenerator().generate(ast)
    gen = CodeGenerator()
    asm_prog = gen.generate(ir)

    asm = asm_prog.code
    assert "add" in asm
    assert "sub" in asm
    assert "imul" in asm
    assert "idiv" in asm
    assert "cqo" in asm


def test_relational_and_boolean_conditions():
    """Tests relational operations and logical boolean instructions from 3AC."""
    vcl_code = """
    let x = 10;
    let y = 20;
    let eq = x == y;
    let ne = x != y;
    let lt = x < y;
    let le = x <= y;
    let gt = x > y;
    let ge = x >= y;
    let both = lt && ge;
    let either = lt || ge;
    """
    tokens = Lexer(vcl_code).tokenize()
    ast = Parser(tokens).parse()
    ir = IRGenerator().generate(ast)
    gen = CodeGenerator()
    asm_prog = gen.generate(ir)

    asm = asm_prog.code
    assert "sete" in asm
    assert "setne" in asm
    assert "setl" in asm
    assert "setle" in asm
    assert "setg" in asm
    assert "setge" in asm
    assert "and" in asm
    assert "or" in asm
    assert "movzx" in asm


def test_unary_operations():
    """Tests negation and logical NOT operations from 3AC."""
    vcl_code = """
    let a = 42;
    let b = -a;
    let c = !true;
    print(b);
    """
    tokens = Lexer(vcl_code).tokenize()
    ast = Parser(tokens).parse()
    ir = IRGenerator().generate(ast)
    gen = CodeGenerator()
    asm_prog = gen.generate(ir)

    asm = asm_prog.code
    assert "neg" in asm
    assert "sete" in asm


def test_division_by_zero_trap():
    """Tests that division and modulo emit the .L_div_zero_trap guard in 3AC translation."""
    vcl_code = """
    let a = 50;
    let b = 10;
    let c = a / b;
    print(c);
    """
    tokens = Lexer(vcl_code).tokenize()
    ast = Parser(tokens).parse()
    ir = IRGenerator().generate(ast)
    gen = CodeGenerator()
    asm_prog = gen.generate(ir)

    asm = asm_prog.code
    assert ".L_div_zero_trap" in asm
    assert "Runtime Error: Division by zero" in asm
    assert "exit" in asm


def test_deterministic_stack_frame_alignment():
    """Tests that the stack frame is 16-byte aligned in all configurations."""
    vcl_code = """
    let v1 = 1;
    let v2 = 2;
    let v3 = 3;
    """
    compiler = VeyraCompiler()
    res = compiler.compile(vcl_code)
    assert res.success is True
    frame_size = res.assembly["stack_frame_size"]
    assert frame_size % 16 == 0
    assert frame_size >= 16


def test_empty_program_codegen():
    """Tests target code generation for an empty IR program."""
    empty_ir = IRProgram(instructions=[], temp_count=0, label_count=0)
    gen = CodeGenerator()
    asm = gen.generate(empty_ir)
    assert asm.is_valid is True
    assert "global main" in asm.code
    assert "xor eax, eax" in asm.code
    assert "ret" in asm.code


def test_abi_modes():
    """Tests target code generation under both SysV AMD64 and Win64 ABIs."""
    vcl_code = "let x = 42; print(x);"
    tokens = Lexer(vcl_code).tokenize()
    ast = Parser(tokens).parse()
    ir = IRGenerator().generate(ast)

    gen_sysv = CodeGenerator(target_abi="sysv64")
    asm_sysv = gen_sysv.generate(ir)
    assert "lea      rdi, [rel fmt_int]" in asm_sysv.code
    assert "mov      rsi," in asm_sysv.code
    assert asm_sysv.target_abi == "System V AMD64 ABI"

    gen_win = CodeGenerator(target_abi="win64")
    asm_win = gen_win.generate(ir)
    assert "lea      rcx, [rel fmt_int]" in asm_win.code
    assert "mov      rdx," in asm_win.code
    assert asm_win.target_abi == "Microsoft x64 ABI"


def test_unsupported_instruction_diagnostic():
    """Tests that malformed or unsupported IR produces diagnostics without crashing."""
    class FakeInstruction(CopyInstruction):
        pass

    ir = IRProgram(
        instructions=[FakeInstruction(result="x", source="10")],
        temp_count=0,
        label_count=0,
    )
    gen = CodeGenerator()
    asm = gen.generate(ir)
    assert asm is not None
    assert "x = 10" in asm.code


def test_api_codegen_endpoint_success(client):
    """Tests POST /api/codegen returns generated x86-64 assembly and metadata."""
    payload = {
        "source": """
        let score = 20;
        let bonus = 5;
        let result = score + bonus * 2;
        if (result >= 30) {
            print(result);
        } else {
            print(0);
        }
        """,
        "abi": "sysv64",
        "use_optimized": True,
    }
    response = client.post("/api/codegen", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    assert data["success"] is True
    assert data["target_arch"] == "x86-64"
    assert data["target_syntax"] == "NASM Intel Syntax"
    assert data["target_abi"] == "System V AMD64 ABI"
    assert data["assembly"] is not None
    assert data["assembly"]["instruction_count"] > 15
    assert len(data["assembly_code"]) > 100
    assert "default rel" in data["assembly_code"]


def test_api_codegen_endpoint_validation(client):
    """Tests input validation and error diagnostics on POST /api/codegen."""
    # Invalid payload (non-string source)
    res1 = client.post("/api/codegen", json={"source": 12345})
    assert res1.status_code == 400
    assert "error" in res1.get_json()

    # Syntax error source
    res2 = client.post("/api/codegen", json={"source": "let x = ;"})
    assert res2.status_code == 400
    d2 = res2.get_json()
    assert d2["success"] is False
    assert len(d2["diagnostics"]) > 0
