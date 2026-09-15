import json
import os
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DESLOP = os.path.join(ROOT, "skills", "writing", "deslop")
HOOK = os.path.join(DESLOP, "hooks", "copy_slop_hook.py")


def run(content, path="draft.md", tool="Write"):
    key = "content" if tool == "Write" else "new_string"
    payload = json.dumps({"tool_name": tool, "tool_input": {"file_path": path, key: content}})
    p = subprocess.run(["python3", HOOK], input=payload, capture_output=True, text=True)
    return p.returncode, p.stderr


BLOCKS = [
    ("fast-paced opener", "In today's fast-paced world we ship."),
    ("not-just reframe", "It's not just a tool. It's a revolution."),
    ("unlock", "Unlock the power of skills."),
    ("sycophancy", "Great question! Here is the answer."),
    ("candor opener", "Honestly, this is fine."),
    ("real talk", "Real talk. It works."),
    ("hits different", "This one hits different."),
    ("but make it", "Coffee but make it corporate."),
    ("came back", "It came back null."),
    ("operationalize", "We need to operationalize this."),
    ("question pile-up", "Top? Bottom? Both ends?"),
    ("negation ladder", "Not 95. Not 98. Fifty for fifty."),
    ("either-or", "Either it matches or it doesn't."),
    ("not only but also", "The build not only compiles but also passes every test."),
    ("hyphen title", "the-thing-that-quietly-broke story"),
    ("triple adjective", "It was specific, careful, deliberate."),
    ("studies show", "Studies show this works."),
    ("moves the needle", "This moves the needle."),
    ("testament", "It stands as a testament to grit."),
    ("chatbot outro", "I hope this helps with the launch."),
    ("tool remnant", "See :contentReference[oaicite:1] for detail."),
    ("serves as", "The file serves as the entry point."),
    ("em dash", "The report is done — mostly."),
    ("curly quote", "He said “fine” and left."),
    ("middot", "Jan · Jul · Dec"),
    ("title case heading", "# The Art Of The Deal"),
    ("heading with banned phrase", "# Unlock the power of skills"),
    ("explainer heading", "# The margin gap, and why it matters"),
    ("comma in short headline", "# One login, every tool"),
    ("comma appositive headline", "# Software, with patients"),
    ("staccato two-beat headline", "# Four rails. One job each."),
    ("staccato three-beat headline", "# Ship Monday. Test Tuesday."),
    ("bold-lead paragraph", "**Evidence boundary.** A timestamp confirms nothing."),
    ("restatement", "The invite button opens the native share sheet from the circle page. The invite button opens the native share sheet from the circle page."),
    ("filler transition", "Furthermore, the plan holds."),
    ("wordy", "We did this in order to ship."),
    ("elliptical setup", "The best part? you don't lift a finger."),
    ("elliptical setup capitalised", "Crazy thing? It actually worked."),
    ("suspense answer", "Scary truth? You're already behind."),
    ("suspense answer catch", "The catch? It costs nothing."),
    ("justifier", "Here's the thing. It works."),
    ("justifier truth is", "Truth is, it works."),
    ("revelation hook", "What nobody tells you about hiring."),
    ("revelation out loud", "The thing nobody says out loud."),
    ("revelation secret", "The secret to fast onboarding."),
    ("big reveal", "Here is what agents actually are."),
    ("overhype", "This changes everything for small teams."),
    ("will revolutionize", "This will revolutionize onboarding."),
    ("fast-changing world", "In a fast-changing world we ship."),
    ("dive into", "Let's dive into the numbers."),
    ("opposing shutdown", "You don't need more tools, you need a system."),
    ("philosophical reduction", "AI is not automating jobs, it's automating tasks."),
    ("reduction isnt", "This isn't a bug, it's a feature."),
    ("no x no y just z", "No meetings, no email, just work."),
    ("law of threes words", "Fast. Cheap. Done."),
    ("law of threes list", "It was fast, cheap, reliable."),
    ("three adjectives mid", "A specific, careful, deliberate plan."),
    ("emoji bullet", "🚀 Ship faster"),
    ("emoji list bullet", "- ✅ done"),
    ("uniform sentences", "We ship the build on Monday. We test the build on Tuesday. We fix the bugs on Wednesday. We review the fixes on Thursday."),
]

PASSES = [
    ("plain report", "The report lists every flow that ran. Three failed on login. Fix the selector and rerun."),
    ("parallel bullets", "- Sprint planning on Aug 20 covered the invite flow\n- Sprint review on Aug 22 covered the invite flow"),
    ("label colon line", "**Pending:** the signed SOW from the client."),
    ("comma in heading", "# Kindred invites, or how circles grow"),
    ("scope heading", "# Invites: what changed"),
    ("schedule not gloss", "# Migration, in three weeks"),
    ("single sentence heading with period", "# The platform team builds this first."),
    ("acronym heading with dotted initials", "# U.S. Trade Deal"),
    ("one furthermore mid-sentence", "The plan holds and furthermore covers the edge."),
    ("real question then answer", "Why did the build fail? The signing certificate expired on Tuesday, and nobody renewed it."),
    ("varied sentences", "We ship Monday. Testing runs Tuesday and Wednesday, with a fix window after. Review is Thursday."),
    ("three items with reason", "The three blockers are certificates, the missing OTP fixture, and the flaky login flow."),
    ("need with reason", "You need a staging account before the suite can log in."),
    ("not only alone", "Not only did the login fail. The signup crashed too."),
    ("emoji inside text", "Shipped the invite flow today 🎉 and the tests are green."),
]


