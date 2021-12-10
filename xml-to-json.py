#!/usr/bin/env python

import datetime
import dateutil.parser
import glob
import json
import os
import re
import time
import xmltodict


def link_to_original_bugzilla_bug(bugzilla_id, text=None):
    assert type(bugzilla_id) is str
    text = text or ('PR' + bugzilla_id)
    return '[%s](https://bugs.llvm.org/show_bug.cgi?id=%s)' % (text, bugzilla_id)


def link_to_pr(bugzilla_id, text=None):
    # TODO FIXME BUG HACK: This should go to something like https://reviews.llvm.org/PR1234 instead.
    # which should then be an HTTP redirect to the correct GitHub issue.
    return link_to_original_bugzilla_bug(bugzilla_id, text)


def link_to_svn_commit(svn_commit_id, text=None):
    text = text or ('rL' + svn_commit_id)
    return '[%s](https://reviews.llvm.org/rL%s)' % (text, svn_commit_id)


def link_to_git_commit(git_commit_id, text=None):
    text = text or ('rG' + git_commit_id)
    return '[%s](https://reviews.llvm.org/rG%s)' % (text, git_commit_id)


def link_to_differential(differential_id, text=None):
    text = text or ('D' + differential_id)
    return '[%s](https://reviews.llvm.org/D%s)' % (text, differential_id)


def replace_all_in_string(text, rx, how):
    rx = re.compile(rx)
    pos = 0
    while True:
        m = rx.search(text, pos)
        if m is None:
            break
        suffix = text[m.end(1):]
        text = text[:m.start(1)] + how(m) + suffix
        pos = len(text) - len(suffix)
    return text


def link_to_mentioned_bugs_and_commits(text):
    # This is where we should deal with comments such as
    # "Duplicate of bug 21377" or "I reverted this in r254044 because PR25607."
    # TODO FIXME BUG HACK: This could still be improved.
    text = replace_all_in_string(
        text,
        r'\b(revision [0-9]{4,5})\b',
        lambda m: link_to_svn_commit(m.group(1)[9:], m.group(1))
    )
    text = replace_all_in_string(
        text,
        r'\b(commit [0-9a-f]{7,40})\b',
        lambda m: link_to_git_commit(m.group(1)[7:], m.group(1))
    )
    text = replace_all_in_string(
        text,
        r'\b([Bb]ug [0-9]{2,5})\b',
        lambda m: link_to_pr(m.group(1)[4:], m.group(1))
    )
    text = replace_all_in_string(
        text,
        r'uplicate of ([0-9]{2,5})\b',
        lambda m: link_to_pr(m.group(1)[12:], m.group(1))
    )
    text = replace_all_in_string(
        text,
        r'[^_A-Za-z0-9/](PR[0-9]{3,5})\b',
        lambda m: link_to_pr(m.group(1)[2:], m.group(1))
    )
    text = replace_all_in_string(
        text,
        r'[^_A-Za-z0-9/](rL[123][0-9]{5})\b',
        lambda m: link_to_svn_commit(m.group(1)[2:], m.group(1))
    )
    text = replace_all_in_string(
        text,
        r'[^_A-Za-z0-9/](r[123][0-9]{5})\b',
        lambda m: link_to_svn_commit(m.group(1)[1:], m.group(1))
    )
    text = replace_all_in_string(
        text,
        r'[^_A-Za-z0-9/](rG[0-9a-f]{7,40})\b',
        lambda m: link_to_git_commit(m.group(1)[2:], m.group(1))
    )
    text = replace_all_in_string(
        text,
        r'[^_A-Za-z0-9/](D[0-9]{4,6})\b',
        lambda m: link_to_differential(m.group(1)[1:], m.group(1))
    )
    return text


def link_to_mentioned_bugs_in_bugzilla_autocomment(text):
    # See detect_bugzilla_autocomment. The only kinds of autocomments
    # we support are the ones where every integer is a bug number.
    text = replace_all_in_string(
        text,
        r'\b([Bb]ug [0-9]{2,5})\b',
        lambda m: link_to_pr(m.group(1)[4:], m.group(1))
    )
    text = replace_all_in_string(
        text,
        r'uplicate of ([0-9]{2,5})\b',
        lambda m: link_to_pr(m.group(1)[12:], m.group(1))
    )
    return text


def wrap_long_line(line):
    line = line.rstrip()
    if (len(line) <= 80) or (' ' not in line) or (line[0] == ' '):
        # Don't wrap lines that look like probably source code.
        return line
    lastspace = line.rfind(' ', 0, 80)
    lasthyphen = line.rfind('-', 0, 80)
    if lastspace > lasthyphen:
        return line[:lastspace].rstrip() + '\n' + wrap_long_line(line[lastspace:].lstrip())
    elif lasthyphen > lastspace:
        return line[:lasthyphen+1] + '\n' + wrap_long_line(line[lasthyphen+1:])
    else:
        assert lastspace == -1 and lasthyphen == -1
        lastspace = line.find(' ', 80)
        lasthyphen = line.find('-', 80)
        assert lastspace != -1
        if lasthyphen != -1 and lasthyphen < lastspace:
            return line[:lasthyphen+1] + '\n' + wrap_long_line(line[lasthyphen+1:])
        else:
            return line[:lastspace].rstrip() + '\n' + wrap_long_line(line[lastspace:].lstrip())


def wrap_long_lines(text):
    text.lstrip('\n')
    return '\n'.join([
        wrap_long_line(line) for line in text.split('\n')
    ])


