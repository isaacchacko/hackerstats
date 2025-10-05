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
            'folder': 'hackers',
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
            'folder': 'devposts',
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
            'folder': 'hackathons',
            'name': content['name'],
            'from': content['from'] if 'from' in content else NO_FROM,
            'done_callback': q_hackathon.task_done
        }

    except Empty:
        # logError("Massive error: no hackers, devposts, or hackathons to process.")
        return {'error': NO_TASK}


def crawler(label, q_todo, q_hacker, q_devpost, q_hackathon, visited, memory):
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
                memory[task['name']] = content
        

                visited[task['folder']]['local'].add(task['name'])

            # if not in the now visited (visited this loop)
            if task['name'] not in visited[task['folder']]['now']:
                if task['name'] not in memory:
                    with open(get_filepath(task), 'r') as f:
                        memory[task['name']] = f.read()
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
        # logError("Massive error: no hackers, devposts, or hackathons to parse.")
        return {'error': NO_TASK}


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
        MERGE (h)-[:CONTRIBUTED_TO]->(d)""",
            hacker=hacker,
            devpost=devpost)

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

def parser(label, q_todo, q_hacker, q_devpost, q_hackathon, memory):
    while True:
        task = get_parser_task(q_todo)
        
        if 'error' in task:
            if task['error'] == NULL_CMD: break

            if task['error'] == NO_TASK:
                continue

        print(f'{label} parsing "{task['name']}" from {task['folder']}')
        content = memory[task['name']]
        del memory[task['name']] 
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

    options = Options()
    options.add_argument("--headless")

    load_dotenv()

    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    driver = GraphDatabase.driver(uri, auth=(username, password), encrypted=True)
    
    q_todo = Queue()
    q_hacker = Queue()
    q_devpost = Queue()
    q_hackathon = Queue()
    
    memory = {}
    visited = {
        'hackers':  {
            'lock': threading.Lock(),
            'local': set(x.split('.')[0] for x in os.listdir('./hackers')),
            'now': set()
        },
        'devposts':  {
            'lock': threading.Lock(),
            'local': set(x.split('.')[0] for x in os.listdir('./devposts')),
            'now': set()
        },
        'hackathons':  {
            'lock': threading.Lock(),
            'local': set(x.split('.')[0] for x in os.listdir('./hackathons')),
            'now': set()
        }
    }

    try:
        CRAWLER_COUNT = 3
        PARSER_COUNT = 4
        crawlers = []
        for i in range(CRAWLER_COUNT):
            t = threading.Thread(target=crawler, args=(f"Crawler {i}", q_todo, q_hacker, q_devpost, q_hackathon, visited, memory))
            t.start()
            crawlers.append(t)

        parsers = []
        for i in range(PARSER_COUNT):
            t = threading.Thread(target=parser, args=(f"Parser {i}", q_todo, q_hacker, q_devpost, q_hackathon, memory))
            t.start()
            parsers.append(t)

        q_hacker.put({'name': 'isaacchacko'})
        
        # Wait for all URLs to be processed
        q_todo.join()
        q_hacker.join()
        q_devpost.join()
        q_hackathon.join()

        for t in crawlers:
            t.join()

        for t in parsers:
            t.join()

        print("All workers stopped.")

    except OSError:
        for i in visited:
            del visited[i]['lock']
        with open('visited.pkl',  'wb') as f:
            pickle.dump(visited, f)

    except KeyboardInterrupt:
        for i in visited:
            del visited[i]['lock']
        with open('visited.pkl',  'wb') as f:
            pickle.dump(visited, f)
