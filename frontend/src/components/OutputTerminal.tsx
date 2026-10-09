import React, { useState } from 'react';
import { Copy, Check, RotateCcw, Terminal } from 'lucide-react';

interface OutputTerminalProps {
  output: string;
  outputLines: string[];
  success: boolean;
  durationMs?: number;
}

export const OutputTerminal: React.FC<OutputTerminalProps> = ({
  output,
  outputLines,
  success,
  durationMs = 1,
}) => {
  const [copied, setCopied] = useState(false);
  const [cleared, setCleared] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const lines = cleared ? [] : outputLines;

  return (
    <div className="view-content-pane">
      {/* Header */}
      <div className="view-content-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="view-content-title">Program Output</span>
          <span style={{ fontSize: 10.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {success ? 'Exit 0 (Success)' : 'Exit 1 (Trapped)'} · {durationMs}ms
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <button
            className="btn btn-secondary"
            onClick={handleCopy}
            disabled={!output}
            style={{ padding: '3px 7px', fontSize: 11 }}
            title="Copy stdout"
          >
            {copied ? <Check size={11} style={{ color: 'var(--color-success)' }} /> : <Copy size={11} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setCleared(!cleared)}
            style={{ padding: '3px 7px', fontSize: 11 }}
            title="Clear output view"
          >
            <RotateCcw size={11} />
            <span>{cleared ? 'Restore' : 'Clear'}</span>
          </button>
        </div>
      </div>

      {/* Terminal View */}
      {lines.length === 0 ? (
        <div className="state-empty-clean">
          <Terminal size={24} style={{ color: 'var(--text-faint)' }} />
          <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Output Stream Empty</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Interpreter prints will appear here upon program execution.
          </div>
        </div>
      ) : (
        <div className="terminal-screen">
          {lines.map((ln, idx) => (
            <div key={idx} style={{ display: 'flex', gap: 8 }}>
              <span style={{ color: 'var(--text-faint)', userSelect: 'none' }}>&gt;</span>
              <span style={{ color: 'var(--text-main)' }}>{ln}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
