#!/usr/bin/env python3
"""Convert remote rules in a Loon config to native lists (requires PyYAML)."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import ipaddress
from pathlib import Path
import re
from urllib.request import urlopen

import yaml


def convert_rules(text):
    """Return native rules and the number of omitted desktop process rules."""
    if re.search(r"^payload:\s*$", text, re.MULTILINE):
        payload = yaml.safe_load(text)["payload"]
        if not isinstance(payload, list):
            raise ValueError("payload must be a list")
    else:
        payload = [line.strip() for line in text.splitlines()
                   if line.strip() and not line.lstrip().startswith(("#", "//"))]
    result = []
    skipped = 0
    for entry in payload:
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError(f"Invalid rule: {entry!r}")
        entry = entry.strip()
        if "," not in entry:
            if "/" in entry:
                network = ipaddress.ip_network(entry, strict=False)
                entry = f"{'IP-CIDR' if network.version == 4 else 'IP-CIDR6'},{network}"
            else:
                suffix = entry.startswith("+.")
                domain = entry[2:] if suffix else entry
                if not re.fullmatch(r"[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*", domain):
                    raise ValueError(f"Unsupported domain pattern: {entry}")
                entry = f"{'DOMAIN-SUFFIX' if suffix else 'DOMAIN'},{domain}"
        kind, value = entry.split(",", 1)
        if kind == "PROCESS-NAME":
            skipped += 1
            continue
        if kind in ("IP-CIDR", "IP-CIDR6", "IP-ASN", "GEOIP"):
            fields = value.split(",")
            if len(fields) > 2 or (len(fields) == 2 and fields[1] != "no-resolve"):
                raise ValueError(f"Invalid IP rule options: {entry}")
            if kind in ("IP-CIDR", "IP-CIDR6"):
                network = ipaddress.ip_network(fields[0], strict=False)
                if network.version != (4 if kind == "IP-CIDR" else 6):
                    raise ValueError(f"Wrong IP address family: {entry}")
            elif kind == "IP-ASN" and not fields[0].isdigit():
                raise ValueError(f"Invalid ASN: {entry}")
        elif kind in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "USER-AGENT"):
            if not value or "," in value:
                raise ValueError(f"Invalid domain rule: {entry}")
        elif kind != "URL-REGEX" or not value:
            raise ValueError(f"Unsupported rule: {entry}")
        result.append(entry)
    return list(dict.fromkeys(result)), skipped


def remote_entries(config):
    section = ""
    source = None
    entries = []
    tags = set()
    for index, line in enumerate(config.splitlines()):
        if line.startswith("["):
            section = line
            source = None
        if section != "[Remote Rule]":
            continue
        if line.startswith("# source: "):
            source = line.removeprefix("# source: ").strip()
        elif line.startswith(("https://", "http://")):
            url, *options = [part.strip() for part in line.split(",")]
            options = dict(part.split("=", 1) for part in options)
            tag = options["tag"]
            if not re.fullmatch(r"[A-Za-z0-9_-]+", tag) or tag in tags:
                raise ValueError(f"Invalid or duplicate rule tag: {tag}")
            tags.add(tag)
            entries.append((index, source or url, options))
            source = None
    if not entries:
        raise ValueError("No remote rules found")
    return entries


def build(config, rules_dir, base_url, cache=None):
    entries = remote_entries(config)

    def download(entry):
        _, source, options = entry
        path = cache / hashlib.sha256(source.encode()).hexdigest() if cache else None
        if path and path.exists():
            data = path.read_text(encoding="utf-8-sig")
        else:
            with urlopen(source, timeout=60) as response:
                data = response.read().decode("utf-8-sig")
            if path:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(data, encoding="utf-8")
        rules, skipped = convert_rules(data)
        return entry, rules, skipped

    # Validate all inputs before writing any output.
    with ThreadPoolExecutor(max_workers=8) as pool:
        converted = list(pool.map(download, entries))
    rules_dir.mkdir(parents=True, exist_ok=True)
    replacements = {}
    lines = config.splitlines()
    counts = {}
    for (index, source, options), rules, skipped in converted:
        tag = options["tag"]
        if index and lines[index - 1].startswith("# source: "):
            replacements[index - 1] = None
        if not rules:
            replacements[index] = f"# Omitted empty rule set: {tag} ({source})"
            continue
        filename = tag + ".list"
        header = f"# Source: {source}\n# Rules: {len(rules)}\n"
        if skipped:
            header += f"# Omitted {skipped} PROCESS-NAME rules (not supported on iOS).\n"
        (rules_dir / filename).write_text(header + "\n".join(rules) + "\n", encoding="utf-8")
        options.pop("type", None)
        options.pop("parser-enabled", None)
        replacements[index] = (
            f"# source: {source}\n{base_url.rstrip('/')}/{filename}, "
            + ", ".join(f"{key}={value}" for key, value in options.items())
        )
        counts[tag] = len(rules)
    output = "\n".join(replacements.get(i, line) for i, line in enumerate(lines)
                       if replacements.get(i, line) is not None) + "\n"
    return output, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--rules-dir", required=True, type=Path)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    output, counts = build(args.config.read_text(encoding="utf-8"), args.rules_dir,
                           args.base_url, args.cache)
    args.output.write_text(output, encoding="utf-8")
    for tag, count in counts.items():
        print(f"{tag}: {count}")
    print(f"Total: {len(counts)} rule sets, {sum(counts.values())} rules")


if __name__ == "__main__":
    main()
