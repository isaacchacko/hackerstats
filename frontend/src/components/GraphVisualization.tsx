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
  highlightQuery?: string;
}

const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  data,
  onNodeClick,
  onLinkClick,
  highlightQuery
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

    // Dotted background pattern
    const defs = svg.append('defs');
    const pattern = defs.append('pattern')
      .attr('id', 'dot-pattern')
      .attr('width', 24)
      .attr('height', 24)
      .attr('patternUnits', 'userSpaceOnUse');
    // Four-corner dots to create a grid feel
    const dots = [
      { cx: 2, cy: 2 },
    ];
    dots.forEach(({ cx, cy }) => {
      pattern.append('circle')
        .attr('cx', cx)
        .attr('cy', cy)
        .attr('r', 1.6)
        .attr('fill', '#94a3b8') // slate-400
        .attr('opacity', 0.9);
    });

    const backgroundGroup = svg.append("g");
    backgroundGroup.append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", "url(#dot-pattern)");

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create main container
    const container = svg.append('g');

    // Dotted background that pans/zooms with the graph
    container.insert('rect', ':first-child')
      .attr('class', 'dot-bg-container')
      .attr('width', width)
      .attr('height', height)
      .attr('fill', 'url(#dot-pattern)')
      .style('pointer-events', 'none');

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.links).id((d: any) => d.id).distance(50))
      .force('charge', d3.forceManyBody().strength(-20))
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
      // .attr('stroke-dasharray', (d: any) => d.type === 'CONTRIBUTED_TO' ? '5,5' : '0')
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
      // .text((d: any) => d.type)
      .style('pointer-events', 'none');

    // Precompute highlight set based on highlightQuery (simple case-insensitive substring match)
    const normalizedQuery = (highlightQuery || '').trim().toLowerCase();
    const isHighlighted = (n: any): boolean => {
      if (!normalizedQuery) return false;
      const label = (n.label || '').toLowerCase();
      const name = (n.properties?.name || '').toLowerCase();
      const displayName = (n.properties?.displayName || '').toLowerCase();
      return label.includes(normalizedQuery) || name.includes(normalizedQuery) || displayName.includes(normalizedQuery);
    };

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

    // Labels layer above nodes so labels always render on top
    const labelLayer = container.append('g').attr('class', 'labels');

    // Add circles for nodes
    node.append('circle')
      .attr('r', (d: any) => {
        if (d.label === 'Undiscovered Devpost') return 20;
        if (d.label === 'Hacker') return 15;
        if (d.label === 'Devpost') return 20;
        return 10;
      })
      .attr('fill', (d: any) => {
        if (d.label === 'Undiscovered Devpost') return '#bbbbbb';
        if (d.label === 'Hacker') return '#4CAF50';
        if (d.label === 'Devpost') return '#2196F3';
        return '#FF9800';
      })
      .attr('stroke', (d: any) => isHighlighted(d) ? '#f59e0b' : '#fff')
      .attr('stroke-width', (d: any) => isHighlighted(d) ? 4 : 2)
      .attr('opacity', (d: any) => normalizedQuery && !isHighlighted(d) ? 0.35 : 1);

    // Add labels for nodes (with dark background for readability)
    node.on('mouseover', function(event, d) {
      // Remove any existing label for this node to avoid duplicates
      labelLayer
        .selectAll('g.hover-label-group')
        .filter((n: any) => n && n.id === d.id)
        .remove();

      // Group per label in the labels layer so it's above nodes
      const labelGroup = labelLayer
        .append('g')
        .attr('class', 'hover-label-group')
        .attr('data-id', d.id)
        // Avoid relying on bound data for positioning; use data-id lookup on tick
        .datum({ id: d.id });

      // Immediately position label group above the node to avoid (0,0) flicker
      const initialRadius = ((): number => {
        if (d.label === 'Undiscovered Devpost') return 20;
        if (d.label === 'Hacker') return 15;
        if (d.label === 'Devpost') return 20;
        return 10;
      })();
      if (typeof d.x === 'number' && typeof d.y === 'number') {
        labelGroup.attr('transform', `translate(${d.x}, ${d.y - initialRadius - 8})`);
      }

      // Text centered; group will be positioned on tick
      const text = labelGroup
        .append('text')
        .attr('x', 0)
        .attr('y', 0)
        .attr('text-anchor', 'middle')
        .attr('font-size', '12px')
        .attr('fill', '#e2e8f0')
        .text(() => {
          if (d.label === 'Hacker') {
            return d.properties.displayName || d.properties.name || 'Unknown Hacker';
          }
          if (d.label === 'Devpost') {
            return d.properties.name || 'Unknown Project';
          }
          if (d.label === 'Undiscovered Devpost') {
            return d.properties.name || "Undiscovered Devpost";
          }
          return d.label;
        })
        .attr('class', 'hover-label')
        .style('pointer-events', 'none');

      // Background sized to text bbox inside the label group
      let bbox = { x: 0, y: 0, width: 0, height: 0 } as DOMRect | { x: number; y: number; width: number; height: number };
      try {
        bbox = (text.node() as SVGGraphicsElement).getBBox();
      } catch (e) {
        // Fallback sizes if bbox not available yet
        const approx = (text.text() || '').length * 7;
        bbox = { x: -approx / 2, y: -10, width: approx, height: 16 } as any;
      }
      labelGroup
        .insert('rect', 'text.hover-label')
        .attr('class', 'hover-label-bg')
        .attr('x', bbox.x - 6)
        .attr('y', bbox.y - 3)
        .attr('width', bbox.width + 12)
        .attr('height', bbox.height + 6)
        .attr('rx', 4)
        .attr('ry', 4)
        .attr('fill', '#0f172a')
        .attr('fill-opacity', 0.9)
        .style('pointer-events', 'none');
    })
      .on('mouseout', function(event, d) {
        // Remove label group from the labels layer by filtering bound data
        labelLayer
          .selectAll('g.hover-label-group')
          .filter((n: any) => n && n.id === d.id)
          .remove();
      });

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

      // Keep labels above nodes and aligned above each node using live node positions
      const idToPos = new Map<string, { x: number; y: number; r: number }>();
      const getRadius = (n: any) => {
        if (n.label === 'Undiscovered Devpost') return 20;
        if (n.label === 'Hacker') return 15;
        if (n.label === 'Devpost') return 20;
        return 10;
      };
      node.each((n: any) => {
        idToPos.set(n.id, { x: n.x, y: n.y, r: getRadius(n) });
      });
      labelLayer
        .selectAll('g.hover-label-group')
        .each(function() {
          const el = this as SVGGElement;
          const id = el.getAttribute('data-id');
          if (!id) return;
          const pos = idToPos.get(id);
          if (!pos) return;
          d3.select(el).attr('transform', `translate(${pos.x}, ${pos.y - pos.r - 8})`);
        });
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

  }, [data, onNodeClick, onLinkClick, highlightQuery]);

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

