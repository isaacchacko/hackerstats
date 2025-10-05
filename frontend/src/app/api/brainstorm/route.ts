import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query, top_k = 10 } = body || {};

    if (!query || typeof query !== 'string') {
      return NextResponse.json(
        { error: 'Query is required' },
        { status: 400 }
      );
    }

    const PY_BACKEND_URL = process.env.PY_BACKEND_URL;
    if (!PY_BACKEND_URL) {
      return NextResponse.json(
        { error: 'PY_BACKEND_URL is not configured' },
        { status: 500 }
      );
    }

    const resp = await fetch(`${PY_BACKEND_URL}/api/brainstorm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k })
    });

    if (!resp.ok) {
      const text = await resp.text();
      return NextResponse.json(
        { error: 'Brainstorm request failed', details: text },
        { status: 502 }
      );
    }

    const json = await resp.json();
    return NextResponse.json(json);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to run brainstorm' },
      { status: 500 }
    );
  }
}


