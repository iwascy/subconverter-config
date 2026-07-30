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

test("Clash and Loon filters only accept canonical prefixes", () => {
  const clash = fs.readFileSync(
    path.join(root, "template-clash-dialer-proxy.yaml"),
    "utf8",
  );
  const loon = fs.readFileSync(
    path.join(root, "template-loon-dialer-proxy.conf"),
    "utf8",
  );

  assert.match(clash, /filter: "\(\?i\)\^\(AIRPORT\|SELF\)-"/);
  assert.match(clash, /filter: "\(\?i\)\^SELF-US-"/);
  assert.doesNotMatch(clash, /bwg\|bagevm\|self-hosted\|oracle/i);
  assert.match(loon, /FilterKey="\(\?i\)\^\(AIRPORT\|SELF\)-"/);
  assert.doesNotMatch(loon, /bwg\|bagevm\|self-hosted\|oracle/i);
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
