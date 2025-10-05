import os
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Heavy deps imported lazily where helpful to avoid cold-start costs
from brainstorm import load_projects_and_vectors, compute_top_k_similar
from vectorizer import DevpostVectorizer


class BrainstormRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10


class VectorizerRequest(BaseModel):
    action: str
    projectId: Optional[str] = None
    query: Optional[str] = None
    project: Optional[Dict[str, Any]] = None


app = FastAPI(title="HackerStats Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Simple in-process caches to avoid reloading on each request
_cache: Dict[str, Any] = {
    "projects": None,
    "project_vectors": None,
    "vectorizer": None,
}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


def get_projects_and_vectors() -> Tuple[List[Dict[str, Any]], Any]:
    if _cache["projects"] is None or _cache["project_vectors"] is None:
        projects, project_vectors = load_projects_and_vectors()
        _cache["projects"] = projects
        _cache["project_vectors"] = project_vectors
    return _cache["projects"], _cache["project_vectors"]


def get_vectorizer() -> DevpostVectorizer:
    if _cache["vectorizer"] is None:
        _cache["vectorizer"] = DevpostVectorizer()
    return _cache["vectorizer"]


@app.post("/api/brainstorm")
def brainstorm_endpoint(req: BrainstormRequest) -> Dict[str, Any]:
    if not req.query or not isinstance(req.query, str):
        raise HTTPException(status_code=400, detail="Query is required")

    projects, project_vectors = get_projects_and_vectors()
    vectorizer = get_vectorizer()

    # Build a minimal project from the query and vectorize
    mock_project = {
        'title': req.query,
        'tagline': '',
        'built_with': [],
        'team_members': [],
        'awards': [],
        'description': [{'heading': 'Query', 'content': req.query}],
    }
    query_vectors = vectorizer.vectorize_project(mock_project)
    query_vector = query_vectors['combined']

    top = compute_top_k_similar(query_vector, project_vectors, top_k=int(req.top_k or 10))

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
            'won': bool(proj.get('won')) or (len(proj.get('awards', [])) > 0),
        })

    return {"success": True, "count": len(results), "results": results}


@app.get("/api/vectorizer")
def vectorizer_status(action: Optional[str] = "status") -> Dict[str, Any]:
    if action == "status":
        return {"success": True, "status": "ok"}
    return {"success": False, "error": "Invalid action"}


@app.post("/api/vectorizer")
def vectorizer_endpoint(req: VectorizerRequest) -> Dict[str, Any]:
    if not req.action:
        raise HTTPException(status_code=400, detail="Action is required")

    if req.action == 'similarity_search':
        if not req.query:
            raise HTTPException(status_code=400, detail="Query is required for similarity_search")
        # Reuse brainstorm implementation
        return brainstorm_endpoint(BrainstormRequest(query=req.query, top_k=10))

    if req.action == 'vectorize_project':
        if not req.project:
            raise HTTPException(status_code=400, detail="project object is required for vectorize_project")
        vectorizer = get_vectorizer()
        vectors = vectorizer.vectorize_project(req.project)
        # Convert numpy arrays to lists for JSON
        serializable = {k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in vectors.items()}
        return {"success": True, "vectors": serializable}

    if req.action == 'scale_test':
        return {"success": False, "error": "scale_test not implemented over HTTP"}

    if req.action == 'repair_vectors':
        return {"success": False, "error": "repair_vectors not implemented over HTTP"}

    raise HTTPException(status_code=400, detail="Invalid action")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)