class CopyHook(unittest.TestCase):
    def test_blocks(self):
        for name, text in BLOCKS:
            with self.subTest(name):
                code, err = run(text)
                self.assertEqual(code, 2, f"{name!r} should block; stderr: {err}")

    def test_passes(self):
        for name, text in PASSES:
            with self.subTest(name):
                code, err = run(text)
                self.assertEqual(code, 0, f"{name!r} should pass; stderr: {err}")

    def test_html_entity_only_decoded_for_html(self):
        self.assertEqual(run("done &mdash; mostly", path="a.md")[0], 0)
        self.assertEqual(run("done &mdash; mostly", path="a.html")[0], 2)

    def test_non_prose_files_skip(self):
        self.assertEqual(run("In today's fast-paced world", path="data.json")[0], 0)

    def test_source_string_literals_checked(self):
        src = 'const x = "In today\'s fast-paced world we ship faster";'
        self.assertEqual(run(src, path="app.ts")[0], 2)
        self.assertEqual(run("// In today's fast-paced world", path="app.ts")[0], 0)

    def test_edit_tool_checks_new_string(self):
        self.assertEqual(run("Unlock the power of X", tool="Edit")[0], 2)

    def test_bypass_env(self):
        payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "a.md", "content": "Great question!"}})
        env = dict(os.environ, DISABLE_ANTI_SLOP_HOOK="1")
        p = subprocess.run(["python3", HOOK], input=payload, capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0)

    def test_skip_paths_env(self):
        payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "/v/_ledger/x.md", "content": "Great question!"}})
        env = dict(os.environ, DESLOP_SKIP_PATHS="_ledger/")
        p = subprocess.run(["python3", HOOK], input=payload, capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0)

    def test_own_docs_pass_the_gate(self):
        docs = [
            os.path.join(DESLOP, "SKILL.md"),
            os.path.join(DESLOP, "README.md"),
            os.path.join(DESLOP, "agents", "slop-detector.md"),
            os.path.join(DESLOP, "agents", "copy-humanizer.md"),
        ]
        for skill in ("qa-review", "product-review"):
            base = os.path.join(ROOT, "skills", "engineering", skill)
            for dirpath, _, files in os.walk(base):
                for f in files:
                    if f.endswith(".md"):
                        docs.append(os.path.join(dirpath, f))
        docs.append(os.path.join(ROOT, "README.md"))
        docs.append(os.path.join(ROOT, "CLAUDE.md"))
        for d in docs:
            if not os.path.exists(d):
                continue
            with self.subTest(os.path.relpath(d, ROOT)):
                # A neutral path so the skip list cannot exempt the file.
                with open(d, encoding="utf-8") as fh:
                    text = fh.read()
                code, err = run(text, path="/check/" + os.path.basename(d))
                self.assertEqual(code, 0, err)


def run_send(tool, tool_input):
    payload = json.dumps({"tool_name": tool, "tool_input": tool_input})
    p = subprocess.run(["python3", HOOK], input=payload, capture_output=True, text=True)
    return p.returncode, p.stderr


class SendGate(unittest.TestCase):
    """Email, ticket, and chat sends never touch a file; the hook gates them by payload."""

    def test_chat_blocks_tells(self):
        self.assertEqual(run_send("mcp__Discord__send_message", {"message": "coming over — will ping"})[0], 2)
        self.assertEqual(run_send("mcp__discord__discord_send", {"message": "this is a robust solution"})[0], 2)

    def test_chat_allows_his_voice(self):
        for msg in ("coming. ill add them sa doc hahaha", "yes okay ra",
                    "few gaps ra. ill add the numbers sa doc later today ok"):
            with self.subTest(msg):
                self.assertEqual(run_send("mcp__Telegram__send_message", {"message": msg})[0], 0)

    def test_chat_skips_prose_shape_checks(self):
        # Four uniform short sentences trip the prose uniform-sentence check; chat must not run it.
        self.assertEqual(run_send("mcp__Discord__send_message", {"message": "ship monday. test tuesday. fix wednesday. review thursday."})[0], 0)

    def test_email_prose_blocks(self):
        # Opaque-hash connector, detected as mail by the payload shape (to + subject + body).
        self.assertEqual(run_send("mcp__abc123__send_message", {"to": "x@y.com", "subject": "update", "body": "Our comprehensive solution will help."})[0], 2)
        self.assertEqual(run_send("mcp__abc123__reply", {"threadId": "t", "body": "Thanks — files attached."})[0], 2)
        self.assertEqual(run_send("mcp__x__outlook_create_draft", {"to": "a@b.com", "subject": "x", "body": "In today's fast-paced world we ship."})[0], 2)

    def test_email_prose_allows_clean(self):
        self.assertEqual(run_send("mcp__x__outlook_create_draft", {"to": "a@b.com", "subject": "files", "body": "Hi team, the files are attached. Thanks, Jarrhey"})[0], 0)

    def test_ticket_comment_blocks_and_allows(self):
        self.assertEqual(run_send("mcp__jira-penbrothers__jira_add_comment", {"comment": "This leverages a cutting-edge approach."})[0], 2)
        self.assertEqual(run_send("mcp__h__addCommentToJiraIssue", {"commentBody": "Made the ID optional. If it is blank we skip the lookup."})[0], 0)

    def test_hard_ban_blocks_on_first_occurrence(self):
        # A single named banned word is below the density threshold but still blocks on a send.
        self.assertEqual(run_send("mcp__x__outlook_send_mail", {"to": "a@b.com", "subject": "s", "body": "A robust plan."})[0], 2)

    def test_non_send_mcp_ignored(self):
        self.assertEqual(run_send("mcp__Discord__read_channel", {"channel": "x"})[0], 0)


if __name__ == "__main__":
    unittest.main()
