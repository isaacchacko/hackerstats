import threading
import time
from queue import Queue, Empty
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import urllib.parse
import sys
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import pickle

NULL_CMD = -1
NO_TASK = -2
NO_FROM = {'name': 'Unknown', 'folder': 'Unknown'}
TIMEOUT = 0.1
DB_WRITE = False
HACKATHONS_FOLDER = 'test/hackathons/'
DEVPOSTS_FOLDER = 'test/devposts/'
HACKERS_FOLDER = 'test/hackers/'

logError = lambda msg: print(msg, file=sys.stderr)
def get_filepath(task): return f'./{task['folder']}/{task['name']}.html'

def get_crawler_task(q_hacker, q_devpost, q_hackathon):
    try:

        content = q_hacker.get(timeout=TIMEOUT)  # Waits 1s, then raises Empty
        
        if content == NULL_CMD:
            return {'error': NULL_CMD}

        url = f'https://www.devpost.com/{content['name']}'

        return {
            'url': url,
            'folder': HACKERS_FOLDER,
            'name': content['name'],
            'from': content['from'] if 'from' in content else NO_FROM,
            'done_callback': q_hacker.task_done
        }

    except Empty:
        pass

    try:

        content = q_devpost.get(timeout=TIMEOUT)  # Waits 1s, then raises Empty
        url = f'https://www.devpost.com/software/{content['name']}'
        
        return {
            'url': url,
            'folder': DEVPOSTS_FOLDER,
            'name': content['name'],
            'from': content['from'] if 'from' in content else NO_FROM,
            'done_callback': q_devpost.task_done
        }

    except Empty:
        pass

    try:
        content = q_hackathon.get(timeout=TIMEOUT)  # Waits 1s, then raises Empty
        url = f'https://www.{content['name']}.devpost.com'
        if 'page_number' in content:
            url += f"?{urllib.parse.urlencode({'page': content['page_number']})}"

        return {
            'url': url,
            'folder': HACKATHONS_FOLDER,
            'name': content['name'],
            'from': content['from'] if 'from' in content else NO_FROM,
            'done_callback': q_hackathon.task_done
        }

    except Empty:
        logError("Massive error: no hackers, devposts, or hackathons to process.")
        return {'error': NO_TASK}


def crawler(label, q_todo, q_hacker, q_devpost, q_hackathon, visited):
    driver = webdriver.Chrome(options=options)
    while True:
        task = get_crawler_task(q_hacker, q_devpost, q_hackathon)
        
        if 'error' in task:
            if task['error'] == NULL_CMD: break

            if task['error'] == NO_TASK:
                logError(f"{label} failed to retrieve a task.")
                continue
        
        with visited[task['folder']]['lock']:
    
            # if not even saved locally
            if task['name'] not in visited[task['folder']]['local']:

                # save it
                print(f'{label} adding "{task['name']}" to {task['folder']} (reference: "{task['from']['name']}" from {task['from']['folder']})')
                driver.get(task['url'])
                content = driver.page_source
                with open(get_filepath(task), 'w') as f:
                    f.write(content)
        

                visited[task['folder']]['local'].add(task['name'])

            # if not in the now visited (visited this loop)
            if task['name'] not in visited[task['folder']]['now']:
                q_todo.put(task)
                visited[task['folder']]['now'].add(task['name'])


            task['done_callback']()

    driver.quit()

    print(f"{label} shut down.")

def get_parser_task(q_todo):
    try:

        content = q_todo.get(timeout=TIMEOUT)  # Waits 1s, then raises Empty

        if content == NULL_CMD:
            return {'error': NULL_CMD}
    
        content['done_callback'] = q_todo.task_done
        return content

    except Empty:
        return {'error': NO_TASK}

    logError("Massive error: no hackers, devposts, or hackathons to parse.")

def parse_hacker(task, content, q_hacker, q_devpost, q_hackathon):

    lines = content.split('\n')
    
    socialURLs = []
    devposts = []
    username = task['name']
    displayName = "undefined"

    for index, line in enumerate(lines):
        if f'<small>({username})' in line:
            displayName = lines[index-1].strip()
            continue
        
        if '<a target="_blank" rel="nofollow" href="http' in line:
            socialURL = line.split('href="')[1][:-2]
            socialURLs.append(socialURL)
            continue 

        if '<a class="block-wrapper-link fade link-to-software" href="' in line:
            devpost = (line
                          .split('href="')[1][:-2]
                          .split('/')[-1])
            devposts.append(devpost)
            continue 
    
    info = {
        'username': username,
        'displayName': displayName,
        'social': socialURLs,
        'devposts': devposts
    }

    # insert some db write
    if DB_WRITE:
        with driver.session() as session:
            session.run("MERGE (:Hacker {name: $name, displayName: $displayName, socialURLs: $socialURLs})", 
                name=task['name'],
                displayName=displayName,
                socialURLs=socialURLs)

            for devpost in devposts:
                generate_connection(session, task['name'], devpost)


    for devpost in devposts:
        q_devpost.put({
            'name': devpost,
            'from': {
                'name': task['name'],
                'folder': task['folder'],
                'info': info
            }
        })
    
    task['done_callback']()

