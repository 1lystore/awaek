#!/usr/bin/env python3
import argparse
import json

import db


DEFAULT_FINAL_LIMIT = 30
DEFAULT_PER_QUERY_LIMIT = 12


def trim_text(text, max_chars, collapse=True):
    text = text or ""
    if collapse:
        text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def compact_bookmark(item, max_chars):
    return {
        "id": item.get("id"),
        "tweet_id": item.get("tweet_id"),
        "url": item.get("url"),
        "author_username": item.get("author_username"),
        "author_name": item.get("author_name"),
        "text": trim_text(item.get("text"), max_chars),
        "tweet_created_at": item.get("tweet_created_at"),
        "topics": item.get("topics", []),
    }


def infer_queries(request):
    text = (request or "").lower()
    queries = [request]

    if any(term in text for term in ["promote", "promotion", "marketing", "launch", "growth", "go to market", "gtm"]):
        queries.extend(
            [
                "marketing launch growth positioning distribution",
                "product launch strategy audience pain points offer",
            ]
        )

    if any(term in text for term in ["tweet", "tweets", "x post", "twitter", "thread"]):
        queries.extend(
            [
                "tweet writing hooks thread copywriting X Twitter",
                "viral tweet examples hook CTA positioning",
            ]
        )

    if any(term in text for term in ["reddit", "subreddit", "reddit post"]):
        queries.extend(
            [
                "reddit growth subreddit comments community launch",
                "reddit post title comments pain points",
            ]
        )

    if any(term in text for term in ["decide", "decision", "choose", "should i", "compare"]):
        queries.append("decision framework tradeoffs pros cons")

    return dedupe_strings(queries)


def infer_topics(request):
    text = (request or "").lower()
    topics = []
    if any(term in text for term in ["promote", "promotion", "marketing", "go to market", "gtm"]):
        topics.append("marketing")
    if "launch" in text:
        topics.append("marketing.launch")
    if any(term in text for term in ["growth", "grow", "acquisition"]):
        topics.append("marketing.growth")
    if "reddit" in text or "subreddit" in text:
        topics.append("marketing.reddit")
    if any(term in text for term in ["tweet", "tweets", "twitter", "x post", "thread"]):
        topics.append("marketing.x")
    if "linkedin" in text:
        topics.append("marketing.linkedin")
    if any(term in text for term in ["agent", "automation"]):
        topics.append("ai.agents")
    if "mcp" in text or "model context protocol" in text:
        topics.append("ai.mcp")
    if any(term in text for term in ["payment", "x402", "wallet", "usdc"]):
        topics.extend(["fintech.payments", "web3.agent_payments"])
    if "base" in text:
        topics.append("crypto.base")
    if "solana" in text:
        topics.append("crypto.solana")
    if any(term in text for term in ["decide", "decision", "choose", "compare"]):
        topics.append("startup")
    return dedupe_strings(topics)


def dedupe_strings(values):
    seen = set()
    output = []
    for value in values:
        normalized = " ".join((value or "").split())
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    return output


def retrieve_for_queries(queries, per_query_limit, final_limit, topics=None):
    merged = {}
    plan = []

    for query in queries:
        rows = db.search(query, per_query_limit, topics=topics)
        scoped_count = len(rows)
        if topics and scoped_count == 0:
            rows = db.search(query, per_query_limit)
        plan.append(
            {
                "query": query,
                "topic_filtered": bool(topics),
                "scoped_matches": scoped_count,
                "matches": len(rows),
            }
        )
        for rank, row in enumerate(rows, 1):
            key = row.get("tweet_id") or row.get("url") or row.get("id")
            if not key:
                continue
            existing = merged.get(key)
            if existing is None:
                row = dict(row)
                row["_matched_queries"] = [query]
                row["_best_rank"] = rank
                merged[key] = row
            else:
                existing["_matched_queries"].append(query)
                existing["_best_rank"] = min(existing["_best_rank"], rank)

    results = list(merged.values())
    results.sort(
        key=lambda item: (
            -len(set(item.get("_matched_queries", []))),
            item.get("_best_rank", 999),
            item.get("score", 0),
        )
    )
    return results[:final_limit], plan


def make_context(results, max_bookmark_chars, max_context_chars):
    if not results:
        return "Awaek found no relevant saved X bookmarks for this query."

    blocks = []
    for i, item in enumerate(results, 1):
        author = item.get("author_username") or item.get("author_name") or "unknown"
        url = item.get("url") or item.get("tweet_id") or item.get("id")
        text = trim_text(item.get("text"), max_bookmark_chars)
        blocks.append(f"[{i}] @{author}\n{text}\nSource: {url}")
    context = "\n\n".join(blocks)
    return trim_text(context, max_context_chars, collapse=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("request")
    parser.add_argument("--query", action="append", default=[], help="Add a focused retrieval query. Can be repeated.")
    parser.add_argument("--topic", action="append", default=[], help="Restrict retrieval to a topic. Can be repeated.")
    parser.add_argument("--limit", type=int, default=DEFAULT_FINAL_LIMIT)
    parser.add_argument("--per-query-limit", type=int, default=DEFAULT_PER_QUERY_LIMIT)
    parser.add_argument("--max-bookmark-chars", type=int, default=1200)
    parser.add_argument("--max-context-chars", type=int, default=16000)
    parser.add_argument("--no-infer", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    queries = [args.request]
    if args.query:
        queries.extend(args.query)
    elif not args.no_infer:
        queries = infer_queries(args.request)
    queries = dedupe_strings(queries)
    topics = dedupe_strings(args.topic or infer_topics(args.request))

    results, plan = retrieve_for_queries(queries, args.per_query_limit, args.limit, topics=topics)
    compact_results = [compact_bookmark(item, args.max_bookmark_chars) for item in results]
    payload = {
        "request": args.request,
        "retrieval_queries": queries,
        "topic_filters": topics,
        "retrieval_plan": plan,
        "count": len(compact_results),
        "instruction": "Use these saved X bookmarks as the primary source. Prefer specific evidence from the returned bookmarks over generic advice. If the returned evidence is weak or off-topic, say so.",
        "context": make_context(compact_results, args.max_bookmark_chars, args.max_context_chars),
        "bookmarks": compact_results,
    }
    if args.pretty:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload, separators=(",", ":")))


if __name__ == "__main__":
    main()
