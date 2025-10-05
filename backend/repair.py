import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# for webscraping
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup
import re
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from functools import partial
import time

# vectorization
from vectorizer import DevpostVectorizer

# similarity
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# Configuration
MAX_SCRAPING_WORKERS = 8  # Number of concurrent browser instances
PROGRESS_REPORT_INTERVAL = 50  # Report progress every N completed tasks

def get_all_devposts():
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    driver = GraphDatabase.driver(uri, auth=(username, password) )
    with driver.session() as session:
        output = list(session.run("MATCH (n:Devpost) RETURN n"))
         
    devposts = [dict(record['n'])['name'] for record in output]
    
    return devposts

def create_browser():
    """Create a new browser instance for thread-safe scraping"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def scrape_devpost_with_browser(devpost_id):
    """Scrape a single devpost with its own browser instance"""
    browser = None
    try:
        browser = create_browser()
        return scrape_devpost(browser, devpost_id)
    except Exception as e:
        print(f"Scraping failed for {devpost_id}: {e}")
        return None
    finally:
        if browser:
            browser.quit()

def vectorize_project_wrapper(args):
    """Wrapper function for multiprocessing vectorization"""
    project_data, index = args
    try:
        vectorizer = DevpostVectorizer()
        return index, vectorizer.vectorize_project(project_data)['combined']
    except Exception as e:
        print(f"Vectorization failed for project {index}: {e}")
        return index, None

def scrape_devpost(browser, devpost_id):
    """Parse HTML file for project data"""
    try:
        url = f'https://devpost.com/software/{devpost_id}'
        
        print(f"Scraping: {url}")
        
        browser.get(url)
        html_content = browser.page_source
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        project_data = {
            'project_id': devpost_id,
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
        return None

def main():
    # Load environment variables first
    load_dotenv()
    
    start_time = time.time()
    print('Getting devposts from database...')
    devposts = get_all_devposts()
    total_count = len(devposts)
    print(f'Found {total_count} devposts to process')

    # Scrape with concurrent threads
    print('Starting concurrent scraping...')
    scraped_devposts = [None] * total_count
    completed_count = 0
    
    # Use ThreadPoolExecutor for I/O bound scraping
    max_workers = min(MAX_SCRAPING_WORKERS, total_count)  # Limit concurrent browsers
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all scraping tasks
        future_to_index = {
            executor.submit(scrape_devpost_with_browser, devpost): i 
            for i, devpost in enumerate(devposts)
        }
        
        # Process completed tasks
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                scraped_devposts[index] = result
                completed_count += 1
                if completed_count % PROGRESS_REPORT_INTERVAL == 0:
                    print(f'Scraped {completed_count}/{total_count} projects ({completed_count/total_count*100:.1f}%)')
            except Exception as e:
                print(f'Scraping failed for project {index}: {e}')
                completed_count += 1

    # Filter out None results
    valid_scraped = [p for p in scraped_devposts if p is not None]
    scraping_time = time.time() - start_time
    print(f'Successfully scraped {len(valid_scraped)}/{total_count} projects in {scraping_time:.1f} seconds')

    if not valid_scraped:
        print('No projects were successfully scraped!')
        return {}

    # Vectorize with multiprocessing
    vectorization_start = time.time()
    print('Starting concurrent vectorization...')
    vectors = {}
    completed_vectorization = 0
    
    # Prepare data for multiprocessing
    vectorization_data = [(project, i) for i, project in enumerate(valid_scraped)]
    
    # Use ProcessPoolExecutor for CPU-bound vectorization
    num_processes = min(mp.cpu_count(), len(valid_scraped))
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # Submit all vectorization tasks
        future_to_index = {
            executor.submit(vectorize_project_wrapper, data): data[1] 
            for data in vectorization_data
        }
        
        # Process completed tasks
        for future in as_completed(future_to_index):
            try:
                index, result = future.result()
                if result is not None:
                    vectors[index] = result
                completed_vectorization += 1
                if completed_vectorization % PROGRESS_REPORT_INTERVAL == 0:
                    print(f'Vectorized {completed_vectorization}/{len(valid_scraped)} projects ({completed_vectorization/len(valid_scraped)*100:.1f}%)')
            except Exception as e:
                print(f'Vectorization failed: {e}')
                completed_vectorization += 1

    vectorization_time = time.time() - vectorization_start
    print(f'Successfully vectorized {len(vectors)} projects in {vectorization_time:.1f} seconds')

    if not vectors:
        print('No projects were successfully vectorized!')
        return {}

    # Generate similarity matrix
    similarity_start = time.time()
    print('Generating similarity matrix...')
    scaler = StandardScaler()
    vectors_array = np.array(list(vectors.values()))
    vectors_normalized = scaler.fit_transform(vectors_array)
    similarity_matrix = cosine_similarity(vectors_normalized)
    np.save('similarity_matrix.npy', similarity_matrix)
    similarity_time = time.time() - similarity_start
    print(f'Similarity matrix saved with shape {similarity_matrix.shape} in {similarity_time:.1f} seconds')

    total_time = time.time() - start_time
    print(f'\n=== PERFORMANCE SUMMARY ===')
    print(f'Total processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)')
    print(f'Scraping: {scraping_time:.1f}s ({scraping_time/total_time*100:.1f}%)')
    print(f'Vectorization: {vectorization_time:.1f}s ({vectorization_time/total_time*100:.1f}%)')
    print(f'Similarity matrix: {similarity_time:.1f}s ({similarity_time/total_time*100:.1f}%)')
    print(f'Projects processed: {len(vectors)}/{total_count} ({len(vectors)/total_count*100:.1f}% success rate)')
    print(f'Average time per project: {total_time/len(vectors):.2f} seconds')

    return vectors
        

if __name__ == '__main__':
    main()
