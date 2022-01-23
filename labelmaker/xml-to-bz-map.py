#!/usr/bin/env python

import collections
import glob
import re
import xmltodict


bz_resolution_map = collections.defaultdict(list)


def bugzilla_to_github(id, bz):
    # If you did Step 1 without valid Bugzilla credentials, '@exporter' will be missing.
    assert sorted(bz.keys()) == ['bugzilla']
    assert sorted(bz['bugzilla'].keys()) == ['@exporter', '@maintainer', '@urlbase', '@version', 'bug']
    bz = bz['bugzilla']['bug']
    assert bz['bug_id'] == str(id)
    assert bz['bug_id'] == str(int(bz['bug_id']))
    if bz['bug_status'] == 'CONFIRMED':
        assert bz['everconfirmed'] == '1'
        bz_resolution_map['CONFIRMED'] += [bz['bug_id']]


def extract_id(fname):
    m = re.match(r'xml/([0-9]+).xml', fname)
    assert m, 'Unexpected filename %s in xml/ subdirectory' % fname
    return int(m.group(1))


if __name__ == '__main__':
    all_xml_filenames = glob.glob('xml/*.xml')
    all_bugzilla_ids = sorted([extract_id(fname) for fname in all_xml_filenames])
    for id in all_bugzilla_ids:
        print('Parsing %d.xml' % id)
        with open('xml/%d.xml' % id) as f:
            xml = f.read()
        xml = xml.replace('\0', '')  # e.g. bug 26078
        bz = xmltodict.parse(xml)
        bugzilla_to_github(id, bz)
    print('\n\nbz_resolution_map = {')
    for key in bz_resolution_map.keys():
        print('    "%s": [' % key, end='')
        for i, bz_id in enumerate(bz_resolution_map[key]):
            if i % 20 == 0:
                print('\n       ', end='')
            print(' %s,' % bz_id, end='')
        print('\n    ],')
    print('}')
