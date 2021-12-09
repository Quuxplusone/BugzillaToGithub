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

GITHUB_REPOSITORY_NAME = 'llvm/llvm-bugzilla-archive'
GITHUB_API_TOKEN = os.environ.get('GITHUB_API_TOKEN', None)


def assert_status_code(r):
    if GITHUB_API_TOKEN is None:
        assert r.status_code != 404, 'ERROR -- HTTP 404 Not Found -- is the repo private, or its name misspelled?'
        assert r.status_code != 401, 'ERROR -- HTTP 401 Unauthorized -- is the repo private?'
        if (r.status_code == 403) and ('API rate limit exceeded' in r.text):
            assert r.status_code != 403, 'ERROR -- HTTP 403, API rate limit exceeded -- try adding an API token?'
    else:
        assert r.status_code != 404, 'ERROR -- HTTP 404 Not Found -- is the repo name misspelled?'
        assert r.status_code != 401, 'ERROR -- HTTP 401 Unauthorized -- is your API token expired or misspelled?'
        if (r.status_code == 403) and ('API rate limit exceeded' in r.text):
            assert r.status_code != 403, 'ERROR -- HTTP 403, API rate limit exceeded -- there may be a bug in this script!'
    assert r.status_code == 200, 'ERROR -- HTTP %d was unexpected' % r.status_code


def clean_gh_comment_in_place(c):
    del c['url']
    del c['html_url']
    del c['issue_url']
    del c['user']['url']
    del c['user']['html_url']
    del c['user']['followers_url']
    del c['user']['following_url']
    del c['user']['gists_url']
    del c['user']['starred_url']
    del c['user']['subscriptions_url']
    del c['user']['organizations_url']
    del c['user']['repos_url']
    del c['user']['events_url']
    del c['user']['received_events_url']
    del c['reactions']['url']
    del c['reactions']['total_count']
    del c['performed_via_github_app']


def get_gh_comments(id):
    page = 0
    all_comments = []
    while True:
        headers = {
            'User-Agent': 'Script from https://github.com/Quuxplusone/BugzillaToGithub',
        }
        if GITHUB_API_TOKEN is not None:
            headers['Authorization'] = 'token %s' % GITHUB_API_TOKEN
        r = requests.get(
            'https://api.github.com/repos/%s/issues/%d/comments?page=%d&per_page=100' % (GITHUB_REPOSITORY_NAME, id, page + 1),
            headers=headers,
        )
        assert_status_code(r)
        new_comments = r.json()
        assert type(new_comments) is list, 'ERROR -- JSON for comments is unexpectedly not a list on page %d of bug %d' % (page, id)
        all_comments += new_comments
        if len(new_comments) == 0:
            break
        page += 1

    for c in all_comments:
        clean_gh_comment_in_place(c)
    all_comments.sort(key=lambda c: c['created_at'])
    return all_comments


def clean_gh_issue_in_place(issue):
    del issue['url']
    del issue['repository_url']
    del issue['labels_url']
    del issue['comments_url']
    del issue['events_url']
    del issue['html_url']
    del issue['user']['avatar_url']
    del issue['user']['url']
    del issue['user']['html_url']
    del issue['user']['followers_url']
    del issue['user']['following_url']
    del issue['user']['gists_url']
    del issue['user']['starred_url']
    del issue['user']['subscriptions_url']
    del issue['user']['organizations_url']
    del issue['user']['repos_url']
    del issue['user']['events_url']
    del issue['user']['received_events_url']
    for label in issue['labels']:
        del label['url']
        del label['description']
    del issue['reactions']['url']
    del issue['reactions']['total_count']
    del issue['timeline_url']
    del issue['performed_via_github_app']


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
        assert_status_code(r)
        bugs = r.json()
        assert type(bugs) is list, 'ERROR -- JSON is unexpectedly not a list on page %d' % page
        if len(bugs) == 0:
            break
        # Filter out pull requests; we care only about issues, not pull requests.
        issues = [b for b in bugs if 'pull_request' not in b]
        for issue in issues:
            clean_gh_issue_in_place(issue)
            if 'number' not in issue:
                print('WARNING -- bug without number on page %d!!' % page)
            else:
                id = issue['number']
                bug = {
                    "issue": issue,
                    "comments": []
                }
                if issue['comments'] != 0:
                    bug["comments"] = get_gh_comments(id)
                with open('json/' + str(id) + '.json', 'w') as f:
                    print(json.dumps(bug, indent=2), file=f)
        page += 1
        retrieved += len(bugs)
        elapsed = time.time() - start_time
        print('Retrieved %d pages containing %d bugs in %.2fs; ???s remaining' % (page, retrieved, elapsed))
