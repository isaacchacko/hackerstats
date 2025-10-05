"""
Reverse engineering helper for project vectors and parsed metadata.

What this does:
- Regenerates parsed_projects_full.json by re-parsing local Devpost HTML in ./devposts
- Recomputes project_vectors.npy using DevpostVectorizer (preferred, exact-ish)
- If only similarity_matrix.npy is available (no vectorizer), produces an
  approximate embedding project_vectors_approx.npy via spectral embedding so that
  cosine similarities between rows roughly match the similarity matrix

Notes on reversibility:
- From a cosine similarity matrix alone, original vectors are NOT uniquely
  recoverable (they are only determined up to an orthogonal transform and row
  scaling; standardization during training further obscures them). Therefore,
  we prefer recomputation using the original feature pipeline when possible.

Usage examples:
  python reverse.py --regen-parsed --recompute-vectors
  python reverse.py --from-similarity  # creates project_vectors_approx.npy

Outputs:
  - parsed_projects_full.json
  - project_vectors.npy (if recomputed) OR project_vectors_approx.npy (if approximated)
"""

import os
import json
import argparse
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    # Vectorizer is optional if only approximating from similarity
    from vectorizer import DevpostVectorizer  # type: ignore
    VECTORIZER_AVAILABLE = True
except Exception:
    VECTORIZER_AVAILABLE = False

from bs4 import BeautifulSoup
import re
from devpost_scraper import scrape_devpost
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp


_AWARD_PATTERNS = [
    re.compile(r'Winner.*?Track.*?([^\.\n]{5,100})', re.IGNORECASE | re.DOTALL),
    re.compile(r'Best.*?([^\.\n]{5,100})', re.IGNORECASE | re.DOTALL),
    re.compile(r'First Place.*?([^\.\n]{5,100})', re.IGNORECASE | re.DOTALL),
    re.compile(r'Second Place.*?([^\.\n]{5,100})', re.IGNORECASE | re.DOTALL),
    re.compile(r'Third Place.*?([^\.\n]{5,100})', re.IGNORECASE | re.DOTALL),
    re.compile(r'Sponsored by.*?([^\.\n]{5,100})', re.IGNORECASE | re.DOTALL),
    re.compile(r'Winner.*?([^\.\n]{5,100})', re.IGNORECASE | re.DOTALL),
    re.compile(r'Award.*?([^\.\n]{5,100})', re.IGNORECASE | re.DOTALL),
    re.compile(r'Prize.*?([^\.\n]{5,100})', re.IGNORECASE | re.DOTALL),
    re.compile(r'Champion.*?([^\.\n]{5,100})', re.IGNORECASE | re.DOTALL),
    re.compile(r'Grand Prize.*?([^\.\n]{5,100})', re.IGNORECASE | re.DOTALL),
]

_AWARD_KEYWORDS = set([
    'hack', 'track', 'prize', 'award', 'winner', 'best', 'first', 'second', 'third',
    'sponsored', 'champion', 'grand', 'overall', 'category', 'theme'
])

_AWARD_NOISE = set([
    'javascript', 'function', 'var ', 'css', 'html', 'script',
    'font-awesome', 'fa-', 'class=', 'href=', 'src=',
    'undefined', 'null', 'true', 'false', 'console.log',
    'document.', 'window.', 'jquery', 'bootstrap',
    'implemented', 'firmware', 'backend', 'database', 'supabase',
    'modern care', 'bottle', 'iot', 'medication', 'tracker',
    'practices', 'planning', 'online', 'in-person'
])


