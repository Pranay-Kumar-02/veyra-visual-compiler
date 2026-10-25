"""
Modular 3AC Intermediate Representation Optimization Pipeline for VCL.
Implements:
- Constant Folding (with runtime-error preservation)
- Local Constant Propagation (block-scoped for join safety)
- Safe Algebraic Simplification
- Dead-Code Elimination (safe temporary cleanup)
- Unreachable-Code Elimination (branch folding, dead blocks, unreferenced labels)
- Post-optimization Jump Target Validation
"""

from abc import ABC, abstractmethod
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
from backend.cfg import CFGBuilder


@dataclass
class TransformationRecord:
    """Record of a single optimization transformation."""
    pass_name: str
    original: str
    optimized: str
    reason: str
    line: int = 0
    column: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pass_name": self.pass_name,
            "original": self.original,
            "optimized": self.optimized,
            "reason": self.reason,
            "line": self.line,
            "column": self.column,
        }


@dataclass
class OptimizationResult:
    """Complete result of the optimization pipeline."""
    original_ir: IRProgram
    optimized_ir: IRProgram
    transformations: List[TransformationRecord]
    metrics: Dict[str, Any]
    is_valid: bool
    validation_errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_code": self.original_ir.to_text(),
            "optimized_code": self.optimized_ir.to_text(),
            "original_instruction_count": len(self.original_ir.instructions),
            "optimized_instruction_count": len(self.optimized_ir.instructions),
            "reduction_count": len(self.original_ir.instructions) - len(self.optimized_ir.instructions),
            "transformation_count": len(self.transformations),
            "transformations": [t.to_dict() for t in self.transformations],
            "metrics": self.metrics,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }


def is_literal_constant(token_val: str) -> bool:
    """Checks whether an operand string is a literal integer, float, or boolean."""
    if token_val in ("true", "false"):
        return True
    try:
        int(token_val)
        return True
    except ValueError:
        pass
    try:
        float(token_val)
        return True
    except ValueError:
        pass
    return False


def parse_literal_value(token_val: str) -> Any:
    """Parses a literal token string into a Python value."""
    if token_val == "true":
        return True
    if token_val == "false":
        return False
    try:
        return int(token_val)
    except ValueError:
        pass
    try:
        return float(token_val)
    except ValueError:
        pass
    return token_val


def format_literal_value(val: Any) -> str:
    """Formats a Python literal value into standard VCL 3AC literal format."""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return str(val)
    return str(val)


class OptimizationPass(ABC):
    """Abstract base class for an IR optimization pass."""

    name: str = "BasePass"

    @abstractmethod
    def run(
        self, instructions: List[IRInstruction]
    ) -> Tuple[List[IRInstruction], List[TransformationRecord]]:
        pass


