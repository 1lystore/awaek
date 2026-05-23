---
name: awaek
description: Personal source engine for saved X bookmarks. Ask, draft, decide, and plan from saved posts using local evidence.
version: 0.1.0
author: Iftakhar Rahmany
homepage: https://github.com/1lystore/awaek
metadata: {"openclaw":{"homepage":"https://github.com/1lystore/awaek","requires":{"bins":["python3"]}}}
---

# Awaek

Awaek turns saved X bookmarks into a local source engine for OpenClaw.

Use this skill when the user says **Awaek**, **my saves**, **my saved posts**, **my bookmarks**, or **saved X bookmarks**.

Do not answer Awaek requests from OpenClaw memory alone. Retrieve local bookmark evidence first, then answer from that evidence.

## Safety

- Data stays local. New installs use `~/.awaek/data/awaek.db`; existing Hermes installs may keep using `~/.hermes/awaek/data/awaek.db`.
- X access is handled by the local `xurl` CLI.
- Never read, print, summarize, upload, or inspect `~/.xurl`.
- Never ask the user to paste X Client IDs, Client Secrets, access tokens, refresh tokens, or `~/.xurl` contents into chat.
- Do not run `xurl` with verbose/debug flags.
- Retrieve focused evidence only. Do not send the full database to the model.
- If saved evidence is weak or missing, say so plainly.

## Commands

Use `{baseDir}` as the installed OpenClaw skill directory. Awaek scripts live in `{baseDir}/skills/awaek/scripts`.

Status:

```bash
python3 {baseDir}/skills/awaek/scripts/status.py
```

Topics and learned themes:

```bash
python3 {baseDir}/skills/awaek/scripts/list_scopes.py --learned
```

Search saved posts:

```bash
python3 {baseDir}/skills/awaek/scripts/search.py "<query>" --limit 20
```

Safe-domain links from saves:

```bash
python3 {baseDir}/skills/awaek/scripts/links.py --stats
python3 {baseDir}/skills/awaek/scripts/links.py --status pending --limit 20
```

Evidence pack for ask, draft, decide, and plan:

```bash
python3 {baseDir}/skills/awaek/scripts/answer_pack.py --plan-stdin --limit 30 <<'JSON'
<strict retrieval plan JSON>
JSON
```

## Setup And Sync

When the user asks to install, set up, or sync Awaek:

```bash
python3 {baseDir}/skills/awaek/scripts/setup.py
xurl auth status
xurl whoami
```

If `xurl` is missing or unauthenticated, tell the user to complete one-time `xurl` setup outside chat. Do not ask for secrets. Requirements:

- X developer app with redirect URI `http://localhost:8080/callback`
- OAuth scopes that allow bookmark reads
- `xurl auth oauth2 --app <app-name>`
- `xurl auth default <app-name>`

After `xurl whoami` works:

```bash
xurl "/2/users/me?user.fields=username,name"
```

Fetch the first bookmark page:

```bash
xurl "/2/users/<user-id>/bookmarks?max_results=100&tweet.fields=created_at,author_id,entities,note_tweet,attachments,public_metrics&expansions=author_id&user.fields=username,name" | python3 {baseDir}/skills/awaek/scripts/sync.py --source input --limit 100
```

If `sync.py` returns `next_token`, fetch the next page:

```bash
xurl "/2/users/<user-id>/bookmarks?max_results=100&pagination_token=<next-token>&tweet.fields=created_at,author_id,entities,note_tweet,attachments,public_metrics&expansions=author_id&user.fields=username,name" | python3 {baseDir}/skills/awaek/scripts/sync.py --source input --limit 100
```

Repeat until `next_token` is null or missing. Do not sync every turn; sync when asked, when no library exists, or when the user agrees the library is stale.

After sync, run status and topics, then report bookmarks indexed, evidence chunks, top topics, learned themes, and 3-4 useful next prompts based on actual topics:

```bash
python3 {baseDir}/skills/awaek/scripts/status.py
python3 {baseDir}/skills/awaek/scripts/list_scopes.py --learned
```

## Ask, Draft, Decide, Plan

For answer/draft/plan/decision requests, create this retrieval plan first. This is planning only; do not answer yet.

```json
{
  "user_request": "Original user message exactly.",
  "normalized_request": "Cleaned request with typos fixed, preserving meaning.",
  "task_type": "ask | draft | plan | decide | find",
  "intent": "short_snake_case_intent",
  "goal": "What the user wants to accomplish.",
  "domain": "Main domain or topic.",
  "platforms": [],
  "entities": [],
  "must_match_terms": [],
  "needed_evidence": [],
  "avoid_evidence": [],
  "output_need": "answer | strategy | draft | comparison | checklist | search results",
  "topic_filters": []
}
```

Plan rules:

- Fix typos in `normalized_request`.
- Preserve product names, people, companies, platforms, protocols, and requested output.
- Use `must_match_terms` only when direct saved-post evidence is required.
- Put evidence types in `needed_evidence`; do not write the final answer there.
- Put likely wrong interpretations in `avoid_evidence`.
- Keep plans domain-general. Do not assume a fixed bookmark library or invent facts about the user's product.

Run `answer_pack.py --plan-stdin`, then answer from returned `context` and `bookmarks`.

Answer rules:

- Use saved-bookmark evidence first.
- Mention that the answer is based on saved X bookmarks.
- Cite or reference saved posts when useful.
- If `evidence_strength.level` is `weak`, say the saved evidence is thin.
- If `evidence_strength.level` is `none`, do not invent bookmark-backed claims. Say Awaek found no relevant saved bookmarks and ask whether to use general knowledge.
- Use OpenClaw memory or user style only after Awaek evidence has been retrieved.

## Direct Search

For "Awaek find..." requests:

```bash
python3 {baseDir}/skills/awaek/scripts/search.py "<query>" --limit 20
```

Return matching saved posts with author, snippet, and URL. Do not synthesize unless asked.

For person, company, role, or handle lookups, resolve obvious names/handles before searching. Search exact identifiers first: person name, handle, company, and topic words. If the user says "CEO/founder of <company>" and the person is known, include that person's name and handle. Do not replace an exact person/handle result with adjacent topic posts.

## Topic Inspection

For "Awaek topics", "Awaek scopes", "What am I saving?", or broad ambiguous requests:

```bash
python3 {baseDir}/skills/awaek/scripts/list_scopes.py --learned
```

Use categories, subcategories, and learned terms to scope the retrieval plan.

## Failure Handling

- Missing `xurl`: tell the user Awaek needs `xurl` before it can sync X bookmarks.
- Unauthenticated `xurl`: tell the user to run `xurl auth status`, authenticate with `xurl auth oauth2 --app <app-name>`, then set default with `xurl auth default <app-name>`.
- Zero bookmark records: say X returned 0 records and mention possible API permission, OAuth scope, rate-limit, or account issues.
- Records without text: say Awaek received records but not usable post text.
- No relevant evidence: say Awaek found no relevant saved X bookmarks for this request.
