"""
Control Flow Graph (CFG) Construction and Analysis for VCL Three-Address Code.
Constructs basic blocks, directed control-flow edges, resolves jump targets,
performs reachability analysis, and detects back-edges.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from backend.ir import (
    IRInstruction,
    IRProgram,
    LabelInstruction,
    JumpInstruction,
    JumpIfFalseInstruction,
    JumpIfTrueInstruction,
    CopyInstruction,
    BinaryOpInstruction,
    UnaryOpInstruction,
    PrintInstruction,
)


@dataclass
class CFGEdge:
    """Directed edge between two basic blocks."""
    from_block: str
    to_block: str
    edge_type: str  # 'unconditional' | 'true' | 'false' | 'fallthrough' | 'backedge'
    condition: Optional[str] = None
    is_backedge: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_block": self.from_block,
            "to_block": self.to_block,
            "edge_type": self.edge_type,
            "condition": self.condition,
            "is_backedge": self.is_backedge,
        }


@dataclass
class BasicBlock:
    """A maximal sequence of consecutive instructions with single-entry and single-exit."""
    id: str  # e.g., 'B0', 'B1'
    index: int
    instructions: List[IRInstruction] = field(default_factory=list)
    predecessors: List[str] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False
    reachable: bool = True
    labels: List[str] = field(default_factory=list)  # Labels defined at the head of this block

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "index": self.index,
            "instructions": [inst.to_dict() for inst in self.instructions],
            "instruction_count": len(self.instructions),
            "predecessors": self.predecessors,
            "successors": self.successors,
            "is_entry": self.is_entry,
            "is_exit": self.is_exit,
            "reachable": self.reachable,
            "labels": self.labels,
            "lines": [inst.to_text() for inst in self.instructions],
        }


@dataclass
class ControlFlowGraph:
    """Complete Control Flow Graph derived from Three-Address Code."""
    blocks: List[BasicBlock]
    edges: List[CFGEdge]
    entry_block_id: Optional[str] = None
    exit_block_ids: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)

    def get_block(self, block_id: str) -> Optional[BasicBlock]:
        for b in self.blocks:
            if b.id == block_id:
                return b
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocks": [b.to_dict() for b in self.blocks],
            "edges": [e.to_dict() for e in self.edges],
            "entry_block_id": self.entry_block_id,
            "exit_block_ids": self.exit_block_ids,
            "block_count": len(self.blocks),
            "edge_count": len(self.edges),
            "validation_errors": self.validation_errors,
            "is_valid": len(self.validation_errors) == 0,
        }


class CFGBuilder:
    """
    Constructs a Control Flow Graph from a list of 3AC instructions.
    Follows canonical leader-identification and block-construction algorithms.
    """

    def build(self, ir_program: IRProgram) -> ControlFlowGraph:
        instructions = ir_program.instructions
        if not instructions:
            return ControlFlowGraph(
                blocks=[],
                edges=[],
                entry_block_id=None,
                exit_block_ids=[],
                validation_errors=[],
            )

        validation_errors: List[str] = []

        # ---------------------------------------------------------------------
        # Step 1: Identify Leader Instructions
        # ---------------------------------------------------------------------
        # Rule 1: The first instruction is a leader.
        # Rule 2: Any instruction that is the target of a conditional or unconditional jump is a leader.
        # Rule 3: Any instruction immediately following a conditional or unconditional jump is a leader.
        n = len(instructions)
        leader_indices: Set[int] = {0}
        label_to_index: Dict[str, int] = {}

        # Collect all label indices
        for i, inst in enumerate(instructions):
            if isinstance(inst, LabelInstruction):
                label_to_index[inst.name] = i
                leader_indices.add(i)

        # Check jump targets and subsequent instructions
        for i, inst in enumerate(instructions):
            if isinstance(inst, JumpInstruction):
                if inst.target in label_to_index:
                    leader_indices.add(label_to_index[inst.target])
                else:
                    validation_errors.append(
                        f"Instruction {i} ('{inst.to_text()}'): Jump target label '{inst.target}' is undefined."
                    )
                if i + 1 < n:
                    leader_indices.add(i + 1)

            elif isinstance(inst, (JumpIfFalseInstruction, JumpIfTrueInstruction)):
                target = inst.target
                if target in label_to_index:
                    leader_indices.add(label_to_index[target])
                else:
                    validation_errors.append(
                        f"Instruction {i} ('{inst.to_text()}'): Conditional jump target label '{target}' is undefined."
                    )
                if i + 1 < n:
                    leader_indices.add(i + 1)

        sorted_leaders = sorted(leader_indices)

        # ---------------------------------------------------------------------
        # Step 2: Form Basic Blocks from Leaders
        # ---------------------------------------------------------------------
        blocks: List[BasicBlock] = []
        inst_index_to_block_id: Dict[int, str] = {}
        label_to_block_id: Dict[str, str] = {}

        for b_idx, start_idx in enumerate(sorted_leaders):
            end_idx = sorted_leaders[b_idx + 1] if b_idx + 1 < len(sorted_leaders) else n
            block_instructions = instructions[start_idx:end_idx]
            block_id = f"B{b_idx}"

            labels: List[str] = []
            for inst in block_instructions:
                if isinstance(inst, LabelInstruction):
                    labels.append(inst.name)
                    label_to_block_id[inst.name] = block_id

            block = BasicBlock(
                id=block_id,
                index=b_idx,
                instructions=block_instructions,
                is_entry=(b_idx == 0),
                labels=labels,
            )
            blocks.append(block)

            for idx in range(start_idx, end_idx):
                inst_index_to_block_id[idx] = block_id

        # ---------------------------------------------------------------------
        # Step 3: Resolve Control-Flow Edges
        # ---------------------------------------------------------------------
        edges: List[CFGEdge] = []
        block_by_id: Dict[str, BasicBlock] = {b.id: b for b in blocks}

        for i, block in enumerate(blocks):
            if not block.instructions:
                continue

            last_inst = block.instructions[-1]

            if isinstance(last_inst, JumpInstruction):
                # Unconditional Jump: single successor
                target_label = last_inst.target
                target_block_id = label_to_block_id.get(target_label)
                if target_block_id:
                    edges.append(
                        CFGEdge(
                            from_block=block.id,
                            to_block=target_block_id,
                            edge_type="unconditional",
                        )
                    )
                else:
                    validation_errors.append(
                        f"Block {block.id} ends with jump to unresolved label '{target_label}'."
                    )

            elif isinstance(last_inst, JumpIfFalseInstruction):
                # Conditional Jump (False): two successors
                # Successor 1: Taken branch when condition is False
                target_label = last_inst.target
                target_block_id = label_to_block_id.get(target_label)
                if target_block_id:
                    edges.append(
                        CFGEdge(
                            from_block=block.id,
                            to_block=target_block_id,
                            edge_type="false",
                            condition=last_inst.condition,
                        )
                    )
                else:
                    validation_errors.append(
                        f"Block {block.id} ends with branch to unresolved label '{target_label}'."
                    )

                # Successor 2: Fall-through branch when condition is True
                if i + 1 < len(blocks):
                    next_block_id = blocks[i + 1].id
                    edges.append(
                        CFGEdge(
                            from_block=block.id,
                            to_block=next_block_id,
                            edge_type="true",
                            condition=last_inst.condition,
                        )
                    )

            elif isinstance(last_inst, JumpIfTrueInstruction):
                # Conditional Jump (True): two successors
                # Successor 1: Taken branch when condition is True
                target_label = last_inst.target
                target_block_id = label_to_block_id.get(target_label)
                if target_block_id:
                    edges.append(
                        CFGEdge(
                            from_block=block.id,
                            to_block=target_block_id,
                            edge_type="true",
                            condition=last_inst.condition,
                        )
                    )
                else:
                    validation_errors.append(
                        f"Block {block.id} ends with branch to unresolved label '{target_label}'."
                    )

                # Successor 2: Fall-through branch when condition is False
                if i + 1 < len(blocks):
                    next_block_id = blocks[i + 1].id
                    edges.append(
                        CFGEdge(
                            from_block=block.id,
                            to_block=next_block_id,
                            edge_type="false",
                            condition=last_inst.condition,
                        )
                    )

            else:
                # Normal Fall-through to next basic block
                if i + 1 < len(blocks):
                    next_block_id = blocks[i + 1].id
                    edges.append(
                        CFGEdge(
                            from_block=block.id,
                            to_block=next_block_id,
                            edge_type="fallthrough",
                        )
                    )

        # Populate predecessors and successors in each block
        for edge in edges:
            src = block_by_id.get(edge.from_block)
            dst = block_by_id.get(edge.to_block)
            if src and edge.to_block not in src.successors:
                src.successors.append(edge.to_block)
            if dst and edge.from_block not in dst.predecessors:
                dst.predecessors.append(edge.from_block)

        # ---------------------------------------------------------------------
        # Step 4: Reachability Analysis & Exit Identification
        # ---------------------------------------------------------------------
        entry_id = blocks[0].id if blocks else None
        reachable_ids: Set[str] = set()

        if entry_id:
            queue = [entry_id]
            reachable_ids.add(entry_id)
            while queue:
                curr_id = queue.pop(0)
                curr_block = block_by_id.get(curr_id)
                if curr_block:
                    for succ_id in curr_block.successors:
                        if succ_id not in reachable_ids:
                            reachable_ids.add(succ_id)
                            queue.append(succ_id)

        exit_block_ids: List[str] = []
        for b in blocks:
            b.reachable = b.id in reachable_ids
            # An exit block has no successors or represents terminal block
            if len(b.successors) == 0:
                b.is_exit = True
                exit_block_ids.append(b.id)

        if not exit_block_ids and blocks:
            # If all blocks have successors (e.g. infinite loop), mark last block as exit
            blocks[-1].is_exit = True
            exit_block_ids.append(blocks[-1].id)

        # ---------------------------------------------------------------------
        # Step 5: Detect Loop Back-Edges (DFS Timestamping)
        # ---------------------------------------------------------------------
        # In DFS from entry, an edge (u, v) is a back-edge iff v is currently an active ancestor in the recursion stack
        visited: Set[str] = set()
        on_stack: Set[str] = set()

        def dfs(u_id: str):
            visited.add(u_id)
            on_stack.add(u_id)
            u_block = block_by_id.get(u_id)
            if u_block:
                for v_id in u_block.successors:
                    if v_id in on_stack:
                        # Found a back-edge u_id -> v_id
                        for e in edges:
                            if e.from_block == u_id and e.to_block == v_id:
                                e.is_backedge = True
                    elif v_id not in visited:
                        dfs(v_id)
            on_stack.remove(u_id)

        if entry_id:
            dfs(entry_id)

        return ControlFlowGraph(
            blocks=blocks,
            edges=edges,
            entry_block_id=entry_id,
            exit_block_ids=exit_block_ids,
            validation_errors=validation_errors,
        )
