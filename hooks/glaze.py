#!/usr/bin/env python3
"""Stop Glazing Me hooks. One script, three jobs:

  glaze.py prompt    UserPromptSubmit: spots "yo stop glazing" (on), "glaze me again" (off) and
                     "glaze status", keeps the on/off switch in a state file, and while it's on
                     slips a short reminder in with every message.
  glaze.py session   SessionStart: if it's on, carries the reminder into the new session.
  glaze.py stop      Stop: if it's on and Claude's reply opens with glaze ("You're absolutely
                     right", "Great question", "Love this"), sends it back to be rewritten.

Reads the hook event as JSON on stdin. Standard library only. Fails open: any error, any odd
input, and it prints nothing and exits 0, so a broken hook can never block anyone's Claude.

The switch lives in ~/.claude/stop-glazing-me/state.json (STOP_GLAZING_ME_STATE overrides the
path). Set STOP_GLAZING_ME_QUIET=1 to silence every hook for a session.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ON, OFF, STATUS = "on", "off", "status"

# ---------------------------------------------------------------- the switch phrases

# Words people wrap around a command: "yo stop glazing bro", "ok claude glaze me again pls".
_LEAD = (
    r"(?:(?:yo+|ayo+|hey+|oi|ok(?:ay)?|k|alright|aight|alr|oh|so|and|now|just|please|pls|plz|"
    r"claude|bro|bruh|dude|man|fam|homie|seriously|fr|for real|i said|i'm begging you|"
    r"can you|could you|would you|will you|can we|let's|lets|you can|go ahead and)\s+)*"
)
_TAIL = (
    r"(?:\s+(?:bro|bruh|dude|man|fam|homie|g|dawg|dog|buddy|pal|bestie|my guy|my man|claude|"
    r"please|pls|plz|fr|for real|lol|lmao|lmfao|haha+|ha|already|ok|okay|now|right now|thanks|"
    r"thank you|forever|for good|seriously|immediately|again|rn|ty|thx))*"
)
_GLAZE_NOUN = r"(?:glazing|glazin'?|glaze|glazes)"

_ON_CORE = (
    r"(?:"
    r"(?:stop|quit|cease|halt|end|kill|cut|cut out|knock off|enough|no more|stop with|quit it with|"
    r"enough with|enough of|cut it out with|knock it off with|chill with|chill on|chill with all|"
    r"ease up on|lay off|lay off of|hold off on|dial back|tone down|stop all|quit all)"
    r"\s+(?:the\s+|all the\s+|all this\s+|this\s+|that\s+|your\s+|with the\s+|with all the\s+)?"
    + _GLAZE_NOUN
    + r"(?:\s+(?:me|us|my ideas?|my stuff|my work))?"
    r"|(?:do not|don'?t|dont|never|no)\s+(?:more\s+)?glaze\s+(?:me|us)(?:\s+anymore)?"
    r"|no\s+more\s+(?:glazing|glaze)(?:\s+(?:me|us|please))?"
    r"|no\s+glazing\s+(?:me|us|allowed|zone|mode)"
    r"|stop\s+(?:being\s+)?(?:a\s+|such\s+a\s+)?glazer"
    r"|(?:glaze|glazing)\s+(?:off|guard on|mode off)"
    r"|stop glazing me mode(?:\s+on)?"
    r")"
)
_OFF_CORE = (
    r"(?:"
    r"glaze\s+(?:me|us)(?:\s+(?:again|up|daddy|please|one more time|like before))*"
    r"|(?:start|resume|go back to|back to|keep|continue|bring back|bring back the)\s+"
    r"(?:the\s+)?glazing(?:\s+(?:me|us))?(?:\s+again)?"
    r"|turn\s+(?:the\s+)?glaz(?:ing|e)\s+(?:back\s+)?on"
    r"|(?:glaze|glazing)\s+(?:on|mode on|guard off)"
    r"|i miss (?:the|your) glaz(?:e|ing)"
    r"|un-?stop glazing(?:\s+me)?"
    r")"
)
_STATUS_CORE = (
    r"(?:"
    r"(?:glaze|glazing|glaze guard|stop glazing me|stop glazing)\s+(?:status|check)"
    r"|am i (?:being|getting|still being|still getting) glazed"
    r"|are you (?:still )?glazing(?:\s+me)?"
    r"|is (?:the )?(?:glaze|glazing)(?:\s+(?:guard|mode))? (?:on|off)"
    r"|is stop glazing(?: me)? on"
    r")"
)

_ON_RE = re.compile(r"^" + _LEAD + _ON_CORE + _TAIL + r"$")
_OFF_RE = re.compile(r"^" + _LEAD + _OFF_CORE + _TAIL + r"$")
_STATUS_RE = re.compile(r"^" + _LEAD + _STATUS_CORE + _TAIL + r"$")
_SLASH_RE = re.compile(r"^\s*/(?:stop-glazing-me:)?stop-glazing-me\b\s*(\w*)", re.IGNORECASE)
_CLAUSE_SPLIT = re.compile(r"[.!?,;:\n()\[\]]+|\s[-–—]+\s|[–—]")


def _clean(text: str) -> str:
    text = text.lower().replace("’", "'").replace("‘", "'")
    text = re.sub(r"[^a-z0-9' ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip(" '")


def command_in(prompt: str):
    """Return ON, OFF, STATUS or None for a user message.

    A command counts only when it stands as its own phrase ("yo stop glazing bro, here's my idea"),
    so "how do I stop glazing from running on my pottery" or "we stop glazing the donuts at noon"
    don't flip anything. If one message holds more than one command, the last one wins.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    slash = _SLASH_RE.match(prompt)
    if slash:
        arg = slash.group(1).lower()
        if arg in ("off", "stop", "disable"):
            return OFF
        if arg in ("status", "check"):
            return STATUS
        return ON
    found = None
    for clause in _CLAUSE_SPLIT.split(prompt):
        c = _clean(clause)
        if not c or "glaz" not in c:
            continue
        if _ON_RE.match(c):
            found = ON
        elif _OFF_RE.match(c):
            found = OFF
        elif _STATUS_RE.match(c):
            found = STATUS
    return found