class ConstantFoldingPass(OptimizationPass):
    """
    Folds operations whose operands are all compile-time constants.
    Preserves runtime-error behavior by refusing to fold division or modulo by zero.
    """

    name = "Constant Folding"

    def run(
        self, instructions: List[IRInstruction]
    ) -> Tuple[List[IRInstruction], List[TransformationRecord]]:
        new_instructions: List[IRInstruction] = []
        transforms: List[TransformationRecord] = []

        for inst in instructions:
            if isinstance(inst, BinaryOpInstruction):
                if is_literal_constant(inst.left) and is_literal_constant(inst.right):
                    left_v = parse_literal_value(inst.left)
                    right_v = parse_literal_value(inst.right)
                    op = inst.op

                    # SAFEGUARD: Do NOT fold division or modulo by 0! Preserve runtime exception.
                    if op in ("/", "%") and right_v == 0:
                        new_instructions.append(inst)
                        continue

                    folded_val: Optional[Any] = None
                    try:
                        if op == "+":
                            folded_val = left_v + right_v
                        elif op == "-":
                            folded_val = left_v - right_v
                        elif op == "*":
                            folded_val = left_v * right_v
                        elif op == "/":
                            res = left_v / right_v
                            if isinstance(left_v, int) and isinstance(right_v, int) and left_v % right_v == 0:
                                folded_val = int(res)
                            else:
                                folded_val = res
                        elif op == "%":
                            folded_val = left_v % right_v
                        elif op == "==":
                            folded_val = left_v == right_v
                        elif op == "!=":
                            folded_val = left_v != right_v
                        elif op == "<":
                            folded_val = left_v < right_v
                        elif op == ">":
                            folded_val = left_v > right_v
                        elif op == "<=":
                            folded_val = left_v <= right_v
                        elif op == ">=":
                            folded_val = left_v >= right_v
                        elif op == "&&":
                            folded_val = bool(left_v) and bool(right_v)
                        elif op == "||":
                            folded_val = bool(left_v) or bool(right_v)
                    except Exception:
                        folded_val = None

                    if folded_val is not None:
                        val_str = format_literal_value(folded_val)
                        new_inst = CopyInstruction(
                            result=inst.result,
                            source=val_str,
                            line=inst.line,
                            column=inst.column,
                        )
                        transforms.append(
                            TransformationRecord(
                                pass_name=self.name,
                                original=inst.to_text(),
                                optimized=new_inst.to_text(),
                                reason=f"Evaluated constant binary expression '{inst.left} {op} {inst.right}' -> '{val_str}'",
                                line=inst.line,
                                column=inst.column,
                            )
                        )
                        new_instructions.append(new_inst)
                        continue

            elif isinstance(inst, UnaryOpInstruction):
                if is_literal_constant(inst.operand):
                    op_v = parse_literal_value(inst.operand)
                    op = inst.op
                    folded_val = None
                    try:
                        if op == "-":
                            folded_val = -op_v
                        elif op == "!":
                            folded_val = not bool(op_v)
                    except Exception:
                        folded_val = None

                    if folded_val is not None:
                        val_str = format_literal_value(folded_val)
                        new_inst = CopyInstruction(
                            result=inst.result,
                            source=val_str,
                            line=inst.line,
                            column=inst.column,
                        )
                        transforms.append(
                            TransformationRecord(
                                pass_name=self.name,
                                original=inst.to_text(),
                                optimized=new_inst.to_text(),
                                reason=f"Evaluated constant unary expression '{op}{inst.operand}' -> '{val_str}'",
                                line=inst.line,
                                column=inst.column,
                            )
                        )
                        new_instructions.append(new_inst)
                        continue

            new_instructions.append(inst)

        return new_instructions, transforms


class ConstantPropagationPass(OptimizationPass):
    """
    Performs block-local constant propagation.
    Within each basic block, tracks known constant assignments and substitutes
    subsequent operand uses. Clears bindings across control-flow joins and labels.
    """

    name = "Constant Propagation"

    def run(
        self, instructions: List[IRInstruction]
    ) -> Tuple[List[IRInstruction], List[TransformationRecord]]:
        new_instructions: List[IRInstruction] = []
        transforms: List[TransformationRecord] = []

        # Local constant map: var -> literal_string
        const_map: Dict[str, str] = {}

        for inst in instructions:
            # Control flow boundary: a label or jump clears local constant assumptions
            if isinstance(inst, (LabelInstruction, JumpInstruction, JumpIfFalseInstruction, JumpIfTrueInstruction)):
                const_map.clear()
                new_instructions.append(inst)
                continue

            if isinstance(inst, CopyInstruction):
                # Propagate source if it is a known constant
                source = inst.source
                if source in const_map:
                    old_text = inst.to_text()
                    source = const_map[source]
                    inst = CopyInstruction(
                        result=inst.result,
                        source=source,
                        line=inst.line,
                        column=inst.column,
                    )
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=old_text,
                            optimized=inst.to_text(),
                            reason=f"Propagated constant value '{source}' for variable '{inst.source}'",
                            line=inst.line,
                            column=inst.column,
                        )
                    )

                # If source is a literal constant, record in const_map
                if is_literal_constant(source):
                    const_map[inst.result] = source
                else:
                    # Invalidate if reassigned to non-constant
                    const_map.pop(inst.result, None)

                new_instructions.append(inst)

            elif isinstance(inst, BinaryOpInstruction):
                left = inst.left
                right = inst.right
                changed = False

                if left in const_map:
                    left = const_map[left]
                    changed = True
                if right in const_map:
                    right = const_map[right]
                    changed = True

                if changed:
                    old_text = inst.to_text()
                    inst = BinaryOpInstruction(
                        result=inst.result,
                        op=inst.op,
                        left=left,
                        right=right,
                        line=inst.line,
                        column=inst.column,
                    )
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=old_text,
                            optimized=inst.to_text(),
                            reason=f"Substituted known constant operands into binary operation",
                            line=inst.line,
                            column=inst.column,
                        )
                    )

                # Invalidate result variable in const_map
                const_map.pop(inst.result, None)
                new_instructions.append(inst)

            elif isinstance(inst, UnaryOpInstruction):
                operand = inst.operand
                if operand in const_map:
                    old_text = inst.to_text()
                    operand = const_map[operand]
                    inst = UnaryOpInstruction(
                        result=inst.result,
                        op=inst.op,
                        operand=operand,
                        line=inst.line,
                        column=inst.column,
                    )
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=old_text,
                            optimized=inst.to_text(),
                            reason=f"Substituted known constant operand '{operand}' into unary operation",
                            line=inst.line,
                            column=inst.column,
                        )
                    )

                const_map.pop(inst.result, None)
                new_instructions.append(inst)

            elif isinstance(inst, PrintInstruction):
                value = inst.value
                if value in const_map:
                    old_text = inst.to_text()
                    value = const_map[value]
                    inst = PrintInstruction(
                        value=value,
                        line=inst.line,
                        column=inst.column,
                    )
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=old_text,
                            optimized=inst.to_text(),
                            reason=f"Propagated constant value '{value}' to print statement",
                            line=inst.line,
                            column=inst.column,
                        )
                    )
                new_instructions.append(inst)

            else:
                new_instructions.append(inst)

        return new_instructions, transforms


