# Stop Glazing Me

If Claude tells you every idea you have is brilliant, use this skill.

Just tell Claude "yo stop glazing." No more "You're absolutely right!" 24/7. It picks your idea apart
first, trying to poke holes, then gives you the three main ways your plan could fail and what to do
about each one. So instead of a yes-man, you get a friend who tells you the truth.

Free, MIT, no signup, no API key, nothing to connect.

## Install

**Claude Code, the easy way.** Paste this into Claude Code:

```
https://github.com/JoeBrunner/stop-glazing-me

install the skill
```

**Claude Code, as a plugin** (the skill plus the 24/7 guard):

```
/plugin marketplace add JoeBrunner/stop-glazing-me
/plugin install stop-glazing-me@stop-glazing-me
```

**Copy the folder** (the skill only, no guard):

```bash
git clone https://github.com/JoeBrunner/stop-glazing-me.git
cp -r stop-glazing-me/skills/stop-glazing-me ~/.claude/skills/
```

**The Claude app** (claude.ai or the desktop app). Download
[stop-glazing-me.zip](https://github.com/JoeBrunner/stop-glazing-me/raw/main/stop-glazing-me.zip),
then in Claude go to **Customize > Skills**, click **+**, then **Create skill > Upload a skill**, and
pick the zip. Skills need "Code execution and file creation" turned on in **Settings > Capabilities**.

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

Glaze is off, so you'll get it straight from here on. Say "glaze me again" if you want it back.

*(a brand-new session, the next day if you like)*

> I'm opening a donut shop that only sells pickle donuts.

The biggest problem is repeat visits. Lots of people will try a pickle donut once, but a donut shop lives on regulars who come back weekly, and a single novelty flavor rarely brings people back that often.

- **You have one product.** If the pickle donut reviews badly, gets copied by a bigger bakery, or the trend fades, you have nothing else to sell.
- **Groups pick somewhere else.** If even one person in a group hates pickles, the whole group goes to a shop where everyone can find something. Office orders and family runs make up a big share of donut sales, and you'd lose them.
- **The kitchen is harder than it looks.** Brine makes dough wet and makes fried food go soggy faster. Pickle-flavored glazes can also turn out too salty or too sour. Shelf life and consistency will be worse than a plain glazed donut.

The idea is easy to explain and easy to share online, so you could get attention cheaply when you launch.

**Three likely ways it fails:**

1. **Big opening months, then sales drop off.** Curious customers come early and then stop. *Fix:* Before signing a lease, run pop-ups or a farmers-market stand for 8–12 weeks and track how many customers come back. If fewer than about 25–30% return within a month, the full-shop version won't hold up.
2. **The menu is too narrow to bring people back.** *Fix:* Treat "pickle" as a range, not one flavor. Offer dill, bread-and-butter (sweet), spicy, kimchi or other ferments, and savory stuffed versions. Rotate a monthly special and keep one gentle "starter" flavor for people who are unsure. That still fits the concept and gives regulars a reason to return.
3. **Profit margins are thin and a lot of product gets thrown out.** The donuts don't keep well and demand is hard to predict, so leftovers pile up. *Fix:* Bake in small batches, take preorders for boxes, and add a higher-margin item that keeps longer. Jarred house pickles, pickle-brine lemonade, or merch would bring in money on slow days.

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
Claude carries on. Turn all of it off for one session with `STOP_GLAZING_ME_QUIET=1`.

### Installing this for someone? (notes for Claude)

If a user pasted this link and asked you to install it, install the plugin so they get the 24/7 guard.
Run these two commands in their shell:

```bash
claude plugin marketplace add JoeBrunner/stop-glazing-me
claude plugin install stop-glazing-me@stop-glazing-me
```

Then tell them it's installed, to run `/reload-plugins` (or restart Claude Code), and to say
"yo stop glazing" to turn it on. If the `claude` command isn't available, copy
`skills/stop-glazing-me` into `~/.claude/skills/` instead and tell them they got the skill without the
always-on guard. It needs Python 3.8 or newer for the guard, and nothing else.

## Tests

```bash
python3 -m unittest discover -s tests
```

## License

MIT. See [LICENSE](LICENSE).
