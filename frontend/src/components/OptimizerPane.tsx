import React, { useState } from 'react';
import { OptimizationReportData, IRData } from '../types';
import { Zap, ArrowRight, Sparkles, Copy, Check, TrendingDown, Layers } from 'lucide-react';

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
        <Zap size={26} style={{ color: 'var(--text-faint)' }} />
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-dim)' }}>No Optimization Report Available</div>
        <div style={{ fontSize: 11.5, color: 'var(--text-muted)', maxWidth: 360, lineHeight: 1.5 }}>
          Run compilation on valid VCL source to inspect modular fixed-point 3AC optimization passes and side-by-side IR reductions.
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

  const reductionPercent = report.original_instruction_count > 0
    ? ((report.reduction_count / report.original_instruction_count) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="view-content-pane" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header Bar */}
      <div className="view-content-header" style={{ height: 42, padding: '0 14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="view-content-title" style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 12 }}>
            <Zap size={14} style={{ color: 'var(--color-warning)' }} />
            <span>Three-Address Code Optimization</span>
          </span>
          <span
            style={{
              fontSize: 10.5,
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              background: 'var(--bg-surface-elevated)',
              padding: '2px 7px',
              borderRadius: 'var(--radius-xs)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            Modular Fixed-Point Pipeline
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={handleCopyOptimized}
            className="pane-action-btn"
            title="Copy optimized 3AC instructions to clipboard"
          >
            {copiedOpt ? <Check size={12} style={{ color: 'var(--color-success)' }} /> : <Copy size={12} />}
            <span>{copiedOpt ? 'Copied' : 'Copy Optimized'}</span>
          </button>
        </div>
      </div>

      {/* Analytical Metric Comparison Banner */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 16px',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-subtle)',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        {/* Instruction Flow Comparison: Original -> Optimized */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Original 3AC
            </span>
            <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
              {report.original_instruction_count} <span style={{ fontSize: 10.5, fontWeight: 500, color: 'var(--text-muted)' }}>insts</span>
            </span>
          </div>

          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: '50%',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-med)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent)',
            }}
          >
            <ArrowRight size={14} />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span style={{ fontSize: 10, color: 'var(--color-success)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Optimized 3AC
            </span>
            <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-success)', fontFamily: 'var(--font-mono)' }}>
              {report.optimized_instruction_count} <span style={{ fontSize: 10.5, fontWeight: 500, color: 'var(--text-muted)' }}>insts</span>
            </span>
          </div>
        </div>

        {/* Analytical Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'rgba(52, 211, 153, 0.08)',
              border: '1px solid rgba(52, 211, 153, 0.25)',
              padding: '4px 10px',
              borderRadius: 'var(--radius-xs)',
            }}
          >
            <TrendingDown size={13} style={{ color: 'var(--color-success)' }} />
            <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)' }}>
              <span style={{ fontWeight: 700, color: 'var(--color-success)' }}>-{report.reduction_count}</span>
              <span style={{ color: 'var(--text-dim)', marginLeft: 4 }}>eliminated ({reductionPercent}%)</span>
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'rgba(251, 191, 36, 0.08)',
              border: '1px solid rgba(251, 191, 36, 0.25)',
              padding: '4px 10px',
              borderRadius: 'var(--radius-xs)',
            }}
          >
            <Sparkles size={13} style={{ color: 'var(--color-warning)' }} />
            <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)' }}>
              <span style={{ fontWeight: 700, color: 'var(--color-warning)' }}>{report.transformation_count}</span>
              <span style={{ color: 'var(--text-dim)', marginLeft: 4 }}>transformations</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Split: Side-by-Side 3AC Comparison & Transformations Log */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Side: Side-by-Side IR Code */}
        <div style={{ flex: 1.25, display: 'flex', borderRight: '1px solid var(--border-subtle)', overflow: 'hidden' }}>
          {/* Original 3AC Column */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--border-subtle)', overflow: 'hidden' }}>
            <div
              style={{
                height: 32,
                padding: '0 12px',
                fontSize: 10.5,
                fontWeight: 600,
                color: 'var(--text-muted)',
                background: 'var(--bg-surface)',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span>ORIGINAL 3AC</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>{originalLines.length} lines</span>
            </div>

            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: 12,
                fontFamily: 'var(--font-mono)',
                fontSize: 11.5,
                lineHeight: 1.7,
                background: 'var(--bg-input)',
              }}
            >
              {originalLines.map((line, idx) => (
                <div key={idx} style={{ display: 'flex', gap: 10 }}>
                  <span style={{ color: 'var(--text-faint)', width: 22, textAlign: 'right', userSelect: 'none' }}>
                    {idx + 1}
                  </span>
                  <span style={{ color: line.trim().endsWith(':') ? 'var(--color-warning)' : 'var(--text-main)' }}>
                    {line}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Optimized 3AC Column */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div
              style={{
                height: 32,
                padding: '0 12px',
                fontSize: 10.5,
                fontWeight: 600,
                color: 'var(--color-success)',
                background: 'var(--bg-surface)',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-success)' }} />
                <span>OPTIMIZED 3AC</span>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>{optimizedLines.length} lines</span>
            </div>

            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: 12,
                fontFamily: 'var(--font-mono)',
                fontSize: 11.5,
                lineHeight: 1.7,
                background: 'var(--bg-input)',
              }}
            >
              {optimizedLines.map((line, idx) => (
                <div key={idx} style={{ display: 'flex', gap: 10 }}>
                  <span style={{ color: 'var(--text-faint)', width: 22, textAlign: 'right', userSelect: 'none' }}>
                    {idx + 1}
                  </span>
                  <span style={{ color: line.trim().endsWith(':') ? 'var(--color-warning)' : 'var(--color-success)' }}>
                    {line}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side: Transformation Records Log */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg-app)', minWidth: 260 }}>
          {/* Filter Bar */}
          <div
            style={{
              height: 36,
              padding: '0 12px',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'var(--bg-surface)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 600, color: 'var(--text-main)' }}>
              <Sparkles size={12} style={{ color: 'var(--color-warning)' }} />
              <span>Transformation Log ({filteredTransformations.length})</span>
            </div>

            <select
              value={selectedPass}
              onChange={(e) => setSelectedPass(e.target.value)}
              className="custom-select"
              title="Filter transformations by pass"
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
              filteredTransformations.map((t, idx) => (
                <div
                  key={idx}
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-med)',
                    borderRadius: 'var(--radius-sm)',
                    padding: 10,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.15)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span
                      style={{
                        fontSize: 9.5,
                        fontWeight: 600,
                        color: 'var(--accent)',
                        background: 'var(--accent-subtle)',
                        border: '1px solid var(--accent-border)',
                        padding: '1px 6px',
                        borderRadius: 'var(--radius-xs)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                      }}
                    >
                      {t.pass_name}
                    </span>

                    <span style={{ fontSize: 9.5, color: 'var(--text-faint)', fontFamily: 'var(--font-mono)' }}>
                      #{idx + 1}
                    </span>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      fontFamily: 'var(--font-mono)',
                      fontSize: 11,
                      padding: '4px 8px',
                      background: 'var(--bg-input)',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <span style={{ color: 'var(--color-error)' }}>{t.original}</span>
                    <ArrowRight size={11} style={{ color: 'var(--text-faint)', flexShrink: 0 }} />
                    <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>{t.optimized}</span>
                  </div>

                  <div style={{ fontSize: 10.5, color: 'var(--text-dim)', lineHeight: 1.4 }}>
                    {t.reason}
                  </div>
                </div>
              ))
            ) : (
              <div className="state-empty-clean" style={{ padding: 24 }}>
                <Layers size={20} style={{ color: 'var(--text-faint)' }} />
                <div style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                  No transformations found for selected pass filter.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OptimizerPane;