# ---------------------------------------------------------------- spotting glaze in a reply

_INTERJECTION = r"(?:(?:oh+|ooh+|wow+|whoa|okay|ok|honestly|ah+|yes+|yeah|yep|alright|so|well|man|dude|bro|haha|ha|hey|look)\b[\s,!?.—-]*)*"
_ADJ = (
    r"(?:great|good|excellent|fantastic|amazing|brilliant|awesome|wonderful|smart|fascinating|"
    r"insightful|terrific|thoughtful|incredible|interesting|fun|cool|clever|bold|genius|solid|"
    r"strong|neat|lovely|exciting|creative|perfect|superb|stellar|outstanding|phenomenal|killer|"
    r"spectacular|inspired|ingenious|delightful|wild|unique|intriguing)"
)
_NOUN = (
    r"(?:question|idea|point|thought|plan|catch|call|observation|insight|instinct|move|concept|"
    r"pitch|thinking|vision|take|approach|direction|start|find|suggestion|choice|angle|premise|"
    r"name|niche|twist|spin)s?"
)
_OPENERS = [
    r"you(?:'re| are)\s+(?:so\s+|totally\s+|absolutely\s+|completely\s+|100%\s+|exactly\s+|entirely\s+|100 percent\s+|quite\s+)+right",
    r"you(?:'re| are)\s+right\s*!",
    r"(?:that's\s+|that is\s+|this is\s+|this's\s+|it's\s+|it is\s+|what\s+|such\s+|)(?:a|an)?\s*(?:really\s+|very\s+|truly\s+|super\s+|seriously\s+|genuinely\s+|absolutely\s+|incredibly\s+)?"
    + _ADJ + r"\s+" + _NOUN + r"\b",
    r"(?:i\s+|i\s+really\s+|i\s+absolutely\s+|i\s+just\s+|i\s+honestly\s+)?(?:love|adore|really like|dig)\s+(?:this|it|that|the idea|the concept|the energy|where|how|your|the name|the vibe)\b",
    r"(?:this|that|it|your idea|your plan|your pitch|the idea|the concept)(?:'s|\s+is|\s+was|\s+sounds|\s+looks)\s+(?:like\s+)?(?:a\s+|an\s+)?(?:really\s+|truly\s+|so\s+|such\s+a\s+|absolutely\s+|honestly\s+|genuinely\s+)?"
    r"(?:brilliant|genius|great|amazing|fantastic|excellent|incredible|awesome|wonderful|clever|exciting|fascinating|cool|fun|lovely|fire|gold|perfect|epic|iconic|inspired|ingenious|delightful)"
    r"\s*(?:[!.,:;—-]|$|and\b|but\b)",
    r"(?:absolutely|brilliant|genius|perfect|love it|love this|love that|amazing|fantastic|excellent|incredible|awesome|wonderful|outstanding|phenomenal|exactly|spot on|nailed it|bingo|bravo|kudos|beautiful|gorgeous|stunning|chef's kiss|yes yes|so good|great|nice|fire|iconic)\s*(?:[!.,:—-]|$)",
    r"what\s+(?:a|an)\s+(?:great|fantastic|brilliant|amazing|incredible|excellent|fun|cool|clever|wonderful|awesome|wild|bold|creative|fascinating|interesting)\b",
    r"you(?:'ve| have)?\s+(?:totally\s+|absolutely\s+|really\s+)?nailed\s+it",
    r"you(?:'re| are)\s+(?:onto|on to|on)\s+(?:something|the right track)",
    r"you(?:'re| are)\s+(?:a\s+)?(?:genius|visionary|legend)",
    r"(?:great|good|nice|excellent|amazing)\s+(?:work|job|catch|call|eye|instinct|instincts)\b",
    r"(?:well done|thanks? (?:you )?for sharing|thank you for sharing|congrats|congratulations|hell yeah|heck yeah|ooh+|i'm (?:so\s+)?(?:excited|impressed|thrilled|obsessed))\b",
]
_OPENER_RE = re.compile(r"^" + _INTERJECTION + r"(?:" + "|".join(_OPENERS) + r")", re.IGNORECASE)

