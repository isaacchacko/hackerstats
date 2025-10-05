# HackerStats Frontend

A Next.js web application for visualizing Neo4j graph data and managing vectorizer operations.

## Features

- **Interactive Graph Visualization**: D3.js-powered visualization of Neo4j graph data
- **Neo4j Integration**: Direct connection to Neo4j database via API routes
- **Vectorizer Management**: Tools for running scale tests and vector repair operations
- **Custom Query Interface**: Execute Cypher queries directly from the web interface
- **Real-time Statistics**: Live updates of graph statistics and node counts

## Setup

### Prerequisites

- Node.js 18+ 
- Neo4j database running locally or remotely
- Python backend with vectorizer tools

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.local.example .env.local
```

3. Configure environment variables in `.env.local`:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

4. Start the development server:
```bash
npm run dev
```

## API Endpoints

### Graph API (`/api/graph`)

- **GET**: Fetch graph data with optional filtering
  - `?nodeType=all|hackers|devposts` - Filter by node type
  - `?limit=100` - Limit number of nodes returned

- **POST**: Execute custom Cypher queries
  - Body: `{ "query": "MATCH (n) RETURN n LIMIT 10" }`

### Vectorizer API (`/api/vectorizer`)

- **GET**: Check system status and list available projects
  - `?action=status` - Check vectorizer status
  - `?action=list_projects` - List available projects

- **POST**: Execute vectorizer operations
  - `{ "action": "scale_test" }` - Run full scale test
  - `{ "action": "repair_vectors" }` - Repair existing vectors
  - `{ "action": "vectorize_project", "projectId": "project-name" }` - Vectorize specific project
  - `{ "action": "similarity_search", "query": "your query" }` - Search for similar projects

## Components

### GraphVisualization

Interactive D3.js graph component with:
- Force-directed layout
- Zoom and pan controls
- Node and link selection
- Real-time position updates
- Custom styling for different node types

### VectorizerRepair

Management interface for:
- System status monitoring
- Scale test execution
- Vector repair operations
- Project-specific vectorization
- Similarity search functionality

## Usage

1. **View Graph Data**: The main page loads and displays the Neo4j graph with interactive controls
2. **Filter Data**: Use the node type dropdown to filter between all nodes, hackers only, or projects only
3. **Execute Queries**: Use the custom query interface to run Cypher queries
4. **Manage Vectors**: Use the vectorizer repair section to run scale tests and repair operations
5. **Search Similarity**: Use the similarity search to find projects similar to your query

## Development

The application uses:
- **Next.js 15** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **D3.js** for graph visualization
- **Neo4j Driver** for database connectivity

## Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**: Check that Neo4j is running and credentials are correct
2. **Vectorizer Operations Fail**: Ensure Python backend is properly configured
3. **Graph Not Loading**: Check browser console for errors and verify API endpoints

### Debug Mode

Enable debug logging by adding to `.env.local`:
```
NEXT_PUBLIC_DEBUG=true
```