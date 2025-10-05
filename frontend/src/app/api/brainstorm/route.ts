import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'node:child_process';
import path from 'path';
import fs from 'node:fs';

// Ensure this route runs on the Node.js runtime (not Edge) so child_process is available
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

    const backendPath = path.join(process.cwd(), '..', 'backend');

    // Prefer the backend venv's python if available
    const venvPython = path.join(backendPath, 'venv', 'bin', 'python');
    const pythonCmd = fs.existsSync(venvPython) ? venvPython : 'python';

    const result = await new Promise<{ stdout: string; stderr: string; exitCode: number }>((resolve) => {
      const child = spawn(pythonCmd, ['brainstorm.py', '--query', query, '--top_k', String(top_k)], {
        cwd: backendPath,
        stdio: 'pipe'
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        resolve({ stdout, stderr, exitCode: code ?? 0 });
      });
    });

    if (result.exitCode !== 0) {
      return NextResponse.json(
        { error: 'Brainstorm process failed', details: result.stderr || result.stdout },
        { status: 500 }
      );
    }

    // The script prints JSON on stdout
    try {
      const json = JSON.parse(result.stdout);
      return NextResponse.json(json);
    } catch (e) {
      return NextResponse.json(
        { error: 'Failed to parse brainstorm output', raw: result.stdout },
        { status: 500 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to run brainstorm' },
      { status: 500 }
    );
  }
}


