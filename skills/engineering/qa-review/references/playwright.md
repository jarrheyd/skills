# Playwright runner

For a web app whose tests are a Playwright suite. Playwright does the driving; qa-review files the results, builds the report and keeps the run history. Maestro and Java are not needed.

## Config

`qa-review.config.json` and `journeys.manifest.json` sit at the repo root (or in `.maestro/` if the repo has one).

```json
{
  "project": "acme-web",
  "platform": "web",
  "runner": "playwright",
  "url": "https://uat.example.com",
  "fingerprintCmd": "node scripts/deployed-build.mjs"
}
```

- `runner: "playwright"` switches both `qa-review-run.sh` and `qa-review-regression.sh`.
- `url` goes through `guard-env.sh` like any other target. Production is refused.
- `fingerprintCmd` is optional. It prints one id for the deployed build under test (a version endpoint, a commit). Without it the run has no fingerprint, so screenshots carried from an older run expire instead of counting green. The test repo's own commit is not used: it says nothing about what is deployed.

## Reporter

Add the reporter to the Playwright config. It reads the run dir from `QA_REVIEW_RUN_DIR`, which the runner sets.

```ts
reporter: [['list'], [`${process.env.HOME}/.claude/skills/qa-review/scripts/playwright-reporter.mjs`]],
```

What it writes:

| File | Meaning |
| --- | --- |
| `result-<flow>.xml` | One result per flow. Red if any check in the flow failed |
| `result-retry-<flow>.xml` | Only when a red flow went green on Playwright's retry. The report then says "Passed on retry" |
| `debug/playwright/<flow>/takeScreenshot/NNN-name.png` | Every PNG a test attached, in order |
| `debug/playwright/<flow>/screenshots/` | Playwright's own failure captures |
| `gaps.json` | Checks marked `test.fail()`, listed in the report as known defects |

## Flows

One flow per spec file: `tests/admin/invites.spec.ts` is the flow `admin-invites`. A spec that runs under several Playwright projects (one per role) becomes one flow per project, `access--client-hr`. To name a flow yourself, annotate the test: `test('...', { annotation: { type: 'flow', description: 'checkout' } }, ...)`.

The manifest `flow` values must match these ids. A flow in the results but not in the manifest still shows, under "Other flows".

A flow whose tests were all skipped gets no result. It reads as not run, never as passed.

## Screenshots

Attach a PNG where a human would want to look. The attachment name becomes the caption.

```ts
await testInfo.attach('01-ticket-list', { body: await page.screenshot(), contentType: 'image/png' });
```

## Running

```bash
scripts/qa-review-regression.sh --repo <path>          # full pass
scripts/qa-review-run.sh --repo <path> --tag smoke      # npx playwright test --grep @smoke
scripts/qa-review-run.sh --repo <path> --flows "tests/admin/invites.spec.ts"
```

The regression script skips the freshness check and the resume loop for this runner. A stale selector fails its spec, and Playwright does not wedge half-way the way a device driver does.

## Analytics

Maestro's rule still holds: test runs stay out of product analytics. With Playwright the suite can do it without an app change. Block the analytics hosts on every browser context:

```ts
await context.route(/googletagmanager\.com|google-analytics\.com|analytics\.google\.com/, (r) => r.abort());
```

## Known defects

Mark a check for an open, known bug with `test.fail(true, 'TICKET-123 short reason')`. The run stays green while the bug is open, the report lists it, and the check turns red the day the bug is fixed so the mark gets removed.
