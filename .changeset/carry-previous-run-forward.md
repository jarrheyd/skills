---
"jarrheyd-skills": minor
---

qa-review carries the previous run forward. A flow that did not run this time now shows its last screenshots instead of an empty card, and counts toward green only while that evidence still describes the build under test and is under 7 days old. Each run fingerprints what was installed (the simulator or device binary, or the commit for web), so evidence survives SKIP_BUILD reruns but expires the moment the binary changes. Expired evidence still shows, dimmed, with the reason and its original date. The header now counts verified, carried, needing a rerun and never run separately, so a partial run cannot read as a full pass. Fixes the off-by-one that made the existing carry-forward pick a report two runs back, which pruning had usually deleted, so nothing was ever carried.
