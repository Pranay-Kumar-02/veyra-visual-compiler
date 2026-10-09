import React from 'react';
import { CompilationResult } from '../types';

interface TelemetryBarProps {
  result: CompilationResult | null;
  isCompiling: boolean;
}

export const TelemetryBar: React.FC<TelemetryBarProps> = ({ result, isCompiling }) => {
  const metrics = result?.metrics;

  return (
    <footer className="telemetry-footer">
      <div className="tel-group">
        <div className="tel-item">
          <span>Pipeline:</span>
          {isCompiling ? (
            <span className="val" style={{ color: 'var(--accent)' }}>Compiling...</span>
          ) : result ? (
            result.success ? (
              <span className="val" style={{ color: 'var(--color-success)' }}>Operational</span>
            ) : (
              <span className="val" style={{ color: 'var(--color-error)' }}>Trapped</span>
            )
          ) : (
            <span className="val">Idle</span>
          )}
        </div>

        <div className="tel-item">
          <span>Tokens:</span>
          <span className="val">{metrics?.token_count ?? (result?.tokens?.length || 0)}</span>
        </div>

        <div className="tel-item">
          <span>Symbols:</span>
          <span className="val">{metrics?.symbol_count ?? (result?.symbol_table?.length || 0)}</span>
        </div>

        <div className="tel-item">
          <span>3AC Instructions:</span>
          <span className="val">{metrics?.ir_instruction_count ?? (result?.ir?.instruction_count || 0)}</span>
        </div>

        <div className="tel-item">
          <span>Output:</span>
          <span className="val">{metrics?.output_line_count ?? (result?.output_lines?.length || 0)} lines</span>
        </div>
      </div>

      <div className="tel-group">
        {result && (
          <div className="tel-item">
            <span>Latency:</span>
            <span className="val">{metrics?.diagnostic_pipeline_duration_ms ?? 1}ms</span>
          </div>
        )}

        <div className="tel-item">
          <span style={{ color: 'var(--text-faint)' }}>VCL 2.0 (IR+3AC)</span>
        </div>

        <div className="tel-item">
          <div
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              backgroundColor: isCompiling ? 'var(--accent)' : 'var(--color-success)',
            }}
          />
          <span style={{ color: 'var(--text-muted)' }}>Flask API :5000</span>
        </div>
      </div>
    </footer>
  );
};
