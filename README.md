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

    TODO FIXME BUG HACK

Step 4: Import your JSON bugs into GitHub.

    TODO FIXME BUG HACK
