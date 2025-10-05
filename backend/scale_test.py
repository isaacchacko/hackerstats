"""
Scale Test Vectorizer - Process ALL 1.5k HTML files
"""

import os
import json
import re
from bs4 import BeautifulSoup
from vectorizer import DevpostVectorizer
import numpy as np
from typing import Dict, List, Any
import time
from datetime import datetime


def parse_html_file(file_path: str) -> Dict[str, Any]:
    """Parse HTML file for project data"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        project_data = {
            'file_path': file_path,
            'project_id': os.path.basename(file_path).replace('.html', ''),
            'title': '',
            'tagline': '',
            'hackathon': '',
            'built_with': [],
            'team_members': [],
            'awards': [],
            'description': []
        }
        
        # Extract title - try multiple selectors
        title_elem = soup.find('h1', id='app-title') or soup.find('h1', id='software-name') or soup.find('h1')
        if title_elem:
            project_data['title'] = title_elem.get_text(strip=True)
        
        # Extract tagline - try multiple selectors
        tagline_elem = (soup.find('p', class_='large') or 
                       soup.find('p', id='software-tagline') or 
                       soup.find('p', class_='tagline'))
        if tagline_elem:
            project_data['tagline'] = tagline_elem.get_text(strip=True)
        
        # Extract built with technologies
        built_with_div = soup.find('div', id='built-with')
        if built_with_div:
            tech_tags = built_with_div.find_all('span', class_='cp-tag')
            project_data['built_with'] = [tag.get_text(strip=True) for tag in tech_tags]
        
        # Extract team members
        team_members = []
        team_section = soup.find('div', id='software-team') or soup.find('ul', class_='software-team')
        if team_section:
            members = team_section.find_all('li', class_='software-team-member')
            for member in members:
                name_elem = member.find('h4') or member.find('a', class_='user-profile-link')
                if name_elem:
                    team_members.append({'name': name_elem.get_text(strip=True)})
        
        project_data['team_members'] = team_members
        
        # Extract description sections
        content_div = (soup.find('div', class_='app-details-left') or 
                      soup.find('div', class_='app-details') or
                      soup.find('div', id='app-details'))
        
        if content_div:
            all_text = content_div.get_text()
            project_data['description'] = [{'heading': 'Description', 'content': all_text[:2000]}]  # Increased limit
        
        # Extract awards
        awards = []
        if content_div:
            content_text = content_div.get_text()
            award_patterns = [
                r'Winner.*?Track.*?([^.\n]{5,100})',
                r'Best.*?([^.\n]{5,100})',
                r'First Place.*?([^.\n]{5,100})',
                r'Second Place.*?([^.\n]{5,100})',
                r'Third Place.*?([^.\n]{5,100})',
                r'Sponsored by.*?([^.\n]{5,100})',
                r'Winner.*?([^.\n]{5,100})',
                r'Award.*?([^.\n]{5,100})',
                r'Prize.*?([^.\n]{5,100})',
                r'Champion.*?([^.\n]{5,100})',
                r'Grand Prize.*?([^.\n]{5,100})',
            ]
            
            for pattern in award_patterns:
                matches = re.findall(pattern, content_text, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    clean_match = match.strip()
                    if (clean_match and 
                        len(clean_match) >= 5 and 
                        len(clean_match) <= 100 and
                        any(word in clean_match.lower() for word in [
                            'hack', 'track', 'prize', 'award', 'winner', 'best', 'first', 'second', 'third',
                            'sponsored', 'champion', 'grand', 'overall', 'category', 'theme'
                        ]) and
                        not any(noise in clean_match.lower() for noise in [
                            'javascript', 'function', 'var ', 'css', 'html', 'script',
                            'font-awesome', 'fa-', 'class=', 'href=', 'src=',
                            'undefined', 'null', 'true', 'false', 'console.log',
                            'document.', 'window.', 'jquery', 'bootstrap',
                            'implemented', 'firmware', 'backend', 'database', 'supabase',
                            'modern care', 'bottle', 'iot', 'medication', 'tracker',
                            'practices', 'planning', 'online', 'in-person'
                        ])):
                        awards.append(clean_match)
        
        project_data['awards'] = list(set(awards))
        
        # Only return if we have at least a title
        if project_data['title']:
            return project_data
        else:
            return None
        
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None


def main():
    print("Scale Test Vectorizer - Processing ALL 1.5k HTML files")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get all HTML files
    devposts_dir = './devposts'
    if not os.path.exists(devposts_dir):
        print(f"Directory {devposts_dir} not found!")
        return
    
    html_files = [f for f in os.listdir(devposts_dir) if f.endswith('.html')]
    print(f"Found {len(html_files)} HTML files")
    
    # Parse all files
    print("\nPhase 1: Parsing HTML files...")
    start_time = time.time()
    
    projects = []
    failed_count = 0
    
    for i, html_file in enumerate(html_files):
        if i % 100 == 0:  # Progress every 100 files
            elapsed = time.time() - start_time
            print(f"Parsed {i}/{len(html_files)} files ({i/len(html_files)*100:.1f}%) - {elapsed:.1f}s elapsed")
        
        file_path = os.path.join(devposts_dir, html_file)
        project_data = parse_html_file(file_path)
        
        if project_data:
            projects.append(project_data)
        else:
            failed_count += 1
    
    parse_time = time.time() - start_time
    print(f"\n✓ Parsing complete!")
    print(f"  Successfully parsed: {len(projects)} projects")
    print(f"  Failed to parse: {failed_count} projects")
    print(f"  Parse time: {parse_time:.1f} seconds")
    print(f"  Average: {parse_time/len(html_files):.3f} seconds per file")
    
    if len(projects) < 2:
        print("Need at least 2 projects for similarity analysis")
        return
    
    # Save parsed data
    print(f"\nSaving parsed data to parsed_projects_full.json...")
    with open('parsed_projects_full.json', 'w', encoding='utf-8') as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)
    print("✓ Data saved!")
    
    # Initialize vectorizer
    print(f"\nPhase 2: Initializing vectorizer...")
    vectorizer = DevpostVectorizer()
    print("✓ Vectorizer initialized!")
    
    # Vectorize all projects
    print(f"\nPhase 3: Vectorizing {len(projects)} projects...")
    vectorize_start = time.time()
    
    project_vectors = {}
    vectorize_failed = 0
    
    for i, project in enumerate(projects):
        if i % 50 == 0:  # Progress every 50 projects
            elapsed = time.time() - vectorize_start
            print(f"Vectorized {i}/{len(projects)} projects ({i/len(projects)*100:.1f}%) - {elapsed:.1f}s elapsed")
        
        try:
            vectors = vectorizer.vectorize_project(project)
            project_vectors[i] = vectors['combined']
        except Exception as e:
            print(f"Vectorization failed for project {i}: {e}")
            vectorize_failed += 1
    
    vectorize_time = time.time() - vectorize_start
    print(f"\n✓ Vectorization complete!")
    print(f"  Successfully vectorized: {len(project_vectors)} projects")
    print(f"  Vectorization failed: {vectorize_failed} projects")
    print(f"  Vectorize time: {vectorize_time:.1f} seconds")
    print(f"  Average: {vectorize_time/len(projects):.3f} seconds per project")
    
    # Save vectors
    print(f"\nSaving vectors to project_vectors.npy...")
    vectors_array = np.array(list(project_vectors.values()))
    np.save('project_vectors.npy', vectors_array)
    print("✓ Vectors saved!")
    
    # Compute similarity matrix
    print(f"\nPhase 4: Computing similarity matrix...")
    similarity_start = time.time()
    
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity
    
    scaler = StandardScaler()
    vectors_normalized = scaler.fit_transform(vectors_array)
    similarity_matrix = cosine_similarity(vectors_normalized)
    
    similarity_time = time.time() - similarity_start
    print(f"✓ Similarity matrix computed!")
    print(f"  Matrix size: {similarity_matrix.shape}")
    print(f"  Compute time: {similarity_time:.1f} seconds")
    
    # Save similarity matrix
    print(f"\nSaving similarity matrix to similarity_matrix.npy...")
    np.save('similarity_matrix.npy', similarity_matrix)
    print("✓ Similarity matrix saved!")
    
    # Find most similar pairs
    print(f"\nPhase 5: Finding most similar project pairs...")
    n = len(projects)
    pairs = []
    
    for i in range(n):
        for j in range(i + 1, n):
            similarity = similarity_matrix[i][j]
            pairs.append((i, j, similarity))
    
    pairs.sort(key=lambda x: x[2], reverse=True)
    top_pairs = pairs[:10]
    
    print(f"\nTop 10 most similar project pairs:")
    print("-" * 80)
    for i, (idx1, idx2, similarity) in enumerate(top_pairs):
        project1 = projects[idx1]
        project2 = projects[idx2]
        print(f"\n{i+1}. Similarity: {similarity:.3f}")
        print(f"   Project 1: {project1['title']}")
        print(f"   Project 2: {project2['title']}")
        print(f"   Tech 1: {', '.join(project1['built_with'][:3])}")
        print(f"   Tech 2: {', '.join(project2['built_with'][:3])}")
    
    # Interactive search
    print(f"\n" + "="*80)
    print("INTERACTIVE SIMILARITY SEARCH")
    print("="*80)
    print("Enter a project idea to find similar projects.")
    print("Type 'quit' to exit, 'stats' for statistics.")
    print("="*80)
    
    while True:
        try:
            query = input("\nEnter your project idea: ").strip()
            
            if query.lower() == 'quit':
                print("Goodbye!")
                break
            elif query.lower() == 'stats':
                print(f"\nScale Test Statistics:")
                print(f"  Total HTML files: {len(html_files)}")
                print(f"  Successfully parsed: {len(projects)}")
                print(f"  Parse success rate: {len(projects)/len(html_files)*100:.1f}%")
                print(f"  Vector dimensions: {vectors_array.shape[1]}")
                print(f"  Parse time: {parse_time:.1f}s")
                print(f"  Vectorize time: {vectorize_time:.1f}s")
                print(f"  Similarity time: {similarity_time:.1f}s")
                print(f"  Total time: {time.time() - start_time:.1f}s")
            
            elif query:
                print(f"\nSearching for projects similar to: '{query}'")
                
                # Create mock project from query
                mock_project = {
                    'title': query,
                    'tagline': '',
                    'built_with': [],
                    'team_members': [],
                    'awards': [],
                    'description': [{'heading': 'Query', 'content': query}]
                }
                
                # Vectorize query
                query_vectors = vectorizer.vectorize_project(mock_project)
                query_vector = query_vectors['combined']
                
                # Find similarities
                similarities = []
                for i, project_vector in project_vectors.items():
                    similarity = np.dot(query_vector, project_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(project_vector)
                    )
                    similarities.append((projects[i], similarity))
                
                # Sort and show top 10
                similarities.sort(key=lambda x: x[1], reverse=True)
                top_10 = similarities[:10]
                
                print(f"\nTop 10 similar projects:")
                print("-" * 80)
                
                for i, (project, similarity) in enumerate(top_10):
                    print(f"\n{i+1}. Similarity: {similarity:.3f}")
                    print(f"   Title: {project['title']}")
                    print(f"   Tagline: {project['tagline'][:100]}...")
                    print(f"   Tech: {', '.join(project['built_with'][:5])}")
                    print(f"   Team Size: {len(project['team_members'])}")
                    if project['awards']:
                        print(f"   Awards: {', '.join(project['awards'][:2])}")
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    total_time = time.time() - start_time
    print(f"\n" + "="*60)
    print(f"SCALE TEST COMPLETE!")
    print(f"Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"Processed {len(projects)} projects successfully")
    print("="*60)


if __name__ == "__main__":
    main()
