---
name: awaek
description: "Personal source engine for saved X bookmarks: ask, draft, decide, and plan from the user's own saves."
version: 0.1.0
author: Iftakhar Rahmany
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [python3, xurl]
metadata:
  hermes:
    tags: [x, twitter, bookmarks, personal-ai, rag, productivity]
    category: productivity
    related_skills: [xurl]
---

# Awaek

Awaek turns saved X bookmarks into a local source engine for Hermes.

If the user says **Awaek**, asks about **my saves**, **my saved posts**, **my bookmarks**, or **saved X bookmarks**, use this skill.

Do not answer these requests from session memory alone.

Do not use `session_search` for Awaek requests unless the user explicitly asks for Hermes memory/session history.

For normal Awaek questions, run the local Awaek script first, then answer from the returned bookmark evidence.

## Hard Routing Rules

These rules override generic memory/search behavior.

If the user says any of these:

- "Awaek, what do my saves say about..."
- "Awaek, use my bookmarks..."
- "Awaek, draft..."
- "Awaek, decide..."
- "Awaek, plan..."
- "What do my saved X bookmarks say about..."
- "Use my saves..."

Run:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/answer_pack.py "<full user request>" --limit 30
```

Then use the returned `context` and `bookmarks` fields as the primary source for the answer.

If the user asks:

- "Awaek status"
- "Awaek, are you ready?"
- "How many bookmarks are indexed?"

Run:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/status.py
```

If the user asks:

- "Awaek topics"
- "Awaek scopes"
- "What am I saving?"

Run:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/list_scopes.py --learned
```

If the user asks:

- "Awaek find..."
- "Find my saved post about..."

Run:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/search.py "<query>" --limit 20
```

For any Awaek request, mention that the answer is based on saved X bookmarks. If no relevant bookmarks are found, say that clearly.

## When To Use

Use Awaek for:

- "What do my saves say about..."
- "Use my bookmarks to..."
- "Draft from my saved posts..."
- "Find the thing I saved about..."
- "Plan/decide based on what I bookmarked..."
- "What topics am I saving?"

Do not use Awaek for generic web research unless the user explicitly asks to combine saved bookmarks with outside knowledge.

Do not answer Awaek prompts by searching Hermes chat/session memory. Awaek has its own local bookmark database.

## Secret Safety

Awaek depends on `xurl` for X API access.

Never read, print, summarize, upload, or inspect `~/.xurl`. It contains app credentials and OAuth tokens.

Never ask the user to paste X Client IDs, Client Secrets, access tokens, refresh tokens, or the contents of `~/.xurl` into chat.

Do not run `xurl` with verbose/debug flags. Avoid commands that may expose headers or tokens.

The user must set up `xurl` credentials themselves outside the agent session. After setup, Awaek may run read-only bookmark commands through the local `xurl` CLI.

## Local Data

Awaek stores its SQLite library at `~/.hermes/awaek/data/awaek.db` by default.

## Quick Reference

```bash
# Check local Awaek state
python3 ${HERMES_SKILL_DIR}/scripts/status.py

# Import bookmark JSON returned by xurl
python3 ${HERMES_SKILL_DIR}/scripts/sync.py --source input --limit 100

# Show bookmark categories and learned candidate topics
python3 ${HERMES_SKILL_DIR}/scripts/list_scopes.py --learned

# Search saved bookmarks directly
python3 ${HERMES_SKILL_DIR}/scripts/search.py "reddit growth" --limit 20

# Build evidence for an ask/draft/plan/decision
python3 ${HERMES_SKILL_DIR}/scripts/answer_pack.py "Awaek request text" --limit 30
```

## First-Time Setup

First check readiness:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/setup.py
```

If `xurl` is missing, tell the user to install and configure it. Do not ask for secrets in chat.

User-side `xurl` setup:

```bash
xurl auth status
xurl whoami
```

If not authenticated, tell the user to follow the `xurl` skill's one-time setup. The important requirements are:

- X developer app with redirect URI `http://localhost:8080/callback`
- OAuth scopes that allow bookmark reads
- `xurl auth oauth2 --app <app-name>`
- `xurl auth default <app-name>`

After `xurl whoami` works, fetch the user's id:

```bash
xurl "/2/users/me?user.fields=username,name"
```

Then fetch bookmarks with that user id and pipe the JSON into Awaek:

```bash
xurl "/2/users/<user-id>/bookmarks?max_results=100&tweet.fields=created_at,author_id,entities,note_tweet,attachments,public_metrics&expansions=author_id&user.fields=username,name" | python3 ${HERMES_SKILL_DIR}/scripts/sync.py --source input --limit 100
python3 ${HERMES_SKILL_DIR}/scripts/status.py
```

If sync succeeds, respond:

```text
Awaek is ready.

I synced your X bookmarks and built your local library.

Try:
- Awaek, what do my saves say about marketing?
- Awaek, use my launch bookmarks to make a 30-day plan for my product.
- Awaek, draft 20 X posts using my saved growth posts.
- Awaek, show my bookmark topics.
```

## Core Workflow

