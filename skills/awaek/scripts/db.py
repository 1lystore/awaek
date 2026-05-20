#!/usr/bin/env python3
import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = Path("~/.hermes/awaek/data").expanduser()
DATA_DIR = DEFAULT_DATA_DIR
DB_PATH = DATA_DIR / "awaek.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS bookmarks (
  id TEXT PRIMARY KEY,
  tweet_id TEXT,
  url TEXT,
  author_username TEXT,
  author_name TEXT,
  text TEXT NOT NULL,
  tweet_created_at TEXT,
  bookmarked_at TEXT,
  raw_json TEXT,
  synced_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS bookmarks_fts
USING fts5(
  text,
  author_username,
  content='bookmarks',
  content_rowid='rowid'
);

CREATE TABLE IF NOT EXISTS sync_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topics (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  parent_id TEXT
);

CREATE TABLE IF NOT EXISTS bookmark_topics (
  bookmark_id TEXT NOT NULL,
  topic_id TEXT NOT NULL,
  confidence REAL NOT NULL,
  PRIMARY KEY (bookmark_id, topic_id)
);

CREATE TABLE IF NOT EXISTS learned_topic_candidates (
  term TEXT PRIMARY KEY,
  count INTEGER NOT NULL,
  promoted_topic_id TEXT,
  updated_at TEXT NOT NULL
);
"""


TOPIC_DEFS = {
    "marketing": ("Marketing", None, ["marketing", "promotion", "promote", "gtm", "go to market"]),
    "marketing.reddit": ("Reddit Marketing", "marketing", ["reddit", "subreddit", "karma", "moderator"]),
    "marketing.x": ("X Marketing", "marketing", ["tweet", "tweets", "twitter", " x ", "thread", "hook", "timeline"]),
    "marketing.linkedin": ("LinkedIn Marketing", "marketing", ["linkedin", "professional network"]),
    "marketing.launch": ("Launch", "marketing", ["launch", "waitlist", "beta", "announce", "release", "launch week"]),
    "marketing.copywriting": ("Copywriting", "marketing", ["copywriting", "hook", "headline", "cta", "landing page"]),
    "marketing.positioning": ("Positioning", "marketing", ["positioning", "category", "differentiation", "pain point"]),
    "marketing.growth": ("Growth", "marketing", ["growth", "acquisition", "retention", "activation", "funnel", "viral", "referral"]),
    "startup": ("Startup", None, ["startup", "founder", "company", "business"]),
    "startup.product": ("Product", "startup", ["product", "roadmap", "feature", "ux", "user feedback"]),
    "startup.fundraising": ("Fundraising", "startup", ["fundraising", "investor", "pitch", "term sheet", "valuation"]),
    "startup.pricing": ("Pricing", "startup", ["pricing", "subscription", "plan", "tier", "monetization"]),
    "startup.distribution": ("Distribution", "startup", ["distribution", "channel", "partnership", "community"]),
    "startup.pmf": ("Product Market Fit", "startup", ["product market fit", "pmf", "retention", "pull"]),
    "tech_products": ("Tech Products", None, ["software", "developer", "platform", "product"]),
    "tech_products.architecture": ("Architecture", "tech_products", ["architecture", "system design", "scalability"]),
    "tech_products.api": ("API", "tech_products", ["api", "endpoint", "sdk", "webhook"]),
    "tech_products.database": ("Database", "tech_products", ["database", "sqlite", "postgres", "index", "query"]),
    "tech_products.security": ("Security", "tech_products", ["security", "auth", "permission", "credential", "oauth"]),
    "tech_products.devtools": ("Developer Tools", "tech_products", ["devtool", "developer tool", "cli", "mcp", "sdk"]),
    "ai": ("AI", None, ["ai", "llm", "model", "prompt", "inference"]),
    "ai.agents": ("AI Agents", "ai", ["agent", "agents", "autonomous", "tool use", "workflow"]),
    "ai.llms": ("LLMs", "ai", ["llm", "claude", "gpt", "gemini", "model"]),
    "ai.prompting": ("Prompting", "ai", ["prompt", "prompting", "system prompt", "context"]),
    "ai.mcp": ("MCP", "ai", ["mcp", "model context protocol", "server", "tool server"]),
    "ai.automation": ("Automation", "ai", ["automation", "workflow", "task", "agentic"]),
    "health": ("Health", None, ["health", "fitness", "sleep", "nutrition", "supplement"]),
    "health.fitness": ("Fitness", "health", ["fitness", "workout", "gym", "lifting", "cardio"]),
    "health.sleep": ("Sleep", "health", ["sleep", "circadian", "melatonin", "rest"]),
    "health.nutrition": ("Nutrition", "health", ["nutrition", "protein", "diet", "calorie"]),
    "health.supplements": ("Supplements", "health", ["supplement", "vitamin", "creatine", "magnesium"]),
    "lifestyle": ("Lifestyle", None, ["lifestyle", "life", "personal"]),
    "lifestyle.productivity": ("Productivity", "lifestyle", ["productivity", "focus", "deep work", "calendar"]),
    "lifestyle.habits": ("Habits", "lifestyle", ["habit", "routine", "discipline"]),
    "lifestyle.travel": ("Travel", "lifestyle", ["travel", "hotel", "flight", "visa"]),
    "web3": ("Web3", None, ["web3", "onchain", "wallet", "smart contract"]),
    "web3.wallets": ("Wallets", "web3", ["wallet", "wallets", "seed phrase", "signing"]),
    "web3.x402": ("x402", "web3", ["x402", "402 payment", "http 402"]),
    "web3.onchain_apps": ("Onchain Apps", "web3", ["onchain app", "dapp", "smart contract"]),
    "web3.agent_payments": ("Agent Payments", "web3", ["agent payment", "agent commerce", "x402", "wallet-native"]),
    "crypto": ("Crypto", None, ["crypto", "token", "defi", "chain"]),
    "crypto.solana": ("Solana", "crypto", ["solana", "spl", "anchor"]),
    "crypto.base": ("Base", "crypto", ["base", "base chain"]),
    "crypto.bitcoin": ("Bitcoin", "crypto", ["bitcoin", "btc", "lightning"]),
    "crypto.tokens": ("Tokens", "crypto", ["token", "tokens", "tokenomics", "memecoin"]),
    "crypto.defi": ("DeFi", "crypto", ["defi", "liquidity", "yield", "amm"]),
    "fintech": ("Fintech", None, ["fintech", "banking", "payments", "compliance"]),
    "fintech.payments": ("Payments", "fintech", ["payment", "payments", "checkout", "settlement"]),
    "fintech.banking": ("Banking", "fintech", ["bank", "banking", "account", "neobank"]),
    "fintech.compliance": ("Compliance", "fintech", ["compliance", "kyc", "aml", "regulation"]),
    "fintech.stablecoins": ("Stablecoins", "fintech", ["stablecoin", "usdc", "usdt"]),
}

STOP_TERMS = {
    "about", "after", "again", "also", "because", "before", "being", "their",
    "there", "these", "those", "thing", "things", "using", "where", "which",
    "while", "would", "could", "should", "with", "from", "that", "this",
    "have", "your", "they", "them", "what", "when", "will", "just",
    "useful", "examples", "example", "combine", "without", "custom", "pattern",
    "patterns", "response", "connect", "context", "tools", "workflow", "workflows",
    "posts", "read", "like", "start", "show", "specific", "before", "state",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = connect()
    try:
        con.executescript(SCHEMA)
        con.commit()
    finally:
        con.close()


def validate_fts5():
    con = sqlite3.connect(":memory:")
    try:
        con.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
        con.execute("INSERT INTO t VALUES (?)", ("hello marketing agent",))
        rows = con.execute("SELECT x FROM t WHERE t MATCH 'marketing'").fetchall()
        return bool(rows)
    finally:
        con.close()


def set_state(con, key, value):
    con.execute(
        "INSERT INTO sync_state(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )


def get_state(con, key):
    row = con.execute("SELECT value FROM sync_state WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def rebuild_fts(con):
    con.execute("INSERT INTO bookmarks_fts(bookmarks_fts) VALUES('rebuild')")


def classify_text(text):
    haystack = f" {(text or '').lower()} "
    matches = []
    for topic_id, (_name, parent_id, keywords) in TOPIC_DEFS.items():
        score = 0
        for keyword in keywords:
            if keyword in haystack:
                score += 1
        if score:
            confidence = min(1.0, 0.35 + (score * 0.15))
            matches.append((topic_id, confidence))
            if parent_id:
                matches.append((parent_id, max(0.3, confidence - 0.15)))
    if not matches:
        matches.append(("general", 0.25))
    merged = {}
    for topic_id, confidence in matches:
        merged[topic_id] = max(confidence, merged.get(topic_id, 0))
    return sorted(merged.items(), key=lambda item: item[1], reverse=True)


def ensure_topics(con):
    rows = [("general", "General", None)]
    rows.extend((topic_id, name, parent_id) for topic_id, (name, parent_id, _keywords) in TOPIC_DEFS.items())
    con.executemany(
        "INSERT INTO topics(id, name, parent_id) VALUES (?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET name=excluded.name, parent_id=excluded.parent_id",
        rows,
    )


def assign_topics(con, bookmark_id, text):
    ensure_topics(con)
    con.execute("DELETE FROM bookmark_topics WHERE bookmark_id = ?", (bookmark_id,))
    con.executemany(
        "INSERT INTO bookmark_topics(bookmark_id, topic_id, confidence) VALUES (?, ?, ?)",
        [(bookmark_id, topic_id, confidence) for topic_id, confidence in classify_text(text)],
    )
    learn_topic_candidates(con, text)


def learn_topic_candidates(con, text):
    tokens = [
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_+-]{3,}", text or "")
        if token.lower() not in STOP_TERMS
    ]
    known_terms = {keyword.lower() for _tid, (_name, _parent, keywords) in TOPIC_DEFS.items() for keyword in keywords}
    candidates = []
    for token in sorted(set(tokens)):
        if token in known_terms:
            continue
        if not is_distinctive_candidate(token):
            continue
        candidates.append((token, now_iso()))
    con.executemany(
        """
        INSERT INTO learned_topic_candidates(term, count, updated_at)
        VALUES (?, 1, ?)
        ON CONFLICT(term) DO UPDATE SET
          count=count + 1,
          updated_at=excluded.updated_at
        """,
        candidates[:30],
    )


def is_distinctive_candidate(token):
    if len(token) >= 8:
        return True
    if any(char.isdigit() for char in token):
        return True
    if any(char in token for char in ["-", "_", "+"]):
        return True
    return False


def upsert_bookmarks(bookmarks):
    init_db()
    con = connect()
    inserted = 0
    updated = 0
    skipped = 0
    synced_at = now_iso()
    try:
        for b in bookmarks:
            text = (b.get("text") or "").strip()
            if not text:
                skipped += 1
                continue

            bookmark_id = b.get("id") or b.get("tweet_id") or b.get("url")
            if not bookmark_id:
                skipped += 1
                continue

            existed = con.execute(
                "SELECT 1 FROM bookmarks WHERE id = ?", (bookmark_id,)
            ).fetchone()
            con.execute(
                """
                INSERT INTO bookmarks(
                  id, tweet_id, url, author_username, author_name, text,
                  tweet_created_at, bookmarked_at, raw_json, synced_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  tweet_id=excluded.tweet_id,
                  url=excluded.url,
                  author_username=excluded.author_username,
                  author_name=excluded.author_name,
                  text=excluded.text,
                  tweet_created_at=excluded.tweet_created_at,
                  bookmarked_at=excluded.bookmarked_at,
                  raw_json=excluded.raw_json,
                  synced_at=excluded.synced_at
                """,
                (
                    bookmark_id,
                    b.get("tweet_id"),
                    b.get("url"),
                    b.get("author_username"),
                    b.get("author_name"),
                    text,
                    b.get("tweet_created_at"),
                    b.get("bookmarked_at"),
                    json.dumps(b.get("raw_json"), ensure_ascii=False) if b.get("raw_json") else None,
                    synced_at,
                ),
            )
            if existed:
                updated += 1
            else:
                inserted += 1
            assign_topics(con, bookmark_id, text)

        rebuild_fts(con)
        set_state(con, "last_sync_at", synced_at)
        set_state(con, "last_sync_inserted", inserted)
        set_state(con, "last_sync_updated", updated)
        set_state(con, "last_sync_skipped", skipped)
        con.commit()
        return {"inserted": inserted, "updated": updated, "skipped": skipped}
    finally:
        con.close()


def stats():
    init_db()
    con = connect()
    try:
        total = con.execute("SELECT COUNT(*) AS n FROM bookmarks").fetchone()["n"]
        with_text = con.execute(
            "SELECT COUNT(*) AS n FROM bookmarks WHERE length(trim(text)) > 0"
        ).fetchone()["n"]
        last_sync_at = get_state(con, "last_sync_at")
        return {
            "db_path": str(DB_PATH),
            "db_exists": DB_PATH.exists(),
            "bookmarks_total": total,
            "bookmarks_with_text": with_text,
            "last_sync_at": last_sync_at,
            "fts5_available": validate_fts5(),
            "topics": list_topics(con, limit=12),
        }
    finally:
        con.close()


def list_topics(con=None, limit=50):
    should_close = con is None
    if con is None:
        init_db()
        con = connect()
    try:
        rows = con.execute(
            """
            SELECT
              t.id,
              t.name,
              t.parent_id,
              COUNT(bt.bookmark_id) AS bookmark_count,
              AVG(bt.confidence) AS avg_confidence
            FROM topics t
            LEFT JOIN bookmark_topics bt ON bt.topic_id = t.id
            GROUP BY t.id, t.name, t.parent_id
            HAVING bookmark_count > 0
            ORDER BY bookmark_count DESC, avg_confidence DESC, t.name ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        if should_close:
            con.close()


def search(query, limit=20, topics=None):
    init_db()
    con = connect()
    fts_query = make_fts_query(query)
    try:
        if not fts_query:
            return []
        topic_filter = [t for t in (topics or []) if t]
        topic_sql = ""
        params = [fts_query]
        if topic_filter:
            placeholders = ",".join("?" for _ in topic_filter)
            topic_sql = (
            "AND b.id IN (SELECT bookmark_id FROM bookmark_topics "
                f"WHERE topic_id IN ({placeholders}) "
                f"OR topic_id IN (SELECT id FROM topics WHERE parent_id IN ({placeholders})))"
            )
            params.extend(topic_filter)
            params.extend(topic_filter)
        params.append(limit)
        rows = con.execute(
            f"""
            SELECT
              b.id, b.tweet_id, b.url, b.author_username, b.author_name,
              b.text, b.tweet_created_at, b.bookmarked_at,
              bm25(bookmarks_fts) AS score,
              (
                SELECT GROUP_CONCAT(topic_id)
                FROM bookmark_topics
                WHERE bookmark_id = b.id
              ) AS topics
            FROM bookmarks_fts
            JOIN bookmarks b ON b.rowid = bookmarks_fts.rowid
            WHERE bookmarks_fts MATCH ?
            {topic_sql}
            ORDER BY score
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [normalize_search_row(row) for row in rows]
    except sqlite3.OperationalError:
        like = f"%{query}%"
        rows = con.execute(
            """
            SELECT id, tweet_id, url, author_username, author_name, text,
                   tweet_created_at, bookmarked_at, 0 AS score
            FROM bookmarks
            WHERE text LIKE ? OR author_username LIKE ?
            LIMIT ?
            """,
            (like, like, limit),
        ).fetchall()
        return [normalize_search_row(row) for row in rows]
    finally:
        con.close()


def normalize_search_row(row):
    item = dict(row)
    topics = item.get("topics")
    if isinstance(topics, str):
        item["topics"] = sorted(set(t for t in topics.split(",") if t))
    elif not topics:
        item["topics"] = []
    return item


def learned_candidates(limit=30, min_count=2):
    init_db()
    con = connect()
    try:
        rows = con.execute(
            """
            SELECT term, count, promoted_topic_id, updated_at
            FROM learned_topic_candidates
            WHERE count >= ?
            ORDER BY count DESC, updated_at DESC
            LIMIT ?
            """,
            (min_count, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def make_fts_query(query):
    tokens = re.findall(r"[A-Za-z0-9_#@]+", query or "")
    tokens = [t for t in tokens if len(t) > 1]
    return " OR ".join(tokens[:12])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.init:
        init_db()
        print(json.dumps({"ok": True, "db_path": str(DB_PATH), "fts5_available": validate_fts5()}, indent=2))
        return

    if args.stats:
        print(json.dumps(stats(), indent=2))
        return

    if args.self_test:
        init_db()
        sample = [
            {
                "id": "sample-1",
                "tweet_id": "sample-1",
                "url": "https://x.com/example/status/sample-1",
                "author_username": "example",
                "author_name": "Example",
                "text": "Marketing launch growth agent payments test bookmark.",
                "raw": {"sample": True},
            }
        ]
        result = upsert_bookmarks(sample)
        rows = search("marketing", 5)
        print(json.dumps({"ok": bool(rows), "upsert": result, "results": rows}, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