def parse_html_file(file_path: str, debug: bool = False) -> Optional[Dict[str, Any]]:
    """Parse Devpost HTML for project data (lightweight; mirrors scale_test/repair).

    Returns None if minimal fields are missing (e.g., no title).
    """
    try:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                html_content = f.read()

        # Use fast lxml parser when available, fallback to html.parser
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except Exception:
            soup = BeautifulSoup(html_content, 'html.parser')

        project_data: Dict[str, Any] = {
            'file_path': file_path,
            'project_id': os.path.basename(file_path).replace('.html', ''),
            'title': '',
            'tagline': '',
            'hackathon': '',
            'built_with': [],
            'team_members': [],  # display names (back-compat)
            'team_usernames': [],  # devpost usernames
            'awards': [],
            'won': False,
            'thumbnail': '',
            'description': []
        }

        # Try many selectors for title
        title_elem = (
            soup.find('h1', id='app-title') or
            soup.find('h1', id='software-name') or
            soup.find('h1', class_='software-name') or
            soup.find('h1', attrs={'data-role': 'software-name'}) or
            soup.find('h1')
        )
        if not title_elem:
            # Fallbacks: meta og:title or <title>
            meta_og = soup.find('meta', property='og:title')
            if meta_og and meta_og.get('content'):
                project_data['title'] = meta_og.get('content').strip()
        else:
            project_data['title'] = title_elem.get_text(strip=True)

        tagline_elem = (soup.find('p', class_='large') or 
                        soup.find('p', id='software-tagline') or 
                        soup.find('p', class_='tagline') or
                        soup.find('div', class_='software-tagline') or
                        soup.find('p', attrs={'data-role': 'software-tagline'}))
        if tagline_elem:
            project_data['tagline'] = tagline_elem.get_text(strip=True)
        elif not project_data['tagline']:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                project_data['tagline'] = meta_desc.get('content').strip()[:200]

        built_with_div = (soup.find('div', id='built-with') or
                          soup.find('div', class_='built-with') or
                          soup.find('div', attrs={'data-role': 'built-with'}) or
                          soup.select_one('.technologies'))
        if built_with_div:
            tech_tags = (built_with_div.find_all('span', class_='cp-tag') or
                         built_with_div.find_all('span', class_='tag') or
                         built_with_div.find_all('a', class_='cp-tag') or
                         built_with_div.find_all('a', class_='tag') or
                         built_with_div.find_all('li') or
                         built_with_div.find_all('span'))
            project_data['built_with'] = [tag.get_text(strip=True) for tag in tech_tags]

        # Thumbnail (prefer OpenGraph)
        thumb = ''
        og_img = soup.find('meta', property='og:image')
        if og_img and og_img.get('content'):
            thumb = og_img.get('content').strip()
        if not thumb:
            link_img = soup.find('link', rel='image_src')
            if link_img and link_img.get('href'):
                thumb = link_img.get('href').strip()
        if not thumb:
            img_tag = (soup.select_one('.gallery img') or
                       soup.select_one('.software-screenshot-image') or
                       soup.select_one('img'))
            if img_tag and img_tag.get('src'):
                thumb = img_tag.get('src').strip()
        project_data['thumbnail'] = thumb

        team_members: List[Dict[str, Any]] = []
        team_usernames: List[str] = []
        team_section = (soup.find('div', id='software-team') or
                        soup.find('ul', class_='software-team') or
                        soup.find('div', class_='software-team') or
                        soup.find('div', attrs={'data-role': 'software-team'}) or
                        soup.select_one('.team-members'))
        if team_section:
            members = (team_section.find_all('li', class_='software-team-member') or
                       team_section.find_all('a', class_='user-profile-link') or
                       team_section.find_all('a', href=lambda x: x and '/users/' in x) or
                       team_section.find_all('div', class_='team-member'))
            for member in members:
                # display name
                name_elem = (member.find('h4') or member.find('a', class_='user-profile-link') or
                             member.find('h3') or member.find('span', class_='name'))
                if name_elem:
                    team_members.append({'name': name_elem.get_text(strip=True)})
                # username from profile link
                link = member.find('a', class_='user-profile-link')
                if link and link.has_attr('href'):
                    href = link['href']
                    # typical href formats: /users/<username> or https://devpost.com/users/<username>
                    m = re.search(r"/users/([A-Za-z0-9_-]+)", href)
                    if m:
                        team_usernames.append(m.group(1))
                elif member.name == 'a' and member.get('href'):
                    href = member.get('href')
                    m = re.search(r"/users/([A-Za-z0-9_-]+)", href)
                    if m:
                        team_usernames.append(m.group(1))
        project_data['team_members'] = team_members
        project_data['team_usernames'] = team_usernames

        content_div = (soup.find('div', class_='app-details-left') or 
                       soup.find('div', class_='app-details') or
                       soup.find('div', id='app-details') or
                       soup.select_one('[data-role="app-details"]') or
                       soup.select_one('.software-details'))
        # Build description and base text source
        page_text = ''
        if content_div:
            # Fast path: avoid building giant strings; still one get_text() for awards/desc
            all_text = content_div.get_text()
            project_data['description'] = [{'heading': 'Description', 'content': all_text[:2000]}]
            page_text = all_text
        else:
            # Fallback: try main/article/body for a coarse description
            container = soup.find('main') or soup.find('article') or soup.find('body')
            if container:
                txt = container.get_text(separator=' ', strip=True)
                if txt:
                    project_data['description'] = [{'heading': 'Description', 'content': txt[:2000]}]
                    page_text = txt

        # Robust awards/winner extraction from multiple locations
        awards: List[str] = []
        # 1) Run strict patterns on primary text source (or whole page if needed)
        content_text = page_text if page_text else soup.get_text()
        for pattern in _AWARD_PATTERNS:
            matches = pattern.findall(content_text)
            for match in matches:
                clean_match = (match or '').strip()
                low = clean_match.lower()
                if (clean_match and 5 <= len(clean_match) <= 100 and
                    any(word in low for word in _AWARD_KEYWORDS) and
                    not any(noise in low for noise in _AWARD_NOISE)):
                    awards.append(clean_match)

        # 2) Submitted/side sections that often list awards
        submitted_section = soup.find('div', class_='software-list-content')
        if submitted_section:
            submitted_text = submitted_section.get_text(strip=True)
            if submitted_text and len(submitted_text) < 160:
                if any(k in submitted_text.lower() for k in ['winner', 'track', 'prize', 'award', 'best', 'finalist', 'honorable']):
                    awards.append(submitted_text)

        # 3) Headings/paragraphs that look like awards
        try:
            award_elements = soup.find_all(
                ['h2', 'h3', 'h4', 'p', 'li', 'span'],
                string=re.compile(r'(Winner|Track|Prize|Award|Best|First|Second|Third|Finalist|Honorable)', re.IGNORECASE)
            )
            for el in award_elements:
                text = el.get_text(strip=True)
                low = text.lower()
                if (text and 5 <= len(text) <= 120 and
                    any(word in low for word in _AWARD_KEYWORDS.union({'finalist', 'honorable'})) and
                    not any(noise in low for noise in _AWARD_NOISE)):
                    awards.append(text)
        except Exception:
            pass

        # Normalize awards and determine win flag
        awards_unique = []
        seen = set()
        for a in awards:
            aa = ' '.join(a.split())  # collapse whitespace
            if aa not in seen:
                seen.add(aa)
                awards_unique.append(aa)
        project_data['awards'] = awards_unique
        # Consider as winner if any awards detected or clear win tokens found
        page_low = (content_text or '').lower()
        project_data['won'] = bool(awards_unique) or any(t in page_low for t in ['winner', 'first place', 'grand prize'])

        # Accept project if at least a reasonable signal exists
        if project_data['title'] or project_data['tagline'] or (project_data['description'] and project_data['description'][0].get('content')):
            if debug:
                print(f"[reverse][debug] Accepted: {os.path.basename(file_path)} | title='{project_data['title'][:60]}' tagline='{project_data['tagline'][:60]}' desc_len={len(project_data['description'][0]['content']) if project_data['description'] else 0}")
            return project_data
        if debug:
            print(f"[reverse][debug] Rejected: {os.path.basename(file_path)} — no title/tagline/desc")
        return None
    except Exception:
        return None


