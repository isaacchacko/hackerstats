import { NextRequest, NextResponse } from 'next/server';
import neo4j from 'neo4j-driver';

// Neo4j connection configuration
const NEO4J_URI = process.env.NEO4J_URI || 'bolt://localhost:7687';
const NEO4J_USERNAME = process.env.NEO4J_USERNAME || 'neo4j';
const NEO4J_PASSWORD = process.env.NEO4J_PASSWORD || 'password';


// Create Neo4j driver with proper encryption settings for Aura
const driver = neo4j.driver(
  NEO4J_URI,
  neo4j.auth.basic(NEO4J_USERNAME, NEO4J_PASSWORD),
  // {
  // encrypted: 'ENCRYPTION_ON',
  // trust: 'TRUST_SYSTEM_CA_SIGNED_CERTIFICATES'
  // }
);

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limitParam = searchParams.get('limit') || 100;
    // const limit = Math.max(1, Math.floor(parseInt(limitParam, 10) || 100));
    const nodeType = searchParams.get('nodeType') || 'all';

    const session = driver.session();

    try {
      let query: string;
      let params: any = { limit: limitParam };

      if (nodeType === 'hackers') {
        query = `
          MATCH (h:Hacker)
          OPTIONAL MATCH (h)-[:CONTRIBUTED_TO]->(d:Devpost)
          RETURN h, collect(d) as devposts
          LIMIT TOINTEGER($limit)
        `;
      } else if (nodeType === 'devposts') {
        query = `
          MATCH (d:Devpost)
          OPTIONAL MATCH (h:Hacker)-[:CONTRIBUTED_TO]->(d)
          RETURN d, collect(h) as hackers
          LIMIT TOINTEGER($limit)
        `;
      } else {
        // Get all nodes and relationships
        query = `
          MATCH (n)
          OPTIONAL MATCH (n)-[r]->(m)
          RETURN n, r, m
          LIMIT TOINTEGER($limit)
        `;
      }

      const result = await session.run(query, params);

      // Transform the result into a format suitable for D3.js
      const nodes: any[] = [];
      const links: any[] = [];
      const nodeMap = new Map();

      result.records.forEach(record => {
        const node = record.get('n');
        const relationship = record.get('r');
        const targetNode = record.get('m');

        if (node) {
          const nodeId = node.identity.toString();
          if (!nodeMap.has(nodeId)) {
            const nodeData = {
              id: nodeId,
              label: node.labels[0],
              properties: node.properties,
              x: Math.random() * 800,
              y: Math.random() * 600
            };
            nodes.push(nodeData);
            nodeMap.set(nodeId, nodeData);
          }
        }

        if (relationship && targetNode) {
          const sourceId = relationship.start.toString();
          const targetId = relationship.end.toString();

          // Ensure both nodes exist
          if (!nodeMap.has(sourceId)) {
            const sourceNode = {
              id: sourceId,
              label: 'Unknown',
              properties: {},
              x: Math.random() * 800,
              y: Math.random() * 600
            };
            nodes.push(sourceNode);
            nodeMap.set(sourceId, sourceNode);
          }

          if (!nodeMap.has(targetId)) {
            const targetNodeData = {
              id: targetId,
              label: 'Unknown',
              properties: {},
              x: Math.random() * 800,
              y: Math.random() * 600
            };
            nodes.push(targetNodeData);
            nodeMap.set(targetId, targetNodeData);
          }

          links.push({
            source: sourceId,
            target: targetId,
            type: relationship.type,
            properties: relationship.properties
          });
        }
      });

      return NextResponse.json({
        nodes,
        links,
        totalNodes: nodes.length,
        totalLinks: links.length
      });

    } finally {
      await session.close();
    }

  } catch (error) {
    console.error('Error fetching graph data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch graph data' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query, params = {} } = body;

    if (!query) {
      return NextResponse.json(
        { error: 'Query is required' },
        { status: 400 }
      );
    }

    const session = driver.session();

    try {
      const result = await session.run(query, params);

      const records = result.records.map(record => {
        const obj: any = {};
        record.keys.forEach(key => {
          obj[key] = record.get(key);
        });
        return obj;
      });

      return NextResponse.json({
        records,
        summary: {
          resultAvailableAfter: result.summary.resultAvailableAfter,
          resultConsumedAfter: result.summary.resultConsumedAfter,
          statementType: result.summary.statementType,
          counters: result.summary.counters
        }
      });

    } finally {
      await session.close();
    }

  } catch (error) {
    console.error('Error executing query:', error);
    return NextResponse.json(
      { error: 'Failed to execute query' },
      { status: 500 }
    );
  }
}
