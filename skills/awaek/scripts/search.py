#!/usr/bin/env python3
import argparse
import json

import db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--topic", action="append", default=[])
    args = parser.parse_args()

    results = db.search(args.query, args.limit, topics=args.topic)
    print(json.dumps({"query": args.query, "topics": args.topic, "count": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    main()
