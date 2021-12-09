## Bugzilla to Github

Step 1: Export your Bugzilla bugs to XML.

    mkdir xml/
    ./bugzilla-to-xml.py

This will take about 36 hours to fetch 53000 bugs,
totaling 2.9GB of disk space.

Step 2: Eliminate non-existent bug numbers,
based on what the XML looks like.

    mkdir invalid-xml/
    for i in $(grep -rL short_desc xml/) ; do mv $i invalid-xml/ ; done

This will take about two minutes, and reduce the
number of files in the `xml/` directory to 51567.
You can inspect the files in `invalid-xml/` to see
what's being thrown out.

Step 3: Process each XML bug into GitHub's JSON schema.

    ./xml-to-json.py

This will take about five minutes to produce 51567 JSON files,
totaling 343MB of disk space.

The resulting JSON files use a schema that's roughly the same
as the one you get by exporting from GitHub's
[Issues API](https://docs.github.com/en/rest/reference/issues#list-repository-issues).
Notice that this is _not_ quite the same as the schema supported
by GitHub's undocumented [Issues Import API](https://gist.github.com/jonmagic/5282384165e0f86ef105).

Step 4: Import your JSON bugs into GitHub.

As noted above, this step can't just pipe our JSON files directly into GitHub's API,
because the schemas don't quite match. It needs to do some extra massaging.
Also, unless you have magic GitHub superpowers, some of the data must necessarily
be thrown away: for example, our JSON provides the authorship of comments, but
we cannot actually forge the authorship of those comments when we import them to
our GitHub project. We rightly don't have the power to impersonate random GitHub users
and submit comments under their names!

    TODO FIXME BUG HACK


For other GitHub Issues API scripts, see

* [erikmd/github-issues-import-api-tools](https://github.com/erikmd/github-issues-import-api-tools) (2018)

* [berestovskyy/bugzilla2github](https://github.com/berestovskyy/bugzilla2github) (2021)