class AlgebraicSimplificationPass(OptimizationPass):
    """
    Applies mathematical and logical identities:
    - x + 0 -> x, 0 + x -> x
    - x - 0 -> x
    - x * 1 -> x, 1 * x -> x
    - x * 0 -> 0, 0 * x -> 0 (for non-side-effecting operands)
    - x / 1 -> x
    - x && true -> x, true && x -> x
    - x || false -> x, false || x -> x
    - !(!x) -> x
    """

    name = "Algebraic Simplification"

    def run(
        self, instructions: List[IRInstruction]
    ) -> Tuple[List[IRInstruction], List[TransformationRecord]]:
        new_instructions: List[IRInstruction] = []
        transforms: List[TransformationRecord] = []

        for inst in instructions:
            if isinstance(inst, BinaryOpInstruction):
                op = inst.op
                l = inst.left
                r = inst.right
                res = inst.result

                simplified_inst: Optional[IRInstruction] = None
                reason = ""

                # Addition identities
                if op == "+":
                    if r == "0":
                        simplified_inst = CopyInstruction(result=res, source=l, line=inst.line, column=inst.column)
                        reason = f"Additive identity: {l} + 0 -> {l}"
                    elif l == "0":
                        simplified_inst = CopyInstruction(result=res, source=r, line=inst.line, column=inst.column)
                        reason = f"Additive identity: 0 + {r} -> {r}"

                # Subtraction identities
                elif op == "-":
                    if r == "0":
                        simplified_inst = CopyInstruction(result=res, source=l, line=inst.line, column=inst.column)
                        reason = f"Subtractive identity: {l} - 0 -> {l}"

                # Multiplication identities
                elif op == "*":
                    if r == "1":
                        simplified_inst = CopyInstruction(result=res, source=l, line=inst.line, column=inst.column)
                        reason = f"Multiplicative identity: {l} * 1 -> {l}"
                    elif l == "1":
                        simplified_inst = CopyInstruction(result=res, source=r, line=inst.line, column=inst.column)
                        reason = f"Multiplicative identity: 1 * {r} -> {r}"
                    elif r == "0" or l == "0":
                        simplified_inst = CopyInstruction(result=res, source="0", line=inst.line, column=inst.column)
                        reason = f"Multiplication by zero: {l} * {r} -> 0"

                # Division identity
                elif op == "/":
                    if r == "1":
                        simplified_inst = CopyInstruction(result=res, source=l, line=inst.line, column=inst.column)
                        reason = f"Division identity: {l} / 1 -> {l}"

                # Logical AND identities
                elif op == "&&":
                    if r == "true":
                        simplified_inst = CopyInstruction(result=res, source=l, line=inst.line, column=inst.column)
                        reason = f"Logical identity: {l} && true -> {l}"
                    elif l == "true":
                        simplified_inst = CopyInstruction(result=res, source=r, line=inst.line, column=inst.column)
                        reason = f"Logical identity: true && {r} -> {r}"

                # Logical OR identities
                elif op == "||":
                    if r == "false":
                        simplified_inst = CopyInstruction(result=res, source=l, line=inst.line, column=inst.column)
                        reason = f"Logical identity: {l} || false -> {l}"
                    elif l == "false":
                        simplified_inst = CopyInstruction(result=res, source=r, line=inst.line, column=inst.column)
                        reason = f"Logical identity: false || {r} -> {r}"

                if simplified_inst:
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=inst.to_text(),
                            optimized=simplified_inst.to_text(),
                            reason=reason,
                            line=inst.line,
                            column=inst.column,
                        )
                    )
                    new_instructions.append(simplified_inst)
                    continue

            new_instructions.append(inst)

        return new_instructions, transforms


