#!/usr/bin/env python

import os
import requests
import time

BUGZILLA_URL = 'https://bugs.llvm.org'
FIRST_BUGZILLA_NUMBER = 1
LAST_BUGZILLA_NUMBER = 53000

if __name__ == '__main__':
    os.makedirs('xml', exist_ok=True)
    start_time = time.time()
    for id in range(FIRST_BUGZILLA_NUMBER, LAST_BUGZILLA_NUMBER + 1):
        r = requests.get(
            '%s/show_bug.cgi?id=%d&ctype=xml' % (BUGZILLA_URL, id),
        )
        xml = r.text
        with open('xml/' + str(id) + '.xml', 'w') as f:
            print(xml, file=f)
        elapsed = time.time() - start_time
        remaining = elapsed * (LAST_BUGZILLA_NUMBER - id) / (id - FIRST_BUGZILLA_NUMBER + 1)
        print('Retrieved %d bugs in %.2fs; %ds remaining' % (id, elapsed, remaining))
