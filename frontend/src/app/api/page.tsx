'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';

export default function APIPage() {
  const [activeEndpoint, setActiveEndpoint] = useState('graph');

  const endpoints = [
    {
      id: 'graph',
      name: 'Graph API',
      method: 'GET/POST',
      path: '/api/graph',
      description: 'Retrieve and query graph data from Neo4j database',
      examples: [
        {
          title: 'Get all nodes',
          code: 'GET /api/graph?nodeType=all&limit=100'
        },
        {
          title: 'Get hackers only',
          code: 'GET /api/graph?nodeType=hackers&limit=50'
        },
        {
          title: 'Custom Cypher query',
          code: `POST /api/graph
{
  "query": "MATCH (h:Hacker)-[:CONTRIBUTED_TO]->(d:Devpost) RETURN h, d LIMIT 10"
}`
        }
      ]
    },
    {
      id: 'vectorizer',
      name: 'Vectorizer API',
      method: 'POST',
      path: '/api/vectorizer',
      description: 'Vectorization and similarity analysis tools',
      examples: [
        {
          title: 'Run scale test',
          code: `POST /api/vectorizer
{
  "action": "scale_test"
}`
        },
        {
          title: 'Repair vectors',
          code: `POST /api/vectorizer
{
  "action": "repair_vectors"
}`
        },
        {
          title: 'Similarity search',
          code: `POST /api/vectorizer
{
  "action": "similarity_search",
  "query": "AI-powered healthcare app"
}`
        }
      ]
    }
  ];

  const activeEndpointData = endpoints.find(ep => ep.id === activeEndpoint);

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
            <a href="/graph" className="text-slate-300 hover:text-blue-400 transition-colors duration-300 hover:-translate-y-0.5">
              Graph
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
          className="mb-8"
        >
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-4">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              API Documentation
            </span>
          </h1>
          <p className="text-xl text-slate-300">
            Comprehensive API reference for HackerStats platform
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <motion.div 
            className="lg:col-span-1"
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6 sticky top-8">
              <h3 className="text-lg font-semibold text-white mb-4">Endpoints</h3>
              <div className="space-y-2">
                {endpoints.map((endpoint) => (
                  <motion.button
                    key={endpoint.id}
                    onClick={() => setActiveEndpoint(endpoint.id)}
                    className={`w-full text-left px-4 py-3 rounded-lg transition-all duration-300 hover:scale-105 ${
                      activeEndpoint === endpoint.id
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-[0_0_20px_rgba(59,130,246,0.3)]'
                        : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="font-medium">{endpoint.name}</div>
                    <div className="text-sm opacity-75">{endpoint.method}</div>
                  </motion.button>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Main Content */}
          <motion.div 
            className="lg:col-span-3"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            {activeEndpointData && (
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-8">
                <div className="mb-6">
                  <div className="flex items-center gap-4 mb-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      activeEndpointData.method === 'GET' 
                        ? 'bg-green-600/20 text-green-300 border border-green-500/30'
                        : 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                    }`}>
                      {activeEndpointData.method}
                    </span>
                    <code className="text-lg font-mono text-slate-300 bg-slate-700/50 px-3 py-1 rounded">
                      {activeEndpointData.path}
                    </code>
                  </div>
                  <p className="text-slate-300 text-lg">{activeEndpointData.description}</p>
                </div>

                <div className="space-y-6">
                  <h4 className="text-xl font-semibold text-white">Examples</h4>
                  {activeEndpointData.examples.map((example, index) => (
                    <motion.div
                      key={index}
                      className="bg-slate-900/50 border border-slate-600/50 rounded-lg p-6 hover:border-slate-500/50 transition-all duration-300"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: index * 0.1 }}
                    >
                      <h5 className="text-lg font-medium text-white mb-3">{example.title}</h5>
                      <pre className="bg-slate-800/50 p-4 rounded-lg overflow-x-auto">
                        <code className="text-slate-300 text-sm">{example.code}</code>
                      </pre>
                    </motion.div>
                  ))}
                </div>

                {/* Response Example */}
                <div className="mt-8">
                  <h4 className="text-xl font-semibold text-white mb-4">Response Format</h4>
                  <div className="bg-slate-900/50 border border-slate-600/50 rounded-lg p-6">
                    <pre className="text-slate-300 text-sm overflow-x-auto">
                      <code>{`{
  "nodes": [
    {
      "id": "node1",
      "label": "Hacker",
      "properties": {
        "name": "John Doe",
        "username": "johndoe"
      }
    }
  ],
  "links": [
    {
      "source": "node1",
      "target": "node2",
      "type": "CONTRIBUTED_TO"
    }
  ],
  "totalNodes": 100,
  "totalLinks": 150
}`}</code>
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        </div>

        {/* Quick Start */}
        <motion.div 
          className="mt-12 bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-xl p-8"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
        >
          <h3 className="text-2xl font-bold text-white mb-4">Quick Start</h3>
          <p className="text-slate-300 mb-6">
            Get started with the HackerStats API in just a few steps:
          </p>
          
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-xl mx-auto mb-4">
                1
              </div>
              <h4 className="font-semibold text-white mb-2">Choose Endpoint</h4>
              <p className="text-slate-300 text-sm">Select the appropriate API endpoint for your use case</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold text-xl mx-auto mb-4">
                2
              </div>
              <h4 className="font-semibold text-white mb-2">Make Request</h4>
              <p className="text-slate-300 text-sm">Send HTTP requests with proper parameters and headers</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center text-white font-bold text-xl mx-auto mb-4">
                3
              </div>
              <h4 className="font-semibold text-white mb-2">Process Data</h4>
              <p className="text-slate-300 text-sm">Handle the JSON response and integrate with your application</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}