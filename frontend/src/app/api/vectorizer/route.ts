import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

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

    // Path to the backend directory
    const backendPath = path.join(process.cwd(), '..', 'backend');
    
    let command: string;
    let args: string[] = [];

    switch (action) {
      case 'vectorize_project':
        if (!projectId) {
          return NextResponse.json(
            { error: 'Project ID is required for vectorization' },
            { status: 400 }
          );
        }
        command = 'python';
        args = ['vectorizer.py', projectId];
        break;

      case 'scale_test':
        command = 'python';
        args = ['scale_test.py'];
        break;

      case 'similarity_search':
        if (!query) {
          return NextResponse.json(
            { error: 'Query is required for similarity search' },
            { status: 400 }
          );
        }
        command = 'python';
        args = ['test_vectorizer.py', '--query', query];
        break;

      case 'repair_vectors':
        command = 'python';
        args = ['scale_test.py', '--repair'];
        break;

      default:
        return NextResponse.json(
          { error: 'Invalid action' },
          { status: 400 }
        );
    }

    // Execute the Python script
    const result = await new Promise<{ stdout: string; stderr: string; exitCode: number }>((resolve) => {
      const process = spawn(command, args, {
        cwd: backendPath,
        stdio: 'pipe'
      });

      let stdout = '';
      let stderr = '';

      process.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      process.on('close', (code) => {
        resolve({
          stdout,
          stderr,
          exitCode: code || 0
        });
      });
    });

    if (result.exitCode !== 0) {
      return NextResponse.json(
        { 
          error: 'Vectorizer process failed',
          details: result.stderr,
          stdout: result.stdout
        },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      output: result.stdout,
      action
    });

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

    // Path to the backend directory
    const backendPath = path.join(process.cwd(), '..', 'backend');
    
    let command: string;
    let args: string[] = [];

    switch (action) {
      case 'status':
        command = 'python';
        args = ['-c', 'import os; print("Vectorizer files exist:", os.path.exists("vectorizer.py"), os.path.exists("scale_test.py"))'];
        break;

      case 'list_projects':
        command = 'python';
        args = ['-c', 'import os, json; print(json.dumps([f for f in os.listdir(".") if f.endswith("_scraped.json")]))'];
        break;

      default:
        return NextResponse.json(
          { error: 'Invalid action' },
          { status: 400 }
        );
    }

    // Execute the Python script
    const result = await new Promise<{ stdout: string; stderr: string; exitCode: number }>((resolve) => {
      const process = spawn(command, args, {
        cwd: backendPath,
        stdio: 'pipe'
      });

      let stdout = '';
      let stderr = '';

      process.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      process.on('close', (code) => {
        resolve({
          stdout,
          stderr,
          exitCode: code || 0
        });
      });
    });

    if (result.exitCode !== 0) {
      return NextResponse.json(
        { 
          error: 'Status check failed',
          details: result.stderr
        },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      output: result.stdout,
      action
    });

  } catch (error) {
    console.error('Error checking vectorizer status:', error);
    return NextResponse.json(
      { error: 'Failed to check vectorizer status' },
      { status: 500 }
    );
  }
}

