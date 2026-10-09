/**
 * Veyra Visual Compiler — Core Data & Pipeline Types
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

export interface DiagnosticItem {
  stage: string;
  message: string;
  line: number;
  column: number;
  severity: string;
  hint: string | null;
  formatted: string;
}

export interface MetricsData {
  token_count: number;
  symbol_count: number;
  ir_instruction_count: number;
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
  diagnostics: DiagnosticItem[];
  output: string;
  output_lines: string[];
  stages_executed: string[];
  metrics: MetricsData;
}

export type ViewTab = 'ast' | 'ir' | 'symbols' | 'tokens' | 'diagnostics' | 'output';

export type WorkspaceMode = '3d-spatial' | 'split-workbench' | 'focus-editor';
