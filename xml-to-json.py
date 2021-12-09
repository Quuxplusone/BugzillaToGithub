#!/usr/bin/env python

import datetime
import dateutil.parser
import glob
import json
import os
import re
import time
import xmltodict


def link_to_svn_commit(svn_commit_id):
    return '[rL%s](https://reviews.llvm.org/rL%s)' % (svn_commit_id, svn_commit_id)


def link_to_git_commit(git_commit_id):
    return '[%s](https://reviews.llvm.org/rG%s)' % (git_commit_id, git_commit_id)


def link_to_mentioned_bugs_and_commits(text):
    # TODO FIXME BUG HACK: this is where we should deal with comments such as
    # "Duplicate of bug 21377" or "I reverted this in r254044 because PR25607."
    # For now, don't bother with this.
    return text


def markdownify(text):
    # TODO FIXME BUG HACK: this should be improved
    if ('```\n' in text) or (' `' in text and '` ' in text):
        # Text containing backticks is probably fine as Markdown.
        return link_to_mentioned_bugs_and_commits(text)
    if '\n' in text:
        # Monospace all multiline text, e.g. clang-format bug reports.
        return "```\n" + text.strip() + "\n```\n"
    if '*' in text:
        # Escape stars, which are significant in C and C++.
        return "`" + text + "`"
    return link_to_mentioned_bugs_and_commits(text)


def link_to_bug(id):
    assert type(id) is int
    return '[%d](https://bugs.llvm.org/show_bug.cgi?id=%d)' % (id, id)


def link_to_bug_if_possible(s):
    m = re.match(r'^([0-9]+)$', s)
    if m:
        return link_to_bug(int(m.group(1)))
    m = re.match(r'^PR([0-9]+)$', s)
    if m:
        return link_to_bug(int(m.group(1)))
    m = re.match(r'^https://bugs.llvm.org/show_bug.cgi?id=([0-9]+)$', s)
    if m:
        return link_to_bug(int(m.group(1)))
    return markdownify(s)


def link_to_commit_if_possible(s):
    m = re.match(r'^r?([23][0-9]{5})$', s)
    if m:
        return link_to_svn_commit(m.group(1))
    m = re.match(r'^rL([23][0-9]{5})$', s)
    if m:
        return link_to_svn_commit(m.group(1))
    m = re.match(r'^https://reviews.llvm.org/rL([23][0-9]{5})$', s)
    if m:
        return link_to_svn_commit(m.group(1))
    m = re.match(r'^([0-9a-f]+)$', s)
    if m:
        return link_to_git_commit(m.group(1))
    m = re.match(r'^rG([0-9a-f]+)$', s)
    if m:
        return link_to_git_commit(m.group(1))
    m = re.match(r'^https://reviews.llvm.org/rG([0-9a-f]+)$', s)
    if m:
        return link_to_git_commit(m.group(1))
    return s


