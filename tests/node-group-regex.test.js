const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const root = path.join(__dirname, "..");
const normalizedNode = /^(?:AIRPORT|SELF)-/i;

function regionRegex(region) {
  return new RegExp(`^(?:AIRPORT|SELF)-${region}-`, "i");
}

function selfHostedRegex(region) {
  return new RegExp(`^SELF-${region}-`, "i");
}

test("forwarded server node is grouped only by its exit", () => {
  const node = "SELF-SG-VIA-HK2-SHOII-Zouter-v4-SS";

  assert.match(node, normalizedNode);
  assert.match(node, regionRegex("SG"));
  assert.doesNotMatch(node, regionRegex("HK"));
  assert.match(node, selfHostedRegex("SG"));
  assert.doesNotMatch(node, selfHostedRegex("HK"));
});

test("direct server node is grouped by its exit", () => {
  const node = "SELF-HK-DIRECT-SHOII-Zouter-HK2-v6";

  assert.match(node, regionRegex("HK"));
  assert.match(node, selfHostedRegex("HK"));
  assert.doesNotMatch(node, regionRegex("SG"));
});

test("airport node uses the same fixed exit field", () => {
  const node = "AIRPORT-HK-LINGYUN-01";

  assert.match(node, normalizedNode);
  assert.match(node, regionRegex("HK"));
  assert.doesNotMatch(node, selfHostedRegex("HK"));
});

test("unknown and historical names do not enter formal groups", () => {
  assert.doesNotMatch("AIRPORT-UN-NINJA-NewRegion", regionRegex("HK"));
  assert.doesNotMatch("HK-LightLayer-Self-hosted", normalizedNode);
  assert.doesNotMatch("BWG-US-01", normalizedNode);
});

test("Europe group accepts canonical German nodes and two legacy Shoii nodes", () => {
  const europe = /^(?:(?:AIRPORT|SELF)-DE-|Shoii-Zouter-HK2-v(?:4|6)-DE-SS$)/i;

  assert.match("SELF-DE-DIRECT-BRDE-01", europe);
  assert.match("Shoii-Zouter-HK2-v4-DE-SS", europe);
  assert.match("Shoii-Zouter-HK2-v6-DE-SS", europe);
  assert.doesNotMatch("Shoii-Zouter-HK2-v5-DE-SS", europe);
  assert.doesNotMatch("Shoii-Zouter-HK2-v4-SG-SS", europe);
});

