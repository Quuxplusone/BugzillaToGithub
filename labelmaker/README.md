## Labelmaker

### Step 1: Export your Bugzilla bugs to XML.

(This is the same as in `../README.md`.)


### Step 2: Discard non-existent bug numbers.

(This is the same as in `../README.md`.)


### Step 3: Process each XML bug to extract those with CONFIRMED status.

    ./labelmaker/xml-to-bz-map.py

This will take about 1 minute, and will print a Python dict
named `bz_resolution_map`. Cut and paste that Python dict
into the top of `bz-map-to-gh-map.py`.


### Step 4: Convert those Bugzilla bug numbers into GitHub issue numbers.

After editing `bz-map-to-gh-map.py` in Step 3, run it:

    cd labelmaker
    ./bz-map-to-gh-map.py

This will take about an hour to fetch all 974 bug numbers, and then
it will print a Python dict named `gh_resolution_map`. Cut and paste
that Python dict into the top of `exclude-already-closed-gh-issues.py`.


### Step 5: Filter out GitHub issues that have already been closed.

After editing `exclude-already-closed-gh-issues.py` in Step 4, run it:

    ./exclude-already-closed-gh-issues.py

It will print a Python list named `issues_to_mark_confirmed`. Cut and paste
that Python dict into the top of `gh-map-to-github.py`.


### Step 6: Apply labels to GitHub.

The following script will apply the `confirmed` label to all the
issues mentioned in the previous step.

We must provide a GitHub "Personal API Token" (which you can generate
[here](https://github.com/settings/tokens/new) if you're logged into
GitHub right now); otherwise GitHub won't accept our API request at all.
All labels applied by this script will be visibly associated with the account
whose API token you use.

    GITHUB_API_TOKEN=~~~ ./gh-map-to-github.py

This last step is for real! It applies actions to the repository on GitHub.

This will take about 20 minutes to apply all 974 updates to GitHub.
