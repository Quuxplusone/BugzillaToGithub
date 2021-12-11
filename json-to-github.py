#!/usr/bin/env python

import glob
import json
import os
import re
import requests
import subprocess
import time


# This script makes irreversible changes to a GitHub repository!
# Therefore, you'll need to generate a "Personal API Token"
# from https://github.com/settings/tokens/new , and store it
# in GITHUB_API_TOKEN below. If your repository is private,
# you'll need to include at least the "repo" permission
# ("Full control of private repositories").
# Do not publish this API token! Do not push it to GitHub!

GITHUB_REPOSITORY_NAME = 'Quuxplusone/ImportTest'
GITHUB_API_TOKEN = os.environ['GITHUB_API_TOKEN']
FIRST_BUGZILLA_ID = 1
LAST_BUGZILLA_ID = 10000


def submit_github_issue(payload):
    assert re.match(r'[A-Za-z0-9_-]+/[A-Za-z0-9_-]+', GITHUB_REPOSITORY_NAME)
    if False:
        # requests.post waits for each server response before continuing, which
        # means you can do only about 1 request per second. This alternative
        # approach can send POST requests vastly faster... but merely succeeds
        # in triggering GitHub's "secondary rate limit", which means the issues
        # get rejected instead of imported. Preserved for historical interest.
        # https://docs.github.com/en/free-pro-team@latest/rest/overview/resources-in-the-rest-api#secondary-rate-limits
        subprocess.Popen([
            'curl',
            '-X', 'POST',
            '-H', 'Authorization: token %s' % GITHUB_API_TOKEN,
            '-d', json.dumps(payload),
            'https://api.github.com/repos/%s/import/issues' % GITHUB_REPOSITORY_NAME,
        ])
    else:
        r = requests.post(
            'https://api.github.com/repos/%s/import/issues' % GITHUB_REPOSITORY_NAME,
            headers={
                'Authorization': 'token %s' % GITHUB_API_TOKEN,
            },
            data=json.dumps(payload),
        )
        assert r.status_code != 401, 'ERROR -- HTTP 401 Unauthorized -- is your API token expired or misspelled?'
        assert r.status_code == 202, 'Expected HTTP 202 Accepted, not HTTP %d: %s' % (r.status_code, r.text)
        print(r.text)


def bugzilla_to_github_user(username):
    # TODO FIXME BUG HACK
    return None


def dumb_down_comment(c):
    # https://gist.github.com/jonmagic/5282384165e0f86ef105#supported-issue-and-comment-fields
    return {
        "created_at": c['created_at'],
        "body": c['body'],
    }


def dumb_down_issue(gh):
    # https://gist.github.com/jonmagic/5282384165e0f86ef105#supported-issue-and-comment-fields
    # Notice that if you don't set a "closed_at" timestamp, then GitHub will assume
    # the issue got closed at the time of the API call, screwing up its last-modified time.
    # Therefore, we explicitly backdate the "closed_at" time.
    return {
        "issue": {
            "title": gh['issue']['title'],
            "body": gh['issue']['body'],
            "created_at": gh['issue']['created_at'],
            "closed_at": gh['issue']['updated_at'],
            "updated_at": gh['issue']['updated_at'],
            "assignee": bugzilla_to_github_user(gh['issue'].get('assignee', {}).get('login', None)),
            # "milestone": None,
            "closed": (gh['issue']['state'] == 'closed'),
            "labels": [tag['name'] for tag in gh['issue']['labels']],
        },
        "comments": [
            # GitHub rejects (and Bugzilla hides) comments with no body text.
            dumb_down_comment(c) for c in gh['comments'] if c['body']
        ]
    }


def extract_id(fname):
    m = re.match(r'json/([0-9]+).json', fname)
    assert m, 'Unexpected filename %s in json/ subdirectory' % fname
    return int(m.group(1))


if __name__ == '__main__':
    os.makedirs('json', exist_ok=True)
    all_json_filenames = glob.glob('json/*.json')
    all_bugzilla_ids = [extract_id(fname) for fname in all_json_filenames]
    all_bugzilla_ids = sorted([id for id in all_bugzilla_ids if FIRST_BUGZILLA_ID <= id <= LAST_BUGZILLA_ID])
    start_time = time.time()
    processed = 0
    for id in all_bugzilla_ids:
        print('Parsing %d.json' % id)
        with open('json/%d.json' % id) as f:
            gh = json.load(f)
        payload = dumb_down_issue(gh)
        submit_github_issue(payload)
        processed += 1
        elapsed = time.time() - start_time
        remaining = elapsed * (len(all_bugzilla_ids) - processed) / processed
        print('Processed %d bugs in %.2fs; %ds remaining' % (processed, elapsed, remaining))