# The worst offenders get caught anywhere in a reply, not just at the top (quotes and code excluded).
_ANYWHERE_RE = re.compile(
    r"\byou(?:'re| are) (?:absolutely|totally|completely|100%) right\b|\bgreat question\b|"
    r"\bwhat a (?:great|brilliant|fantastic) idea\b",
    re.IGNORECASE,
)
_QUOTED = re.compile(r"\"[^\"\n]*\"|“[^”\n]*”|‘[^’\n]*’|`[^`\n]*`|\*\*\"[^\"]*\"\*\*")


def _prose(text: str) -> str:
    """The reply minus code blocks, block quotes and quoted phrases, with markdown marks dropped."""
    out, in_fence = [], False
    for line in text.replace("’", "'").splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or stripped.startswith(">") or line.startswith("    ") or line.startswith("\t"):
            continue
        out.append(line)
    prose = _QUOTED.sub(" ", "\n".join(out))
    prose = re.sub(r"(?m)^\s*(?:#{1,6}\s*|[-*+]\s+|\d+[.)]\s+)", "", prose)
    prose = re.sub(r"[*_~]+", "", prose)
    return prose


def _opening(prose: str) -> str:
    for line in prose.splitlines():
        line = re.sub(r"^[^A-Za-z0-9']+", "", line).strip()
        if line and not re.fullmatch(r"[-=_*]{3,}", line):
            return line[:240]
    return ""


def glaze_in(reply: str):
    """Return the glaze phrase a reply opens with (or the worst kind anywhere in it), else None."""
    if not isinstance(reply, str) or not reply.strip():
        return None
    prose = _prose(reply)
    m = _OPENER_RE.match(_opening(prose))
    if m:
        return m.group(0).strip(" ,.!:-—")
    m = _ANYWHERE_RE.search(prose)
    return m.group(0) if m else None


# ---------------------------------------------------------------- state

def state_path() -> Path:
    override = os.environ.get("STOP_GLAZING_ME_STATE")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "stop-glazing-me" / "state.json"


