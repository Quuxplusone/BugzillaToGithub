#!/usr/bin/env python

import json
import os
import re
import requests
import time


# This script makes irreversible changes to a GitHub repository!
# Therefore, you'll need to generate a "Personal API Token"
# from https://github.com/settings/tokens/new , and store it
# in GITHUB_API_TOKEN below. If your repository is private,
# you'll need to include at least the "repo" permission
# ("Full control of private repositories").
# Do not publish this API token! Do not push it to GitHub!

GITHUB_REPOSITORY_NAME = 'llvm/llvm-project'
GITHUB_API_TOKEN = os.environ['GITHUB_API_TOKEN']


# TODO FIXME BUG HACK: I'll fill this in with the result of bz-map-to-gh-map.py.
# Right now, this is only the first 10 issues in each category.
gh_resolution_map = {
    "WORKSFORME": [
        375, 522, 539, 688, 806, 832, 908, 942, 945, 961,
    ],
    "INVALID": [
        384, 385, 414, 415, 448, 542, 601, 618, 620, 622,
    ],
    "DUPLICATE": [
        387, 433, 516, 517, 526, 528, 535, 545, 555, 604,
    ],
    "WONTFIX": [
        394, 395, 428, 432, 446, 472, 478, 483, 493, 501,
    ],
    "LATER": [
        579, 659, 747, 770, 778, 959, 970, 1072, 1089, 1122,
    ],
    "REMIND": [
        2095, 6581, 8918, 10243, 14312, 20755, 23897, 45113,
    ],
    "MOVED": [
        4674, 4724, 4839, 4969, 5008, 5035, 7540, 11657, 13493, 14012,
    ],
}


def submit_github_label(gh_id, labelname):
    assert re.match(r'[A-Za-z0-9_-]+/[A-Za-z0-9_-]+', GITHUB_REPOSITORY_NAME)
    assert type(gh_id) is int
    assert re.match(r'[a-z]+', labelname)
    r = requests.post(
        'https://api.github.com/repos/%s/issues/%d/labels' % (GITHUB_REPOSITORY_NAME, gh_id),
        headers={
            'Authorization': 'token %s' % GITHUB_API_TOKEN,
        },
        data=json.dumps({
            'labels': [labelname]
        }),
    )
    assert r.status_code != 401, 'ERROR -- HTTP 401 Unauthorized -- is your API token expired or misspelled?'
    assert r.status_code == 200, 'Expected HTTP 200 OK, not HTTP %d: %s' % (r.status_code, r.text)
    print(r.text)


if __name__ == '__main__':
    del gh_resolution_map['LATER']
    del gh_resolution_map['REMIND']
    del gh_resolution_map['MOVED']
    assert sorted(gh_resolution_map.keys()) == ['DUPLICATE', 'INVALID', 'WONTFIX', 'WORKSFORME']

    total = sum(len(gh_ids) for gh_ids in gh_resolution_map.values())
    processed = 0
    start_time = time.time()
    for key, gh_ids in gh_resolution_map.items():
        labelname = key.lower()
        for gh_id in gh_ids:
            assert type(gh_id) is int
            submit_github_label(gh_id, labelname)
            processed += 1
            elapsed = time.time() - start_time
            remaining = elapsed * (total - processed) / processed
            print('Processed %d of %d bugs in %.2fs; %ds remaining' % (processed, total, elapsed, remaining))
