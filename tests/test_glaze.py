import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "glaze.py"
sys.path.insert(0, str(HOOK.parent))
sys.path.insert(0, str(ROOT))
from glaze import OFF, ON, STATUS, command_in, glaze_in  # noqa: E402

TURN_ON = [
    "yo stop glazing",
    "yo stop glazing bro",
    "Yo, stop glazing!!",
    "YO STOP GLAZING BRO",
    "stop glazing me",
    "Stop glazing me.",
    "quit glazing",
    "Quit glazing...",
    "stop glazing",
    "stop-glazing",
    "“yo stop glazing”",
    "yo stop glazing bro \U0001f369",
    "ok claude, stop glazing me please",
    "can you stop glazing",
    "dude quit glazing me fr",
    "don't glaze me",
    "no more glazing",
    "stop with the glazing",
    "yo stop glazing bro, I'm opening a donut shop that only sells pickle donuts",
    "I'm opening a donut shop that only sells pickle donuts. yo stop glazing",
    "/stop-glazing-me",
    "/stop-glazing-me:stop-glazing-me on",
]

TURN_OFF = [
    "glaze me again",
    "ok glaze me again",
    "OK, glaze me again!",
    "glaze me",
    "you can glaze me again",
    "go back to glazing me",
    "/stop-glazing-me off",
]

STATUS_CHECKS = [
    "glaze status",
    "Glaze status?",
    "am I getting glazed?",
    "are you still glazing me",
    "is glazing on?",
    "/stop-glazing-me status",
]

NOT_COMMANDS = [
    "how do I stop glazing from running on my pottery",
    "the donuts stop glazing evenly after an hour",
    "we should stop glazing the donuts by hand",
    "what does glazing mean in pottery",
    "I want to glaze my donuts again tomorrow",
    "plain donut, no glaze",
    "should we stop glazing?",
    "tell the night crew to stop glazing at 5",
    "write a function called stop_glazing",
    "fix the login bug",
    "",
    "   ",
]


class SwitchTest(unittest.TestCase):
    def test_on_phrases(self):
        for text in TURN_ON:
            with self.subTest(text=text):
                self.assertEqual(command_in(text), ON)

    def test_off_phrases(self):
        for text in TURN_OFF:
            with self.subTest(text=text):
                self.assertEqual(command_in(text), OFF)

    def test_status_phrases(self):
        for text in STATUS_CHECKS:
            with self.subTest(text=text):
                self.assertEqual(command_in(text), STATUS)

    def test_ordinary_messages_flip_nothing(self):
        for text in NOT_COMMANDS:
            with self.subTest(text=text):
                self.assertIsNone(command_in(text))

    def test_last_command_wins(self):
        self.assertEqual(command_in("glaze me again. jk, stop glazing"), ON)
        self.assertEqual(command_in("stop glazing. actually nvm, glaze me again"), OFF)

    def test_odd_input(self):
        for value in (None, 42, [], {}):
            with self.subTest(value=value):
                self.assertIsNone(command_in(value))


GLAZED = [
    "You're absolutely right! The function should return early.",
    "You’re absolutely right, I missed that.",
    "You are absolutely right.",
    "Great question! Pickle donuts are...",
    "Great question.",
    "What a great idea! Pickle donuts could be huge.",
    "What a fun concept. Let's dig in.",
    "Brilliant! Here's the plan.",
    "Love this! A pickle donut shop is bold.",
    "I love this idea.",
    "Excellent point, and here's why.",
    "This is genius.",
    "This is a brilliant idea, honestly.",
    "Ooh, I love where you're going with this.",
    "Oh wow, what a creative idea!",
    "Honestly? Great idea.",
    "**Great question!** Here's the answer.",
    "## Love this idea\n\nHere's my take.",
    "\U0001f369 Love it! Here's the thing.",
    "Perfect! I'll make that change.",
    "Absolutely! Here's how.",
    "You're onto something here.",
    "Great catch, fixed.",
    "That sounds great, but the rent is high.",
    "Thanks for sharing this! A few thoughts.",
    "Here's the plan.\n\nAnd you're absolutely right that rent matters.",
]