def _parse_file_worker(file_path: str, debug: bool = False) -> Optional[Dict[str, Any]]:
    try:
        return parse_html_file(file_path, debug=debug)
    except Exception:
        return None


def regenerate_parsed_projects(
    devposts_dir: str,
    output_path: str,
    use_scraper: bool = False,
    ids_file: Optional[str] = None,
    workers: Optional[int] = None,
    debug_sample: int = 0
) -> List[Dict[str, Any]]:
    """Regenerate parsed_projects_full.json by parsing local HTML or scraping live pages.

    When use_scraper=True, derive project IDs from HTML filenames in devposts_dir (sans .html)
    or from ids_file if provided, and scrape with devpost_scraper.scrape_devpost.
    """
    projects: List[Dict[str, Any]] = []

    if use_scraper:
        ids: List[str] = []
        if ids_file and os.path.exists(ids_file):
            print(f"[reverse] Loading project IDs from {ids_file}...")
            with open(ids_file, 'r', encoding='utf-8') as f:
                ids = [line.strip() for line in f if line.strip()]
        else:
            print(f"[reverse] Scanning devposts directory for IDs: {devposts_dir}")
            if not os.path.isdir(devposts_dir):
                raise FileNotFoundError(f"Devposts directory not found: {devposts_dir}")
            html_files = [f for f in os.listdir(devposts_dir) if f.endswith('.html')]
            html_files.sort()
            ids = [os.path.splitext(f)[0] for f in html_files]

        print(f"[reverse] Scraping {len(ids)} projects via devpost_scraper...")
        for i, pid in enumerate(ids, start=1):
            if i % 25 == 0 or i == 1:
                print(f"[reverse] Scraping progress: {i}/{len(ids)}")
            try:
                raw = scrape_devpost(pid, debug=False)
            except Exception as e:
                print(f"[reverse] scrape_devpost failed for {pid}: {e}")
                continue

            # Normalize to match reverse.py schema
            proj: Dict[str, Any] = {
                'file_path': '',
                'project_id': raw.get('project_id', pid),
                'title': raw.get('title', ''),
                'tagline': raw.get('tagline', ''),
                'hackathon': raw.get('hackathon', ''),
                'built_with': raw.get('built_with', []),
                'team_members': [{'name': m.get('name', '')} for m in raw.get('team_members', [])],
                'team_usernames': [m.get('username', '') for m in raw.get('team_members', []) if m.get('username')],
                'awards': raw.get('awards', []),
                'won': bool(raw.get('awards')),
                'description': raw.get('description') if isinstance(raw.get('description'), list) else (
                    [{'heading': 'Description', 'content': raw.get('description', '')}] if raw.get('description') else []
                )
            }
            if proj['title']:
                projects.append(proj)

        print(f"[reverse] Scraped {len(projects)}/{len(ids)} projects successfully")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)
        print(f"[reverse] Saved parsed projects to: {output_path}")
        return projects
    else:
        print(f"[reverse] Scanning devposts directory: {devposts_dir}")
        if not os.path.isdir(devposts_dir):
            raise FileNotFoundError(f"Devposts directory not found: {devposts_dir}")

        # Fast directory scan
        html_paths: List[str] = []
        with os.scandir(devposts_dir) as it:
            for entry in it:
                if entry.is_file() and entry.name.endswith('.html'):
                    html_paths.append(entry.path)
        html_paths.sort()

        total = len(html_paths)
        if total == 0:
            print("[reverse] No HTML files found.")
        else:
            print(f"[reverse] Parsing {total} local HTML files with concurrency...")

        # Concurrent parse using threads (I/O bound)
        max_workers = workers or min(32, (mp.cpu_count() or 4) * 4)
        parsed_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_parse_file_worker, p, (debug_sample > 0 and i <= debug_sample)): p for i, p in enumerate(html_paths, start=1)}
            for i, fut in enumerate(as_completed(futures), start=1):
                data = fut.result()
                if data:
                    projects.append(data)
                if i % 200 == 0 or i == total:
                    print(f"[reverse] Progress: {i}/{total} files processed (valid {len(projects)})")

        print(f"[reverse] Parsed {len(projects)} valid projects (from {total} files)")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)
        print(f"[reverse] Saved parsed projects to: {output_path}")
        return projects


