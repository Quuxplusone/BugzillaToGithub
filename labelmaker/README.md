## Labelmaker

### Step 1: Export your Bugzilla bugs to XML.

(This is the same as in `../README.md`.)


### Step 2: Discard non-existent bug numbers.

(This is the same as in `../README.md`.)


### Step 3: Process each XML bug to extract resolutions.

    ./xml-to-bz-map.py

This will take about 1 minute, and will print a Python dict
named `bz_resolution_map`. Cut and paste that Python dict
into the top of `bz-map-to-gh-map.py`.


### Step 4: Convert those Bugzilla bug numbers into GitHub issue numbers.

After editing `bz-map-to-gh-map.py` in Step 3, run it:

    ./bz-map-to-gh-map.py

This will take about 5.5 hours to fetch all 8293 bug numbers, and then
it will print a Python dict named `gh_resolution_map`. Cut and paste
that Python dict into the top of `gh-map-to-github.py`.


### Step 5: Apply labels to GitHub.

The following script will apply these four labels: `invalid`, `wontfix`,
`duplicate`, `worksforme`.

It will *not* apply `later`, `remind`, or `moved`. (Nor `fixed`, because
on GitHub that's indicated by simply closing the issue.) But if we
want to apply `later`, `remind`, or `moved`, we've already got the data
from the previous steps and therefore only have to repeat this one.

We must provide a GitHub "Personal API Token" (which you can generate
[here](https://github.com/settings/tokens/new) if you're logged into
GitHub right now); otherwise GitHub won't accept our API request at all.
All labels applied by this script will be visibly associated with the account
whose API token you use.

    GITHUB_API_TOKEN=~~~ ./gh-map-to-github.py

This last step is for real! It applies actions to the repository on GitHub.

This will take about 3 hours to upload all 8020 updates to GitHub.
