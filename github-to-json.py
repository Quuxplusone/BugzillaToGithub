#!/usr/bin/env python

import json
import os
import requests
import time

# This script works as-is for public repos.
# If your repository is private, then you'll need to generate a "Personal API Token"
# from https://github.com/settings/tokens/new , including at least the "repo" permission
# ("Full control of private repositories"), and store it in GITHUB_API_TOKEN below.
# Do not publish this API token! Do not push it to GitHub!

GITHUB_REPOSITORY_NAME = 'Quuxplusone/ImportTest'
GITHUB_API_TOKEN = None

if __name__ == '__main__':
    os.makedirs('json', exist_ok=True)
    start_time = time.time()
    page = 0
    retrieved = 0
    while True:
        headers = {
            'User-Agent': 'Script from https://github.com/Quuxplusone/BugzillaToGithub',
        }
        if GITHUB_API_TOKEN is not None:
            headers['Authorization'] = 'token %s' % GITHUB_API_TOKEN
        r = requests.get(
            'https://api.github.com/repos/%s/issues?page=%d&per_page=100' % (GITHUB_REPOSITORY_NAME, page + 1),
            headers=headers,
        )
        if GITHUB_API_TOKEN is None:
            assert r.status_code != 404, 'ERROR -- HTTP 404 Not Found -- is the repo private, or its name misspelled?'
            assert r.status_code != 401, 'ERROR -- HTTP 401 Unauthorized -- is the repo private?'
        else:
            assert r.status_code != 404, 'ERROR -- HTTP 404 Not Found -- is the repo name misspelled?'
            assert r.status_code != 401, 'ERROR -- HTTP 401 Unauthorized -- is your API token expired or misspelled?'
        assert r.status_code == 200, 'ERROR -- HTTP %d was unexpected' % r.status_code
        bugs = r.json()
        assert type(bugs) is list, 'ERROR -- JSON is unexpectedly not a list on page %d' % page
        if len(bugs) == 0:
            break
        # Filter out pull requests; we care only about issues, not pull requests.
        bugs = [b for b in bugs if 'pull_request' not in b]
        for bug in bugs:
            if 'number' not in bug:
                print('WARNING -- bug without number on page %d!!' % page)
            else:
                id = bug['number']
                with open('json/' + str(id) + '.json', 'w') as f:
                    print(json.dumps(bug, indent=2), file=f)
        page += 1
        retrieved += len(bugs)
        elapsed = time.time() - start_time
        print('Retrieved %d pages containing %d bugs in %.2fs; ???s remaining' % (page, retrieved, elapsed))