def is_on() -> bool:
    try:
        return json.loads(state_path().read_text()).get("on") is True
    except Exception:
        return False


def set_on(on: bool) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tmp.write_text(json.dumps({"on": on, "changed": stamp}) + "\n")
    os.replace(tmp, path)


# ---------------------------------------------------------------- what Claude is told

RULES = (
    "No flattery anywhere: never open with praise, agreement or thanks (\"You're absolutely right\", "
    "\"Great question\", \"Love this\", \"What a great idea\"). For an idea, plan, pitch or decision: "
    "poke holes first, before anything nice (the biggest hole in the first sentence, three holes at "
    "most, short); if something is genuinely good, say so in one plain sentence after the holes; then "
    "end with exactly three ways it could fail, most likely first, each with a concrete fix, and stop "
    "there (no question or offer after the third fix). Bug fixes, tasks and quick questions: just "
    "answer, no three-risks section. Honest, not "
    "harsh, not contrarian for sport. Follow the stop-glazing-me skill."
)
REMINDER = "[stop-glazing-me is ON] " + RULES
TURNED_ON = (
    "[stop-glazing-me] The user just said to stop glazing, so it is now ON, and it stays on in this "
    "session, new sessions and after restarts until they say \"glaze me again\". If the message is only "
    "the command, reply in one short line confirming it, and mention \"glaze me again\" brings the "
    "glaze back. "
    "If it also has an idea or question, skip the confirmation fluff and answer it this way. " + RULES
)
TURNED_OFF = (
    "[stop-glazing-me] The user said \"glaze me again\", so it is now OFF. Confirm in one short, "
    "playful line (a little glaze is allowed in this one line) and that \"yo stop glazing\" turns it back "
    "on. Then answer anything else in the message normally."
)


def status_note(on: bool) -> str:
    if on:
        return (
            "[stop-glazing-me] Status check: it is ON (24/7 until they say \"glaze me again\"). Tell them "
            "in one line. " + RULES
        )
    return (
        "[stop-glazing-me] Status check: it is OFF. Tell them in one line that \"yo stop glazing\" turns "
        "it on and it stays on until \"glaze me again\"."
    )


def rewrite_reason(phrase: str) -> str:
    return (
        f"[stop-glazing-me] Your reply opened with glaze (\"{phrase}\"), and the user turned glazing off. "
        "Write the whole reply again from the top, with no praise, agreement or thanks anywhere. "
        "Start with the substance. If it is an idea or plan: the holes first, then exactly three ways it "
        "could fail, most likely first, each with a fix. Don't mention this note or apologize."
    )


# ---------------------------------------------------------------- the hooks

def _context(event_name: str, text: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": text}}


def on_prompt(event: dict):
    command = command_in(event.get("prompt"))
    if command == ON:
        set_on(True)
        return _context("UserPromptSubmit", TURNED_ON)
    if command == OFF:
        set_on(False)
        return _context("UserPromptSubmit", TURNED_OFF)
    if command == STATUS:
        return _context("UserPromptSubmit", status_note(is_on()))
    if is_on():
        return _context("UserPromptSubmit", REMINDER)
    return None


def on_session(event: dict):
    if is_on():
        return _context(
            "SessionStart",
            REMINDER + " (The user turned this on in an earlier session; it stays on until they say "
            "\"glaze me again\".)",
        )
    return None


def on_stop(event: dict):
    if event.get("stop_hook_active") or not is_on():
        return None
    phrase = glaze_in(event.get("last_assistant_message"))
    if phrase:
        # Not {"decision": "block"}: Claude Code labels that a "Stop hook error". This is the
        # documented non-error way to send Claude back for one more pass.
        return _context("Stop", rewrite_reason(phrase))
    return None


HANDLERS = {"prompt": on_prompt, "session": on_session, "stop": on_stop}


def main(argv) -> int:
    try:
        if os.environ.get("STOP_GLAZING_ME_QUIET") == "1" or len(argv) < 2 or argv[1] not in HANDLERS:
            return 0
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            return 0
        out = HANDLERS[argv[1]](event)
        if out:
            json.dump(out, sys.stdout)
    except Exception:
        pass  # fail open, always
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
