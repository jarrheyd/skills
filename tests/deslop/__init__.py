import os
import tempfile

# Hooks run as subprocesses and inherit this env. Start every test with house rules off, so a
# developer's own $DESLOP_DATA/house-rules.md never changes what the shared checks do.
os.environ["DESLOP_DATA"] = tempfile.mkdtemp(prefix="deslop-test-")
os.environ.pop("DESLOP_HOUSE", None)
