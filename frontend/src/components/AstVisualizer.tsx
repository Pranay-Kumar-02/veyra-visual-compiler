import React, { useState } from 'react';
import { ASTNodeData } from '../types';
import { ZoomIn, ZoomOut, RotateCcw, Search, Code, Network, Maximize2 } from 'lucide-react';

interface AstVisualizerProps {
  ast: ASTNodeData | null;
  onSelectNodeLocation?: (line: number, col: number) => void;
}

export const AstVisualizer: React.FC<AstVisualizerProps> = ({ ast, onSelectNodeLocation }) => {
  const [scale, setScale] = useState<number>(0.95);
  const [viewMode, setViewMode] = useState<'tree' | 'json'>('tree');
  const [selectedNode, setSelectedNode] = useState<ASTNodeData | null>(null);
  const [searchFilter, setSearchFilter] = useState<string>('');

  if (!ast) {
    return (
      <div className="state-empty-clean">
        <Network size={24} style={{ color: 'var(--text-faint)' }} />
        <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>No AST Available</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          Compile valid VCL code to generate the syntax tree.
        </div>
      </div>
    );
  }

  const getNodeKindColor = (type: string) => {
    switch (type) {
      case 'Program': return '#58a6ff';
      case 'VarDeclaration':
      case 'Assignment': return '#79c0ff';
      case 'BinaryExpression':
      case 'UnaryExpression': return '#56d364';
      case 'IfStatement':
      case 'ConditionBranch':
      case 'ThenBranch':
      case 'ElseBranch': return '#d2a8ff';
      case 'Literal': return '#e3b341';
      case 'Identifier': return '#ffa657';
      case 'PrintStatement': return '#7ee787';
      case 'BlockStatement': return '#bc8cff';
      default: return '#8b949e';
    }
  };

  const renderNodeSummary = (node: ASTNodeData) => {
    if (node.name) return `let ${node.name}`;
    if (node.value !== undefined && node.value !== null) return String(node.value);
    if (node.operator) return `Op: ${node.operator}`;
    if (node.target) return `Target: ${node.target}`;
    if (node.node_type === 'BlockStatement') return 'Block { }';
    if (node.node_type === 'PrintStatement') return 'print()';
    if (node.node_type === 'IfStatement') return 'if (...)';
    return node.label || node.node_type;
  };

  const renderTree = (node: ASTNodeData, depth: number = 0): React.ReactNode => {
    const isSelected = selectedNode === node;
    const kindColor = getNodeKindColor(node.node_type);
    const summary = renderNodeSummary(node);
    const matchesFilter =
      searchFilter &&
      (node.node_type.toLowerCase().includes(searchFilter.toLowerCase()) ||
        summary.toLowerCase().includes(searchFilter.toLowerCase()));

    return (
      <div
        key={`${node.node_type}-${node.line}-${node.column}-${depth}`}
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          margin: '0 4px',
        }}
      >
        {/* Compact Node Card */}
        <div
          onClick={(e) => {
            e.stopPropagation();
            setSelectedNode(node);
            if (onSelectNodeLocation) onSelectNodeLocation(node.line, node.column);
          }}
          className={`ast-tree-node ${isSelected ? 'selected' : ''}`}
          style={{
            borderLeft: `2.5px solid ${kindColor}`,
            boxShadow: matchesFilter ? '0 0 0 1px var(--accent)' : '0 2px 6px rgba(0,0,0,0.2)',
            minWidth: 80,
            maxWidth: 160,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 4 }}>
            <span style={{ fontSize: 9.5, color: kindColor, fontWeight: 600 }}>
              {node.node_type}
            </span>
            <span style={{ fontSize: 9, color: 'var(--text-faint)' }}>
              {node.line}:{node.column}
            </span>
          </div>

          {summary !== node.node_type && (
            <div style={{ fontSize: 11, color: 'var(--text-main)', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {summary}
            </div>
          )}
        </div>

        {/* Children Branches */}
        {node.children && node.children.length > 0 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              marginTop: 10,
              position: 'relative',
            }}
          >
            {/* Direct vertical drop from parent */}
            <div
              style={{
                position: 'absolute',
                top: -10,
                width: 1,
                height: 10,
                backgroundColor: 'var(--border-med)',
              }}
            />

            {/* Sibling branches row */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'flex-start',
                width: '100%',
                paddingTop: 8,
              }}
            >
              {node.children.map((ch, idx) => {
                const isFirst = idx === 0;
                const isLast = idx === (node.children?.length ?? 1) - 1;
                const isOnly = (node.children?.length ?? 0) === 1;

                return (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      position: 'relative',
                      padding: '0 4px',
                    }}
                  >
                    {/* Horizontal connector segment */}
                    {!isOnly && (
                      <div
                        style={{
                          position: 'absolute',
                          top: 0,
                          height: 1,
                          backgroundColor: 'var(--border-med)',
                          left: isFirst ? '50%' : 0,
                          right: isLast ? '50%' : 0,
                        }}
                      />
                    )}
                    {/* Vertical drop tick to child */}
                    <div
                      style={{
                        position: 'absolute',
                        top: 0,
                        width: 1,
                        height: 8,
                        backgroundColor: 'var(--border-med)',
                        left: '50%',
                      }}
                    />
                    <div style={{ paddingTop: 8 }}>
                      {renderTree(ch, depth + 1)}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="view-content-pane">
      {/* Header Controls */}
      <div className="view-content-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="view-content-title">Abstract Syntax Tree</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <button
              className={`btn-icon ${viewMode === 'tree' ? 'active' : ''}`}
              onClick={() => setViewMode('tree')}
              title="Tree view"
            >
              <Network size={12} />
            </button>
            <button
              className={`btn-icon ${viewMode === 'json' ? 'active' : ''}`}
              onClick={() => setViewMode('json')}
              title="Raw JSON view"
            >
              <Code size={12} />
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {viewMode === 'tree' && (
            <>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Search size={10} style={{ position: 'absolute', left: 6, color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Filter tree..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
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

              <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <button
                  className="btn-icon"
                  onClick={() => setScale((s) => Math.min(s + 0.1, 1.5))}
                  title="Zoom in"
                >
                  <ZoomIn size={12} />
                </button>
                <button
                  className="btn-icon"
                  onClick={() => setScale((s) => Math.max(s - 0.1, 0.5))}
                  title="Zoom out"
                >
                  <ZoomOut size={12} />
                </button>
                <button
                  className="btn-icon"
                  onClick={() => setScale(0.9)}
                  title="Fit to view"
                >
                  <Maximize2 size={12} />
                </button>
                <button
                  className="btn-icon"
                  onClick={() => setScale(1)}
                  title="Reset scale"
                >
                  <RotateCcw size={12} />
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Main Body */}
      {viewMode === 'tree' ? (
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          <div className="ast-canvas-wrap">
            <div
              style={{
                transform: `scale(${scale})`,
                transformOrigin: 'top center',
                transition: 'transform 0.12s ease-out',
                display: 'inline-flex',
                justifyContent: 'center',
                padding: '10px 20px',
              }}
            >
              {renderTree(ast)}
            </div>
          </div>

          {/* Node Inspector Drawer */}
          {selectedNode && (
            <div
              style={{
                width: 220,
                backgroundColor: 'var(--bg-surface)',
                borderLeft: '1px solid var(--border-subtle)',
                padding: 12,
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-main)' }}>
                  Node Details
                </span>
                <button
                  className="btn-icon"
                  style={{ width: 18, height: 18 }}
                  onClick={() => setSelectedNode(null)}
                >
                  ×
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div style={{ color: 'var(--text-muted)' }}>Type:</div>
                <div style={{ color: getNodeKindColor(selectedNode.node_type) }}>
                  {selectedNode.node_type}
                </div>

                <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>Position:</div>
                <div style={{ color: 'var(--text-dim)' }}>
                  Line {selectedNode.line}, Column {selectedNode.column}
                </div>

                {selectedNode.name && (
                  <>
                    <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>Identifier:</div>
                    <div style={{ color: '#ffa657' }}>{selectedNode.name}</div>
                  </>
                )}

                {selectedNode.value !== undefined && (
                  <>
                    <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>Value:</div>
                    <div style={{ color: '#e3b341' }}>{String(selectedNode.value)}</div>
                  </>
                )}

                {selectedNode.operator && (
                  <>
                    <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>Operator:</div>
                    <div style={{ color: '#56d364' }}>{selectedNode.operator}</div>
                  </>
                )}

                <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>Children:</div>
                <div style={{ color: 'var(--text-dim)' }}>
                  {selectedNode.children ? selectedNode.children.length : 0}
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <pre
          style={{
            flex: 1,
            padding: 14,
            overflow: 'auto',
            fontFamily: 'var(--font-mono)',
            fontSize: 11.5,
            color: 'var(--text-dim)',
            lineHeight: 1.5,
            margin: 0,
            backgroundColor: 'var(--bg-input)',
          }}
        >
          {JSON.stringify(ast, null, 2)}
        </pre>
      )}
    </div>
  );
};
