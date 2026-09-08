# Migrating a project off the old "scout" names

The skill used to call itself scout internally. It now uses one name, qa-review, with no fallback to the old one. A project set up before that rename needs four things moved. Do all four, or the next run cannot find its config.

## 1. Evidence root

Holds your `.env` credentials and every past run. Move it, do not recreate it: carry-forward reads the reports already in there.

```bash
mv ~/.scout ~/.qa-review
```

## 2. Config file, per repo

```bash
git mv .maestro/scout.config.json .maestro/qa-review.config.json
```

Every worktree of the same repo carries its own copy on its own branch, so each needs this. A branch that merges the rename later gets a conflict on that path; keep the renamed file.

## 3. Env keys in flows and .env

Only for projects whose keys use the old prefix. Check first:

```bash
grep -rl 'SCOUT_' .maestro
```

Then rename in both the flows and the credentials file:

```bash
grep -rl 'SCOUT_' .maestro | xargs perl -pi -e 's/\bSCOUT_/QA_REVIEW_/g'
perl -pi -e 's/\bSCOUT_/QA_REVIEW_/g' ~/.qa-review/<project>/.env
```

Projects whose `envKeys` were never prefixed (plain `PHONE`, `CIRCLE_NAME`) need nothing here; the runner passes every key through as written.

## 4. Your own shell

The control variables took the same prefix: `QA_REVIEW_SKIP_BUILD`, `QA_REVIEW_ALLOW_PROD`, `QA_REVIEW_NO_OPEN`, `QA_REVIEW_PER_FLOW`, `QA_REVIEW_KEEP_RUNS`, `QA_REVIEW_FLOW_TIMEOUT`, `QA_REVIEW_SUITE_TIMEOUT`, `QA_REVIEW_NO_RETRY`, `QA_REVIEW_OPEN_CMD`, `QA_REVIEW_PROJECT`. Update any alias or script that exported the old ones.

## Checking it worked

```bash
scripts/qa-review-run.sh --repo <repo> --flows "<one flow>"
```

A missing config fails immediately and says which path it wanted, so a half-finished migration cannot pass silently.
