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
    const limitParam = searchParams.get('limit') || '500';
    const nameParam = searchParams.get('name') || 'isaacchacko';
    const connectionsParam = searchParams.get('connections') || searchParams.get('depth') || '100';

    // Sanitize parameters
    const limit = Math.max(1, Math.floor(parseInt(limitParam, 10) || 500));
    // Allow large exploration but guard against unbounded values
    const depth = Math.min(100, Math.max(1, Math.floor(parseInt(connectionsParam, 10) || 2)));

    const session = driver.session();

    try {
      // Build a query that starts from a specific Hacker by name and explores up to `depth` hops.
      // We limit on DISTINCT nodes (not paths) to maximize unique nodes while keeping the subgraph connected from the start node.
      // Note: variable-length upper bounds cannot be parameterized, so we safely inline the validated integer depth
      const query = `
        MATCH (h:Hacker {name: $name})
        MATCH p=(h)-[*..${depth}]-(m)
        WITH p
        UNWIND nodes(p) AS n
        WITH DISTINCT n LIMIT TOINTEGER($nodeLimit)
        WITH collect(n) AS nodes
        UNWIND nodes AS n
        MATCH (n)-[r]-(m)
        WHERE m IN nodes
        WITH nodes, collect(DISTINCT r) AS rs
        RETURN nodes AS ns, rs AS rs
      `;

      const params: any = { name: nameParam, nodeLimit: limit };
      const result = await session.run(query, params);

      // Transform returned node/relationship arrays into D3-style nodes/links
      const nodes: any[] = [];
      const links: any[] = [];
      const nodeMap = new Map<string, any>();

      if (result.records.length > 0) {
        const record = result.records[0];
        const ns = record.get('ns') || [];
        const rs = record.get('rs') || [];

        ns.forEach((neoNode: any) => {
          const nodeId = neoNode.identity.toString();
          if (nodeMap.has(nodeId)) return;
          const nodeData = {
            id: nodeId,
            label: neoNode.labels && neoNode.labels.length ? neoNode.labels[0] : 'Node',
            properties: neoNode.properties,
            x: Math.random() * 800,
            y: Math.random() * 600
          };
          nodes.push(nodeData);
          nodeMap.set(nodeId, nodeData);
        });

        rs.forEach((rel: any) => {
          const sourceId = rel.start.toString();
          const targetId = rel.end.toString();
          // Only include links where both nodes are in our node set
          if (!nodeMap.has(sourceId) || !nodeMap.has(targetId)) return;
          links.push({
            source: sourceId,
            target: targetId,
            type: rel.type,
            properties: rel.properties
          });
        });
      }

      return NextResponse.json({
        nodes,
        links,
        totalNodes: nodes.length,
        totalLinks: links.length,
        start: nameParam,
        depth
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
          // statementType: result.summary.statementType,
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