def reformat_timestamp(t):
    # GitHub is very picky about its timestamp formats.
    assert re.match(r'\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d [+-]\d\d00', t), 'Unexpected timestamp %s' % t
    t = t[:19] + t[20:]  # remove the space
    dt = dateutil.parser.isoparse(t)
    result = dt.astimezone(datetime.timezone.utc).isoformat()
    assert result.endswith('+00:00'), 'Unexpected timestamp %s formatted to %s' % (t, result)
    result = result[:-6] + 'Z'
    assert re.match(r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ', result), 'Unexpected timestamp %s formatted to %s' % (t, result)
    return result


def repeated_element(bz, key):
    # Handle the fact that xmltodict turns "<a>1</a>" into {"a": "1"},
    # but "<a>1</a><a>2</a>" becomes {"a": ["1","2"]}.
    # If x is not list, it might be either str or dict/OrderedDict.
    x = bz.get(key, [])
    return x if (type(x) is list) else [x]


def parse_bz_status(bz):
    status = bz['bug_status']
    resolution = bz['resolution']
    if status not in ['NEW', 'CONFIRMED', 'REOPENED', 'RESOLVED']:
        assert False, 'Unexpected status string %s' % status
    if resolution is not None:
        return status + ' ' + resolution
    else:
        return status


def parse_bz_tags(bz):
    keywords = bz['keywords']
    if keywords is None:
        return []
    assert type(keywords) is str
    return keywords.split(', ')


def to_github_userblob(bz_userblob):
    if bz_userblob is None:
        return None
    elif type(bz_userblob) is str:
        gh_username = bz_userblob
    else:
        gh_username = bz_userblob['#text']
    return {
        "login": gh_username
    }


def to_human_readable_userblob(bz_userblob):
    if bz_userblob is None:
        return ''
    elif type(bz_userblob) is str:
        return bz_userblob
    else:
        return '%s (%s)' % (bz_userblob['@name'], bz_userblob['#text'])


def generate_summary_table(bz):
    if bz['cf_fixed_by_commits']:
        fixed_by_commits = ', '.join([
            link_to_commit_if_possible(c)
            for c in re.split(r'[, ]+', bz['cf_fixed_by_commits'])
        ])
    else:
        fixed_by_commits = ''

    summary = '\n'.join([
        '|                    |    |',
        '|--------------------|----|',
        '| Bugzilla Link      | %s |',
        '| Status             | %s |',
        '| Importance         | %s |',
        '| Reported by        | %s |',
        '| Reported on        | %s |',
        '| Last modified on   | %s |',
        '| Version            | %s |',
        '| Hardware           | %s |',
        '| CC                 | %s |',
        '| Fixed by commit(s) | %s |',
        '| Attachments        | %s |',
        '| Blocks             | %s |',
        '| See also           | %s |',
    ])
    return summary % (
        link_to_bug(int(bz['bug_id'])),
        parse_bz_status(bz),
        '%s %s' % (bz['priority'], bz['bug_severity']),
        to_human_readable_userblob(bz['reporter']),
        bz['creation_ts'],
        bz['delta_ts'],
        bz['version'],
        '%s %s' % (bz['rep_platform'], bz['op_sys']),
        ', '.join(repeated_element(bz, 'cc')),
        fixed_by_commits,
        '<br/>'.join([to_human_readable_attachment(a) for a in repeated_element(bz, 'attachment')]),
        ', '.join([link_to_bug_if_possible(s) for s in repeated_element(bz, 'blocked')]),
        ', '.join([link_to_bug_if_possible(s) for s in repeated_element(bz, 'see_also')]),
    )


def to_github_comment(c):
    return {
        "user": to_github_userblob(c['who']),
        "created_at": reformat_timestamp(c['bug_when']),
        "updated_at": reformat_timestamp(c['bug_when']),
        "body": markdownify(c['thetext'] or ''),
    }


def to_human_readable_attachment(a):
    return '[`%s`](https://bugs.llvm.org/attachment.cgi?id=%s) (%s bytes, %s)' % (
        a['filename'],
        a['attachid'],
        a['size'], a['type'],
    )


def to_github_attachment_comment(a):
    return {
        "user": to_github_userblob(a['attacher']),
        "created_at": reformat_timestamp(a['date']),
        "updated_at": reformat_timestamp(a['delta_ts']),
        "body": "Attached %s: %s" % (to_human_readable_attachment(a), markdownify(a['desc'] or '')),
    }


def bugzilla_to_github(id, bz):
    assert len(bz) == 1
    bz = bz['bugzilla']
    assert sorted(bz.keys()) == ['@maintainer', '@urlbase', '@version', 'bug']
    bz = bz['bug']
    assert bz['bug_id'] == str(id)
    status = parse_bz_status(bz)
    tags = parse_bz_tags(bz)

    comments = [to_github_comment(c) for c in repeated_element(bz, 'long_desc')[1:]]
    for a in repeated_element(bz, 'attachment'):
        # Eliminate boring Bugzilla-generated comments in favor of our custom attachment comments.
        boring_body = 'Created attachment %s' % a['attachid']
        attachment_comment = to_github_attachment_comment(a)
        comments = [c for c in comments if c['body'] != boring_body] + [attachment_comment]
    comments.sort(key=lambda c: c['updated_at'])

    return {
        "issue": {
            "number": bz['bug_id'],
            "title": bz['short_desc'],
            "user": to_github_userblob(bz['reporter']),
            "labels": [
                {"name": x} for x in tags
            ],
            "state": "closed" if status.startswith('RESOLVED') else "open",
            "locked": False,
            "assignee": to_github_userblob(bz['assigned_to']),
            "assignees": None if (bz['assigned_to'] is None) else [
                to_github_userblob(bz['assigned_to'])
            ],
            "comments": len(comments),
            "created_at": reformat_timestamp(bz['creation_ts']),
            "updated_at": reformat_timestamp(bz['delta_ts']),
            "closed_at": None,
            "body": generate_summary_table(bz) + '\n\n\n' + markdownify(repeated_element(bz, 'long_desc')[0]['thetext'] or ''),
        },
        "comments": comments,
    }


def extract_id(fname):
    m = re.match(r'xml/([0-9]+).xml', fname)
    assert m, 'Unexpected filename %s in xml/ subdirectory' % fname
    return int(m.group(1))


if __name__ == '__main__':
    os.makedirs('json', exist_ok=True)
    all_xml_filenames = glob.glob('xml/*.xml')
    all_bugzilla_ids = [extract_id(fname) for fname in all_xml_filenames]
    start_time = time.time()
    processed = 0
    for id in all_bugzilla_ids:
        print('Parsing %d.xml' % id)
        with open('xml/%d.xml' % id) as f:
            xml = f.read()
        xml = xml.replace('\0', '')  # e.g. bug 26078
        bz = xmltodict.parse(xml)
        gh = bugzilla_to_github(id, bz)
        with open('json/%d.json' % id, 'w') as f:
            print(json.dumps(gh, indent=2), file=f)
        processed += 1
        if processed % 100 == 0:
            elapsed = time.time() - start_time
            remaining = elapsed * (len(all_bugzilla_ids) - processed) / processed
            print('Processed %d bugs in %.2fs; %ds remaining' % (processed, elapsed, remaining))