For ask, draft, decide, and plan requests:

1. Run `answer_pack.py` with the full user request.
2. Read the returned `context`, `bookmarks`, `retrieval_queries`, and `retrieval_plan`.
3. Answer from the bookmark evidence first.
4. Cite or reference the saved posts that shaped the answer.
5. Say clearly if the saved evidence is thin, weak, or off-topic.
6. Use Hermes memory/style only after the bookmark evidence has been retrieved.

Default command:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/answer_pack.py "<full user request>" --limit 30
```

For broad requests, add focused queries instead of increasing context blindly:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/answer_pack.py "<full user request>" \
  --query "reddit growth subreddit launch" \
  --query "marketing positioning pain points" \
  --query "tweet hooks launch copywriting" \
  --limit 30
```

Use the returned `context` and `bookmarks` fields as the source material for the final answer.

Never skip this command for an Awaek ask/draft/decide/plan request.

## Canonical Patterns

### "Awaek status"

Run:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/status.py
```

If no bookmarks are indexed, tell the user to run setup/sync.

### "Awaek sync"

Run:

```bash
xurl "/2/users/me?user.fields=username,name"
xurl "/2/users/<user-id>/bookmarks?max_results=100&tweet.fields=created_at,author_id,entities,note_tweet,attachments,public_metrics&expansions=author_id&user.fields=username,name" | python3 ${HERMES_SKILL_DIR}/scripts/sync.py --source input --limit 100
python3 ${HERMES_SKILL_DIR}/scripts/status.py
```

Do not sync on every turn. Sync when the user asks, when no library exists, or when the library is stale and the user agrees.

### "Awaek scopes" / "What am I saving?"

Run:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/list_scopes.py --learned
```

Use this to show categories, subcategories, and emerging repeated terms.

### "Awaek find ..."

Run:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/search.py "<query>" --limit 20
```

Return matching saved posts with author, snippet, and URL. Do not synthesize unless the user asks.

### Ask / Draft / Decide / Plan

Run `answer_pack.py`, then synthesize from the returned evidence.

Do not use `session_search` as a substitute for `answer_pack.py`.

Examples:

- Ask: answer with themes and supporting saved posts.
- Draft: write the requested content using the evidence and the user's style if Hermes memory is available.
- Decide: present tradeoffs grounded in saved posts.
- Plan: sequence steps using the user's saved tactics and examples.

## Categories

Awaek organizes bookmarks into parent categories and subcategories.

Primary categories:

- `marketing`: Reddit, X, LinkedIn, launch, copywriting, positioning, growth
- `startup`: product, fundraising, pricing, distribution, product-market fit
- `tech_products`: architecture, APIs, databases, security, developer tools
- `ai`: agents, LLMs, prompting, MCP, automation
- `health`: fitness, sleep, nutrition, supplements
- `lifestyle`: productivity, habits, travel
- `web3`: wallets, x402, onchain apps, agent payments
- `crypto`: Solana, Base, Bitcoin, tokens, DeFi
- `fintech`: payments, banking, compliance, stablecoins

If the request is broad or ambiguous, inspect scopes first:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/list_scopes.py --learned
```

If one scope clearly dominates, route there. If multiple scopes fit, ask which angle to use or offer a combined answer.

## Evidence Rules

- Search the full local library.
- Retrieve the evidence needed for the current job, not a fixed number of random bookmarks.
- Do not send the whole database to the model.
- Do not include raw JSON in final answers.
- Do not claim the answer is bookmark-grounded when no relevant bookmarks were found.
- Prefer patterns across saved posts, with a few concrete citations.
- Use general model knowledge only to connect, structure, or explain the saved evidence.

Source priority:

1. Awaek bookmark evidence.
2. Hermes memory/style, if available.
3. General model knowledge only as support.

## Failure Modes

**`xurl` missing**

Tell the user:

```text
Awaek needs xurl before it can sync X bookmarks. Install xurl, authenticate it with your X developer app, then ask: Awaek sync.
```

**`xurl` not authenticated**

Tell the user:

```text
Awaek found xurl, but it is not authenticated yet. Run xurl auth status, then authenticate with xurl auth oauth2 --app <your-app> and xurl auth default <your-app>.
```

**Bookmark sync returns zero records**

Tell the user:

```text
Awaek reached X through xurl, but bookmark retrieval returned 0 records. This may be an X API permission, OAuth scope, rate-limit, or account issue.
```

**Bookmark records lack post text**

Tell the user:

```text
Awaek received bookmark records, but they did not include usable post text. I need post text before I can build a useful local library.
```

**Weak evidence**

Tell the user:

```text
I found only a few weak matches in your saved X bookmarks. I can still help, but this answer will rely partly on general reasoning unless you want me to broaden the search.
```

## Verification

After setup or sync:

```bash
python3 ${HERMES_SKILL_DIR}/scripts/status.py
python3 ${HERMES_SKILL_DIR}/scripts/list_scopes.py --learned
```

After any grounded answer:

- The response should mention saved-post evidence.
- The response should not invent sources.
- If no relevant bookmarks were found, the response should say so.
