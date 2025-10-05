'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

interface Node {
  id: string;
  label: string;
  properties: any;
  x: number;
  y: number;
}

interface Link {
  source: string;
  target: string;
  type: string;
  properties: any;
}

interface GraphData {
  nodes: Node[];
  links: Link[];
  totalNodes: number;
  totalLinks: number;
}

interface GraphVisualizationProps {
  data?: GraphData;
  onNodeClick?: (node: Node) => void;
  onLinkClick?: (link: Link) => void;
}

const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  data,
  onNodeClick,
  onLinkClick
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedLink, setSelectedLink] = useState<Link | null>(null);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 1400;
    const height = 900;
    svg.attr('width', width).attr('height', height);

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create main container
    const container = svg.append('g');

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.links).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Create links
    const link = container.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(data.links)
      .enter().append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', (d: any) => d.type === 'CONTRIBUTED_TO' ? '5,5' : '0')
      .on('click', (event, d: any) => {
        event.stopPropagation();
        setSelectedLink(d);
        onLinkClick?.(d);
      });

    // Create link labels
    const linkLabels = container.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(data.links)
      .enter().append('text')
      .attr('font-size', '12px')
      .attr('fill', '#94a3b8')
      .text((d: any) => d.type)
      .style('pointer-events', 'none');

    // Create nodes
    const node = container.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(data.nodes)
      .enter().append('g')
      .attr('class', 'node')
      .call(d3.drag<SVGGElement, Node>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended))
      .on('click', (event, d: any) => {
        event.stopPropagation();
        setSelectedNode(d);
        onNodeClick?.(d);
      });

    // Add circles for nodes
    node.append('circle')
      .attr('r', (d: any) => {
        if (d.label === 'Hacker') return 15;
        if (d.label === 'Devpost') return 20;
        return 10;
      })
      .attr('fill', (d: any) => {
        if (d.label === 'Hacker') return '#4CAF50';
        if (d.label === 'Devpost') return '#2196F3';
        return '#FF9800';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    // Add labels for nodes
    node.append('text')
      .attr('dx', (d: any) => d.label === 'Hacker' ? 20 : 25)
      .attr('dy', 5)
      .attr('font-size', '12px')
      .attr('fill', '#e2e8f0')
      .text((d: any) => {
        if (d.label === 'Hacker') {
          return d.properties.displayName || d.properties.name || 'Unknown Hacker';
        }
        if (d.label === 'Devpost') {
          return d.properties.name || 'Unknown Project';
        }
        return d.label;
      })
      .style('pointer-events', 'none');

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      linkLabels
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2);

      node
        .attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Cleanup
    return () => {
      simulation.stop();
    };

  }, [data, onNodeClick, onLinkClick]);

  if (!data) {
    return (
      <div className="flex items-center justify-center h-[900px] bg-slate-800 rounded-lg border border-slate-600/50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading graph data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-4 flex justify-between items-center">
        <div className="text-sm text-slate-300">
          Nodes: {data.totalNodes} | Links: {data.totalLinks}
        </div>
        <div className="text-sm text-slate-400">
          Click and drag to pan, scroll to zoom
        </div>
      </div>
      
      <div className="border border-slate-600/50 rounded-lg overflow-hidden">
        <svg ref={svgRef} className="w-full h-[900px] bg-slate-800"></svg>
      </div>

    </div>
  );
};

export default GraphVisualization;

