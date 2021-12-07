#!/usr/bin/env python

import os
import requests
import time

MAX_BUGZILLA_NUMBER = 60000

if __name__ == '__main__':
    os.makedirs('xml', exist_ok=True)
    start_time = time.time()
    for id in range(1, MAX_BUGZILLA_NUMBER):
        bugzilla_url = 'https://bugs.llvm.org/show_bug.cgi?id=' + str(id) + '&ctype=xml'
        r = requests.get(bugzilla_url)
        xml = r.text
        with open('xml/' + str(id) + '.xml', 'w') as f:
            print(xml, file=f)
        elapsed = time.time() - start_time
        print('Retrieved %d bugs in %.2fs; %ds remaining' % (id, elapsed, (MAX_BUGZILLA_NUMBER - id) * (elapsed / id)))
