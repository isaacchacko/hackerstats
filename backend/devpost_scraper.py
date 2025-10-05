"""
Simple Devpost Project Scraper
Scrapes text sections from any Devpost project page given its ID.

Usage:
    python devpost_scraper.py plate-o
    python devpost_scraper.py <devpost-id>
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import sys
import json
import re


def setup_driver():
    """Setup headless Chrome driver"""
    options = Options()
    options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def scrape_devpost(devpost_id, debug=False):
    """
    Scrape a Devpost project page for its text sections.
    
    Args:
        devpost_id (str): The Devpost project ID (e.g., 'plate-o')
        debug (bool): Print debug information about what's being found
    
    Returns:
        dict: Dictionary containing all scraped text sections
    """
    url = f'https://devpost.com/software/{devpost_id}'
    
    print(f"Scraping: {url}")
    
    try:
        driver = setup_driver()
        driver.get(url)
        
        # Wait a bit for dynamic content to load
        import time
        time.sleep(2)
        
        html_content = driver.page_source
        driver.quit()
        
        if debug:
            print(f"DEBUG - HTML content length: {len(html_content)}")
            # Save HTML for debugging
            with open(f"{devpost_id}_debug.html", 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"DEBUG - HTML saved to {devpost_id}_debug.html")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        if debug:
            print(f"DEBUG - Page title: {soup.title.get_text() if soup.title else 'No title found'}")
            
    except Exception as e:
        print(f"Error during scraping: {e}")
        return {
            'project_id': devpost_id,
            'url': url,
            'title': '',
            'tagline': '',
            'description': '',
            'built_with': [],
            'team_members': [],
            'hackathon': '',
            'awards': [],
            'error': str(e)
        }
    
    result = {
        'project_id': devpost_id,
        'url': url,
        'title': '',
        'tagline': '',
        'description': '',
        'built_with': [],
        'team_members': [],
        'hackathon': '',
        'awards': []
    }
    
    # Extract project title - try multiple selectors
    title_elem = soup.find('h1', id='software-name') or soup.find('h1', class_='software-name') or soup.find('h1', {'data-role': 'software-name'})
    if not title_elem:
        # Try alternative selectors
        title_elem = soup.find('h1') or soup.find('h2', class_='software-name') or soup.select_one('h1[data-role="software-name"]')
    
    if title_elem:
        result['title'] = title_elem.get_text(strip=True)
    
    # Extract tagline - try multiple selectors
    tagline_elem = soup.find('p', id='software-tagline') or soup.find('p', class_='software-tagline') or soup.find('div', class_='software-tagline')
    if not tagline_elem:
        # Try alternative selectors
        tagline_elem = soup.find('p', {'data-role': 'software-tagline'}) or soup.select_one('.tagline') or soup.select_one('[data-role="software-tagline"]')
    
    if tagline_elem:
        result['tagline'] = tagline_elem.get_text(strip=True)
    
    # Extract main description/story content - try multiple selectors
    story_div = soup.find('div', id='app-details-left') or soup.find('div', class_='app-details-left')
    if not story_div:
        # Try alternative selectors for main content
        story_div = soup.find('div', class_='app-details') or soup.find('div', {'data-role': 'app-details'}) or soup.select_one('.software-details') or soup.select_one('[data-role="app-details"]')
    
    if story_div:
        # Get all text content from the story section
        sections = []
        
        # Find all h2 headers and their following content
        for h2 in story_div.find_all('h2'):
            section_title = h2.get_text(strip=True)
            section_content = []
            
            # Get all siblings until the next h2
            for sibling in h2.find_next_siblings():
                if sibling.name == 'h2':
                    break
                if sibling.name in ['p', 'ul', 'ol', 'blockquote']:
                    section_content.append(sibling.get_text(strip=True))
            
            sections.append({
                'heading': section_title,
                'content': '\n\n'.join(section_content)
            })
        
        result['description'] = sections
    
    # Extract "Built With" technologies - try multiple selectors
    built_with_div = soup.find('div', id='built-with') or soup.find('div', class_='built-with')
    if not built_with_div:
        # Try alternative selectors
        built_with_div = soup.find('div', {'data-role': 'built-with'}) or soup.select_one('.technologies') or soup.select_one('[data-role="built-with"]')
    
    if built_with_div:
        # Try multiple tag selectors
        tech_tags = (built_with_div.find_all('span', class_='cp-tag') or 
                    built_with_div.find_all('span', class_='tag') or
                    built_with_div.find_all('a', class_='cp-tag') or
                    built_with_div.find_all('a', class_='tag') or
                    built_with_div.find_all('li') or
                    built_with_div.find_all('span'))
        
        technologies = []
        for tag in tech_tags:
            text = tag.get_text(strip=True)
            if text and len(text) > 0 and len(text) < 50:  # Reasonable tech name length
                technologies.append(text)
        
        result['built_with'] = list(set(technologies))  # Remove duplicates
    
    # Extract team members - try multiple selectors
    team_section = soup.find('div', id='software-team') or soup.find('div', class_='software-team')
    if not team_section:
        # Try alternative selectors
        team_section = soup.find('div', {'data-role': 'software-team'}) or soup.select_one('.team-members') or soup.select_one('[data-role="software-team"]')
    
    if team_section:
        # Try multiple member selectors
        members = (team_section.find_all('a', class_='user-profile-link') or
                  team_section.find_all('a', class_='profile-link') or
                  team_section.find_all('div', class_='team-member') or
                  team_section.find_all('div', class_='member') or
                  team_section.find_all('a', href=lambda x: x and '/users/' in x))
        
        for member in members:
            # Try multiple name selectors
            name_elem = (member.find('h4') or member.find('h3') or member.find('h2') or 
                        member.find('span', class_='name') or member.find('div', class_='name'))
            
            if name_elem:
                name = name_elem.get_text(strip=True)
                if name:
                    # Extract username from href or use name as fallback
                    href = member.get('href', '')
                    username = href.split('/')[-1] if href and '/' in href else name.lower().replace(' ', '-')
                    result['team_members'].append({
                        'name': name,
                        'username': username
                    })
    
    # Extract hackathon info - try multiple selectors
    hackathon_elem = soup.find('a', href=lambda x: x and '.devpost.com' in x)
    if not hackathon_elem:
        # Try alternative selectors
        hackathon_elem = (soup.find('div', class_='hackathon') or 
                         soup.find('div', class_='event') or
                         soup.find('span', class_='hackathon') or
                         soup.find('a', href=lambda x: x and '/hackathons/' in x) or
                         soup.select_one('.hackathon-name') or
                         soup.select_one('[data-role="hackathon"]'))
    
    if hackathon_elem:
        hackathon_text = hackathon_elem.get_text(strip=True)
        if hackathon_text:
            result['hackathon'] = hackathon_text
    
    # Extract awards/prizes - be extremely specific to only get actual awards
    awards = []
    
    # Method 1: Look for very specific award patterns that are clearly awards
    content_div = soup.find('div', class_='app-details-left')
    if content_div:
        content_text = content_div.get_text()
        
        # Very specific patterns that are clearly awards
        award_patterns = [
            r'Winner.*?Track.*?([^.\n]{5,100})',  # Winner Track: [award name]
            r'Best.*?([^.\n]{5,100})',  # Best [something]
            r'First Place.*?([^.\n]{5,100})',  # First Place [something]
            r'Second Place.*?([^.\n]{5,100})',  # Second Place [something]
            r'Third Place.*?([^.\n]{5,100})',  # Third Place [something]
            r'Sponsored by.*?([^.\n]{5,100})',  # Sponsored by [something]
            r'Winner.*?([^.\n]{5,100})',  # Winner [something]
            r'Award.*?([^.\n]{5,100})',  # Award [something]
            r'Prize.*?([^.\n]{5,100})',  # Prize [something]
            r'Champion.*?([^.\n]{5,100})',  # Champion [something]
            r'Grand Prize.*?([^.\n]{5,100})',  # Grand Prize [something]
        ]
        
        for pattern in award_patterns:
            matches = re.findall(pattern, content_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                clean_match = match.strip()
                # Very strict filtering - must look like an award
                if (clean_match and 
                    len(clean_match) >= 5 and 
                    len(clean_match) <= 100 and
                    # Must contain award-like words
                    any(word in clean_match.lower() for word in [
                        'hack', 'track', 'prize', 'award', 'winner', 'best', 'first', 'second', 'third',
                        'sponsored', 'champion', 'grand', 'overall', 'category', 'theme'
                    ]) and
                    # Must NOT contain non-award content
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
    
    # Method 2: Look for "Submitted to" section which often contains awards
    submitted_section = soup.find('div', class_='software-list-content')
    if submitted_section:
        hackathon_text = submitted_section.get_text(strip=True)
        if hackathon_text and len(hackathon_text) < 100:
            # Check if it mentions winning or awards
            if any(word in hackathon_text.lower() for word in ['winner', 'track', 'prize', 'award', 'best']):
                awards.append(hackathon_text)
    
    # Method 3: Look for specific award-related elements with very strict filtering
    award_elements = soup.find_all(['h2', 'h3', 'h4', 'p'], text=re.compile(r'(Winner|Track|Prize|Award|Best|First|Second|Third)', re.IGNORECASE))
    for element in award_elements:
        text = element.get_text(strip=True)
        if (text and 
            len(text) >= 5 and 
            len(text) <= 100 and
            # Must contain award-like words
            any(word in text.lower() for word in [
                'hack', 'track', 'prize', 'award', 'winner', 'best', 'first', 'second', 'third',
                'sponsored', 'champion', 'grand', 'overall', 'category', 'theme'
            ]) and
            # Must NOT contain non-award content
            not any(noise in text.lower() for noise in [
                'javascript', 'css', 'function', 'var ', 'implemented', 'firmware', 'backend',
                'modern care', 'bottle', 'iot', 'medication', 'tracker', 'practices', 'planning'
            ])):
            awards.append(text)
    
    # Final cleanup - very strict filtering
    cleaned_awards = []
    for award in awards:
        # Must be clearly an award, not project description or technical content
        if (award and 
            len(award) >= 5 and 
            len(award) <= 100 and
            not award.startswith(('{', '[', '(', '<')) and  # Not JSON/HTML
            # Must contain award keywords
            any(word in award.lower() for word in [
                'hack', 'track', 'prize', 'award', 'winner', 'best', 'first', 'second', 'third',
                'sponsored', 'champion', 'grand', 'overall', 'category', 'theme'
            ]) and
            # Must NOT contain project/technical content
            not any(noise in award.lower() for noise in [
                'javascript', 'function', 'var ', 'css', 'html', 'script',
                'font-awesome', 'fa-', 'class=', 'href=', 'src=',
                'undefined', 'null', 'true', 'false', 'console.log',
                'document.', 'window.', 'jquery', 'bootstrap',
                'implemented', 'firmware', 'backend', 'database', 'supabase',
                'modern care', 'bottle', 'iot', 'medication', 'tracker',
                'practices', 'planning', 'online', 'in-person', 'webinar',
                'dashboard', 'statistics', 'calculations', 'receiver'
            ])):
            cleaned_awards.append(award)
    
    result['awards'] = list(set(cleaned_awards))
    
    # Fallback: If we still haven't found basic info, try generic selectors
    if not result['title']:
        # Try to find any h1 or h2 that might be the title
        title_candidates = soup.find_all(['h1', 'h2'])
        for candidate in title_candidates:
            text = candidate.get_text(strip=True)
            if text and len(text) > 3 and len(text) < 200:
                result['title'] = text
                break
    
    if not result['tagline']:
        # Try to find any p or div that might be the tagline
        tagline_candidates = soup.find_all(['p', 'div'], class_=lambda x: x and any(word in x.lower() for word in ['tagline', 'subtitle', 'description']))
        for candidate in tagline_candidates:
            text = candidate.get_text(strip=True)
            if text and len(text) > 10 and len(text) < 300:
                result['tagline'] = text
                break
    
    if not result['description'] and not result['title']:
        # Last resort: try to extract any meaningful text content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and 'content' in x.lower())
        if main_content:
            # Extract all paragraphs
            paragraphs = main_content.find_all('p')
            if paragraphs:
                sections = []
                for i, p in enumerate(paragraphs[:5]):  # Limit to first 5 paragraphs
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        sections.append({
                            'heading': f'Section {i+1}',
                            'content': text
                        })
                if sections:
                    result['description'] = sections
    
    if debug:
        print(f"\nDEBUG - Awards found: {len(result['awards'])}")
        for i, award in enumerate(result['awards']):
            print(f"  {i+1}. {award}")
        print(f"\nDEBUG - Title: '{result['title']}'")
        print(f"DEBUG - Tagline: '{result['tagline']}'")
        print(f"DEBUG - Description sections: {len(result['description']) if result['description'] else 0}")
        print(f"DEBUG - Built with: {len(result['built_with'])}")
        print(f"DEBUG - Team members: {len(result['team_members'])}")
        print(f"DEBUG - Hackathon: '{result['hackathon']}'")
    
    return result


def print_result(data):
    """Pretty print the scraped data"""
    print("\n" + "="*80)
    print(f"PROJECT: {data['title']}")
    print("="*80)
    
    if data['tagline']:
        print(f"\nTagline: {data['tagline']}")
    
    if data['hackathon']:
        print(f"\nHackathon: {data['hackathon']}")
    
    if data['awards']:
        print(f"\nAwards:")
        for award in data['awards']:
            print(f"  - {award}")
    
    if data['team_members']:
        print(f"\nTeam Members:")
        for member in data['team_members']:
            print(f"  - {member['name']} (@{member['username']})")
    
    if data['built_with']:
        print(f"\nBuilt With: {', '.join(data['built_with'])}")
    
    if data['description']:
        print(f"\n{'='*80}")
        print("STORY SECTIONS:")
        print("="*80)
        for section in data['description']:
            print(f"\n## {section['heading']}")
            print("-" * 80)
            print(section['content'])
    
    print("\n" + "="*80)


def save_to_json(data, filename=None):
    """Save scraped data to JSON file"""
    if filename is None:
        filename = f"{data['project_id']}_scraped.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\nData saved to: {filename}")


def scrape_multiple_projects(project_ids, debug=False):
    """Scrape multiple Devpost projects"""
    results = []
    
    for i, project_id in enumerate(project_ids, 1):
        print(f"\n[{i}/{len(project_ids)}] Processing: {project_id}")
        try:
            data = scrape_devpost(project_id, debug=debug)
            results.append(data)
            
            if debug:
                print(f"  Title: {data.get('title', 'Not found')}")
                print(f"  Tagline: {data.get('tagline', 'Not found')}")
                print(f"  Built with: {len(data.get('built_with', []))} technologies")
                print(f"  Team members: {len(data.get('team_members', []))}")
                
        except Exception as e:
            print(f"  Error processing {project_id}: {e}")
            results.append({
                'project_id': project_id,
                'url': f'https://devpost.com/software/{project_id}',
                'title': '',
                'tagline': '',
                'description': '',
                'built_with': [],
                'team_members': [],
                'hackathon': '',
                'awards': [],
                'error': str(e)
            })
    
    return results


if __name__ == "__main__":
    print(scrape_devpost('dose-ebmo9z'))