test("client configs contain no chained-proxy groups", () => {
  const relay = fs.readFileSync(path.join(root, "relay.ini"), "utf8");
  const config = fs.readFileSync(path.join(root, "config.ini"), "utf8");

  assert.doesNotMatch(
    relay,
    /custom_proxy_group=(?:EXIT|TRANSIT|RELAY-CHAIN)/,
  );
  assert.doesNotMatch(relay, /\[\](?:EXIT|TRANSIT|RELAY-CHAIN)(?:`|$)/);
  assert.doesNotMatch(relay, /^\[rename_proxy\]$/m);
  assert.doesNotMatch(config, /custom_proxy_group=Vless/);
});

test("Clash and Loon filters accept canonical prefixes and explicit compatibility nodes", () => {
  const clash = fs.readFileSync(
    path.join(root, "template-clash-dialer-proxy.yaml"),
    "utf8",
  );
  const loon = fs.readFileSync(
    path.join(root, "template-loon-dialer-proxy.conf"),
    "utf8",
  );

  assert.match(clash, /filter: "\(\?i\)\(\^\(AIRPORT\|SELF\)-\|\^Shoii-Zouter-HK2-v\(4\|6\)-DE-SS\$\)"/);
  assert.match(clash, /filter: "\(\?i\)\^SELF-US-"/);
  assert.match(clash, /name: Europe/);
  assert.match(clash, /Shoii-Zouter-HK2-v\(4\|6\)-DE-SS/);
  assert.doesNotMatch(clash, /bwg\|bagevm\|self-hosted\|oracle/i);
  assert.match(loon, /FilterKey="\(\?i\)\(\^\(AIRPORT\|SELF\)-\|\^Shoii-Zouter-HK2-v\(4\|6\)-DE-SS\$\)"/);
  assert.match(loon, /Filter-Europe = NameRegex/);
  assert.match(loon, /Shoii-Zouter-HK2-v\(4\|6\)-DE-SS/);
  assert.doesNotMatch(loon, /bwg\|bagevm\|self-hosted\|oracle/i);
});

test("every selectable routing group offers Europe", () => {
  const clash = fs.readFileSync(
    path.join(root, "template-clash-dialer-proxy.yaml"),
    "utf8",
  );
  const loon = fs.readFileSync(
    path.join(root, "template-loon-dialer-proxy.conf"),
    "utf8",
  );
  const routingGroups = [
    "YouTube",
    "Telegram",
    "TelegramNL",
    "TelegramSG",
    "TelegramUS",
    "Streaming media",
    "AI",
    "Google",
    "Claude",
    "Gemini",
    "Grok",
    "Perplexity",
    "Social Media",
    "Media",
    "Scholar",
    "Longbridge",
    "Personal",
    "Personal-Direct",
    "CN Direct",
    "GFW",
    "Final",
  ];

  for (const group of [...routingGroups, "Games"]) {
    const start = clash.indexOf(`  - name: ${group}\n`);
    const end = clash.indexOf("\n  - name:", start + 1);
    const block = clash.slice(start, end === -1 ? undefined : end);

    assert.notEqual(start, -1, `missing Clash group ${group}`);
    assert.match(block, /^      - Europe$/m, `Clash group ${group}`);
  }

  for (const group of routingGroups) {
    const line = loon.match(new RegExp(`^${group} = select,.*$`, "m"));

    assert.ok(line, `missing Loon group ${group}`);
    assert.match(line[0], /(?:^|, )Europe(?:, |$)/, `Loon group ${group}`);
  }

  assert.match(clash, /  - name: Global Direct\n    type: select\n    proxies:\n      - DIRECT\n/);
  assert.match(loon, /^Global Direct = select, DIRECT,/m);
});

test("AI fallback follows dedicated providers and exposes all nodes", () => {
  const aiList = fs.readFileSync(path.join(root, "AI.list"), "utf8");
  const config = fs.readFileSync(path.join(root, "config.ini"), "utf8");
  const relay = fs.readFileSync(path.join(root, "relay.ini"), "utf8");
  const clash = fs.readFileSync(
    path.join(root, "template-clash-dialer-proxy.yaml"),
    "utf8",
  );
  const loon = fs.readFileSync(
    path.join(root, "template-loon-dialer-proxy.conf"),
    "utf8",
  );

  assert.match(aiList, /^DOMAIN-SUFFIX,opencode\.ai$/m);

  for (const source of [config, relay]) {
    const dedicated = source.indexOf("ruleset=Perplexity,");
    const fallback = source.indexOf("ruleset=AI,");
    const aiGroup = source.match(/^custom_proxy_group=AI.*$/m)?.[0] ?? "";

    assert.ok(dedicated !== -1 && dedicated < fallback);
    assert.match(aiGroup, /\[\]US/);
    assert.match(aiGroup, /\(\?i\)\^\(AIRPORT\|SELF\)-/);
  }

  const clashGroupStart = clash.indexOf("  - name: AI\n");
  const clashGroupEnd = clash.indexOf("\n  - name:", clashGroupStart + 1);
  const clashGroup = clash.slice(clashGroupStart, clashGroupEnd);
  const clashDedicated = clash.indexOf("  - RULE-SET,Perplexity,Perplexity");
  const clashFallback = clash.indexOf("  - RULE-SET,AI,AI");

  assert.notEqual(clashGroupStart, -1);
  assert.match(clashGroup, /^      - Self-Hosted-US$/m);
  assert.match(clashGroup, /^    use:\n      - ALL_PROVIDER$/m);
  assert.match(clash, /^  - DOMAIN-SUFFIX,opencode\.ai,AI$/m);
  assert.ok(clashDedicated !== -1 && clashDedicated < clashFallback);
  assert.doesNotMatch(clash, /name: ChatGPT|RULE-SET,OpenAI,ChatGPT/);

  const loonGroup = loon.match(/^AI = select,.*$/m)?.[0] ?? "";
  const loonDedicated = loon.indexOf("policy=Perplexity");
  const loonFallback = loon.indexOf("policy=AI, tag=AI");

  assert.match(loonGroup, /(?:^|, )Filter-All(?:, |$)/);
  assert.match(loon, /^DOMAIN-SUFFIX,opencode\.ai,AI$/m);
  assert.ok(loonDedicated !== -1 && loonDedicated < loonFallback);
  assert.doesNotMatch(loon, /^ChatGPT =|policy=ChatGPT/m);
});

test("full migration covers every Sub-Store subscription", () => {
  const migration = fs.readFileSync(
    path.join(root, "scripts", "substore-canonical-names.jq"),
    "utf8",
  );
  const mappings = migration.match(/set_rename\("/g) ?? [];
  const airportMappings = migration.match(/set_airport\("/g) ?? [];

  assert.equal(mappings.length + airportMappings.length, 31);
  assert.doesNotMatch(migration, /"now": "(?:EXIT|TRANSIT)-/);
  assert.match(migration, /Canonical metadata filter/);
  assert.equal(airportMappings.length, 4);
});