def recompute_vectors_from_projects(projects: List[Dict[str, Any]], output_path: str) -> np.ndarray:
    """Recompute project vectors using DevpostVectorizer and save to output_path."""
    if not VECTORIZER_AVAILABLE:
        raise RuntimeError('DevpostVectorizer is not available in this environment.')

    print("[reverse] Initializing DevpostVectorizer for recomputation...")
    vectorizer = DevpostVectorizer()

    project_vectors: List[np.ndarray] = []
    expected_dim: Optional[int] = None
    invalid_dim = 0
    for idx, proj in enumerate(projects, start=1):
        try:
            vectors = vectorizer.vectorize_project(proj)
            vec = vectors.get('combined')
            if not isinstance(vec, np.ndarray):
                invalid_dim += 1
                continue
            if vec.ndim != 1:
                invalid_dim += 1
                continue
            if expected_dim is None:
                expected_dim = vec.shape[0]
            if vec.shape[0] != expected_dim:
                invalid_dim += 1
                continue
            project_vectors.append(vec)
            if idx % 50 == 0:
                print(f"[reverse] Vectorized {idx}/{len(projects)} projects...")
        except Exception:
            # Skip failures to mirror robustness in prior scripts
            continue

    if not project_vectors:
        raise RuntimeError('No project vectors could be computed.')

    # Ensure homogenous shape
    try:
        arr = np.stack(project_vectors, axis=0)
    except Exception as e:
        print(f"[reverse] Failed to stack vectors due to shape mismatch: {e}")
        print(f"[reverse] expected_dim={expected_dim} valid_count={len(project_vectors)} invalid_dim_count={invalid_dim}")
        # Try filtering again strictly
        filtered = [v for v in project_vectors if isinstance(v, np.ndarray) and v.ndim == 1 and (expected_dim is None or v.shape[0] == expected_dim)]
        arr = np.stack(filtered, axis=0)
    np.save(output_path, arr)
    print(f"[reverse] Saved recomputed vectors to: {output_path} with shape {arr.shape}")
    return arr