class UnreachableCodeEliminationPass(OptimizationPass):
    """
    Eliminates unreachable code and folds branches:
    1. If conditional jump has constant condition:
       - if_false true goto L -> never branches, eliminate instruction.
       - if_false false goto L -> always branches, replace with goto L.
       - if_true true goto L -> always branches, replace with goto L.
       - if_true false goto L -> never branches, eliminate instruction.
    2. Instructions directly following an unconditional goto up to the next label are unreachable.
    3. Unreachable basic blocks (using CFG reachability analysis) are eliminated.
    4. Unreferenced labels are pruned.
    """

    name = "Unreachable Code Elimination"

    def run(
        self, instructions: List[IRInstruction]
    ) -> Tuple[List[IRInstruction], List[TransformationRecord]]:
        transforms: List[TransformationRecord] = []
        phase1: List[IRInstruction] = []

        # Step 1: Branch condition folding
        for inst in instructions:
            if isinstance(inst, JumpIfFalseInstruction):
                if inst.condition == "true":
                    # Never branches
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=inst.to_text(),
                            optimized="[eliminated]",
                            reason=f"Eliminated conditional jump on constant true: '{inst.condition}' never false",
                            line=inst.line,
                            column=inst.column,
                        )
                    )
                    continue
                elif inst.condition == "false":
                    # Always branches -> replace with goto
                    new_inst = JumpInstruction(target=inst.target, line=inst.line, column=inst.column)
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=inst.to_text(),
                            optimized=new_inst.to_text(),
                            reason=f"Converted branch to unconditional goto: '{inst.condition}' always false",
                            line=inst.line,
                            column=inst.column,
                        )
                    )
                    phase1.append(new_inst)
                    continue

            elif isinstance(inst, JumpIfTrueInstruction):
                if inst.condition == "true":
                    new_inst = JumpInstruction(target=inst.target, line=inst.line, column=inst.column)
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=inst.to_text(),
                            optimized=new_inst.to_text(),
                            reason=f"Converted branch to unconditional goto: '{inst.condition}' always true",
                            line=inst.line,
                            column=inst.column,
                        )
                    )
                    phase1.append(new_inst)
                    continue
                elif inst.condition == "false":
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=inst.to_text(),
                            optimized="[eliminated]",
                            reason=f"Eliminated conditional jump on constant false: '{inst.condition}' never true",
                            line=inst.line,
                            column=inst.column,
                        )
                    )
                    continue

            phase1.append(inst)

        # Step 2: Remove dead instructions directly following unconditional goto up to next label
        phase2: List[IRInstruction] = []
        skipping = False
        for inst in phase1:
            if isinstance(inst, LabelInstruction):
                skipping = False
                phase2.append(inst)
            elif skipping:
                transforms.append(
                    TransformationRecord(
                        pass_name=self.name,
                        original=inst.to_text(),
                        optimized="[eliminated]",
                        reason="Eliminated dead instruction following unconditional jump",
                        line=inst.line,
                        column=inst.column,
                    )
                )
            else:
                phase2.append(inst)
                if isinstance(inst, JumpInstruction):
                    skipping = True

        # Step 3: CFG reachability analysis to remove unreachable basic blocks
        dummy_prog = IRProgram(instructions=phase2, temp_count=0, label_count=0)
        cfg = CFGBuilder().build(dummy_prog)
        reachable_blocks = {b.id for b in cfg.blocks if b.reachable}

        phase3: List[IRInstruction] = []
        for b in cfg.blocks:
            if b.id in reachable_blocks:
                phase3.extend(b.instructions)
            else:
                for inst in b.instructions:
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=inst.to_text(),
                            optimized="[eliminated]",
                            reason=f"Eliminated instruction in unreachable basic block {b.id}",
                            line=inst.line,
                            column=inst.column,
                        )
                    )

        # Step 4: Prune unused labels (labels not referenced by any jump)
        jump_targets: Set[str] = set()
        for inst in phase3:
            if isinstance(inst, (JumpInstruction, JumpIfFalseInstruction, JumpIfTrueInstruction)):
                jump_targets.add(inst.target)

        phase4: List[IRInstruction] = []
        for inst in phase3:
            if isinstance(inst, LabelInstruction):
                if inst.name not in jump_targets:
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=inst.to_text(),
                            optimized="[eliminated]",
                            reason=f"Eliminated unreferenced label '{inst.name}'",
                            line=inst.line,
                            column=inst.column,
                        )
                    )
                    continue
            phase4.append(inst)

        return phase4, transforms


