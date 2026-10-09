/**
 * Veyra Visual Compiler — Presets and Stage Definitions
 */

export interface PresetProgram {
  id: string;
  name: string;
  description: string;
  code: string;
}

export const PRESET_PROGRAMS: Record<string, PresetProgram> = {
  'phase2_demo': {
    id: 'phase2_demo',
    name: 'Phase 2 Flagship: 3AC & Branching',
    description: 'Representative arithmetic precedence with conditional if/else branching and 3AC linearization.',
    code: `let score = 20;
let bonus = 5;
let result = score + bonus * 2;

if (result >= 30) {
    print(result);
} else {
    print(0);
}`,
  },
  'arithmetic': {
    id: 'arithmetic',
    name: 'Arithmetic & Operator Precedence',
    description: 'Parenthesized expression parsing and arithmetic precedence evaluation.',
    code: `let a = 10;
let b = 5;
let c = 2;
let result = (a + b) * c;
print(result);`,
  },
  'conditions': {
    id: 'conditions',
    name: 'Conditional Evaluation',
    description: 'Relational operator comparison with boolean branch routing.',
    code: `let score = 85;
let threshold = 50;

if (score >= threshold) {
    print(1);
} else {
    print(0);
}`,
  },
  'scope': {
    id: 'scope',
    name: 'Block Scoping & Shadowing',
    description: 'Nested block scope variable isolation and mutations.',
    code: `let a = 10;
let b = 20;
let total = 0;

{
    let factor = 3;
    total = (a + b) * factor;
}

print(total);`,
  },
  'error_undeclared': {
    id: 'error_undeclared',
    name: 'Diagnostic: Undeclared Variable',
    description: 'Demonstrates static semantic analyzer catching undeclared symbol reference.',
    code: `let x = 10;
print(y);`,
  },
  'error_scope': {
    id: 'error_scope',
    name: 'Diagnostic: Scope Isolation Violation',
    description: 'Demonstrates static semantic analyzer preventing block-local variable access.',
    code: `let x = 10;

if (x > 5) {
    let y = 20;
}

print(y);`,
  },
  'error_syntax': {
    id: 'error_syntax',
    name: 'Diagnostic: Syntax Recovery Error',
    description: 'Demonstrates recursive-descent parser capturing malformed expression.',
    code: `let x = 10 + ;`,
  },
  'error_runtime': {
    id: 'error_runtime',
    name: 'Diagnostic: Division by Zero',
    description: 'Demonstrates 3AC generated cleanly, with runtime interpreter exception trap.',
    code: `let z = 10 / 0;
print(z);`,
  },
};

export interface StageDefinition {
  id: string;
  title: string;
  shortLabel: string;
  description: string;
  viewTab: 'ast' | 'ir' | 'symbols' | 'tokens' | 'diagnostics' | 'output';
  color: string;
  glowColor: string;
  positionX: number; // 3D spatial coordinate
  positionY: number;
  positionZ: number;
}

export const COMPILER_STAGES: StageDefinition[] = [
  {
    id: 'source',
    title: 'Source Code',
    shortLabel: 'SOURCE',
    description: 'Raw VCL program input text',
    viewTab: 'ast',
    color: '#94a3b8',
    glowColor: 'rgba(148, 163, 184, 0.4)',
    positionX: -14,
    positionY: 0,
    positionZ: 0,
  },
  {
    id: 'lexer',
    title: 'Lexical Analysis',
    shortLabel: 'LEXER',
    description: 'Character scanner producing token stream',
    viewTab: 'tokens',
    color: '#60a5fa',
    glowColor: 'rgba(96, 165, 250, 0.5)',
    positionX: -10,
    positionY: 1.2,
    positionZ: -1.5,
  },
  {
    id: 'parser',
    title: 'Syntactic Parsing',
    shortLabel: 'PARSER',
    description: 'Recursive-descent grammar enforcement',
    viewTab: 'ast',
    color: '#38bdf8',
    glowColor: 'rgba(56, 189, 248, 0.5)',
    positionX: -6,
    positionY: -0.5,
    positionZ: 1.2,
  },
  {
    id: 'ast',
    title: 'Abstract Syntax Tree',
    shortLabel: 'AST',
    description: 'Typed hierarchical syntax tree representation',
    viewTab: 'ast',
    color: '#2dd4bf',
    glowColor: 'rgba(45, 212, 191, 0.6)',
    positionX: -2,
    positionY: 1.5,
    positionZ: 0,
  },
  {
    id: 'semantic',
    title: 'Semantic Analysis',
    shortLabel: 'SEMANTIC',
    description: 'Static type checking and identifier resolution',
    viewTab: 'symbols',
    color: '#a78bfa',
    glowColor: 'rgba(167, 139, 250, 0.5)',
    positionX: 2,
    positionY: -0.8,
    positionZ: -1.5,
  },
  {
    id: 'symbols',
    title: 'Symbol Table',
    shortLabel: 'SYMBOLS',
    description: 'Hierarchical scope and variable binding records',
    viewTab: 'symbols',
    color: '#f59e0b',
    glowColor: 'rgba(245, 158, 11, 0.5)',
    positionX: 6,
    positionY: 1.0,
    positionZ: 1.2,
  },
  {
    id: 'ir',
    title: 'Three-Address Code (3AC)',
    shortLabel: '3AC / IR',
    description: 'Linear intermediate representation with temporaries & labels',
    viewTab: 'ir',
    color: '#14b8a6',
    glowColor: 'rgba(20, 184, 166, 0.6)',
    positionX: 10,
    positionY: -0.5,
    positionZ: -0.8,
  },
  {
    id: 'execution',
    title: 'Runtime Execution',
    shortLabel: 'EXECUTION',
    description: 'Interpreter environment & standard output capture',
    viewTab: 'output',
    color: '#10b981',
    glowColor: 'rgba(16, 185, 129, 0.6)',
    positionX: 14,
    positionY: 0.5,
    positionZ: 0,
  },
];
