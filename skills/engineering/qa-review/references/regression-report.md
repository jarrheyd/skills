# Regression report and failure classification

The report is the deliverable, and it should read like a regression test suite a
release manager can sign off from: every journey is a numbered test case with a
status, and every red is classified so a reader knows in one glance whether the
app is broken or the test is stale.

## Every flow is a test case

Render each flow in the manifest as one row of a regression matrix, not just a
filmstrip. A row carries:

- **ID**: stable, from the manifest (e.g. `FT-03`). Never renumber; a case keeps
  its ID for life so a human can refer to "FT-03 failed again".
- **Title**: what the journey proves, in plain words ("Zoom the whole tree out
  to the minimum without crashing").
- **Preconditions**: the state the case assumes (logged in as the test user, one
  family tree exists, on a fresh install). Name them so a reader can reproduce.
- **Steps**: the numbered user actions, read from the flow's own steps, in plain
  language, not raw YAML.
- **Expected**: what should happen at the end (and at each asserted checkpoint).
- **Actual**: what happened this run.
- **Status**: PASS / FAIL / BLOCKED / NOT RUN / CARRIED (see below).
- **Evidence**: the screenshots for this case, linked, newest run.
- **Classification** (only when not PASS): CRASH / DEFECT / FLOW-ROT / ENV (see
  the next section).

Above the matrix, a coverage summary: total cases, passed, failed by class, not
run, and the percentage of manifest journeys with at least one case. A journey
in the manifest with no flow is itself a NOT RUN row, so gaps are visible, never
silent.

Statuses:

- **PASS**: every step and assertion completed this run, on the build under test.
- **FAIL**: a step or assertion failed this run. Always carries a classification.
- **BLOCKED**: a precondition could not be met, so the case never reached its
  point (a prior case left the wrong state, a fixture was missing). Distinct from
  FAIL: the thing under test was never exercised.
- **NOT RUN**: selected out this run, or a manifest journey with no flow.
- **CARRIED**: not run this time, showing its last screenshots, still valid only
  while they match the build fingerprint and are under 7 days old (see the main
  carried-evidence rule). Counted separately from PASS.

## Classify every red

A red flow is not automatically an app bug. Before writing the verdict, put each
FAIL in exactly one class. This is the single most useful thing the report can
do, because it tells the reader whether to call an engineer or fix the test.

- **CRASH**: the app process died, the screen went white, or a red-box/native
  error appeared. Detect it, do not infer it: capture the app's running state and
  the OS crash log after a failed step (see "Capturing crashes" below). A crash
  is always a release blocker.
- **DEFECT**: the app stayed alive and on the right screen, but did the wrong
  thing (wrong data, a control that did nothing, a value that did not save, an
  error banner where there should be none). The app is at fault. Release blocker
  unless the owner defers it.
- **FLOW-ROT**: the app rendered the correct screen, but the flow could not find
  or reach an element because a selector, label, or layout changed since the flow
  was written. The test is at fault, not the app. Repair the flow, do not report
  it as an app failure. The tell: the failure is "element not visible / not
  found", and a screenshot of the moment shows the expected screen looking
  correct, or shows input that landed in the wrong field because a tap missed.
- **ENV**: the failure is the harness or the environment, not the app or the
  flow (the simulator driver wedged, the backend was down, a shared account was
  evicted). Name it so it is never counted against the app.

How to tell them apart, mechanically:

1. On any failed step, take a screenshot and read the app's process state and the
   current screen's element tree.
2. Process gone or a crash log written in the last minute -> CRASH.
3. App alive, screen is the one the step expected, element genuinely missing or
   changed -> FLOW-ROT.
4. App alive, screen is the one the step expected, element present but the app's
   behavior or data is wrong -> DEFECT.
5. Driver/backend error in the logs, app never got a fair run -> ENV.

The verdict never explains a red away in prose. A CRASH or DEFECT is NO-GO until
fixed. A FLOW-ROT is repaired and rerun before the verdict, so the final report
has no unclassified reds.

## Flow freshness (catch rot before it hides a bug)

Flow rot is dangerous because a stale flow can pass by luck or fail for the wrong
reason, and either way it stops testing what it claims to. Two habits keep flows
honest:

1. Update flows in the same change as the feature. When a screen gains, renames,
   or moves a field or a control, update its flows in that same change. A feature
   is not done until its flows still drive it. A flow that references a testID no
   longer in the code is a broken build, not a backlog item.
2. Run a freshness check each audit: cross-reference every selector a flow uses
   against the testIDs present in the current code. A selector with no match in
   code is rot. List it in `gaps.json` as `{ kind: "rot", flow, selector }` and
   repair it before the run counts, so a flow never fails later for a confusing
   reason.

## Clean state per case

A case's preconditions must actually hold at its start, or its result is noise.
Reset the shared state the suite depends on between cases that create data (a
family tree, a page, a circle), so case N never inherits case N-1's leftovers.
When a full reset is not possible, make each flow tolerant of pre-existing data
(open the existing item, or create with a unique name), and say in the case's
preconditions which it assumes. A case that fails only because a prior case
dirtied the state is BLOCKED, not FAIL, and points at suite hygiene, not the app.

## Capturing crashes and freezes

Happy-path taps rarely crash; edges do. So the suite earns its keep by capturing
crashes whenever they happen and by pushing on the edges:

- After every failed step, and at the end of every flow, pull the simulator's
  crash reports and the app's own console/red-box output into the run folder.
  Any crash log dated within the run is a CRASH row, wherever it happened.
- A freeze is a step that times out while the app is still foregrounded and
  unresponsive (the screen never changes across the timeout). Record it as a
  CRASH-class blocker named "freeze", distinct from a normal timeout where the
  app had simply moved on.
- Add edge and stress steps to the flows that matter: a control driven to its
  limit (zoom to the minimum and maximum), rapid repeated taps, opening a menu or
  picker while another sheet or the fullscreen viewer is already open (nested
  modals), backgrounding and returning mid-flow. These are where real crashes
  and dead controls live, and where source review and unit tests do not reach.

## Production-readiness line

End the report with one line a non-engineer can act on: READY or NOT READY, then
the count of open CRASH and DEFECT cases. READY only when there are zero open
CRASH and DEFECT cases and no BLOCKED case hiding an untested critical journey.
FLOW-ROT and ENV never block READY once repaired, but an unrepaired one means the
journey is untested, so the honest status there is NOT READY on that journey.
