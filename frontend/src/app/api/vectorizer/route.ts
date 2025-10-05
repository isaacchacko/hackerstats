import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, projectId, query } = body;

    if (!action) {
      return NextResponse.json(
        { error: 'Action is required' },
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

    const resp = await fetch(`${PY_BACKEND_URL}/api/vectorizer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, projectId, query })
    });

    const text = await resp.text();
    if (!resp.ok) {
      return NextResponse.json(
        { error: 'Vectorizer request failed', details: text },
        { status: 502 }
      );
    }

    try {
      const json = JSON.parse(text);
      return NextResponse.json(json);
    } catch {
      return NextResponse.json({ success: true, output: text, action });
    }

  } catch (error) {
    console.error('Error executing vectorizer:', error);
    return NextResponse.json(
      { error: 'Failed to execute vectorizer operation' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get('action') || 'status';

    const PY_BACKEND_URL = process.env.PY_BACKEND_URL;
    if (!PY_BACKEND_URL) {
      return NextResponse.json(
        { error: 'PY_BACKEND_URL is not configured' },
        { status: 500 }
      );
    }

    const resp = await fetch(`${PY_BACKEND_URL}/api/vectorizer?action=${encodeURIComponent(action)}`, {
      method: 'GET'
    });

    const text = await resp.text();
    if (!resp.ok) {
      return NextResponse.json(
        { error: 'Vectorizer status failed', details: text },
        { status: 502 }
      );
    }

    try {
      const json = JSON.parse(text);
      return NextResponse.json(json);
    } catch {
      return NextResponse.json({ success: true, output: text, action });
    }

  } catch (error) {
    console.error('Error checking vectorizer status:', error);
    return NextResponse.json(
      { error: 'Failed to check vectorizer status' },
      { status: 500 }
    );
  }
}