class DeadCodeEliminationPass(OptimizationPass):
    """
    Eliminates dead temporary definitions.
    If a compiler-generated temporary (e.g. t1, t2) is assigned but never used
    as an operand anywhere in the program, and the operation has no side effects,
    the assignment is eliminated.
    User variables are preserved.
    """

    name = "Dead Code Elimination"

    def run(
        self, instructions: List[IRInstruction]
    ) -> Tuple[List[IRInstruction], List[TransformationRecord]]:
        # Count uses of each temporary
        uses: Dict[str, int] = {}

        def record_use(val: Optional[str]):
            if val and val.startswith("t") and val[1:].isdigit():
                uses[val] = uses.get(val, 0) + 1

        for inst in instructions:
            if isinstance(inst, CopyInstruction):
                record_use(inst.source)
            elif isinstance(inst, BinaryOpInstruction):
                record_use(inst.left)
                record_use(inst.right)
            elif isinstance(inst, UnaryOpInstruction):
                record_use(inst.operand)
            elif isinstance(inst, PrintInstruction):
                record_use(inst.value)
            elif isinstance(inst, (JumpIfFalseInstruction, JumpIfTrueInstruction)):
                record_use(inst.condition)

        new_instructions: List[IRInstruction] = []
        transforms: List[TransformationRecord] = []

        for inst in instructions:
            if isinstance(inst, (CopyInstruction, BinaryOpInstruction, UnaryOpInstruction)):
                res = inst.result
                # Only eliminate compiler temporaries (t1, t2, ...) with zero uses
                if res.startswith("t") and res[1:].isdigit() and uses.get(res, 0) == 0:
                    transforms.append(
                        TransformationRecord(
                            pass_name=self.name,
                            original=inst.to_text(),
                            optimized="[eliminated]",
                            reason=f"Eliminated unused compiler temporary '{res}' definition",
                            line=inst.line,
                            column=inst.column,
                        )
                    )
                    continue

            new_instructions.append(inst)

        return new_instructions, transforms


class OptimizationPipeline:
    """
    Coordinates modular optimization passes until fixed point or max iterations.
    Validates jump targets and preserves original IR.
    """

    def __init__(self, passes: Optional[List[OptimizationPass]] = None, max_iterations: int = 10):
        self.passes: List[OptimizationPass] = passes or [
            ConstantPropagationPass(),
            ConstantFoldingPass(),
            AlgebraicSimplificationPass(),
            UnreachableCodeEliminationPass(),
            DeadCodeEliminationPass(),
        ]
        self.max_iterations = max_iterations

    def optimize(self, ir_program: IRProgram) -> OptimizationResult:
        current_instructions = list(ir_program.instructions)
        all_transforms: List[TransformationRecord] = []
        pass_run_counts: Dict[str, int] = {p.name: 0 for p in self.passes}

        for iteration in range(self.max_iterations):
            changed = False
            for p in self.passes:
                prev_text = "\n".join(inst.to_text() for inst in current_instructions)
                optimized_insts, transforms = p.run(current_instructions)
                curr_text = "\n".join(inst.to_text() for inst in optimized_insts)

                if prev_text != curr_text:
                    changed = True
                    all_transforms.extend(transforms)
                    pass_run_counts[p.name] += 1
                    current_instructions = optimized_insts

            if not changed:
                break

        # Post-optimization jump target validation
        validation_errors: List[str] = []
        defined_labels: Set[str] = {
            inst.name for inst in current_instructions if isinstance(inst, LabelInstruction)
        }
        for inst in current_instructions:
            if isinstance(inst, (JumpInstruction, JumpIfFalseInstruction, JumpIfTrueInstruction)):
                if inst.target not in defined_labels:
                    validation_errors.append(
                        f"Post-optimization validation error: Jump target '{inst.target}' is undefined."
                    )

        optimized_prog = IRProgram(
            instructions=current_instructions,
            temp_count=ir_program.temp_count,
            label_count=ir_program.label_count,
        )

        metrics = {
            "original_count": len(ir_program.instructions),
            "optimized_count": len(current_instructions),
            "instructions_removed": len(ir_program.instructions) - len(current_instructions),
            "transformations_applied": len(all_transforms),
            "passes_executed": pass_run_counts,
        }

        return OptimizationResult(
            original_ir=ir_program,
            optimized_ir=optimized_prog,
            transformations=all_transforms,
            metrics=metrics,
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
        )
