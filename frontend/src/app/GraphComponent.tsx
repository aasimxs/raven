"use client";

import React, { useRef, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

export default function GraphComponent({ caseId, theme = 'dark' }: { caseId: number, theme?: 'dark' | 'light' }) {
  const fgRef = useRef<any>(null);
  const [graphData, setGraphData] = useState<any>({ nodes: [], links: [] });

  useEffect(() => {
    fetch(`http://localhost:8000/cases/${caseId}/graph`)
      .then(res => res.json())
      .then(data => setGraphData(data))
      .catch(err => console.error("Error fetching graph data:", err));
  }, [caseId]);

  const isDark = theme === 'dark';

  return (
    <div style={{ width: '100%', height: '600px', backgroundColor: isDark ? '#111113' : '#ffffff', borderRadius: '1rem', overflow: 'hidden' }}>
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeLabel="name"
        nodeColor={node => node.group === 'Target' ? '#ef4444' : '#10b981'}
        nodeRelSize={6}
        linkColor={() => isDark ? '#374151' : '#e5e7eb'}
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
        onNodeClick={node => {
          // Optional: Center view on clicked node
        }}
      />
    </div>
  );
}
