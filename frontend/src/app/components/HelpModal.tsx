/**
 * Help/Instructions Modal - Comprehensive guide for using the Thesis Graph Builder
 */

import React from 'react'

type HelpModalProps = {
  onClose: () => void
}

export default function HelpModal({ onClose }: HelpModalProps) {
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        background: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: 20
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: 12,
          maxWidth: 800,
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
          position: 'relative'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid #e8e8e8',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          background: '#fff',
          zIndex: 1
        }}>
          <h2 style={{ margin: 0, fontSize: 20, color: '#262626' }}>
            Thesis Graph Builder - User Guide
          </h2>
          <button
            onClick={onClose}
            style={{
              border: 'none',
              background: 'none',
              fontSize: 24,
              cursor: 'pointer',
              padding: '0 8px',
              color: '#8c8c8c'
            }}
            title="Close help"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: 24, lineHeight: 1.6 }}>
          {/* Getting Started */}
          <section style={{ marginBottom: 32 }}>
            <h3 style={{ color: '#1890ff', marginTop: 0, marginBottom: 12, fontSize: 16 }}>
              🚀 Getting Started
            </h3>
            <p style={{ margin: '0 0 12px 0', color: '#595959' }}>
              The Thesis Graph Builder helps you construct and visualize causal arguments using a directed
              acyclic graph (DAG). Build your thesis by adding nodes (variables/claims) and connecting them
              with edges (relationships).
            </p>
          </section>

          {/* Project Management */}
          <section style={{ marginBottom: 32 }}>
            <h3 style={{ color: '#1890ff', marginBottom: 12, fontSize: 16 }}>
              📁 Project Management
            </h3>
            <ul style={{ margin: 0, paddingLeft: 20, color: '#595959' }}>
              <li><strong>Create Project:</strong> Enter a title and click "Create" to start a new project</li>
              <li><strong>Load Project:</strong> Use the dropdown to select and load existing projects</li>
              <li><strong>Save:</strong> Changes are automatically saved when you modify the graph</li>
              <li><strong>Delete:</strong> Click "Delete" to remove the current project (cannot be undone)</li>
            </ul>
          </section>

          {/* Graph Tools */}
          <section style={{ marginBottom: 32 }}>
            <h3 style={{ color: '#1890ff', marginBottom: 12, fontSize: 16 }}>
              🛠️ Graph Tools
            </h3>
            <div style={{ marginBottom: 16 }}>
              <h4 style={{ fontSize: 14, color: '#262626', marginBottom: 8 }}>Node Types:</h4>
              <ul style={{ margin: 0, paddingLeft: 20, color: '#595959' }}>
                <li><strong>Thesis (Orange):</strong> Your main thesis statement or argument</li>
                <li><strong>Claim (Green):</strong> Supporting claims or assertions that can be true/false</li>
                <li><strong>Evidence (Brown):</strong> Data, quotes, statistics, or observations that support claims</li>
                <li><strong>Variable (Blue):</strong> Measurable concepts mentioned in your research</li>
              </ul>
            </div>
            <div style={{ marginBottom: 16 }}>
              <h4 style={{ fontSize: 14, color: '#262626', marginBottom: 8 }}>Adding Nodes:</h4>
              <ul style={{ margin: 0, paddingLeft: 20, color: '#595959' }}>
                <li><strong>+ Thesis:</strong> Add your main thesis statement</li>
                <li><strong>+ Claim:</strong> Add supporting claims</li>
                <li><strong>+ Evidence:</strong> Add evidence nodes with data or quotes</li>
                <li><strong>Extract from Text:</strong> Highlight text in a PDF and click "Extract" to create nodes with AI assistance</li>
              </ul>
            </div>
            <div style={{ marginBottom: 16 }}>
              <h4 style={{ fontSize: 14, color: '#262626', marginBottom: 8 }}>Creating Edges:</h4>
              <ul style={{ margin: 0, paddingLeft: 20, color: '#595959' }}>
                <li><strong>Edge Mode:</strong> Enable the checkbox, then click two nodes to connect them</li>
                <li><strong>Shift+Drag:</strong> Hold Shift and drag from one node to another</li>
                <li><strong>Relation Types:</strong></li>
                <ul style={{ marginTop: 4 }}>
                  <li><strong>SUPPORTS:</strong> Evidence supports a claim, or a claim supports the thesis</li>
                  <li><strong>CONTRADICTS:</strong> Claims that contradict each other</li>
                  <li><strong>DEFINES:</strong> Evidence that defines or measures a variable</li>
                </ul>
              </ul>
            </div>
            <div>
              <h4 style={{ fontSize: 14, color: '#262626', marginBottom: 8 }}>Layout Options:</h4>
              <ul style={{ margin: 0, paddingLeft: 20, color: '#595959' }}>
                <li><strong>Hierarchical:</strong> Arrange nodes in layers based on their dependencies</li>
                <li><strong>Force:</strong> Use physics simulation to position nodes naturally</li>
                <li><strong>Manual:</strong> Drag nodes to position them wherever you like</li>
              </ul>
            </div>
          </section>

          {/* Canvas Controls */}
          <section style={{ marginBottom: 32 }}>
            <h3 style={{ color: '#1890ff', marginBottom: 12, fontSize: 16 }}>
              🖱️ Canvas Controls
            </h3>
            <ul style={{ margin: 0, paddingLeft: 20, color: '#595959' }}>
              <li><strong>Click:</strong> Select/deselect a node</li>
              <li><strong>Drag Node:</strong> Click and drag to move a node</li>
              <li><strong>Shift + Drag Canvas:</strong> Pan the entire canvas</li>
              <li><strong>Zoom In/Out:</strong> Use the + and − buttons in the bottom-right corner</li>
              <li><strong>Reset View:</strong> Click the ↺ button to reset zoom and pan</li>
            </ul>
          </section>

          {/* AI Features */}
          <section style={{ marginBottom: 32 }}>
            <h3 style={{ color: '#1890ff', marginBottom: 12, fontSize: 16 }}>
              🤖 AI-Powered Features
            </h3>
            <div style={{ marginBottom: 16 }}>
              <h4 style={{ fontSize: 14, color: '#262626', marginBottom: 8 }}>Node Extraction:</h4>
              <p style={{ margin: '0 0 8px 0', color: '#595959' }}>
                Highlight text in the PDF viewer and click "Extract" to have AI suggest a canonical
                variable name, definition, and synonyms.
              </p>
            </div>
            <div style={{ marginBottom: 16 }}>
              <h4 style={{ fontSize: 14, color: '#262626', marginBottom: 8 }}>Edge Rationale:</h4>
              <p style={{ margin: '0 0 8px 0', color: '#595959' }}>
                When creating edges, AI provides mechanisms, assumptions, and potential confounders
                to strengthen your argument.
              </p>
            </div>
            <div style={{ marginBottom: 16 }}>
              <h4 style={{ fontSize: 14, color: '#262626', marginBottom: 8 }}>Find Missing Pieces:</h4>
              <p style={{ margin: '0 0 8px 0', color: '#595959' }}>
                Right-click a node and select "Find missing pieces" to get AI suggestions for
                mediators, moderators, and study designs.
              </p>
            </div>
            <div>
              <h4 style={{ fontSize: 14, color: '#262626', marginBottom: 8 }}>Graph Critique:</h4>
              <p style={{ margin: '0 0 8px 0', color: '#595959' }}>
                Click "Critique Graph" to have AI analyze your DAG for logical issues, missing
                evidence, and methodological concerns.
              </p>
            </div>
          </section>

          {/* Export Options */}
          <section style={{ marginBottom: 32 }}>
            <h3 style={{ color: '#1890ff', marginBottom: 12, fontSize: 16 }}>
              💾 Export Options
            </h3>
            <ul style={{ margin: 0, paddingLeft: 20, color: '#595959' }}>
              <li><strong>PNG:</strong> Export the graph as a high-resolution image</li>
              <li><strong>JSON:</strong> Export all graph data for backup or sharing</li>
              <li><strong>MD:</strong> Export as a formatted Markdown document</li>
              <li><strong>Compose:</strong> Generate an essay from your graph structure</li>
            </ul>
          </section>

          {/* Tips & Tricks */}
          <section style={{ marginBottom: 0 }}>
            <h3 style={{ color: '#1890ff', marginBottom: 12, fontSize: 16 }}>
              💡 Tips & Tricks
            </h3>
            <ul style={{ margin: 0, paddingLeft: 20, color: '#595959' }}>
              <li>Use <strong>Ctrl+Z / Ctrl+Y</strong> to undo/redo changes</li>
              <li>Upload PDFs to extract evidence and create nodes</li>
              <li>Pin citations to nodes and edges for stronger arguments</li>
              <li>Use the critique feature regularly to identify logical gaps</li>
              <li>Export frequently to save your progress</li>
              <li>Organize complex graphs using hierarchical or force layouts</li>
            </ul>
          </section>
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid #e8e8e8',
          background: '#fafafa',
          textAlign: 'center',
          position: 'sticky',
          bottom: 0
        }}>
          <button
            onClick={onClose}
            style={{
              padding: '8px 24px',
              background: '#1890ff',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 600
            }}
          >
            Got it!
          </button>
        </div>
      </div>
    </div>
  )
}
