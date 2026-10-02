// Playwright reporter that files a run the way the qa-review report reads it.
//
//   playwright.config: reporter: [['list'], ['<skill>/scripts/playwright-reporter.mjs']]
//   env QA_REVIEW_RUN_DIR: the run dir (qa-review-run.sh sets it)
//
// One flow per spec file. A spec that runs under several Playwright projects
// (one per role, say) becomes one flow per project: <spec>--<project>.
// A test can name its own flow with the annotation { type: 'flow', description: '<id>' }.
//
// Written into the run dir:
//   result-<flow>.xml                        one JUnit testcase, name = flow
//   result-retry-<flow>.xml                  only when a red flow went green on retry
//   debug/playwright/<flow>/takeScreenshot/  PNG attachments, in order, NN-name.png
//   debug/playwright/<flow>/screenshots/     Playwright's own failure captures
//   gaps.json                                expected failures (test.fail), for --gaps
//
// A flow whose tests were all skipped gets no result file, so it reads as
// "not run" instead of passed.
import fs from 'node:fs';
import path from 'node:path';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const slug = (s) => String(s).replace(/\.(spec|test)\.[cm]?[jt]sx?$/, '').replace(/[^A-Za-z0-9]+/g, '-').replace(/^-+|-+$/g, '').toLowerCase();
const stripAnsi = (s) => String(s || '').replace(/\u001b\[[0-9;]*m/g, '');

export default class QaReviewReporter {
  constructor(options = {}) {
    this.runDir = path.resolve(options.runDir || process.env.QA_REVIEW_RUN_DIR || 'qa-review-run');
    this.tests = [];
  }

  onBegin(config, suite) {
    this.rootDir = config.rootDir;
    // Which specs run under more than one project: those get a project suffix.
    const projectsPerFile = new Map();
    for (const t of suite.allTests()) {
      const set = projectsPerFile.get(t.location.file) || new Set();
      set.add(this.projectOf(t).name);
      projectsPerFile.set(t.location.file, set);
    }
    this.multiProject = new Set([...projectsPerFile].filter(([, set]) => set.size > 1).map(([file]) => file));
  }

  projectOf(test) {
    let s = test.parent;
    while (s) {
      const p = s.project && s.project();
      if (p) return { name: p.name || '', testDir: p.testDir };
      s = s.parent;
    }
    return { name: '', testDir: this.rootDir };
  }

  flowOf(test) {
    const named = (test.annotations || []).find((a) => a.type === 'flow' && a.description);
    if (named) return slug(named.description);
    const project = this.projectOf(test);
    const base = slug(path.relative(project.testDir || this.rootDir, test.location.file));
    return this.multiProject.has(test.location.file) && project.name ? `${base}--${slug(project.name)}` : base;
  }

  onTestEnd(test, result) {
    this.tests.push({ test, result });
  }

  onEnd() {
    fs.mkdirSync(this.runDir, { recursive: true });
    // Last attempt per test is the verdict; earlier attempts say whether it retried.
    const byTest = new Map();
    for (const { test, result } of this.tests) {
      const list = byTest.get(test) || [];
      list.push(result);
      byTest.set(test, list);
    }
    const flows = new Map();
    for (const [test, results] of byTest) {
      const id = this.flowOf(test);
      const flow = flows.get(id) || { tests: [] };
      flow.tests.push({ test, results: results.sort((a, b) => a.retry - b.retry) });
      flows.set(id, flow);
    }

    const known = [];
    for (const [id, flow] of flows) {
      const ran = flow.tests.filter(({ results }) => results[results.length - 1].status !== 'skipped');
      if (!ran.length) continue;
      const bad = (r, t) => r.status !== 'skipped' && r.status !== t.expectedStatus;
      const firstFails = ran.filter(({ test, results }) => bad(results[0], test));
      const finalFails = ran.filter(({ test, results }) => bad(results[results.length - 1], test));
      const seconds = ran.reduce((sum, { results }) => sum + results.reduce((a, r) => a + r.duration, 0), 0) / 1000;

      for (const { test, results } of ran) {
        const last = results[results.length - 1];
        if (test.expectedStatus === 'failed' && last.status === 'failed') {
          const why = (test.annotations || []).find((a) => a.type === 'fail' || a.type === 'issue');
          known.push({ area: id, kind: 'known defect', note: `${test.title}${why?.description ? `: ${why.description}` : ''}` });
        }
      }

      const failureText = (fails, attempt) => fails.map(({ test, results }) => {
        const r = attempt === 'first' ? results[0] : results[results.length - 1];
        const msg = stripAnsi(r.error?.message || r.errors?.[0]?.message || `status ${r.status}`).split('\n').slice(0, 6).join('\n');
        return `${test.title}: ${msg}`;
      }).join('\n\n');
      const junit = (fails, attempt) => {
        const body = fails.length
          ? `<failure message="${esc(`${fails.length} of ${ran.length} checks failed: ${fails[0].test.title}`)}">${esc(failureText(fails, attempt))}</failure>`
          : '';
        return `<?xml version="1.0"?><testsuites><testsuite name="playwright" tests="1" failures="${fails.length ? 1 : 0}">` +
          `<testcase id="${esc(id)}" name="${esc(id)}" time="${seconds.toFixed(3)}">${body}</testcase></testsuite></testsuites>\n`;
      };
      // Red first, green after a retry: both files, so the report says "Passed on retry".
      if (firstFails.length && !finalFails.length) {
        fs.writeFileSync(path.join(this.runDir, `result-${id}.xml`), junit(firstFails, 'first'));
        fs.writeFileSync(path.join(this.runDir, `result-retry-${id}.xml`), junit([], 'last'));
      } else {
        fs.writeFileSync(path.join(this.runDir, `result-${id}.xml`), junit(finalFails, 'last'));
      }

      // Screenshots: the last attempt of each test, in test order.
      const named = path.join(this.runDir, 'debug', 'playwright', id, 'takeScreenshot');
      const failed = path.join(this.runDir, 'debug', 'playwright', id, 'screenshots');
      let n = 0;
      for (const { test, results } of ran) {
        const last = results[results.length - 1];
        for (const a of last.attachments || []) {
          if (a.contentType !== 'image/png') continue;
          const auto = a.name === 'screenshot';
          const dir = auto ? failed : named;
          n += 1;
          const label = auto ? `FAILED-${slug(test.title)}` : slug(a.name);
          const file = path.join(dir, `${String(n).padStart(3, '0')}-${label.slice(0, 80)}.png`);
          fs.mkdirSync(dir, { recursive: true });
          if (a.body) fs.writeFileSync(file, a.body);
          else if (a.path && fs.existsSync(a.path)) fs.copyFileSync(a.path, file);
        }
      }
    }
    if (known.length) {
      fs.writeFileSync(path.join(this.runDir, 'gaps.json'), JSON.stringify({ title: 'Known defects', sub: 'Checks marked as expected to fail', items: known }, null, 2) + '\n');
    }
  }

  printsToStdio() {
    return false;
  }
}
