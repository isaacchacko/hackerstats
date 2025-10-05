"""
Brainstorm query -> top-10 similar projects

Usage:
  python brainstorm.py --query "your idea here"

This script loads precomputed project vectors and parsed project metadata,
vectorizes the query using the same `DevpostVectorizer` combined vector,
and returns the top-10 most similar projects as JSON to stdout.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Tuple

import numpy as np

from vectorizer import DevpostVectorizer


def load_projects_and_vectors() -> Tuple[List[Dict[str, Any]], np.ndarray]:
    """Load parsed projects and their precomputed vectors if available.

    Expects files in current working directory:
      - parsed_projects_full.json     (metadata scraped from devposts)
      - project_vectors.npy           (NxD array of combined vectors)
    """
    projects_path = 'parsed_projects_full.json'
    vectors_path = 'project_vectors.npy'

    if not os.path.exists(projects_path):
        raise FileNotFoundError(
            f"Missing {projects_path}. Run your parsing/vectorization pipeline first."
        )
    if not os.path.exists(vectors_path):
        raise FileNotFoundError(
            f"Missing {vectors_path}. Run your vectorization pipeline to produce it."
        )

    with open(projects_path, 'r', encoding='utf-8') as f:
        projects = json.load(f)

    vectors = np.load(vectors_path)
    if vectors.ndim != 2 or len(projects) != vectors.shape[0]:
        raise ValueError(
            "Mismatch between number of projects and vectors. Ensure both were generated together."
        )

    return projects, vectors


def compute_top_k_similar(
    query_vector: np.ndarray, project_vectors: np.ndarray, top_k: int = 10
) -> List[Tuple[int, float]]:
    """Compute cosine similarity between query and each project vector.

    Returns list of (index, similarity) sorted desc by similarity.
    """
    # Normalize vectors to avoid repeated norm computations
    q_norm = np.linalg.norm(query_vector)
    if q_norm == 0:
        # Avoid division by zero; all similarities zero
        return [(i, 0.0) for i in range(project_vectors.shape[0])][:top_k]

    pv_norms = np.linalg.norm(project_vectors, axis=1)
    # Cosine similarity = (q · p) / (||q|| * ||p||)
    dots = project_vectors @ query_vector
    denom = q_norm * pv_norms
    # Avoid divide-by-zero
    denom[denom == 0] = 1e-12
    sims = dots / denom

    # Get top-k indices efficiently
    if top_k >= sims.shape[0]:
        top_indices = np.argsort(-sims)
    else:
        top_part = np.argpartition(-sims, top_k)[:top_k]
        top_indices = top_part[np.argsort(-sims[top_part])]

    return [(int(i), float(sims[i])) for i in top_indices[:top_k]]


def main() -> int:
    parser = argparse.ArgumentParser(description='Brainstorm similarity search')
    parser.add_argument('--query', required=True, help='User prompt / project idea')
    parser.add_argument('--top_k', type=int, default=10, help='Number of results to return')
    args = parser.parse_args()

    try:
        projects, project_vectors = load_projects_and_vectors()
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': f'Failed to load data: {e}'
        }), flush=True)
        return 1

    # Build a mock project like scale_test interactive section
    mock_project = {
        'title': args.query,
        'tagline': '',
        'built_with': [],
        'team_members': [],
        'awards': [],
        'description': [{'heading': 'Query', 'content': args.query}]
    }

    try:
        vectorizer = DevpostVectorizer()
        query_vectors = vectorizer.vectorize_project(mock_project)
        query_vector = query_vectors['combined']
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': f'Failed to vectorize query: {e}'
        }), flush=True)
        return 1

    top = compute_top_k_similar(query_vector, project_vectors, top_k=args.top_k)

    results: List[Dict[str, Any]] = []
    for idx, sim in top:
        proj = projects[idx]
        project_id = proj.get('project_id', '')
        if not project_id and proj.get('file_path'):
            try:
                import os as _os
                fn = _os.path.basename(proj.get('file_path') or '')
                if fn.endswith('.html'):
                    project_id = fn[:-5]
            except Exception:
                pass
        url = f"https://devpost.com/software/{project_id}" if project_id else ''
        results.append({
            'index': idx,
            'similarity': sim,
            'title': proj.get('title', ''),
            'tagline': proj.get('tagline', ''),
            'hackathon': proj.get('hackathon', ''),
            'built_with': proj.get('built_with', [])[:8],
            'awards': proj.get('awards', [])[:4],
            'team_size': len(proj.get('team_members', [])),
            'project_id': project_id,
            'file_path': proj.get('file_path', ''),
            'url': url,
            'thumbnail': proj.get('thumbnail', ''),
            'won': bool(proj.get('won')) or (len(proj.get('awards', [])) > 0)
        })

    print(json.dumps({
        'success': True,
        'count': len(results),
        'results': results
    }, ensure_ascii=False), flush=True)

    return 0


if __name__ == '__main__':
    sys.exit(main())


