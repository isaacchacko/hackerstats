'use client';

import React from 'react';
import { motion } from 'framer-motion';
import VectorizerRepair from '@/components/VectorizerRepair';

export default function VectorizerPage() {
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
              Vector Tools
            </span>
          </h1>
          <p className="text-xl text-slate-300">
            Advanced vectorization and machine learning tools for project analysis
          </p>
        </motion.div>

        {/* Vectorizer Component */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <VectorizerRepair />
        </motion.div>
      </div>
    </div>
  );
}