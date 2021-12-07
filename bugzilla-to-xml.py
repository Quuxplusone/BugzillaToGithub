#!/usr/bin/env python

import os
import requests
import time

BUGZILLA_URL = 'https://bugs.llvm.org'
MAX_BUGZILLA_NUMBER = 60000

if __name__ == '__main__':
    os.makedirs('xml', exist_ok=True)
    start_time = time.time()
    for id in range(1, MAX_BUGZILLA_NUMBER):
        r = requests.get(
            '%s/show_bug.cgi?id=%d&ctype=xml' % (BUGZILLA_URL, id),
        )
        xml = r.text
        with open('xml/' + str(id) + '.xml', 'w') as f:
            print(xml, file=f)
        elapsed = time.time() - start_time
        print('Retrieved %d bugs in %.2fs; %ds remaining' % (id, elapsed, (MAX_BUGZILLA_NUMBER - id) * (elapsed / id)))