def approximate_vectors_from_similarity(similarity_path: str, output_path: str, max_dim: int = 256) -> np.ndarray:
    """Create an approximate embedding whose cosine similarity matches given matrix.

    We use symmetric eigendecomposition S = Q Λ Q^T (assuming S ~ PSD),
    then X = Q_k sqrt(Λ_k). Row-normalize to unit length so that dot(X_i, X_j)
    approximates cosine similarity. Save X to output_path.
    """
    print(f"[reverse] Approximating vectors from similarity: {similarity_path}")
    if not os.path.exists(similarity_path):
        raise FileNotFoundError(f"similarity matrix not found: {similarity_path}")

    S = np.load(similarity_path)
    if S.ndim != 2 or S.shape[0] != S.shape[1]:
        raise ValueError('similarity_matrix.npy must be a square matrix')

    # Ensure symmetry
    S = (S + S.T) / 2.0

    # Eigendecompose; use eigh for symmetric matrices
    eigvals, eigvecs = np.linalg.eigh(S)

    # Take top-k components
    idx = np.argsort(eigvals)[::-1]
    k = min(max_dim, S.shape[0])
    sel = idx[:k]
    Lambda_k = np.clip(eigvals[sel], a_min=0.0, a_max=None)
    Q_k = eigvecs[:, sel]

    # Construct embedding
    X = Q_k @ np.diag(np.sqrt(Lambda_k + 1e-12))

    # Row-normalize to target cosine behavior
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    X = X / norms

    np.save(output_path, X)
    print(f"[reverse] Saved approximate vectors to: {output_path} with shape {X.shape}")
    return X


def main() -> int:
    parser = argparse.ArgumentParser(description='Reverse engineer project vectors and parsed data')
    parser.add_argument('--devposts-dir', default='./devposts', help='Directory containing Devpost HTML files')
    parser.add_argument('--parsed-output', default='parsed_projects_full.json', help='Output path for parsed JSON')
    parser.add_argument('--vectors-output', default='project_vectors.npy', help='Output path for recomputed vectors')
    parser.add_argument('--approx-output', default='project_vectors_approx.npy', help='Output path for approximate vectors from similarity')
    parser.add_argument('--similarity-path', default='similarity_matrix.npy', help='Path to similarity matrix')
    parser.add_argument('--regen-parsed', action='store_true', help='Regenerate parsed_projects_full.json')
    parser.add_argument('--recompute-vectors', action='store_true', help='Recompute project vectors using DevpostVectorizer')
    parser.add_argument('--from-similarity', action='store_true', help='Approximate vectors from similarity_matrix.npy')
    parser.add_argument('--use-scraper', action='store_true', help='Use devpost_scraper.scrape_devpost to rebuild parsed data')
    parser.add_argument('--ids-file', default=None, help='Optional file with one devpost ID per line when using scraper')
    parser.add_argument('--workers', type=int, default=None, help='Max workers for local HTML parsing')
    parser.add_argument('--debug-sample', type=int, default=0, help='Enable debug logs for first N files')
    parser.add_argument('--force', action='store_true', help='Overwrite existing outputs')
    parser.add_argument('--max-dim', type=int, default=256, help='Max embedding dimension when approximating from similarity')
    args = parser.parse_args()

    # Step 1: Regenerate parsed data if requested or missing
    projects: Optional[List[Dict[str, Any]]] = None
    if args.regen_parsed or args.force or not os.path.exists(args.parsed_output):
        projects = regenerate_parsed_projects(
            args.devposts_dir,
            args.parsed_output,
            use_scraper=args.use_scraper,
            ids_file=args.ids_file,
            workers=args.workers,
            debug_sample=args.debug_sample
        )
        print(f"[reverse] Saved parsed data: {args.parsed_output} ({len(projects)} projects)")
    else:
        try:
            with open(args.parsed_output, 'r', encoding='utf-8') as f:
                projects = json.load(f)
        except Exception:
            projects = None

    # Step 2: Preferred - recompute vectors via vectorizer
    if args.recompute_vectors:
        if not projects:
            raise RuntimeError('Parsed projects not available to recompute vectors.')
        arr = recompute_vectors_from_projects(projects, args.vectors_output)
        print(f"[reverse] Saved recomputed vectors: {args.vectors_output} with shape {arr.shape}")

    # Step 3: Fallback - approximate from similarity matrix
    if args.from_similarity:
        X = approximate_vectors_from_similarity(args.similarity_path, args.approx_output, max_dim=args.max_dim)
        print(f"[reverse] Saved approximate vectors from similarity: {args.approx_output} with shape {X.shape}")

    if not (args.recompute_vectors or args.from_similarity or args.regen_parsed):
        print('[reverse] Nothing to do. Use --regen-parsed, --recompute-vectors, or --from-similarity.')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())


