import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# for webscraping
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup
import re
import threading

# vectorization
from vectorizer import DevpostVectorizer

# similarity
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

def get_all_devposts():
    load_dotenv()

    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    driver = GraphDatabase.driver(uri, auth=(username, password) )
    with driver.session() as session:
        output = list(session.run("MATCH (n:Devpost) RETURN n"))
         
    devposts = [dict(record['n'])['name'] for record in output]
    
    return devposts

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

    print('devposts = get_all_devposts()')
    devposts = get_all_devposts()

    # scrape
    print('scrape')
    options = Options()
    options.add_argument("--headless")
    browser = webdriver.Chrome(options=options)
    scraped_devposts = []
    scrapers = []
    def execute(index, devpost):
        scraped_devposts.append(scrape_devpost(browser, devpost))
        print(f'completed {index}')

    total_count = len(devposts)
    for index, devpost in enumerate(devposts):
        try:
            if index % 4 == 0 and index != 0:
                for t in scrapers:
                    t.join()
                scrapers = []

            t = threading.Thread(target=execute, args=(f'{index}/{total_count}', devpost))
            scrapers.append(t)
            t.start()
        except Exception as e:
            print(f"Scraping failed for project: {e}")

    for t in scrapers:
        t.join()

    browser.quit()

    # vectorize
    print('vectorize')
    vectorizer = DevpostVectorizer()
    vectors = {}
    for index, devpost in enumerate(scraped_devposts):
        try:
            vectors[index] = vectorizer.vectorize_project(devpost)['combined']
        except Exception as e:
            print(f"Vectorization failed for project: {e}")
    
    # similarity
    print('generate matrix')
    scaler = StandardScaler()
    vectors_array = np.array(list(vectors.values()))
    vectors_normalized = scaler.fit_transform(vectors_array)
    similarity_matrix = cosine_similarity(vectors_normalized)
    np.save('similarity_matrix.npy', similarity_matrix)

    return vectors
        

if __name__ == '__main__':
    main()