CLEAN = [
    "Nobody has ever searched for \"pickle donut.\" That's the first problem.",
    "Rent is the biggest hole. A donut shop needs 400 sales a day to break even.",
    "The bug is on line 12: the loop never ends.",
    "Right. Here's the fix.",
    "You're right that rent matters, but it isn't the biggest hole.",
    "This is a great way to lose $80,000.",
    "This blocks openers like \"You're absolutely right\" and \"Great question.\"",
    "> You're absolutely right!\n\nThat's the kind of reply this skill stops.",
    "```\nprint(\"Great question!\")\n```\nThat line prints a glazed string.",
    "The hook flags `You're absolutely right` at the top of a reply.",
    "Done. The tests pass.",
    "Great Clips is a chain, so check their pricing first.",
    "",
]


class GuardTest(unittest.TestCase):
    def test_glazed_openers_are_caught(self):
        for text in GLAZED:
            with self.subTest(text=text):
                self.assertIsNotNone(glaze_in(text))

    def test_honest_replies_quotes_and_code_pass(self):
        for text in CLEAN:
            with self.subTest(text=text):
                self.assertIsNone(glaze_in(text))

    def test_odd_input(self):
        for value in (None, 42, [], {}):
            with self.subTest(value=value):
                self.assertIsNone(glaze_in(value))


