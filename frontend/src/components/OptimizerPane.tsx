import React, { useState } from 'react';
import { OptimizationReportData, IRData } from '../types';
import { Zap, ArrowRight, Sparkles, Copy, Check } from 'lucide-react';

interface OptimizerPaneProps {
  originalIr: IRData | null;
  originalCode: string;
  optimizedIr?: IRData | null;
  optimizedCode?: string;
  report?: OptimizationReportData | null;
}

export const OptimizerPane: React.FC<OptimizerPaneProps> = ({
  originalCode,
  optimizedCode,
  report,
}) => {
  const [selectedPass, setSelectedPass] = useState<string>('all');
  const [copiedOpt, setCopiedOpt] = useState<boolean>(false);

  if (!report || !optimizedCode) {
    return (
      <div className="state-empty-clean">
        <Zap size={24} style={{ color: 'var(--text-faint)' }} />
        <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>No Optimization Report Available</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          Run compilation on valid VCL source to inspect modular 3AC optimization passes.
        </div>
      </div>
    );
  }

  const handleCopyOptimized = () => {
    navigator.clipboard.writeText(optimizedCode);
    setCopiedOpt(true);
    setTimeout(() => setCopiedOpt(false), 1500);
  };

  const filteredTransformations = selectedPass === 'all'
    ? report.transformations
    : report.transformations.filter((t) => t.pass_name.toLowerCase().includes(selectedPass.toLowerCase()));

  const originalLines = originalCode.split('\n').filter((l) => l.trim().length > 0);
  const optimizedLines = optimizedCode.split('\n').filter((l) => l.trim().length > 0);

  return (
    <div className="view-content-pane" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header Bar */}
      <div className="view-content-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="view-content-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Zap size={14} style={{ color: '#eab308' }} />
            3AC Intermediate-Code Optimization
          </span>
          <span style={{ fontSize: 10.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Modular Fixed-Point Pipeline
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={handleCopyOptimized}
            className="pane-action-btn"
            title="Copy Optimized 3AC"
          >
            {copiedOpt ? <Check size={12} style={{ color: '#10b981' }} /> : <Copy size={12} />}
            <span>{copiedOpt ? 'Copied' : 'Copy Optimized'}</span>
          </button>
        </div>
      </div>

      {/* Metric Summary Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 10,
          padding: '12px 16px',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ padding: '8px 10px', background: 'var(--bg-app)', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Original 3AC Instructions</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
            {report.original_instruction_count}
          </div>
        </div>

        <div style={{ padding: '8px 10px', background: 'var(--bg-app)', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Optimized 3AC Instructions</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#10b981', fontFamily: 'var(--font-mono)' }}>
            {report.optimized_instruction_count}
          </div>
        </div>

        <div style={{ padding: '8px 10px', background: 'var(--bg-app)', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Instructions Eliminated</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
            {report.reduction_count}
          </div>
        </div>

        <div style={{ padding: '8px 10px', background: 'var(--bg-app)', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Transformations Applied</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>
            {report.transformation_count}
          </div>
        </div>
      </div>

      {/* Main Split: Side-by-Side 3AC Comparison & Transformations Log */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Side: Side-by-Side IR Code */}
        <div style={{ flex: 1.2, display: 'flex', borderRight: '1px solid var(--border-subtle)', overflow: 'hidden' }}>
          {/* Original 3AC Column */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--border-subtle)', overflow: 'hidden' }}>
            <div
              style={{
                padding: '6px 12px',
                fontSize: 10.5,
                fontWeight: 600,
                color: 'var(--text-muted)',
                background: 'rgba(255, 255, 255, 0.02)',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span>ORIGINAL THREE-ADDRESS CODE</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>{originalLines.length} lines</span>
            </div>

            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: 12,
                fontFamily: 'var(--font-mono)',
                fontSize: 11.5,
                lineHeight: 1.7,
                background: 'var(--bg-app)',
              }}
            >
              {originalLines.map((line, idx) => (
                <div key={idx} style={{ display: 'flex', gap: 10 }}>
                  <span style={{ color: 'var(--text-faint)', width: 20, textAlign: 'right', userSelect: 'none' }}>
                    {idx + 1}
                  </span>
                  <span style={{ color: 'var(--text-main)' }}>{line}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Optimized 3AC Column */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div
              style={{
                padding: '6px 12px',
                fontSize: 10.5,
                fontWeight: 600,
                color: '#10b981',
                background: 'rgba(16, 185, 129, 0.05)',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span>OPTIMIZED THREE-ADDRESS CODE</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>{optimizedLines.length} lines</span>
            </div>

            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: 12,
                fontFamily: 'var(--font-mono)',
                fontSize: 11.5,
                lineHeight: 1.7,
                background: 'var(--bg-app)',
              }}
            >
              {optimizedLines.map((line, idx) => (
                <div key={idx} style={{ display: 'flex', gap: 10 }}>
                  <span style={{ color: 'var(--text-faint)', width: 20, textAlign: 'right', userSelect: 'none' }}>
                    {idx + 1}
                  </span>
                  <span style={{ color: line.trim().endsWith(':') ? '#eab308' : '#10b981' }}>{line}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side: Transformation Records Log */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg-surface)' }}>
          {/* Filter Bar */}
          <div
            style={{
              padding: '8px 12px',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 600, color: 'var(--text-main)' }}>
              <Sparkles size={12} style={{ color: '#eab308' }} />
              Transformation Log ({filteredTransformations.length})
            </div>

            <select
              value={selectedPass}
              onChange={(e) => setSelectedPass(e.target.value)}
              style={{
                background: 'var(--bg-app)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 4,
                padding: '2px 8px',
                color: 'var(--text-main)',
                fontSize: 10.5,
                outline: 'none',
              }}
            >
              <option value="all">All Passes</option>
              <option value="constant folding">Constant Folding</option>
              <option value="constant propagation">Constant Propagation</option>
              <option value="algebraic">Algebraic Simplification</option>
              <option value="dead code">Dead Code Elimination</option>
              <option value="unreachable">Unreachable Code Elimination</option>
            </select>
          </div>

          {/* Transformation Cards List */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {filteredTransformations.length > 0 ? (
              filteredTransformations.map((trans, idx) => (
                <div
                  key={idx}
                  style={{
                    background: 'var(--bg-app)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 6,
                    padding: '8px 10px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 5,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span
                      style={{
                        fontSize: 10,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        color:
                          trans.pass_name.includes('Folding') ? '#10b981' :
                          trans.pass_name.includes('Propagation') ? '#3b82f6' :
                          trans.pass_name.includes('Algebraic') ? '#a855f7' :
                          '#ef4444',
                        background: 'rgba(255, 255, 255, 0.05)',
                        padding: '1px 6px',
                        borderRadius: 3,
                      }}
                    >
                      {trans.pass_name}
                    </span>
                    {trans.line > 0 && (
                      <span style={{ fontSize: 9.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        Line {trans.line}
                      </span>
                    )}
                  </div>

                  {/* Transformation Before -> After */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      fontFamily: 'var(--font-mono)',
                      fontSize: 11,
                      padding: '4px 6px',
                      background: 'rgba(0, 0, 0, 0.25)',
                      borderRadius: 4,
                    }}
                  >
                    <span style={{ color: '#ef4444', textDecoration: 'line-through' }}>{trans.original}</span>
                    <ArrowRight size={12} style={{ color: 'var(--text-faint)' }} />
                    <span style={{ color: '#10b981', fontWeight: 600 }}>{trans.optimized}</span>
                  </div>

                  <div style={{ fontSize: 10.5, color: 'var(--text-muted)', lineHeight: 1.4 }}>
                    {trans.reason}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: 11, textAlign: 'center', padding: 20 }}>
                No transformations applied for the selected pass filter.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OptimizerPane;
