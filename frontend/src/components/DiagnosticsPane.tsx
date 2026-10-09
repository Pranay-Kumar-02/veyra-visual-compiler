import React from 'react';
import { DiagnosticItem } from '../types';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

interface DiagnosticsPaneProps {
  diagnostics: DiagnosticItem[];
  onSelectLocation?: (line: number, col: number) => void;
}

export const DiagnosticsPane: React.FC<DiagnosticsPaneProps> = ({
  diagnostics,
  onSelectLocation,
}) => {
  if (!diagnostics || diagnostics.length === 0) {
    return (
      <div className="state-empty-clean">
        <CheckCircle2 size={24} style={{ color: 'var(--color-success)' }} />
        <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-main)' }}>
          No Diagnostics Reported
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          Source code parsed, verified, and compiled without errors.
        </div>
      </div>
    );
  }

  return (
    <div className="view-content-pane">
      {/* Header */}
      <div className="view-content-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertCircle size={13} style={{ color: 'var(--color-error)' }} />
          <span className="view-content-title">Diagnostics</span>
          <span style={{ fontSize: 10.5, color: 'var(--color-error)', fontFamily: 'var(--font-mono)' }}>
            {diagnostics.length} {diagnostics.length === 1 ? 'issue' : 'issues'}
          </span>
        </div>
        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
          Click an issue to jump to source
        </span>
      </div>

      {/* List */}
      <div className="diag-list">
        {diagnostics.map((diag, i) => (
          <div
            key={i}
            className="diag-item"
            onClick={() => onSelectLocation && onSelectLocation(diag.line, diag.column)}
            title="Click to jump to line in editor"
          >
            <div className="diag-item-header">
              <span className="diag-stage">{diag.stage}</span>
              <span className="diag-pos">
                Line {diag.line}, Column {diag.column}
              </span>
            </div>

            <div className="diag-text">{diag.message}</div>

            {diag.hint && (
              <div className="diag-hint-box">
                Hint: {diag.hint}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
