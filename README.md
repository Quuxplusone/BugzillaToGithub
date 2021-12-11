## Bugzilla to Github

### Step 1: Export your Bugzilla bugs to XML.

    mkdir xml/
    BUGZILLA_LOGIN=~~~~ BUGZILLA_LOGINCOOKIE=~~~~~~~~~~ ./bugzilla-to-xml.py

This will take about 36 hours to fetch 53000 bugs,
totaling 2.9GB of disk space.

Bugzilla will accept our requests and serve partial data
even if we do not present a valid `BUGZILLA_LOGINCOOKIE`.
However, in that case it will strip the domains of email
addresses (see [this SO question](https://stackoverflow.com/questions/70307092/)).
If you want email addresses (which you do), you must
provide your login cookies.

This step is repeatable, but it takes a very long time.
You can parallelize it by running copies of the script with
different ranges of `(FIRST_BUGZILLA_NUMBER, LAST_BUGZILLA_NUMBER)`,
all writing into the same `xml/` directory.


### Step 2: Discard non-existent bug numbers.

Some bug numbers don't exist in Bugzilla. We can detect these
based on what the XML looks like, and segregate them into a different
directory.

    mkdir invalid-xml/
    for i in $(grep -rL short_desc xml/) ; do mv $i invalid-xml/ ; done

This will take about two minutes, and reduce the
number of files in the `xml/` directory to 51567.
You can inspect the files in `invalid-xml/` to see
what's being thrown out.


### Step 3: Process each XML bug into GitHub's JSON schema.

    ./xml-to-json.py

This will take about seven minutes to produce 51567 JSON files,
totaling 349MB of disk space.

The resulting JSON files use a schema that's roughly the same
as the one you get by exporting from GitHub's
[Issues API](https://docs.github.com/en/rest/reference/issues#list-repository-issues).
Notice that this is _not_ quite the same as the schema supported
by GitHub's [undocumented Issues Import API](https://gist.github.com/jonmagic/5282384165e0f86ef105).


### Step 4: Import your JSON bugs into GitHub.

As noted above, this step can't just pipe our JSON files directly into GitHub's
[undocumented Issues Import API](https://gist.github.com/jonmagic/5282384165e0f86ef105),
because the schemas don't quite match. It needs to do some extra massaging.
Also, unless you have magic GitHub superpowers, some of the data must necessarily
be thrown away: for example, our JSON provides the authorship of comments, but
we cannot actually forge the authorship of those comments when we import them to
our GitHub project. We rightly don't have the power to impersonate random GitHub users
and submit comments under their names!

In fact, we must provide a GitHub "Personal API Token"
(which you can generate [here](https://github.com/settings/tokens/new) if you're logged
into GitHub right now); otherwise GitHub won't accept our API request at all.
All issues and comments created by this script will be associated with the account
whose API token you use; there's (rightly) no way for this script to forge issues or
comments as if they came from other GitHub users.

    GITHUB_API_TOKEN=~~~ ./json-to-github.py

This last step is irreversible! It increments the issue numbers on the GitHub repo you
point it at. There is no way to "decrement and try again," except to delete the entire
repo and re-create it.

This will take about 17 hours to upload 51567 issues to GitHub.


### Further reading

For other GitHub Issues API scripts, see

* [erikmd/github-issues-import-api-tools](https://github.com/erikmd/github-issues-import-api-tools) (2018)

* [berestovskyy/bugzilla2github](https://github.com/berestovskyy/bugzilla2github) (2021)
