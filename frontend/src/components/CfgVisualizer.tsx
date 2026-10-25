import React, { useState } from 'react';
import { CFGData, CFGBlock } from '../types';
import { GitBranch, ArrowRight, CheckCircle2, AlertTriangle, Layers, Info } from 'lucide-react';

interface CfgVisualizerProps {
  cfg?: CFGData | null;
  onSelectBlock?: (block: CFGBlock) => void;
}

export const CfgVisualizer: React.FC<CfgVisualizerProps> = ({ cfg }) => {
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);

  if (!cfg || !cfg.blocks || cfg.blocks.length === 0) {
    return (
      <div className="state-empty-clean">
        <GitBranch size={24} style={{ color: 'var(--text-faint)' }} />
        <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>No Control Flow Graph Available</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          CFG is constructed from Three-Address Code basic blocks and branch edges.
        </div>
      </div>
    );
  }

  const selectedBlock = cfg.blocks.find((b) => b.id === selectedBlockId) || cfg.blocks[0];

  const getEdgeStyle = (edgeType: string) => {
    switch (edgeType) {
      case 'true':
        return {
          color: '#10b981',
          bg: 'rgba(16, 185, 129, 0.12)',
          border: 'rgba(16, 185, 129, 0.4)',
          label: 'True Branch',
        };
      case 'false':
        return {
          color: '#ef4444',
          bg: 'rgba(239, 68, 68, 0.12)',
          border: 'rgba(239, 68, 68, 0.4)',
          label: 'False Branch',
        };
      case 'unconditional':
        return {
          color: '#3b82f6',
          bg: 'rgba(59, 130, 246, 0.12)',
          border: 'rgba(59, 130, 246, 0.4)',
          label: 'Goto (Jump)',
        };
      case 'backedge':
        return {
          color: '#a855f7',
          bg: 'rgba(168, 85, 247, 0.12)',
          border: 'rgba(168, 85, 247, 0.4)',
          label: 'Loop Back-Edge',
        };
      case 'fallthrough':
      default:
        return {
          color: '#94a3b8',
          bg: 'rgba(148, 163, 184, 0.1)',
          border: 'rgba(148, 163, 184, 0.3)',
          label: 'Fall-through',
        };
    }
  };

  return (
    <div className="view-content-pane" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Top Header Bar */}
      <div className="view-content-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="view-content-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <GitBranch size={14} style={{ color: 'var(--accent-primary)' }} />
            Control Flow Graph (CFG)
          </span>
          <span style={{ fontSize: 10.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {cfg.block_count} Basic Blocks · {cfg.edge_count} Directed Edges
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {cfg.validation_errors && cfg.validation_errors.length > 0 ? (
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                fontSize: 10,
                color: '#ef4444',
                background: 'rgba(239, 68, 68, 0.1)',
                padding: '2px 8px',
                borderRadius: 4,
                border: '1px solid rgba(239, 68, 68, 0.25)',
              }}
            >
              <AlertTriangle size={12} />
              {cfg.validation_errors.length} Validation Issue(s)
            </span>
          ) : (
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                fontSize: 10,
                color: '#10b981',
                background: 'rgba(16, 185, 129, 0.1)',
                padding: '2px 8px',
                borderRadius: 4,
                border: '1px solid rgba(16, 185, 129, 0.25)',
              }}
            >
              <CheckCircle2 size={12} />
              Valid CFG (All targets resolved)
            </span>
          )}
        </div>
      </div>

      {/* Main Split: Left Graph Flow / Right Inspector */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left: Interactive Basic Block Flow */}
        <div
          style={{
            flex: 1.4,
            overflowY: 'auto',
            padding: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            background: 'var(--bg-app)',
          }}
        >
          {cfg.blocks.map((block) => {
            const isSelected = selectedBlock?.id === block.id;
            const outgoingEdges = cfg.edges.filter((e) => e.from_block === block.id);

            return (
              <div
                key={block.id}
                onClick={() => setSelectedBlockId(block.id)}
                style={{
                  background: isSelected ? 'var(--bg-surface-elevated)' : 'var(--bg-surface)',
                  border: isSelected
                    ? '1.5px solid var(--accent-primary)'
                    : block.is_entry
                    ? '1px solid rgba(59, 130, 246, 0.4)'
                    : '1px solid var(--border-subtle)',
                  borderRadius: 8,
                  padding: 12,
                  boxShadow: isSelected ? '0 0 12px rgba(99, 102, 241, 0.2)' : 'none',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {/* Block Header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 700,
                        fontSize: 13,
                        color: isSelected ? 'var(--accent-primary)' : 'var(--text-main)',
                      }}
                    >
                      {block.id}
                    </span>

                    {block.labels && block.labels.length > 0 && (
                      <span
                        style={{
                          fontSize: 10,
                          fontFamily: 'var(--font-mono)',
                          color: '#eab308',
                          background: 'rgba(234, 179, 8, 0.12)',
                          padding: '1px 6px',
                          borderRadius: 4,
                          border: '1px solid rgba(234, 179, 8, 0.3)',
                        }}
                      >
                        {block.labels.join(', ')}:
                      </span>
                    )}

                    {block.is_entry && (
                      <span
                        style={{
                          fontSize: 9.5,
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          color: '#3b82f6',
                          background: 'rgba(59, 130, 246, 0.12)',
                          padding: '1px 5px',
                          borderRadius: 3,
                        }}
                      >
                        Entry
                      </span>
                    )}

                    {block.is_exit && (
                      <span
                        style={{
                          fontSize: 9.5,
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          color: '#8b5cf6',
                          background: 'rgba(139, 92, 246, 0.12)',
                          padding: '1px 5px',
                          borderRadius: 3,
                        }}
                      >
                        Exit
                      </span>
                    )}

                    {!block.reachable && (
                      <span
                        style={{
                          fontSize: 9.5,
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          color: '#ef4444',
                          background: 'rgba(239, 68, 68, 0.12)',
                          padding: '1px 5px',
                          borderRadius: 3,
                        }}
                      >
                        Unreachable
                      </span>
                    )}
                  </div>

                  <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {block.instruction_count} inst(s)
                  </span>
                </div>

                {/* Instructions Inside Basic Block */}
                <div
                  style={{
                    background: 'rgba(0, 0, 0, 0.25)',
                    borderRadius: 5,
                    padding: '8px 10px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11.5,
                    lineHeight: '1.6',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                    border: '1px solid rgba(255, 255, 255, 0.04)',
                  }}
                >
                  {block.lines && block.lines.length > 0 ? (
                    block.lines.map((line, idx) => {
                      const isLabel = line.trim().endsWith(':');
                      const isBranch = line.includes('goto') || line.includes('if_');
                      return (
                        <div
                          key={idx}
                          style={{
                            color: isLabel ? '#eab308' : isBranch ? '#38bdf8' : 'var(--text-main)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 8,
                          }}
                        >
                          <span style={{ color: 'var(--text-faint)', fontSize: 10, width: 16 }}>{idx + 1}</span>
                          <span>{line}</span>
                        </div>
                      );
                    })
                  ) : (
                    <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Empty basic block</span>
                  )}
                </div>

                {/* Outgoing Edges Pills */}
                {outgoingEdges.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                    {outgoingEdges.map((edge, eIdx) => {
                      const style = getEdgeStyle(edge.edge_type);
                      return (
                        <div
                          key={eIdx}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 5,
                            fontSize: 10,
                            fontFamily: 'var(--font-mono)',
                            color: style.color,
                            background: style.bg,
                            border: `1px solid ${style.border}`,
                            padding: '2px 8px',
                            borderRadius: 12,
                          }}
                        >
                          <span>{style.label}</span>
                          <ArrowRight size={10} />
                          <span style={{ fontWeight: 700 }}>{edge.to_block}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Right: Block Inspector & Relationships Drawer */}
        <div
          style={{
            flex: 1,
            borderLeft: '1px solid var(--border-subtle)',
            padding: 16,
            overflowY: 'auto',
            background: 'var(--bg-surface)',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, borderBottom: '1px solid var(--border-subtle)', paddingBottom: 10 }}>
            <Layers size={14} style={{ color: 'var(--accent-primary)' }} />
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-main)' }}>
              Block Inspector: {selectedBlock ? selectedBlock.id : 'None'}
            </span>
          </div>

          {selectedBlock ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {/* Properties Grid */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 8,
                  fontSize: 11,
                  fontFamily: 'var(--font-mono)',
                }}
              >
                <div style={{ padding: 8, background: 'var(--bg-app)', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: 10, marginBottom: 2 }}>Block ID</div>
                  <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>{selectedBlock.id}</div>
                </div>

                <div style={{ padding: 8, background: 'var(--bg-app)', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: 10, marginBottom: 2 }}>Reachability</div>
                  <div style={{ fontWeight: 700, color: selectedBlock.reachable ? '#10b981' : '#ef4444' }}>
                    {selectedBlock.reachable ? 'Reachable from Entry' : 'Unreachable (Dead)'}
                  </div>
                </div>

                <div style={{ padding: 8, background: 'var(--bg-app)', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: 10, marginBottom: 2 }}>Predecessors</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                    {selectedBlock.predecessors.length > 0 ? selectedBlock.predecessors.join(', ') : 'None (Entry)'}
                  </div>
                </div>

                <div style={{ padding: 8, background: 'var(--bg-app)', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: 10, marginBottom: 2 }}>Successors</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                    {selectedBlock.successors.length > 0 ? selectedBlock.successors.join(', ') : 'None (Exit/Terminal)'}
                  </div>
                </div>
              </div>

              {/* Instructions List */}
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-dim)', marginBottom: 6 }}>
                  Block Instructions ({selectedBlock.instructions.length})
                </div>
                <div
                  style={{
                    background: 'var(--bg-app)',
                    borderRadius: 6,
                    border: '1px solid var(--border-subtle)',
                    padding: 8,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 4,
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11,
                  }}
                >
                  {selectedBlock.instructions.map((inst, iIdx) => (
                    <div
                      key={iIdx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '4px 6px',
                        borderRadius: 4,
                        background: 'rgba(255, 255, 255, 0.02)',
                      }}
                    >
                      <span style={{ color: 'var(--text-main)' }}>{inst.formatted}</span>
                      <span
                        style={{
                          fontSize: 9.5,
                          color: 'var(--text-muted)',
                          background: 'rgba(255, 255, 255, 0.05)',
                          padding: '1px 5px',
                          borderRadius: 3,
                        }}
                      >
                        {inst.kind}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* CFG Construction Rules Guide */}
              <div
                style={{
                  background: 'rgba(99, 102, 241, 0.05)',
                  border: '1px solid rgba(99, 102, 241, 0.2)',
                  borderRadius: 6,
                  padding: 10,
                  fontSize: 10.5,
                  color: 'var(--text-muted)',
                  lineHeight: '1.5',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--accent-primary)', fontWeight: 600, marginBottom: 4 }}>
                  <Info size={12} />
                  Basic Block & Edge Rules
                </div>
                Leaders identify basic block heads: initial instruction, jump targets, and post-jump instructions.
                Branches split control flow into conditional paths ('true', 'false', 'goto', 'fallthrough').
              </div>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: 11 }}>Select a block to inspect its properties.</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CfgVisualizer;
