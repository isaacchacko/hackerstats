'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import GraphVisualization from '@/components/GraphVisualization';

interface GraphData {
  nodes: any[];
  links: any[];
  totalNodes: number;
  totalLinks: number;
}

export default function GraphPage() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nodeType, setNodeType] = useState<string>('all');
  const [limit, setLimit] = useState<number>(100);
  const [selectedNode, setSelectedNode] = useState<any>(null);

  const fetchGraphData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/graph?nodeType=${nodeType}&limit=${limit}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setGraphData(data);
    } catch (err) {
      console.error('Error fetching graph data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch graph data');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = (node: any) => {
    console.log('Node clicked:', node);
    setSelectedNode(node);
  };

  const handleLinkClick = (link: any) => {
    console.log('Link clicked:', link);
  };


  useEffect(() => {
    fetchGraphData();
  }, [nodeType]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Navigation */}
      <motion.nav
        className="relative z-50 p-6"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <motion.a
            href="/"
            className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400"
            whileHover={{ scale: 1.05 }}
          >
            HackerStats
          </motion.a>

          <div className="flex space-x-6">
            <a href="/" className="text-slate-300 hover:text-blue-400 transition-colors duration-300 hover:-translate-y-0.5">
              Home
            </a>
            <a href="/vectorizer" className="text-slate-300 hover:text-blue-400 transition-colors duration-300 hover:-translate-y-0.5">
              Vector Tools
            </a>
          </div>
        </div>
      </motion.nav>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="mb-8 flex flex-row justify-between"
        >
          <div className='flex flex-col'>
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-4">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                Graph Visualization
              </span>
            </h1>
            <p className="text-xl text-slate-300">
              Explore the interconnected world of hackathons, projects, and hackers
            </p>
          </div>

          <div className="flex flex-wrap gap-6 items-center">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Node Type
              </label>
              <select
                value={nodeType}
                onChange={(e) => setNodeType(e.target.value)}
                className="bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 hover:bg-slate-600"
              >
                <option value="all">All Nodes</option>
                <option value="hackers">Hackers Only</option>
                <option value="devposts">Projects Only</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Limit
              </label>
              <input
                type="number"
                value={limit}
                onChange={(e) => setLimit(Math.max(1, Math.floor(parseInt(e.target.value) || 100)))}
                min="1"
                max="1000"
                step="1"
                className="bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 hover:bg-slate-600"
              />
            </div>

            <motion.button
              onClick={fetchGraphData}
              disabled={loading}
              className="relative px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-blue-500/50 disabled:opacity-50 hover:shadow-[0_0_30px_rgba(59,130,246,0.6),0_0_60px_rgba(147,51,234,0.4)]"
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.95 }}
            >
              {loading ? 'Loading...' : 'Refresh Data'}
            </motion.button>
          </div>
        </motion.div>

        {/* Controls */}
        <motion.div
          className={`${error ? 'block' : 'hidden'} bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6 mb-6`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {error && (
            <motion.div
              className="mt-4 bg-red-900/50 border border-red-500/50 rounded-lg p-4"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-300">
                    Error
                  </h3>
                  <div className="mt-2 text-sm text-red-200">
                    {error}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>

        {/* Graph Visualization with Right Panel */}
        <motion.div
          className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <h2 className="text-2xl font-bold text-white mb-6">
            Interactive Graph
          </h2>

          <div className="flex gap-6">
            {/* Graph Area */}
            <div className="flex-1">
              <GraphVisualization
                data={graphData}
                onNodeClick={handleNodeClick}
                onLinkClick={handleLinkClick}
              />
            </div>

            {/* Right Panel for Selected Node */}
            {selectedNode && (
              <motion.div
                className="w-80 bg-slate-700/50 backdrop-blur-sm border border-slate-600/50 rounded-xl p-6"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-bold text-white">Node Details</h3>
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="text-slate-400 hover:text-white transition-colors"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-lg font-semibold text-blue-300 mb-2">
                      {selectedNode.label}
                    </h4>
                    <div className="text-sm text-slate-300 space-y-1">
                      <p><span className="font-medium">ID:</span> {selectedNode.id}</p>
                      {Object.entries(selectedNode.properties).map(([key, value]) => (
                        <p key={key}>
                          <span className="font-medium">{key}:</span> {String(value)}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>

        {/* Statistics */}
        {graphData && (
          <motion.div
            className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <div className="bg-gradient-to-br from-blue-600/20 to-blue-800/20 border border-blue-500/30 rounded-xl p-6 hover:shadow-[0_0_30px_rgba(59,130,246,0.3)] transition-all duration-300">
              <h3 className="font-semibold text-blue-300 mb-2">Total Nodes</h3>
              <p className="text-3xl font-bold text-blue-100">{graphData.totalNodes}</p>
            </div>

            <div className="bg-gradient-to-br from-purple-600/20 to-purple-800/20 border border-purple-500/30 rounded-xl p-6 hover:shadow-[0_0_30px_rgba(147,51,234,0.3)] transition-all duration-300">
              <h3 className="font-semibold text-purple-300 mb-2">Total Links</h3>
              <p className="text-3xl font-bold text-purple-100">{graphData.totalLinks}</p>
            </div>

            <div className="bg-gradient-to-br from-slate-600/20 to-slate-800/20 border border-slate-500/30 rounded-xl p-6 hover:shadow-[0_0_30px_rgba(71,85,105,0.3)] transition-all duration-300">
              <h3 className="font-semibold text-slate-300 mb-2">Node Types</h3>
              <div className="text-sm text-slate-200">
                {Array.from(new Set(graphData.nodes.map(n => n.label))).map(label => (
                  <div key={label} className="flex justify-between">
                    <span>{label}:</span>
                    <span>{graphData.nodes.filter(n => n.label === label).length}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
