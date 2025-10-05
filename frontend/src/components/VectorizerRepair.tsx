'use client';

import React, { useState, useEffect } from 'react';

interface VectorizerStatus {
  success: boolean;
  output: string;
  action: string;
}

interface Project {
  id: string;
  name: string;
}

const VectorizerRepair: React.FC = () => {
  const [status, setStatus] = useState<VectorizerStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [query, setQuery] = useState<string>('');

  const checkStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/vectorizer?action=status');
      const data = await response.json();
      
      if (data.success) {
        setStatus(data);
      } else {
        setError(data.error || 'Failed to check status');
      }
    } catch (err) {
      console.error('Error checking status:', err);
      setError(err instanceof Error ? err.message : 'Failed to check status');
    } finally {
      setLoading(false);
    }
  };

  const listProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/vectorizer?action=list_projects');
      const data = await response.json();
      
      if (data.success) {
        try {
          const projectList = JSON.parse(data.output);
          setProjects(projectList.map((name: string) => ({
            id: name.replace('_scraped.json', ''),
            name: name.replace('_scraped.json', '')
          })));
        } catch (parseError) {
          console.error('Error parsing projects:', parseError);
          setError('Failed to parse project list');
        }
      } else {
        setError(data.error || 'Failed to list projects');
      }
    } catch (err) {
      console.error('Error listing projects:', err);
      setError(err instanceof Error ? err.message : 'Failed to list projects');
    } finally {
      setLoading(false);
    }
  };

  const executeAction = async (action: string, payload: any = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/vectorizer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action, ...payload }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setStatus(data);
      } else {
        setError(data.error || 'Operation failed');
      }
    } catch (err) {
      console.error('Error executing action:', err);
      setError(err instanceof Error ? err.message : 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  const runScaleTest = () => {
    executeAction('scale_test');
  };

  const repairVectors = () => {
    executeAction('repair_vectors');
  };

  const vectorizeProject = () => {
    if (!selectedProject) {
      setError('Please select a project');
      return;
    }
    executeAction('vectorize_project', { projectId: selectedProject });
  };

  const searchSimilarity = () => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }
    executeAction('similarity_search', { query });
  };

  useEffect(() => {
    checkStatus();
    listProjects();
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Vectorizer Repair & Analysis
      </h2>
      
      <div className="space-y-6">
        {/* Status Section */}
        <div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">System Status</h3>
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={checkStatus}
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Checking...' : 'Check Status'}
            </button>
            
            <button
              onClick={listProjects}
              disabled={loading}
              className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'List Projects'}
            </button>
          </div>
          
          {status && (
            <div className="bg-gray-50 p-4 rounded-md">
              <h4 className="font-medium text-gray-800 mb-2">Status Output:</h4>
              <pre className="text-sm text-gray-600 whitespace-pre-wrap">{status.output}</pre>
            </div>
          )}
        </div>

        {/* Scale Test Section */}
        <div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">Scale Test</h3>
          <p className="text-sm text-gray-600 mb-4">
            Run the full scale test to process all 1.5k HTML files and generate vectors.
          </p>
          <button
            onClick={runScaleTest}
            disabled={loading}
            className="bg-purple-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
          >
            {loading ? 'Running...' : 'Run Scale Test'}
          </button>
        </div>

        {/* Vector Repair Section */}
        <div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">Vector Repair</h3>
          <p className="text-sm text-gray-600 mb-4">
            Repair and regenerate vectors for existing projects.
          </p>
          <button
            onClick={repairVectors}
            disabled={loading}
            className="bg-orange-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:opacity-50"
          >
            {loading ? 'Repairing...' : 'Repair Vectors'}
          </button>
        </div>

        {/* Project Vectorization Section */}
        <div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">Project Vectorization</h3>
          <p className="text-sm text-gray-600 mb-4">
            Vectorize a specific project for analysis.
          </p>
          
          <div className="flex items-center gap-4 mb-4">
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a project</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
            
            <button
              onClick={vectorizeProject}
              disabled={loading || !selectedProject}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Vectorizing...' : 'Vectorize Project'}
            </button>
          </div>
        </div>

        {/* Similarity Search Section */}
        <div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">Similarity Search</h3>
          <p className="text-sm text-gray-600 mb-4">
            Search for projects similar to your query using vector similarity.
          </p>
          
          <div className="flex items-center gap-4 mb-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your project idea or description..."
              className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            
            <button
              onClick={searchSimilarity}
              disabled={loading || !query.trim()}
              className="bg-teal-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:opacity-50"
            >
              {loading ? 'Searching...' : 'Search Similar'}
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Error
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  {error}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results Display */}
        {status && status.action !== 'status' && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">
                  Operation Completed: {status.action}
                </h3>
                <div className="mt-2 text-sm text-green-700">
                  <pre className="whitespace-pre-wrap">{status.output}</pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VectorizerRepair;

