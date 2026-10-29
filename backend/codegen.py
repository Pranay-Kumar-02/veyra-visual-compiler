"""
Target Code Generator for Veyra Visual Compiler.
Translates optimized Three-Address Code (3AC) Intermediate Representation
into readable, correct, NASM-compatible x86-64 assembly using Intel syntax.

Supports:
- Target Architectures: x86-64 (AMD64 / Intel 64)
- Syntax: NASM-compatible Intel syntax (default rel)
- ABIs: System V AMD64 ABI (Linux/macOS default) and Microsoft x64 ABI (Windows)
- Frame Layout: Base-pointer relative stack allocation ([rbp - offset])
- 16-byte stack frame alignment for runtime call compatibility
- Arithmetic, relational, logical, unary, branching, and output instructions
- Runtime error trapping (e.g., division by zero detection)
- Deterministic variable and temporary slot allocation
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.ir import (
    IRInstruction,
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
from backend.errors import (
    Diagnostic,
    DiagnosticStage,
    DiagnosticSeverity,
)


@dataclass
class AssemblyInstruction:
    """Represents a single target assembly line or instruction."""

    mnemonic: str = ""
    operands: str = ""
    comment: str = ""
    label: Optional[str] = None
    is_directive: bool = False
    line_number: int = 0

    def to_text(self) -> str:
        """Emits formatted assembly line."""
        if self.label:
            lbl_line = f"{self.label}:"
            if self.comment:
                return f"{lbl_line:<24} ; {self.comment}"
            return lbl_line

        if self.is_directive:
            line = f"{self.mnemonic} {self.operands}".strip()
            if self.comment:
                return f"{line:<32} ; {self.comment}"
            return line

        if not self.mnemonic:
            if self.comment:
                if self.comment.startswith(("=", "---", "Veyra", "Generated", "Target", "Allocated")):
                    return f"; {self.comment}"
                return f"    ; {self.comment}"
            return ""

        inst = f"    {self.mnemonic:<8} {self.operands}".rstrip()
        if self.comment:
            return f"{inst:<36} ; {self.comment}"
        return inst

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "mnemonic": self.mnemonic,
            "operands": self.operands,
            "comment": self.comment,
            "is_directive": self.is_directive,
            "formatted": self.to_text(),
            "line_number": self.line_number,
        }


@dataclass
class AssemblyProgram:
    """Complete result of Target Code Generation."""

    code: str
    instructions: List[AssemblyInstruction]
    instruction_count: int
    stack_frame_size: int
    variable_offsets: Dict[str, int]
    target_arch: str = "x86-64"
    target_syntax: str = "NASM Intel Syntax"
    target_abi: str = "System V AMD64 ABI"
    runtime_dependencies: List[str] = field(default_factory=lambda: ["printf", "exit"])
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)
    is_valid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "instructions": [i.to_dict() for i in self.instructions],
            "instruction_count": self.instruction_count,
            "stack_frame_size": self.stack_frame_size,
            "variable_offsets": {
                k: f"[rbp - {v}]" for k, v in self.variable_offsets.items()
            },
            "target_arch": self.target_arch,
            "target_syntax": self.target_syntax,
            "target_abi": self.target_abi,
            "runtime_dependencies": self.runtime_dependencies,
            "diagnostics": self.diagnostics,
            "is_valid": self.is_valid,
        }


class CodeGenerator:
    """
    Translates validated VCL 3AC IR into x86-64 NASM assembly code.
    Allocates stack slots for all variables and temporaries deterministically.
    Preserves CFG control flow, branches, and semantic execution.
    """

    SUPPORTED_BINARY_OPS = {
        "+": "add",
        "-": "sub",
        "*": "imul",
        "/": "idiv",
        "%": "imod",
        "==": "sete",
        "!=": "setne",
        "<": "setl",
        "<=": "setle",
        ">": "setg",
        ">=": "setge",
        "&&": "and",
        "||": "or",
    }

    SUPPORTED_UNARY_OPS = {
        "-": "neg",
        "!": "not",
    }

    def __init__(self, target_abi: str = "sysv64"):
        """
        Args:
            target_abi: "sysv64" (Linux/macOS default) or "win64" (Windows x64)
        """
        self.target_abi = target_abi.lower()
        if self.target_abi not in ("sysv64", "win64"):
            self.target_abi = "sysv64"

        self.instructions: List[AssemblyInstruction] = []
        self.diagnostics: List[Diagnostic] = []
        self.var_offsets: Dict[str, int] = {}
        self.current_offset: int = 0
        self.needs_div_zero_trap: bool = False
        self.defined_labels: Set[str] = set()
        self.referenced_labels: Set[str] = set()

    def generate(self, ir_program: IRProgram, abi: Optional[str] = None) -> AssemblyProgram:
        """Translates an IRProgram into an AssemblyProgram."""
        if abi:
            self.target_abi = abi.lower()
            if self.target_abi not in ("sysv64", "win64"):
                self.target_abi = "sysv64"

        self.instructions = []
        self.diagnostics = []
        self.var_offsets = {}
        self.current_offset = 0
        self.needs_div_zero_trap = False
        self.defined_labels = set()
        self.referenced_labels = set()

        if not isinstance(ir_program, IRProgram) or not ir_program.instructions:
            # Empty program
            code_lines = [
                "; Veyra Visual Compiler — Target Code Generation (Empty Program)",
                "default rel",
                "section .text",
                "    global main",
                "main:",
                "    xor eax, eax",
                "    ret",
            ]
            empty_code = "\n".join(code_lines)
            return AssemblyProgram(
                code=empty_code,
                instructions=[
                    AssemblyInstruction(mnemonic="default", operands="rel", is_directive=True),
                    AssemblyInstruction(mnemonic="global", operands="main", is_directive=True),
                    AssemblyInstruction(label="main"),
                    AssemblyInstruction(mnemonic="xor", operands="eax, eax", comment="Return 0"),
                    AssemblyInstruction(mnemonic="ret"),
                ],
                instruction_count=2,
                stack_frame_size=0,
                variable_offsets={},
                target_arch="x86-64",
                target_syntax="NASM Intel Syntax",
                target_abi="System V AMD64 ABI" if self.target_abi == "sysv64" else "Microsoft x64 ABI",
                runtime_dependencies=[],
                diagnostics=[],
                is_valid=True,
            )

        # 1. First pass: Collect all distinct identifiers and temporaries
        self._allocate_stack_frame(ir_program)

        # Calculate aligned stack frame size (multiple of 16)
        # Note: In x86-64 calling convention, on entry before push rbp, (rsp % 16) == 8.
        # After push rbp, (rsp % 16) == 0.
        # Therefore, allocating a multiple of 16 bytes keeps rsp 16-byte aligned for calls!
        # On Windows x64, caller must also provide at least 32 bytes of shadow space.
        raw_size = self.current_offset
        if self.target_abi == "win64":
            raw_size += 32  # 32 bytes shadow space
        aligned_frame_size = ((raw_size + 15) // 16) * 16
        if aligned_frame_size < 16:
            aligned_frame_size = 16

        # 2. Translate 3AC instructions
        body_instructions: List[AssemblyInstruction] = []
        for inst in ir_program.instructions:
            inst_asm = self._translate_instruction(inst)
            body_instructions.extend(inst_asm)

        # 3. Validate jump targets
        for target in self.referenced_labels:
            if target not in self.defined_labels:
                self.diagnostics.append(
                    Diagnostic(
                        stage=DiagnosticStage.SEMANTIC,
                        message=f"Undefined jump label destination: '{target}'",
                        line=1,
                        column=1,
                        severity=DiagnosticSeverity.ERROR,
                    )
                )

        # 4. Assemble the full program with headers, prologue, body, and epilogue
        abi_name = "System V AMD64 ABI" if self.target_abi == "sysv64" else "Microsoft x64 ABI"
        header: List[AssemblyInstruction] = [
            AssemblyInstruction(comment="============================================================================="),
            AssemblyInstruction(comment="Veyra Visual Compiler — x86-64 Target Code Generation"),
            AssemblyInstruction(comment="Generated from Three-Address Code (3AC) Intermediate Representation"),
            AssemblyInstruction(comment=f"Target Architecture: x86-64 (Intel syntax)"),
            AssemblyInstruction(comment=f"Target ABI: {abi_name}"),
            AssemblyInstruction(comment=f"Allocated Stack Frame: {aligned_frame_size} bytes ({len(self.var_offsets)} slots)"),
            AssemblyInstruction(comment="============================================================================="),
            AssemblyInstruction(comment=""),
            AssemblyInstruction(mnemonic="default", operands="rel", is_directive=True, comment="Use RIP-relative addressing"),
            AssemblyInstruction(comment=""),
            AssemblyInstruction(mnemonic="section", operands=".rodata", is_directive=True, comment="Read-only data section"),
            AssemblyInstruction(mnemonic="fmt_int:", operands='db "%ld", 10, 0', is_directive=True, comment="Integer print format"),
            AssemblyInstruction(mnemonic="str_true:", operands='db "true", 10, 0', is_directive=True, comment="Boolean true string"),
            AssemblyInstruction(mnemonic="str_false:", operands='db "false", 10, 0', is_directive=True, comment="Boolean false string"),
        ]

        if self.needs_div_zero_trap:
            header.append(
                AssemblyInstruction(
                    mnemonic="err_div0:",
                    operands='db "Runtime Error: Division by zero", 10, 0',
                    is_directive=True,
                    comment="Runtime error string",
                )
            )

        header.extend([
            AssemblyInstruction(comment=""),
            AssemblyInstruction(mnemonic="section", operands=".text", is_directive=True, comment="Executable code section"),
            AssemblyInstruction(mnemonic="global", operands="main", is_directive=True, comment="Export main symbol"),
            AssemblyInstruction(mnemonic="extern", operands="printf", is_directive=True, comment="C runtime printf"),
            AssemblyInstruction(mnemonic="extern", operands="exit", is_directive=True, comment="C runtime exit"),
            AssemblyInstruction(comment=""),
            AssemblyInstruction(label="main", comment="Program entry point"),
            AssemblyInstruction(comment="--- Function Prologue ---"),
            AssemblyInstruction(mnemonic="push", operands="rbp", comment="Save caller frame pointer"),
            AssemblyInstruction(mnemonic="mov", operands="rbp, rsp", comment="Establish new frame pointer"),
            AssemblyInstruction(
                mnemonic="sub",
                operands=f"rsp, {aligned_frame_size}",
                comment=f"Allocate {aligned_frame_size} bytes (16-byte aligned)",
            ),
            AssemblyInstruction(comment=""),
            AssemblyInstruction(comment="--- Begin 3AC Instruction Translation ---"),
        ])

        epilogue: List[AssemblyInstruction] = [
            AssemblyInstruction(comment=""),
            AssemblyInstruction(comment="--- Function Epilogue ---"),
            AssemblyInstruction(label=".L_exit_normal", comment="Normal program termination"),
            AssemblyInstruction(mnemonic="xor", operands="eax, eax", comment="Return code 0"),
            AssemblyInstruction(mnemonic="mov", operands="rsp, rbp", comment="Restore stack pointer"),
            AssemblyInstruction(mnemonic="pop", operands="rbp", comment="Restore frame pointer"),
            AssemblyInstruction(mnemonic="ret", comment="Return to runtime caller"),
        ]

        if self.needs_div_zero_trap:
            if self.target_abi == "win64":
                div_trap_insts = [
                    AssemblyInstruction(comment=""),
                    AssemblyInstruction(label=".L_div_zero_trap", comment="Division by zero runtime trap"),
                    AssemblyInstruction(mnemonic="lea", operands="rcx, [rel err_div0]", comment="Error message argument"),
                    AssemblyInstruction(mnemonic="call", operands="printf", comment="Emit runtime error"),
                    AssemblyInstruction(mnemonic="mov", operands="rcx, 1", comment="Exit code 1"),
                    AssemblyInstruction(mnemonic="call", operands="exit", comment="Terminate process"),
                ]
            else:
                div_trap_insts = [
                    AssemblyInstruction(comment=""),
                    AssemblyInstruction(label=".L_div_zero_trap", comment="Division by zero runtime trap"),
                    AssemblyInstruction(mnemonic="lea", operands="rdi, [rel err_div0]", comment="Error message argument"),
                    AssemblyInstruction(mnemonic="xor", operands="eax, eax", comment="0 vector registers for printf"),
                    AssemblyInstruction(mnemonic="call", operands="printf", comment="Emit runtime error"),
                    AssemblyInstruction(mnemonic="mov", operands="rdi, 1", comment="Exit code 1"),
                    AssemblyInstruction(mnemonic="call", operands="exit", comment="Terminate process"),
                ]
            epilogue.extend(div_trap_insts)

        all_instructions = header + body_instructions + epilogue

        # Number lines and generate full text
        code_lines = []
        inst_count = 0
        for idx, inst in enumerate(all_instructions, start=1):
            inst.line_number = idx
            code_lines.append(inst.to_text())
            if inst.mnemonic and not inst.is_directive and not inst.mnemonic.endswith(":"):
                inst_count += 1

        full_code = "\n".join(code_lines)
        is_valid = not any(d.severity == DiagnosticSeverity.ERROR for d in self.diagnostics)

        return AssemblyProgram(
            code=full_code,
            instructions=all_instructions,
            instruction_count=inst_count,
            stack_frame_size=aligned_frame_size,
            variable_offsets=self.var_offsets,
            target_arch="x86-64",
            target_syntax="NASM Intel Syntax",
            target_abi=abi_name,
            runtime_dependencies=["printf", "exit"],
            diagnostics=[d.to_dict() for d in self.diagnostics],
            is_valid=is_valid,
        )

    # -------------------------------------------------------------------------
    # Stack Allocation
    # -------------------------------------------------------------------------

    def _allocate_stack_frame(self, ir_program: IRProgram) -> None:
        """Assigns deterministic [rbp - offset] stack positions for all variables/temps."""
        for inst in ir_program.instructions:
            if isinstance(inst, CopyInstruction):
                self._register_operand(inst.result)
                self._register_operand(inst.source)
            elif isinstance(inst, BinaryOpInstruction):
                self._register_operand(inst.result)
                self._register_operand(inst.left)
                self._register_operand(inst.right)
            elif isinstance(inst, UnaryOpInstruction):
                self._register_operand(inst.result)
                self._register_operand(inst.operand)
            elif isinstance(inst, PrintInstruction):
                self._register_operand(inst.value)
            elif isinstance(inst, (JumpIfFalseInstruction, JumpIfTrueInstruction)):
                self._register_operand(inst.condition)
            elif isinstance(inst, LabelInstruction):
                self.defined_labels.add(inst.name)
            elif isinstance(inst, JumpInstruction):
                self.referenced_labels.add(inst.target)

    def _register_operand(self, operand: Optional[str]) -> None:
        if not operand:
            return
        # If literal constant, no stack allocation needed
        if self._is_literal(operand):
            return
        # If identifier or temporary
        if operand not in self.var_offsets:
            self.current_offset += 8  # 64-bit quadword (8 bytes)
            self.var_offsets[operand] = self.current_offset

    def _is_literal(self, val: str) -> bool:
        if val in ("true", "false"):
            return True
        try:
            int(val)
            return True
        except ValueError:
            pass
        try:
            float(val)
            return True
        except ValueError:
            pass
        return False

    def _get_operand_loc(self, operand: str) -> str:
        """Returns the assembly operand representation (immediate or [rbp - offset])."""
        if operand == "true":
            return "1"
        if operand == "false":
            return "0"
        try:
            int(operand)
            return operand
        except ValueError:
            pass
        try:
            f = float(operand)
            return str(int(f))
        except ValueError:
            pass

        # Identifier or temporary variable
        if operand in self.var_offsets:
            offset = self.var_offsets[operand]
            return f"qword [rbp - {offset}]"

        # If not found, register on the fly
        self.current_offset += 8
        self.var_offsets[operand] = self.current_offset
        return f"qword [rbp - {self.current_offset}]"

    # -------------------------------------------------------------------------
    # Instruction Translation
    # -------------------------------------------------------------------------

    def _translate_instruction(self, inst: IRInstruction) -> List[AssemblyInstruction]:
        out: List[AssemblyInstruction] = []

        if isinstance(inst, LabelInstruction):
            self.defined_labels.add(inst.name)
            out.append(AssemblyInstruction(comment=""))
            out.append(AssemblyInstruction(label=inst.name, comment=f"3AC: {inst.to_text()}"))
            return out

        if isinstance(inst, JumpInstruction):
            self.referenced_labels.add(inst.target)
            out.append(
                AssemblyInstruction(
                    mnemonic="jmp",
                    operands=inst.target,
                    comment=f"3AC: {inst.to_text()}",
                )
            )
            return out

        if isinstance(inst, JumpIfFalseInstruction):
            self.referenced_labels.add(inst.target)
            cond_loc = self._get_operand_loc(inst.condition)
            out.append(AssemblyInstruction(comment=f"3AC: {inst.to_text()}"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"rax, {cond_loc}", comment="Load condition value"))
            out.append(AssemblyInstruction(mnemonic="cmp", operands="rax, 0", comment="Check if condition is false (0)"))
            out.append(AssemblyInstruction(mnemonic="je", operands=inst.target, comment=f"Branch to {inst.target} if false"))
            return out

        if isinstance(inst, JumpIfTrueInstruction):
            self.referenced_labels.add(inst.target)
            cond_loc = self._get_operand_loc(inst.condition)
            out.append(AssemblyInstruction(comment=f"3AC: {inst.to_text()}"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"rax, {cond_loc}", comment="Load condition value"))
            out.append(AssemblyInstruction(mnemonic="cmp", operands="rax, 0", comment="Check if condition is true (!= 0)"))
            out.append(AssemblyInstruction(mnemonic="jne", operands=inst.target, comment=f"Branch to {inst.target} if true"))
            return out

        if isinstance(inst, CopyInstruction):
            res_loc = self._get_operand_loc(inst.result)
            src_loc = self._get_operand_loc(inst.source)
            out.append(AssemblyInstruction(comment=f"3AC: {inst.to_text()}"))

            # If source is an immediate constant
            if not src_loc.startswith("qword"):
                out.append(
                    AssemblyInstruction(
                        mnemonic="mov",
                        operands=f"{res_loc}, {src_loc}",
                        comment=f"{inst.result} = {inst.source}",
                    )
                )
            else:
                # Memory to memory requires a register intermediary
                out.append(AssemblyInstruction(mnemonic="mov", operands=f"rax, {src_loc}", comment=f"Load {inst.source}"))
                out.append(AssemblyInstruction(mnemonic="mov", operands=f"{res_loc}, rax", comment=f"Store to {inst.result}"))
            return out

        if isinstance(inst, BinaryOpInstruction):
            out.extend(self._translate_binary_op(inst))
            return out

        if isinstance(inst, UnaryOpInstruction):
            out.extend(self._translate_unary_op(inst))
            return out

        if isinstance(inst, PrintInstruction):
            out.extend(self._translate_print(inst))
            return out

        # Unsupported instruction fallback
        self.diagnostics.append(
            Diagnostic(
                stage=DiagnosticStage.SEMANTIC,
                message=f"Unsupported 3AC instruction type: '{inst.__class__.__name__}'",
                line=getattr(inst, "line", 1),
                column=getattr(inst, "column", 1),
                severity=DiagnosticSeverity.ERROR,
            )
        )
        out.append(
            AssemblyInstruction(
                comment=f"UNSUPPORTED INSTRUCTION: {inst.to_text()}"
            )
        )
        return out

    def _translate_binary_op(self, inst: BinaryOpInstruction) -> List[AssemblyInstruction]:
        out: List[AssemblyInstruction] = []
        op = inst.op
        res_loc = self._get_operand_loc(inst.result)
        left_loc = self._get_operand_loc(inst.left)
        right_loc = self._get_operand_loc(inst.right)

        out.append(AssemblyInstruction(comment=f"3AC: {inst.to_text()}"))

        if op not in self.SUPPORTED_BINARY_OPS:
            self.diagnostics.append(
                Diagnostic(
                    stage=DiagnosticStage.SEMANTIC,
                    message=f"Unsupported binary operator in target code generation: '{op}'",
                    line=inst.line,
                    column=inst.column,
                    severity=DiagnosticSeverity.ERROR,
                )
            )
            out.append(AssemblyInstruction(comment=f"ERROR: unsupported operator {op}"))
            return out

        # Load left operand into rax
        out.append(AssemblyInstruction(mnemonic="mov", operands=f"rax, {left_loc}", comment=f"rax = {inst.left}"))

        if op == "+":
            out.append(AssemblyInstruction(mnemonic="add", operands=f"rax, {right_loc}", comment=f"rax += {inst.right}"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"{res_loc}, rax", comment=f"{inst.result} = rax"))

        elif op == "-":
            out.append(AssemblyInstruction(mnemonic="sub", operands=f"rax, {right_loc}", comment=f"rax -= {inst.right}"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"{res_loc}, rax", comment=f"{inst.result} = rax"))

        elif op == "*":
            # If right is memory or reg, imul rax, right_loc works directly in 64-bit
            if not right_loc.startswith("qword"):
                out.append(AssemblyInstruction(mnemonic="imul", operands=f"rax, {right_loc}", comment=f"rax *= {inst.right}"))
            else:
                out.append(AssemblyInstruction(mnemonic="mov", operands=f"rbx, {right_loc}", comment=f"rbx = {inst.right}"))
                out.append(AssemblyInstruction(mnemonic="imul", operands="rax, rbx", comment="rax *= rbx"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"{res_loc}, rax", comment=f"{inst.result} = rax"))

        elif op in ("/", "%"):
            self.needs_div_zero_trap = True
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"rbx, {right_loc}", comment=f"rbx = {inst.right} (divisor)"))
            out.append(AssemblyInstruction(mnemonic="cmp", operands="rbx, 0", comment="Check divisor == 0"))
            out.append(AssemblyInstruction(mnemonic="je", operands=".L_div_zero_trap", comment="Trap division by zero"))
            out.append(AssemblyInstruction(mnemonic="cqo", operands="", comment="Sign-extend rax into rdx:rax"))
            out.append(AssemblyInstruction(mnemonic="idiv", operands="rbx", comment="Signed divide rdx:rax by rbx"))
            if op == "/":
                out.append(AssemblyInstruction(mnemonic="mov", operands=f"{res_loc}, rax", comment=f"{inst.result} = quotient (rax)"))
            else:
                out.append(AssemblyInstruction(mnemonic="mov", operands=f"{res_loc}, rdx", comment=f"{inst.result} = remainder (rdx)"))

        elif op in ("==", "!=", "<", "<=", ">", ">="):
            set_inst = self.SUPPORTED_BINARY_OPS[op]
            out.append(AssemblyInstruction(mnemonic="cmp", operands=f"rax, {right_loc}", comment=f"Compare {inst.left} vs {inst.right}"))
            out.append(AssemblyInstruction(mnemonic=set_inst, operands="al", comment=f"Set byte if {op} condition holds"))
            out.append(AssemblyInstruction(mnemonic="movzx", operands="rax, al", comment="Zero-extend boolean byte to 64-bit"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"{res_loc}, rax", comment=f"{inst.result} = rax"))

        elif op == "&&":
            out.append(AssemblyInstruction(mnemonic="cmp", operands="rax, 0", comment=f"Test {inst.left} != 0"))
            out.append(AssemblyInstruction(mnemonic="setne", operands="al", comment="al = (left != 0)"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"rbx, {right_loc}", comment=f"rbx = {inst.right}"))
            out.append(AssemblyInstruction(mnemonic="cmp", operands="rbx, 0", comment=f"Test {inst.right} != 0"))
            out.append(AssemblyInstruction(mnemonic="setne", operands="bl", comment="bl = (right != 0)"))
            out.append(AssemblyInstruction(mnemonic="and", operands="al, bl", comment="al = al && bl"))
            out.append(AssemblyInstruction(mnemonic="movzx", operands="rax, al", comment="Zero-extend to 64-bit"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"{res_loc}, rax", comment=f"{inst.result} = rax"))

        elif op == "||":
            out.append(AssemblyInstruction(mnemonic="cmp", operands="rax, 0", comment=f"Test {inst.left} != 0"))
            out.append(AssemblyInstruction(mnemonic="setne", operands="al", comment="al = (left != 0)"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"rbx, {right_loc}", comment=f"rbx = {inst.right}"))
            out.append(AssemblyInstruction(mnemonic="cmp", operands="rbx, 0", comment=f"Test {inst.right} != 0"))
            out.append(AssemblyInstruction(mnemonic="setne", operands="bl", comment="bl = (right != 0)"))
            out.append(AssemblyInstruction(mnemonic="or", operands="al, bl", comment="al = al || bl"))
            out.append(AssemblyInstruction(mnemonic="movzx", operands="rax, al", comment="Zero-extend to 64-bit"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"{res_loc}, rax", comment=f"{inst.result} = rax"))

        return out

    def _translate_unary_op(self, inst: UnaryOpInstruction) -> List[AssemblyInstruction]:
        out: List[AssemblyInstruction] = []
        op = inst.op
        res_loc = self._get_operand_loc(inst.result)
        op_loc = self._get_operand_loc(inst.operand)

        out.append(AssemblyInstruction(comment=f"3AC: {inst.to_text()}"))

        if op not in self.SUPPORTED_UNARY_OPS:
            self.diagnostics.append(
                Diagnostic(
                    stage=DiagnosticStage.SEMANTIC,
                    message=f"Unsupported unary operator in target code generation: '{op}'",
                    line=inst.line,
                    column=inst.column,
                    severity=DiagnosticSeverity.ERROR,
                )
            )
            out.append(AssemblyInstruction(comment=f"ERROR: unsupported unary operator {op}"))
            return out

        out.append(AssemblyInstruction(mnemonic="mov", operands=f"rax, {op_loc}", comment=f"rax = {inst.operand}"))

        if op == "-":
            out.append(AssemblyInstruction(mnemonic="neg", operands="rax", comment="Two's complement negation"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"{res_loc}, rax", comment=f"{inst.result} = -rax"))

        elif op == "!":
            out.append(AssemblyInstruction(mnemonic="cmp", operands="rax, 0", comment="Test if operand == 0"))
            out.append(AssemblyInstruction(mnemonic="sete", operands="al", comment="al = (operand == 0)"))
            out.append(AssemblyInstruction(mnemonic="movzx", operands="rax, al", comment="Zero-extend boolean byte"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"{res_loc}, rax", comment=f"{inst.result} = !operand"))

        return out

    def _translate_print(self, inst: PrintInstruction) -> List[AssemblyInstruction]:
        out: List[AssemblyInstruction] = []
        val_loc = self._get_operand_loc(inst.value)

        out.append(AssemblyInstruction(comment=f"3AC: {inst.to_text()}"))

        if inst.value == "true":
            if self.target_abi == "win64":
                out.append(AssemblyInstruction(mnemonic="lea", operands="rcx, [rel str_true]", comment="Argument: 'true' string"))
                out.append(AssemblyInstruction(mnemonic="call", operands="printf", comment="Print boolean true"))
            else:
                out.append(AssemblyInstruction(mnemonic="lea", operands="rdi, [rel str_true]", comment="Argument 1: 'true' string"))
                out.append(AssemblyInstruction(mnemonic="xor", operands="eax, eax", comment="0 vector registers"))
                out.append(AssemblyInstruction(mnemonic="call", operands="printf", comment="Print boolean true"))
            return out

        if inst.value == "false":
            if self.target_abi == "win64":
                out.append(AssemblyInstruction(mnemonic="lea", operands="rcx, [rel str_false]", comment="Argument: 'false' string"))
                out.append(AssemblyInstruction(mnemonic="call", operands="printf", comment="Print boolean false"))
            else:
                out.append(AssemblyInstruction(mnemonic="lea", operands="rdi, [rel str_false]", comment="Argument 1: 'false' string"))
                out.append(AssemblyInstruction(mnemonic="xor", operands="eax, eax", comment="0 vector registers"))
                out.append(AssemblyInstruction(mnemonic="call", operands="printf", comment="Print boolean false"))
            return out

        # Integer or computed numeric expression
        if self.target_abi == "win64":
            out.append(AssemblyInstruction(mnemonic="lea", operands="rcx, [rel fmt_int]", comment="Argument 1: '%ld\\n' format"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"rdx, {val_loc}", comment=f"Argument 2: {inst.value}"))
            out.append(AssemblyInstruction(mnemonic="call", operands="printf", comment=f"Print integer {inst.value}"))
        else:
            out.append(AssemblyInstruction(mnemonic="lea", operands="rdi, [rel fmt_int]", comment="Argument 1: '%ld\\n' format"))
            out.append(AssemblyInstruction(mnemonic="mov", operands=f"rsi, {val_loc}", comment=f"Argument 2: {inst.value}"))
            out.append(AssemblyInstruction(mnemonic="xor", operands="eax, eax", comment="0 vector registers for printf"))
            out.append(AssemblyInstruction(mnemonic="call", operands="printf", comment=f"Print integer {inst.value}"))

        return out
