#! /usr/bin/env python
from plumbum import local
from plumbum.commands.processes import ProcessExecutionError
import requests
import time
import math
import os
import ruamel.yaml

def download_from_github(repo_url:str):
    print(f'cloning {repo_url}')
    git = local['git']
    try:
        output = git['clone', repo_url]()
    except ProcessExecutionError as ex:
        print(ex)

def github_search_da_repos(just_suffolk=True):
    per_page = 100 # by default 100 items in the result
    URL = "https://api.github.com/search/repositories" #The basic URL to use the GitHub API
    params = {
        'q': 'docassemble- in:name', # get only repos with the word 'docassemble' in the repo name
        'per_page': per_page
    }
    if just_suffolk:
        params['q'] += ' org:SuffolkLITLab'
    DELAY_BETWEEN_QUERIES = 3 #The time to wait between different queries to GitHub 
    response = requests.get(URL, params=params)
    if not response.ok:
        print(response)
        return None
    json_resp = response.json()
    all_repos = set([repo['svn_url'] for repo in json_resp.get('items', []) if not repo['archived']])
    print(json_resp.get('total_count'))
    if json_resp.get('total_count', 0) > per_page:
        page_count = int(math.ceil(json_resp.get('total_count', 0) / per_page))
        for page_idx in range(1, page_count+1):
            params['page'] = page_idx
            time.sleep(DELAY_BETWEEN_QUERIES)
            response = requests.get(URL, params=params)
            if not response.ok:
                print(response)
                continue
            json_resp = response.json()
            all_repos.update([repo['svn_url'] for repo in json_resp.get('items', []) if not repo['archived']])
    #all_repos.remove('https://github.com/jhpyle/docassemble')
    # TOOD: work when not there
    return sorted(list(all_repos))

def find_all_yamls(start_dir='.'):
    all_yamls = []
    for base_dir, dirs, files in os.walk(start_dir):
        for filename in files:
            if '.github' in base_dir:
                continue
            if filename.endswith('.yml'):
                all_yamls.append(base_dir + '\\' + filename)
    return all_yamls

def all_questions(all_yamls):
    all_qs = []
    for yaml_filename in all_yamls:
        with open(yaml_filename, 'r') as yaml_file:
            yaml_parsed = list(ruamel.yaml.safe_load_all(yaml_file.read()))
        all_qs.extend(yaml_parsed)
    return all_qs
    

def main():
    repos = github_search_da_repos()
    print(repos)
    for repo in repos:
        time.sleep(3)
        download_from_github(repo)


if __name__ == '__main__':
    main()