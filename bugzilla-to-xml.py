#!/usr/bin/env python

import os
import requests
import time

# This script works as-is, but without providing login credentials to Bugzilla
# you won't be able to see certain information (e.g. the domains of email addresses);
# Bugzilla will censor that from the XML it serves to unauthenticated users.
# Log into Bugzilla, find your 'Bugzilla_login' and 'Bugzilla_logincookie' cookies
# for that domain, and store them in BUGZILLA_LOGIN and BUGZILLA_LOGINCOOKIE below.
# Do not publish your BUGZILLA_LOGINCOOKIE! Do not push it to GitHub!

BUGZILLA_LOGIN = os.environ.get('BUGZILLA_LOGIN', None)
BUGZILLA_LOGINCOOKIE = os.environ.get('BUGZILLA_LOGINCOOKIE', None)
BUGZILLA_URL = 'https://bugs.llvm.org'
FIRST_BUGZILLA_NUMBER = 1
LAST_BUGZILLA_NUMBER = 53000

if __name__ == '__main__':
    assert (BUGZILLA_LOGIN is None) == (BUGZILLA_LOGINCOOKIE is None)
    if BUGZILLA_LOGIN is not None:
        cookies = {
            'Bugzilla_login': BUGZILLA_LOGIN,
            'Bugzilla_logincookie': BUGZILLA_LOGINCOOKIE,
        }
    else:
        cookies = {}

    os.makedirs('xml', exist_ok=True)
    start_time = time.time()
    for id in range(FIRST_BUGZILLA_NUMBER, LAST_BUGZILLA_NUMBER + 1):
        r = requests.get(
            '%s/show_bug.cgi?id=%d&ctype=xml' % (BUGZILLA_URL, id),
            cookies=cookies,
        )
        assert r.status_code == 200, 'Unexpected HTTP %d response: %s' % (r.status_code, r.text)
        xml = r.text
        if cookies:
            assert 'exporter=' in xml, 'Are your Bugzilla login cookies expired or misspelled?'
        with open('xml/' + str(id) + '.xml', 'w') as f:
            print(xml, file=f)
        elapsed = time.time() - start_time
        remaining = elapsed * (LAST_BUGZILLA_NUMBER - id) / (id - FIRST_BUGZILLA_NUMBER + 1)
        print('Retrieved %d bugs in %.2fs; %ds remaining' % (id, elapsed, remaining))
