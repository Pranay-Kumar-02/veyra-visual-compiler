import React, { useState } from 'react';
import { IRData, IRInstructionItem } from '../types';
import { Copy, Check, Search, Cpu } from 'lucide-react';

interface ThreeAddressCodePaneProps {
  ir: IRData | null;
  irCode: string;
}

export const ThreeAddressCodePane: React.FC<ThreeAddressCodePaneProps> = ({ ir, irCode }) => {
  const [copied, setCopied] = useState(false);
  const [filterText, setFilterText] = useState('');
  const [selectedInstruction, setSelectedInstruction] = useState<IRInstructionItem | null>(null);

  if (!ir || !ir.instructions || ir.instructions.length === 0) {
    return (
      <div className="state-empty-clean">
        <Cpu size={24} style={{ color: 'var(--text-faint)' }} />
        <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>No IR Instructions</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          Linear Three-Address Code is emitted upon successful semantic analysis.
        </div>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(irCode || ir.instructions.map((i) => i.formatted).join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const filteredInstructions = ir.instructions.filter((inst) =>
    inst.formatted.toLowerCase().includes(filterText.toLowerCase()) ||
    inst.kind.toLowerCase().includes(filterText.toLowerCase())
  );

  const renderInstructionText = (inst: IRInstructionItem) => {
    const text = inst.formatted;

    if (inst.kind === 'Label') {
      return <span className="ir-label">{text}</span>;
    }
    if (inst.kind.startsWith('Jump')) {
      return <span className="ir-branch">{text}</span>;
    }
    if (inst.kind === 'Print') {
      return <span className="ir-print">{text}</span>;
    }

    const parts = text.split(/(\s+|[=+\-*/%><]=?|==|!=)/g);
    return (
      <span>
        {parts.map((p, idx) => {
          if (/^t\d+$/.test(p)) {
            return <span key={idx} className="ir-temp">{p}</span>;
          }
          if (['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>='].includes(p)) {
            return <span key={idx} className="ir-op">{p}</span>;
          }
          if (p === '=') {
            return <span key={idx} style={{ color: 'var(--text-faint)' }}>{p}</span>;
          }
          return <span key={idx}>{p}</span>;
        })}
      </span>
    );
  };

  return (
    <div className="view-content-pane">
      {/* Header */}
      <div className="view-content-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="view-content-title">Three-Address Code (3AC)</span>
          <span style={{ fontSize: 10.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {ir.instruction_count} insts · {ir.temp_count} temps · {ir.label_count} labels
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={10} style={{ position: 'absolute', left: 6, color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Filter IR..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-xs)',
                padding: '2px 6px 2px 20px',
                color: 'var(--text-main)',
                fontSize: 11,
                fontFamily: 'var(--font-mono)',
                outline: 'none',
                width: 110,
              }}
            />
          </div>

          <button
            className="btn btn-secondary"
            onClick={handleCopy}
            style={{ padding: '3px 7px', fontSize: 11 }}
            title="Copy IR text"
          >
            {copied ? <Check size={11} style={{ color: 'var(--color-success)' }} /> : <Copy size={11} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* Main IR Code View */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div className="ir-editor-view">
          <div className="ir-line-col">
            {filteredInstructions.map((_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>

          <div className="ir-code-pane">
            {filteredInstructions.map((inst, i) => {
              const isSelected = selectedInstruction === inst;
              return (
                <div
                  key={i}
                  className={`ir-code-row ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedInstruction(isSelected ? null : inst)}
                >
                  <div>{renderInstructionText(inst)}</div>
                  {isSelected && (
                    <span style={{ fontSize: 10, color: 'var(--text-faint)' }}>
                      {inst.kind}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Instruction Details */}
        {selectedInstruction && (
          <div
            style={{
              width: 220,
              backgroundColor: 'var(--bg-surface)',
              borderLeft: '1px solid var(--border-subtle)',
              padding: 12,
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>Instruction</span>
              <button
                className="btn-icon"
                style={{ width: 18, height: 18 }}
                onClick={() => setSelectedInstruction(null)}
              >
                ×
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div style={{ color: 'var(--text-muted)' }}>Text:</div>
              <div style={{ color: 'var(--text-main)' }}>{selectedInstruction.formatted}</div>

              <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>Kind:</div>
              <div style={{ color: 'var(--accent)' }}>{selectedInstruction.kind}</div>

              {selectedInstruction.op && (
                <>
                  <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>Op:</div>
                  <div style={{ color: 'var(--text-dim)' }}>{selectedInstruction.op}</div>
                </>
              )}

              {selectedInstruction.result && (
                <>
                  <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>Result:</div>
                  <div style={{ color: 'var(--accent)' }}>{selectedInstruction.result}</div>
                </>
              )}

              <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>Source:</div>
              <div style={{ color: 'var(--text-dim)' }}>
                {selectedInstruction.line}:{selectedInstruction.column}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
