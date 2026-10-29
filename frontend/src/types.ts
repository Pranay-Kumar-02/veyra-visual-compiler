/**
 * Veyra Visual Compiler — Core Data & Pipeline Types
 * Supports Review 1, 2, and 3: AST, Symbol Table, 3AC IR,
 * Control Flow Graph (CFG), 3AC Optimization, and Step-by-Step Debugger.
 */

export interface TokenItem {
  type: string;
  lexeme: string;
  literal: any;
  line: number;
  column: number;
  source_pos: number;
  category: string;
}

export interface ASTNodeData {
  node_type: string;
  label: string;
  line: number;
  column: number;
  details?: string;
  children?: ASTNodeData[];
  operator?: string;
  value?: any;
  name?: string;
  target?: string;
  raw_type?: string;
}

export interface SymbolItem {
  name: string;
  type: string;
  value: string;
  scope: string;
  scope_level: number;
  line: number;
  column: number;
}

export interface IRInstructionItem {
  kind: string;
  op: string;
  result: string | null;
  arg1: string | null;
  arg2: string | null;
  formatted: string;
  line: number;
  column: number;
}

export interface IRData {
  instructions: IRInstructionItem[];
  code: string;
  instruction_count: number;
  temp_count: number;
  label_count: number;
}

// ----------------------------------------------------------------------------
// Phase 3: Control Flow Graph (CFG) Types
// ----------------------------------------------------------------------------
export interface CFGBlock {
  id: string;
  index: number;
  instructions: IRInstructionItem[];
  instruction_count: number;
  predecessors: string[];
  successors: string[];
  is_entry: boolean;
  is_exit: boolean;
  reachable: boolean;
  labels: string[];
  lines: string[];
}

export interface CFGEdge {
  from_block: string;
  to_block: string;
  edge_type: 'unconditional' | 'true' | 'false' | 'fallthrough' | 'backedge';
  condition?: string | null;
  is_backedge?: boolean;
}

export interface CFGData {
  blocks: CFGBlock[];
  edges: CFGEdge[];
  entry_block_id: string | null;
  exit_block_ids: string[];
  block_count: number;
  edge_count: number;
  validation_errors: string[];
  is_valid: boolean;
}

// ----------------------------------------------------------------------------
// Phase 3: 3AC Optimization Types
// ----------------------------------------------------------------------------
export interface TransformationItem {
  pass_name: string;
  original: string;
  optimized: string;
  reason: string;
  line: number;
  column: number;
}

export interface OptimizationReportData {
  original_code: string;
  optimized_code: string;
  original_instruction_count: number;
  optimized_instruction_count: number;
  reduction_count: number;
  transformation_count: number;
  transformations: TransformationItem[];
  metrics: {
    original_count: number;
    optimized_count: number;
    instructions_removed: number;
    transformations_applied: number;
    passes_executed: Record<string, number>;
  };
  is_valid: boolean;
  validation_errors: string[];
}

// ----------------------------------------------------------------------------
// Phase 3: Step-by-Step Debugger Types
// ----------------------------------------------------------------------------
export interface VariableSnapshot {
  value: any;
  type: string;
}

export interface BranchDecisionInfo {
  condition_line: number;
  evaluated_result: boolean;
  branch_taken: string;
}

export interface DebugEventItem {
  step_index: number;
  event_type: 'start' | 'step' | 'var_declare' | 'assignment' | 'branch_decision' | 'print' | 'runtime_error' | 'completed';
  line: number;
  column: number;
  node_type: string;
  description: string;
  variables: Record<string, VariableSnapshot>;
  changed_variable?: string | null;
  branch_info?: BranchDecisionInfo | null;
  output_so_far: string[];
  error?: {
    message: string;
    line: number;
    column: number;
    hint?: string | null;
  } | null;
}

export interface DebugTraceData {
  events: DebugEventItem[];
  total_steps: number;
  completed_normally: boolean;
  final_output: string[];
  runtime_error?: string | null;
}

// ----------------------------------------------------------------------------
// Diagnostic & Telemetry Types
// ----------------------------------------------------------------------------
export interface DiagnosticItem {
  stage: string;
  message: string;
  line: number;
  column: number;
  severity: string;
  hint: string | null;
  formatted: string;
}

// ----------------------------------------------------------------------------
// Target Code Generation (x86-64 NASM Assembly) Types
// ----------------------------------------------------------------------------
export interface AssemblyInstructionItem {
  label?: string | null;
  mnemonic?: string | null;
  operands?: string | null;
  comment?: string | null;
  is_directive?: boolean;
  formatted: string;
  line_number: number;
}

export interface AssemblyData {
  code: string;
  instructions: AssemblyInstructionItem[];
  instruction_count: number;
  stack_frame_size: number;
  variable_offsets: Record<string, string>;
  target_arch: string;
  target_syntax: string;
  target_abi: string;
  runtime_dependencies: string[];
  diagnostics: DiagnosticItem[];
  is_valid: boolean;
}

export interface MetricsData {
  token_count: number;
  symbol_count: number;
  ir_instruction_count: number;
  optimized_instruction_count?: number;
  assembly_instruction_count?: number;
  cfg_block_count?: number;
  cfg_edge_count?: number;
  debug_step_count?: number;
  diagnostic_count: number;
  output_line_count: number;
  diagnostic_pipeline_duration_ms: number;
}

export interface CompilationResult {
  success: boolean;
  tokens: TokenItem[];
  ast: ASTNodeData | null;
  symbol_table: SymbolItem[];
  ir: IRData | null;
  ir_code: string;
  cfg?: CFGData | null;
  optimized_ir?: IRData | null;
  optimized_ir_code?: string;
  optimization_report?: OptimizationReportData | null;
  assembly?: AssemblyData | null;
  assembly_code?: string;
  debug_trace?: DebugTraceData | null;
  diagnostics: DiagnosticItem[];
  output: string;
  output_lines: string[];
  stages_executed: string[];
  metrics: MetricsData;
}

export type ViewTab = 'ast' | 'ir' | 'cfg' | 'optimizer' | 'target' | 'debugger' | 'symbols' | 'tokens' | 'diagnostics' | 'output';

export type WorkspaceMode = '3d-spatial' | 'split-workbench' | 'focus-editor';