class HookTest(unittest.TestCase):
    """Runs the real script the way Claude Code does: JSON on stdin, a state file on disk."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.state = Path(self.dir) / "nested" / "state.json"

    def tearDown(self):
        shutil.rmtree(self.dir)

    def run_hook(self, kind, payload, env=None):
        if not isinstance(payload, str):
            payload = json.dumps(payload)
        return subprocess.run(
            [sys.executable, str(HOOK), kind],
            input=payload,
            capture_output=True,
            text=True,
            timeout=5,
            env={**os.environ, "STOP_GLAZING_ME_STATE": str(self.state), **(env or {})},
        )

    def prompt(self, text):
        return self.run_hook("prompt", {"hook_event_name": "UserPromptSubmit", "prompt": text})

    def context(self, out):
        self.assertEqual(out.returncode, 0)
        return json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"] if out.stdout else ""

    def test_off_by_default_and_silent(self):
        self.assertEqual(self.prompt("fix the login bug").stdout, "")
        self.assertEqual(self.run_hook("session", {"source": "startup"}).stdout, "")
        out = self.run_hook("stop", {"last_assistant_message": "Great question!", "stop_hook_active": False})
        self.assertEqual((out.returncode, out.stdout), (0, ""))

    def test_turn_on_then_every_message_gets_the_reminder(self):
        self.assertIn("now ON", self.context(self.prompt("yo stop glazing bro")))
        self.assertTrue(json.loads(self.state.read_text())["on"])
        reminder = self.context(self.prompt("I'm opening a donut shop that only sells pickle donuts"))
        self.assertIn("stop-glazing-me is ON", reminder)
        self.assertIn("three ways it could fail", reminder)

    def test_state_survives_into_new_sessions(self):
        self.prompt("stop glazing me")
        for source in ("startup", "resume", "clear", "compact"):
            with self.subTest(source=source):
                note = self.context(self.run_hook("session", {"hook_event_name": "SessionStart", "source": source}))
                self.assertIn("stop-glazing-me is ON", note)

    def test_off_switch(self):
        self.prompt("yo stop glazing")
        self.assertIn("now OFF", self.context(self.prompt("ok glaze me again")))
        self.assertFalse(json.loads(self.state.read_text())["on"])
        self.assertEqual(self.prompt("pitch me a donut").stdout, "")
        self.assertEqual(self.run_hook("session", {"source": "startup"}).stdout, "")

    def test_status_check(self):
        self.assertIn("OFF", self.context(self.prompt("glaze status")))
        self.prompt("quit glazing")
        self.assertIn("ON", self.context(self.prompt("am I getting glazed?")))

    def test_stop_guard_sends_glaze_back(self):
        self.prompt("yo stop glazing")
        out = self.run_hook("stop", {"last_assistant_message": "What a great idea! Pickle donuts...", "stop_hook_active": False})
        self.assertEqual(out.returncode, 0)
        verdict = json.loads(out.stdout)["hookSpecificOutput"]
        self.assertEqual(verdict["hookEventName"], "Stop")
        self.assertIn("What a great idea", verdict["additionalContext"])
        self.assertIn("Write the whole reply again", verdict["additionalContext"])

    def test_stop_guard_never_loops(self):
        self.prompt("yo stop glazing")
        out = self.run_hook("stop", {"last_assistant_message": "Great question!", "stop_hook_active": True})
        self.assertEqual((out.returncode, out.stdout), (0, ""))

    def test_stop_guard_lets_honest_replies_through(self):
        self.prompt("yo stop glazing")
        out = self.run_hook("stop", {"last_assistant_message": "Nobody searches for pickle donuts.", "stop_hook_active": False})
        self.assertEqual((out.returncode, out.stdout), (0, ""))

    def test_fails_open_on_bad_input(self):
        for kind in ("prompt", "session", "stop", "nonsense"):
            for payload in ("not json", "[]", "null", '{"prompt": 42}', '{"last_assistant_message": null}', ""):
                with self.subTest(kind=kind, payload=payload):
                    out = self.run_hook(kind, payload)
                    self.assertEqual((out.returncode, out.stdout), (0, ""))

    def test_fails_open_on_broken_state_file(self):
        self.state.parent.mkdir(parents=True)
        self.state.write_text("{broken")
        out = self.run_hook("stop", {"last_assistant_message": "Great question!"})
        self.assertEqual((out.returncode, out.stdout), (0, ""))
        self.assertIn("now ON", self.context(self.prompt("stop glazing")))

    def test_fails_open_when_state_cannot_be_written(self):
        blocker = Path(self.dir) / "file"
        blocker.write_text("x")
        out = self.run_hook("prompt", {"prompt": "stop glazing"}, env={"STOP_GLAZING_ME_STATE": str(blocker / "state.json")})
        self.assertEqual((out.returncode, out.stdout), (0, ""))

    def test_quiet_switch(self):
        out = self.run_hook("prompt", {"prompt": "stop glazing"}, env={"STOP_GLAZING_ME_QUIET": "1"})
        self.assertEqual(out.stdout, "")
        self.assertFalse(self.state.exists())


class PackageTest(unittest.TestCase):
    def test_hooks_json_points_at_real_script(self):
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
        for event, kind in (("UserPromptSubmit", "prompt"), ("SessionStart", "session"), ("Stop", "stop")):
            with self.subTest(event=event):
                hook = hooks[event][0]["hooks"][0]
                self.assertEqual(hook["command"], f'python3 "${{CLAUDE_PLUGIN_ROOT}}/hooks/glaze.py" {kind}')
                self.assertLessEqual(hook["timeout"], 5)

    def test_skill_frontmatter_fits_every_claude(self):
        text = (ROOT / "skills" / "stop-glazing-me" / "SKILL.md").read_text()
        self.assertTrue(text.startswith("---\nname: stop-glazing-me\ndescription: "))
        description = text.split("\n")[2][len("description: "):]
        self.assertLessEqual(len(description), 200)  # the Claude app's limit
        self.assertNotIn(": ", description)  # keeps the YAML valid
        self.assertNotIn("<", description)

    def test_plugin_manifests_parse(self):
        for name in ("plugin.json", "marketplace.json"):
            json.loads((ROOT / ".claude-plugin" / name).read_text())

    def test_claude_app_zip_matches_the_skill(self):
        import make_zip

        with zipfile.ZipFile(ROOT / "stop-glazing-me.zip") as z:
            names = z.namelist()
            self.assertEqual(names, ["stop-glazing-me/SKILL.md"])
            shipped = z.read("stop-glazing-me/SKILL.md")
        self.assertEqual(shipped, (ROOT / "skills" / "stop-glazing-me" / "SKILL.md").read_bytes(), "run make_zip.py")
        with tempfile.TemporaryDirectory() as tmp:
            fresh = make_zip.build(Path(tmp) / "x.zip")
            self.assertEqual(fresh.read_bytes(), (ROOT / "stop-glazing-me.zip").read_bytes(), "run make_zip.py")

    def test_claude_plugin_validate(self):
        if not shutil.which("claude"):
            self.skipTest("Claude Code is not installed")
        out = subprocess.run(["claude", "plugin", "validate", str(ROOT)], capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("Validation passed", out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
