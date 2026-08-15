#!/usr/bin/env python3

import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List only the generated node names for every Sub-Store subscription.",
    )
    parser.add_argument("config", type=Path, help="Path to sub-store.json")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:3000",
        help="Sub-Store backend URL",
    )
    parser.add_argument(
        "--collection",
        help="Audit one collection and print a validation summary",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Audit all subscriptions and print only validation totals and anomalies",
    )
    return parser.parse_args()


def generated_names(base_url: str, name: str, collection: bool = False) -> list[str]:
    import yaml

    encoded_name = quote(name, safe="")
    resource = f"collection/{encoded_name}" if collection else encoded_name
    request = Request(
        f"{base_url}/download/{resource}?target=ClashMeta",
        headers={"User-Agent": "sub-store-name-audit/1.0"},
    )
    with urlopen(request, timeout=30) as response:
        document = yaml.safe_load(response.read())

    proxies = document.get("proxies", []) if isinstance(document, dict) else []
    return [
        proxy["name"]
        for proxy in proxies
        if isinstance(proxy, dict) and isinstance(proxy.get("name"), str)
    ]


def collection_summary(names: list[str]) -> dict:
    counts = Counter(names)
    roles = Counter(name.split("-", 1)[0] for name in names)
    regions = Counter(
        parts[1]
        for name in names
        if len(parts := name.split("-", 2)) >= 2
    )

    return {
        "total": len(names),
        "roles": dict(sorted(roles.items())),
        "regions": dict(sorted(regions.items())),
        "unnormalized": [
            name
            for name in names
            if not name.startswith(("AIRPORT-", "SELF-"))
        ],
        "unknown": [
            name
            for name in names
            if name.startswith(("AIRPORT-UN-", "SELF-UN-"))
        ],
        "duplicates": [
            {"name": name, "count": count}
            for name, count in sorted(counts.items())
            if count > 1
        ],
    }


def main() -> None:
    args = parse_args()
    data = json.loads(args.config.read_text(encoding="utf-8"))

    if args.collection:
        names = generated_names(args.base_url, args.collection, collection=True)
        print(json.dumps(collection_summary(names), ensure_ascii=False, indent=2))
        return

    if args.summary:
        report = {
            "subscriptions": len(data.get("subs", [])),
            "available": 0,
            "totalNodes": 0,
            "errors": [],
            "unnormalized": [],
            "unknown": [],
            "duplicates": [],
        }
        for subscription in data.get("subs", []):
            name = subscription["name"]
            try:
                names = generated_names(args.base_url, name)
                summary = collection_summary(names)
                report["available"] += 1
                report["totalNodes"] += summary["total"]
                for field in ("unnormalized", "unknown", "duplicates"):
                    if summary[field]:
                        report[field].append(
                            {"subscription": name, "items": summary[field]},
                        )
            except Exception as error:
                report["errors"].append(
                    {"subscription": name, "error": str(error)},
                )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    for subscription in data.get("subs", []):
        name = subscription["name"]
        try:
            names = generated_names(args.base_url, name)
            result = {"subscription": name, "nodes": names}
        except Exception as error:
            result = {"subscription": name, "nodes": [], "error": str(error)}
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
