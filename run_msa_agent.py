from __future__ import annotations

import argparse
import json

from biomni_msa import MSAAgent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="User query")
    parser.add_argument(
        "--stream", action="store_true", help="Print stage messages while running"
    )
    parser.add_argument(
        "--no-trace", action="store_true", help="Hide messages from return payload"
    )
    args = parser.parse_args()

    agent = MSAAgent()
    result = agent.go(args.query, verbose=not args.no_trace, stream=args.stream)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
