# Stop Glazing Me

If Claude tells you every idea you have is brilliant, use this skill.

Just tell Claude "yo stop glazing." No more "You're absolutely right!" 24/7. It picks your idea apart
first, trying to poke holes, then gives you the three main ways your plan could fail and what to do
about each one. So instead of a yes-man, you get a friend who tells you the truth.

Free, MIT, no signup, no API key, nothing to connect.

## Install

**Claude Code.** Paste this into Claude Code:

```
https://github.com/JoeBrunner/stop-glazing-me

install the skill
```

Claude installs it as a plugin: the skill plus the little guard that keeps it on 24/7. Or run the
same two lines yourself in Claude Code:

```
/plugin marketplace add JoeBrunner/stop-glazing-me
/plugin install stop-glazing-me@stop-glazing-me
```

**The Claude app** (claude.ai or the desktop app). Download
[stop-glazing-me.zip](https://github.com/JoeBrunner/stop-glazing-me/raw/main/stop-glazing-me.zip),
then in Claude go to **Customize > Skills**, click **+**, then **Create skill > Upload a skill**, and
pick the zip. Skills need "Code execution and file creation" turned on in **Settings > Capabilities**.

**Just the skill file** (no guard), if that's how you like it:

```bash
git clone https://github.com/JoeBrunner/stop-glazing-me.git
cp -r stop-glazing-me/skills/stop-glazing-me ~/.claude/skills/
```

### Notes for Claude, if you're installing this for someone

Stop Glazing Me is one package: the skill and its hooks ship together as a Claude Code plugin. The
promise that it stays on in new sessions and after a restart is the hooks. The skill file alone can't
keep it. So when someone pastes this link and asks you to install the skill, install the plugin:

```bash
claude plugin marketplace add JoeBrunner/stop-glazing-me
claude plugin install stop-glazing-me@stop-glazing-me
```

What the hooks do, so you can check before you run anything: `hooks/glaze.py` is one file of
standard library Python. No network, no API key, no dependencies. It writes one file,
`~/.claude/stop-glazing-me/state.json`, which holds the on/off switch. Each hook times out in 5
seconds and fails open. Afterward, tell them what you installed, to run `/reload-plugins` (or restart
Claude Code), to say "yo stop glazing" to turn it on, and that
`claude plugin uninstall stop-glazing-me@stop-glazing-me` removes it. If the `claude` command isn't
available, copy `skills/stop-glazing-me` into `~/.claude/skills/` and tell them they got the skill
without the always-on guard.

### What you get where

| | Claude Code plugin | Claude app or copied folder |
|---|---|---|
| "yo stop glazing" turns it on | Yes | Yes |
| Holes first, then the 3 ways it fails, with fixes | Yes | Yes |
| Stays on in the whole chat | Yes | Yes |
| Stays on in new sessions and after a restart | Yes | No, say it again in each new chat |
| The guard that sends a glazed reply back to be rewritten | Yes | No |

The 24/7 part and the guard are hooks, and hooks only run in Claude Code.

## Use it

```
yo stop glazing
```

That's it. Caps, no caps, "yo stop glazing bro", "stop glazing me", "quit glazing", all work.

- **Turn it off:** `glaze me again`
- **Check it:** `glaze status`

Then pitch it your idea. It leads with the biggest hole, gives the rest of the holes (three at most),
says what's actually good in one plain sentence if anything is, and ends with exactly three ways the
plan fails, most likely first, each with a fix you could start this week.

It is honest, not a jerk. It won't invent problems to look tough, and a good idea gets called good,
once, plainly. Bug fixes and quick questions get a straight answer with no glaze and no forced
three-risks section.

## The pickle donut test

Real transcripts, word for word, from a fresh Claude Code session. Both full versions are in
[examples/pickle-donut.md](examples/pickle-donut.md).

**Without it:**

> I'm opening a donut shop that only sells pickle donuts.

That's a bold concept, and it has a better chance than it sounds. Pickle flavor has become a real
trend (pickle chips, pickle lemonade, pickle pizza) ... *(then four tips and a menu of ways to help)*

**With it:**

> yo stop glazing bro

Glaze is off, so from here on you get straight answers. Say "glaze me again" to turn it back on.

*(a brand-new session, the next day if you like)*

> I'm opening a donut shop that only sells pickle donuts.

The biggest problem is repeat business. Most people will try a pickle donut once for the novelty and the photo, and a donut shop needs regulars who come back weekly. Pickle-only also lets one person in a group veto the stop: if one of four friends hates pickles, the whole group goes somewhere else. And the theme is easy to copy. Any existing bakery can add a pickle donut as a limited special and take your novelty traffic without giving up its main business.

What it has going for it is a strong, memorable identity that's easy to market. Pickle fans are vocal and share things online, so you'll get free attention at launch.

Three ways it could fail, most likely first:

1. **Sales drop sharply after the launch buzz.** Months 1–3 look great, then foot traffic falls off. *Fix:* Treat "pickle" as a broad range, not one flavor. Rotate sweet-leaning options (dill sugar, bread-and-butter glaze, pickle-brine lemonade glaze) and savory ones (pickle and cream cheese, a Cuban-style donut sandwich), and launch a new one every 2–4 weeks so regulars have a reason to come back.

2. **Customers who don't like pickles can't buy anything.** You lose groups, office orders and parents with kids. *Fix:* Keep one mild "gateway" donut where pickle is barely there, plus coffee and a non-pickle drink. You can stay pickle-only in spirit without turning away a third of your customers.

3. **The donuts aren't consistent or don't keep well.** Brine adds moisture and acid, which can make dough gummy and glaze weep, and that's a problem for wholesale or anything sitting in a case. *Fix:* Test recipes and shelf life before signing a lease. Measure texture at 0, 4 and 8 hours, and use pickle powder or reduced brine instead of raw brine where it holds up better.

## How the guard works

Three small hooks, one Python file, standard library only:

1. **The switch.** Every message you send gets checked for "stop glazing" and "glaze me again". The
   switch is saved in `~/.claude/stop-glazing-me/state.json`, so it survives new sessions and restarts.
   It only counts the phrase when it stands on its own, so "how do I stop glazing from running on my
   pottery" won't flip anything.
2. **The reminder.** While it's on, a short reminder rides along with every message and every new
   session, so Claude can't drift back into hype-man mode 40 messages in.
3. **The guard.** Before Claude finishes, the guard reads the reply. If it opens with glaze ("You're
   absolutely right", "Great question", "What a great idea", "Love this" and dozens of cousins),
   Claude has to write it again. Quotes and code that merely contain the words don't count, and it
   never asks twice, so it can't loop.

Every hook times out in 5 seconds and fails open: if anything goes wrong, it does nothing and your
Claude carries on. It needs Python 3.8 or newer and nothing else. Turn all of it off for one session
with `STOP_GLAZING_ME_QUIET=1`.

## Tests

```bash
python3 -m unittest discover -s tests
```

## License

MIT. See [LICENSE](LICENSE).
