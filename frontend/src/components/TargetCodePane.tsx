import React, { useState } from 'react';
import { AssemblyData, DiagnosticItem } from '../types';
import {
  Copy,
  Check,
  Download,
  Search,
  Binary,
  Layers,
  ShieldCheck,
  AlertTriangle,
  Info,
} from 'lucide-react';

interface TargetCodePaneProps {
  assembly: AssemblyData | null;
  assemblyCode: string;
  diagnostics?: DiagnosticItem[];
}

export const TargetCodePane: React.FC<TargetCodePaneProps> = ({
  assembly,
  assemblyCode,
  diagnostics = [],
}) => {
  const [copied, setCopied] = useState(false);
  const [filterText, setFilterText] = useState('');
  const [showStackDrawer, setShowStackDrawer] = useState(true);

  if (!assembly || !assembly.code) {
    return (
      <div className="state-empty-clean">
        <Binary size={26} style={{ color: 'var(--text-faint)' }} />
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-dim)', marginTop: 8 }}>
          No Target Assembly Emitted
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', maxWidth: 360, textAlign: 'center', marginTop: 4 }}>
          Target machine code synthesis converts optimized Three-Address Code into x86-64 NASM Intel-syntax assembly with stack frame allocation.
        </div>
      </div>
    );
  }

  const rawText = assemblyCode || assembly.code;

  const handleCopy = () => {
    navigator.clipboard.writeText(rawText);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  const handleDownload = () => {
    const blob = new Blob([rawText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'veyra_target_code.asm';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const rawLines = rawText.split('\n');
  const filteredLines = filterText.trim() === ''
    ? rawLines
    : rawLines.filter((l) => l.toLowerCase().includes(filterText.toLowerCase()));

  // Render a single line with precise x86-64 syntax highlighting
  const renderHighlightedLine = (line: string) => {
    // Empty line
    if (!line.trim()) {
      return <span>&nbsp;</span>;
    }

    // Comment-only line
    const trimmed = line.trim();
    if (trimmed.startsWith(';')) {
      return <span className="asm-token-comment">{line}</span>;
    }

    // Split line into code and trailing comment
    const commentIdx = line.indexOf(';');
    let codePart = commentIdx !== -1 ? line.substring(0, commentIdx) : line;
    const commentPart = commentIdx !== -1 ? line.substring(commentIdx) : '';

    // Directives: section, default, global, extern, db
    if (/^\s*(default|section|global|extern)\b/i.test(codePart)) {
      return (
        <span>
          <span className="asm-token-directive">{codePart}</span>
          {commentPart && <span className="asm-token-comment">{commentPart}</span>}
        </span>
      );
    }

    // Labels: e.g. main:, L1:, .L_exit_normal:, fmt_int:
    if (/^([a-zA-Z0-9_.]+):/i.test(codePart.trim())) {
      const match = codePart.trim().match(/^([a-zA-Z0-9_.]+):(.*)$/);
      if (match) {
        return (
          <span>
            <span className="asm-token-label">{match[1]}:</span>
            <span className="asm-token-label-rest">{match[2]}</span>
            {commentPart && <span className="asm-token-comment">{commentPart}</span>}
          </span>
        );
      }
    }

    // General Instruction parsing: Mnemonic + Operands
    // Split into leading spaces, mnemonic, and operands
    const matchInst = codePart.match(/^(\s*)([a-zA-Z]+)(\s+)(.*)$/);
    if (matchInst) {
      const [, leadSpace, mnemonic, midSpace, operands] = matchInst;

      // Colorize operand tokens
      const formattedOperands = renderOperands(operands);

      return (
        <span>
          <span>{leadSpace}</span>
          <span className="asm-token-mnemonic">{mnemonic}</span>
          <span>{midSpace}</span>
          {formattedOperands}
          {commentPart && <span className="asm-token-comment">{commentPart}</span>}
        </span>
      );
    }

    // Single token without operands (e.g. ret, cqo)
    const matchSingle = codePart.match(/^(\s*)([a-zA-Z]+)(\s*)$/);
    if (matchSingle) {
      const [, leadSpace, mnemonic, trailSpace] = matchSingle;
      return (
        <span>
          <span>{leadSpace}</span>
          <span className="asm-token-mnemonic">{mnemonic}</span>
          <span>{trailSpace}</span>
          {commentPart && <span className="asm-token-comment">{commentPart}</span>}
        </span>
      );
    }

    return (
      <span>
        {codePart}
        {commentPart && <span className="asm-token-comment">{commentPart}</span>}
      </span>
    );
  };

  const renderOperands = (operandsStr: string) => {
    // Tokenize operands: registers, memory [rbp - X], numbers, commas, strings
    const parts = operandsStr.split(/(\[.*?\]|"[^"]*"|[a-zA-Z0-9_.]+|[,+\-*])/g);
    const registers = new Set([
      'rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rbp', 'rsp',
      'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15',
      'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp',
      'al', 'bl', 'cl', 'dl', 'sil', 'dil',
    ]);

    return parts.map((part, idx) => {
      if (!part) return null;
      const lower = part.toLowerCase();

      if (registers.has(lower)) {
        return <span key={idx} className="asm-token-register">{part}</span>;
      }
      if (part.startsWith('[') && part.endsWith(']')) {
        return <span key={idx} className="asm-token-memory">{part}</span>;
      }
      if (/^qword$/i.test(part)) {
        return <span key={idx} className="asm-token-type">{part}</span>;
      }
      if (/^-?\d+$/.test(part)) {
        return <span key={idx} className="asm-token-imm">{part}</span>;
      }
      if (part.startsWith('"') && part.endsWith('"')) {
        return <span key={idx} className="asm-token-string">{part}</span>;
      }
      if (['L1', 'L2', 'L3', 'L4', 'L5', '.L_exit_normal', '.L_div_zero_trap'].includes(part)) {
        return <span key={idx} className="asm-token-label-ref">{part}</span>;
      }
      if (part === ',') {
        return <span key={idx} style={{ color: 'var(--text-faint)', marginRight: 4 }}>,</span>;
      }
      return <span key={idx}>{part}</span>;
    });
  };

  const varOffsetEntries = Object.entries(assembly.variable_offsets || {});
  const codegenDiagnostics = diagnostics.filter(
    (d) => d.stage === 'Semantic Error' || d.stage === 'System Error' || d.message.toLowerCase().includes('target')
  );

  return (
    <div className="view-content-pane">
      {/* Top Banner / Metadata Header */}
      <div className="view-content-header" style={{ flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Binary size={13} style={{ color: 'var(--accent)' }} />
            <span className="view-content-title">x86-64 Target Code</span>
          </div>

          <span className="asm-meta-badge" title="Target architecture and syntax">
            {assembly.target_arch} · {assembly.target_syntax}
          </span>

          <span className="asm-meta-badge muted" title="Target Calling Convention">
            {assembly.target_abi}
          </span>

          <span style={{ fontSize: 10.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {assembly.instruction_count} insts · {assembly.stack_frame_size}B frame
          </span>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {/* Filter Search */}
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={10} style={{ position: 'absolute', left: 6, color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Filter ASM..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              className="asm-filter-input"
            />
          </div>

          {/* Toggle Stack Slot Drawer */}
          <button
            className={`pane-action-btn ${showStackDrawer ? 'active' : ''}`}
            onClick={() => setShowStackDrawer(!showStackDrawer)}
            title="Toggle Stack Allocation Map ([rbp - offset])"
          >
            <Layers size={11} />
            <span>Stack Slots ({varOffsetEntries.length})</span>
          </button>

          {/* Copy Assembly */}
          <button
            className="pane-action-btn"
            onClick={handleCopy}
            title="Copy NASM assembly to clipboard"
          >
            {copied ? (
              <Check size={11} style={{ color: 'var(--color-success)' }} />
            ) : (
              <Copy size={11} />
            )}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {/* Download .asm File */}
          <button
            className="pane-action-btn primary"
            onClick={handleDownload}
            title="Download target code as .asm file"
          >
            <Download size={11} />
            <span>Download .asm</span>
          </button>
        </div>
      </div>

      {/* Diagnostics Alert Banner (if any) */}
      {codegenDiagnostics.length > 0 && (
        <div className="asm-diagnostics-banner">
          <AlertTriangle size={13} style={{ color: 'var(--color-warning)', flexShrink: 0 }} />
          <div style={{ flex: 1, fontSize: 11 }}>
            <span style={{ fontWeight: 600 }}>Target Generation Notice: </span>
            {codegenDiagnostics.map((d, i) => (
              <span key={i}>{d.message} </span>
            ))}
          </div>
        </div>
      )}

      {/* Main Workspace Body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left: Syntax-Highlighted Assembly Editor View */}
        <div className="asm-editor-view">
          <div className="asm-line-col">
            {filteredLines.map((_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>

          <div className="asm-code-col">
            {filteredLines.map((line, idx) => (
              <div key={idx} className="asm-code-line">
                {renderHighlightedLine(line)}
              </div>
            ))}
          </div>
        </div>

        {/* Right: Stack Frame & ABI Inspector Sidebar */}
        {showStackDrawer && (
          <div className="asm-stack-drawer">
            <div className="asm-drawer-header">
              <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-main)' }}>
                Stack Frame Allocation
              </span>
              <span className="asm-pill-sm">
                16-byte Aligned
              </span>
            </div>

            <div className="asm-drawer-content">
              {/* Stack Frame Summary Card */}
              <div className="asm-card-summary">
                <div className="asm-stat-row">
                  <span className="asm-stat-label">Stack Reserved:</span>
                  <span className="asm-stat-val">{assembly.stack_frame_size} bytes</span>
                </div>
                <div className="asm-stat-row">
                  <span className="asm-stat-label">Base Register:</span>
                  <span className="asm-stat-val" style={{ color: 'var(--color-purple)' }}>rbp</span>
                </div>
                <div className="asm-stat-row">
                  <span className="asm-stat-label">Alignment:</span>
                  <span className="asm-stat-val" style={{ color: 'var(--color-success)' }}>0 mod 16</span>
                </div>
                <div className="asm-stat-row">
                  <span className="asm-stat-label">Runtime Call:</span>
                  <span className="asm-stat-val">{assembly.runtime_dependencies.join(', ')}</span>
                </div>
              </div>

              {/* Variable to Slot Mapping Table */}
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.04em' }}>
                  Symbol Stack Slots
                </div>

                {varOffsetEntries.length === 0 ? (
                  <div style={{ fontSize: 11, color: 'var(--text-faint)', fontStyle: 'italic', padding: 4 }}>
                    No stack slots allocated (registers only).
                  </div>
                ) : (
                  <div className="asm-slots-list">
                    {varOffsetEntries.map(([name, slot], idx) => {
                      const isTemp = /^t\d+$/.test(name);
                      return (
                        <div key={idx} className="asm-slot-item">
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span className={isTemp ? 'asm-temp-pill' : 'asm-var-pill'}>
                              {name}
                            </span>
                          </div>
                          <span className="asm-slot-addr">{slot}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* ABI Information Card */}
              <div className="asm-abi-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <ShieldCheck size={12} style={{ color: 'var(--accent)' }} />
                  <span style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-dim)' }}>
                    ABI Calling Standard
                  </span>
                </div>
                <p style={{ fontSize: 10, color: 'var(--text-muted)', lineHeight: 1.45 }}>
                  {assembly.target_abi.includes('System V')
                    ? 'SysV AMD64: Args in rdi, rsi, rdx, rcx, r8, r9. rax = 0 for varargs printf. Stack aligned to 16 bytes.'
                    : 'Win64: Args in rcx, rdx, r8, r9 with 32 bytes shadow space allocated on stack frame.'}
                </p>
              </div>

              {/* Verification Info */}
              <div style={{ marginTop: 10, padding: '8px 10px', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Info size={11} style={{ color: 'var(--text-muted)' }} />
                  <span style={{ fontSize: 10, color: 'var(--text-dim)', fontWeight: 500 }}>
                    Deterministic Generation
                  </span>
                </div>
                <div style={{ fontSize: 9.5, color: 'var(--text-muted)', marginTop: 2 }}>
                  Generated directly from optimized 3AC instructions without heuristic alteration.
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