def markdownify(text):
    # TODO FIXME BUG HACK: this should be improved
    if ('```\n' in text) or (' `' in text and '` ' in text):
        # Text containing backticks is probably fine as Markdown.
        return link_to_mentioned_bugs_and_commits(text)
    if (text.count('\n') == 2 * text.count('\n\n')) and ('*' not in text):
        # If every line is a new paragraph, it's probably fine as Markdown.
        return link_to_mentioned_bugs_and_commits(text)
    if '\n' in text:
        # Monospace all multiline text, e.g. clang-format bug reports.
        # Bugzilla breaks lines around 84 columns; we choose 80.
        return "```\n" + wrap_long_lines(text) + "\n```\n"
    if '*' in text:
        # Escape stars, which are significant in C and C++.
        return "`" + text + "`"
    return link_to_mentioned_bugs_and_commits(text)


def link_to_pr_if_possible(s):
    m = (
        re.match(r'^([0-9]+)$', s) or
        re.match(r'^PR([0-9]+)$', s) or
        re.match(r'^https://bugs.llvm.org//show_bug.cgi[?]id=([0-9]+)$', s) or
        re.match(r'^https://bugs.llvm.org/show_bug.cgi[?]id=([0-9]+)$', s) or
        re.match(r'^http://bugs.llvm.org/show_bug.cgi[?]id=([0-9]+)$', s) or
        re.match(r'^https://llvm.org/bugs/show_bug.cgi[?]id=([0-9]+)$', s) or
        re.match(r'^http://llvm.org/bugs/show_bug.cgi[?]id=([0-9]+)$', s) or
        None
    )
    if m is not None:
        return link_to_pr(m.group(1))
    # I've manually verified that all these external links look reasonable.
    assert s.startswith('http') and ('llvm' not in s), s
    return markdownify(s)


def link_to_commit_if_possible(s):
    m = re.match(r'^r?([123][0-9]{5})$', s)
    if m:
        return link_to_svn_commit(m.group(1))
    m = re.match(r'^rL([123][0-9]{4,5})$', s)
    if m:
        return link_to_svn_commit(m.group(1))
    m = re.match(r'^https://reviews.llvm.org/rL([123][0-9]{4,5})$', s)
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
    valid_statuses = ['NEW', 'CONFIRMED', 'REOPENED', 'RESOLVED']
    valid_resolutions = ['DUPLICATE', 'FIXED', 'INVALID', 'LATER', 'MOVED', 'REMIND', 'WONTFIX', 'WORKSFORME']
    assert status in valid_statuses, 'Unexpected status string %s' % status
    if resolution is not None:
        assert resolution in valid_resolutions, 'Unexpected resolution string %s' % resolution
        assert status == 'RESOLVED'
        if resolution == 'DUPLICATE':
            return link_to_mentioned_bugs_and_commits('RESOLVED DUPLICATE of bug %d' % int(bz['dup_id']))
        else:
            return 'RESOLVED %s' % resolution
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
        '| Blocked by         | %s |',
        '| See also           | %s |',
    ])
    return summary % (
        link_to_original_bugzilla_bug(bz['bug_id']),
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
        ', '.join([link_to_pr_if_possible(s) for s in repeated_element(bz, 'blocked')]),
        ', '.join([link_to_pr_if_possible(s) for s in repeated_element(bz, 'dependson')]),
        ', '.join([link_to_pr_if_possible(s) for s in repeated_element(bz, 'see_also')]),
    )


def detect_bugzilla_autocomment(text):
    text = text.lstrip('\n').rstrip()
    if not text.endswith('***'):
        return (text, '')
    partition_point = None
    m1 = re.search(r'\*\*\* This bug has been marked as a duplicate of bug \d+ \*\*\*', text)
    m2 = re.search(r'\*\*\* This bug has been marked as a duplicate of \d+ \*\*\*', text)
    m3 = re.search(r'\*\*\* Bug \d+ has been marked as a duplicate of this bug. \*\*\*', text)
    assert not((m1 and m2) or (m1 and m3) or (m2 and m3))
    if (m1 or m2 or m3):
        partition_point = (m1 or m2 or m3).start(0)
        autocomment = text[partition_point:].strip()
        assert autocomment.startswith('*** ')
        assert autocomment.endswith(' ***')
        autocomment = '_%s_' % link_to_mentioned_bugs_in_bugzilla_autocomment(autocomment[4:-4].strip())
        text = text[:partition_point].strip()
        assert not text.endswith('***')
        return (text, autocomment)
    else:
        return (text, '')


def to_github_comment(c):
    bodytext, autocomment = detect_bugzilla_autocomment(c['thetext'] or '')
    bodytext = markdownify(bodytext)
    if bodytext and autocomment:
        bodytext = bodytext.strip() + '\n\n'
    return {
        "user": to_github_userblob(c['who']),
        "created_at": reformat_timestamp(c['bug_when']),
        "updated_at": reformat_timestamp(c['bug_when']),
        "body": bodytext + autocomment,
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
    # If you did Step 1 without valid Bugzilla credentials, '@exporter' will be missing.
    assert sorted(bz.keys()) == ['bugzilla']
    assert sorted(bz['bugzilla'].keys()) == ['@exporter', '@maintainer', '@urlbase', '@version', 'bug']
    bz = bz['bugzilla']['bug']
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
    all_bugzilla_ids = sorted([extract_id(fname) for fname in all_xml_filenames])
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
