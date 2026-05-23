# Awaek

**Chat with your saved X bookmarks.**

Everyone saves good posts. Almost nobody uses them later. Awaek fixes that.

Awaek turns your saved X posts into a personal AI you can chat with — running locally inside Hermes Agent or OpenClaw. Ask questions, find old saves, draft content, compare ideas, or plan launches grounded in the links and posts you already curated.

No hosted backend. No pasted X secrets. Your bookmark library lives locally in SQLite.

```text
Awaek, what do my saves say about AI agents?
Awaek, use my launch bookmarks to make a 30-day plan.
Awaek, draft 5 X posts from my saved growth posts.
```

## Demo

Ask Awaek what it can do with your saved posts:

![Awaek examples in Hermes Telegram](img/whatIcandowithAwaek.png)

Ask for a quick read on what your saved posts are mostly about:

![Awaek summary of saved X posts](img/savedpost_Awaek.png)

## Why Awaek

Awaek gives your AI agent access to the ideas you already cared enough to save.

Use it to:

- answer questions from your own saved posts
- rediscover old bookmarks
- draft tweets, essays, and launch copy from your swipe file
- plan products, launches, and research from your curated examples
- understand what topics you keep saving
- build a private personal knowledge base from X

## What It Does

Awaek:

- answers questions using your saved posts as the source
- drafts tweets, threads, plans, and decisions grounded in your library
- surfaces old saves you forgot you had
- shows what topics you keep saving
- breaks long saved posts into searchable evidence chunks
- tells your agent when saved evidence is strong, weak, or missing
- learns repeated niche themes from your saves
- makes answers cite and follow your saved-post evidence

Under the hood, Awaek syncs via `xurl`, stores locally in SQLite, categorizes bookmarks, chunks long posts, tracks links from reputable domains, and builds evidence packs your AI agent can cite.

## Install

Ask Hermes:

```text
Install Awaek from 1lystore/awaek/skills/awaek and set it up for my saved X bookmarks.
```

You can send that in any Hermes chat: terminal, Telegram, Slack, Discord, or Open Web.

Ask OpenClaw:

```text
Install Awaek from git:1lystore/awaek and set it up for my saved X bookmarks.
```

Or install from terminal.

Hermes:

```bash
hermes skills install 1lystore/awaek/skills/awaek
```

OpenClaw:

```bash
openclaw skills install git:1lystore/awaek
```

Restart your agent session or run:

```text
/reset
```

Then ask:

```text
Awaek status
```

If no bookmarks are indexed yet, Awaek will tell you to run:

```text
Awaek sync
```

## Requirements

- Hermes Agent or OpenClaw
- Python 3
- `xurl` authenticated with an X account that can read bookmarks

`xurl` is the X API CLI Awaek uses to read saved X bookmarks through the official API.

OpenClaw ships an official `xurl` skill:

https://github.com/openclaw/openclaw/blob/main/skills/xurl/SKILL.md

If you use OpenClaw with Grok, set up the xAI provider here:

https://docs.openclaw.ai/providers/xai

For X bookmark sync, install and authenticate `xurl`. The Hermes + xurl setup flow is covered here:

https://x.com/XDevelopers/status/2056871280599847054

Install `xurl`:

```bash
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash
```

Check X authentication:

```bash
xurl auth status
xurl whoami
```

## Sync Bookmarks

In Hermes or OpenClaw, ask:

```text
Awaek sync
```

On sync, Awaek fetches saved X bookmarks page by page, stores them in SQLite, categorizes them, chunks long posts into searchable evidence, tracks links from safe domains, and builds the local search index.

Then try:

```text
Awaek, what do my saves say about marketing?
Awaek, show my bookmark topics.
Awaek, find my saved posts about business automation.
```

After setup, your agent reports how many bookmarks were indexed, how many searchable evidence chunks were created, which topics were found, and which repeated niche themes Awaek noticed.

## Privacy

Awaek is local-first. It stores your bookmark library locally.

- Bookmark data is stored at `~/.awaek/data/awaek.db` for new installs
- Existing Hermes installs may continue using `~/.hermes/awaek/data/awaek.db`
- No hosted backend
- No cloud database
- No pasted X secrets
- X auth stays with `xurl`

## Roadmap

- Sample mode for trying Awaek without X setup
- More saved-source connectors beyond X
- Richer writing and style workflows
- Optional link hydration for safe/reputable domains