def generate_connection(session, hacker, devpost):
    result = session.run("""
        MATCH (h:Hacker {name: $hacker}), (d:Devpost {name: $devpost})
        CREATE (h)-[:CONTRIBUTED_TO]->(d)""",
            hacker=hacker,
            devpost=devpost)
    print(f'attempting to gen between {hacker} and {devpost}: result {result.single()}')

def parse_devpost(task, content, q_hacker, q_devpost, q_hackathon):

    lines = content.split('\n')
    
    hackers = {}
    hackathonName = "undefined"
    hackathonDisplayName = "undefined"

    for index, line in enumerate(lines):
        if '<a class="user-profile-link" href="' in line and '<img alt=' not in line:
            hackerURL = (line
                         .split('<a class="user-profile-link" href="')[1]
                         .split('">')[0]
                         )
            hackerUsername = hackerURL.split('/')[-1]
            hackerDisplayName = (line
                                 .split('">')[1]
                                 .split('</a>')[0]
                                 )

            # TODO: change this to just use a list
            if hackerUsername not in hackers:
                hackers[hackerUsername] = {
                    'username': hackerUsername,
                    'displayName': hackerDisplayName
                }
                continue
            
        if "software-list-content" in line:
            hackathonName = (lines[index+2]
                             .split('<a href="')[1]
                             .split('">')[0]
                             .split('//')[1]
                             .split('.')[0])
            hackathonDisplayName = (lines[index+2]
                                    .split('">')[1]
                                    .split('</a>')[0]
                                    )
            continue
        
    info = {
        'name': task['name'],
        'hackathon': {
            "name": hackathonName,
            "displayName": hackathonDisplayName
        },
        'hackers': hackers
    }

    # again insert some db write
    if DB_WRITE:
        with driver.session() as session:
            session.run("MERGE (:Devpost {name: $name, hackathonName: $hackathonName, hackathonDisplayName: $hackathonDisplayName})", 
                name=task['name'],
                hackathonName=hackathonName,
                hackathonDisplayName=hackathonDisplayName)

            for hacker in hackers:
                generate_connection(session, hacker, task['name'])
     
    for hacker in hackers:
        q_hacker.put({
            'name': hacker,
            'from': {
                'name': task['name'],
                'folder': task['folder']
            } })

    task['done_callback']()

def parse_hackathon(task, content, q_hacker, q_devpost, q_hackathon):
    lines = content.split('\n')
    
    total_page_count = -1
    for index, line in enumerate(lines):
        if "</b> of <b>" in line:
            try:
                total_page_count = int(line
                                    .split('</b> of <b>')[1]
                                    .split('</b>')[0])
            except ValueError:
                pass
            continue 
        
        if "<h5>" in line:
            devpostDisplayName = (lines[index+1].strip())
    return total_page_count

def parser(label, q_todo, q_hacker, q_devpost, q_hackathon):
    while True:
        task = get_parser_task(q_todo)
        
        if 'error' in task:
            if task['error'] == NULL_CMD: break

            if task['error'] == NO_TASK:
                continue

        print(f'{label} parsing "{task['name']}" from {task['folder']}')
        with open(get_filepath(task), 'r') as f:
            content = f.read()
        
        if task['folder'] == 'hackers':
            parse_hacker(task, content, q_hacker, q_devpost, q_hackathon)

        if task['folder'] == 'devposts':
            parse_devpost(task, content, q_hacker, q_devpost, q_hackathon)

        # if task['folder'] == 'hackathons':
        #     parse_hackathon(task, content, q_hacker, q_devpost, q_hackathon, done_callback)

    print(f"{label} shut down.")

def purge_all(folders):
    for folder in folders:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    
if __name__ == "__main__":
    with open("hackgt-12.html", 'r') as f:
        content = f.read()
    print(parse_hackathon({}, content, 1, 2, 3))
