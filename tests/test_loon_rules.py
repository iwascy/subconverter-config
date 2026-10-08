import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "converter", Path(__file__).resolve().parents[1] / "scripts/convert_loon_rules.py")
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class RuleConversionTests(unittest.TestCase):
    def test_domain_matching_scope(self):
        rules, _ = converter.convert_rules('payload:\n  - "+.example.com"\n  - exact.example.net\n')
        self.assertEqual(rules, ["DOMAIN-SUFFIX,example.com", "DOMAIN,exact.example.net"])

    def test_classical_rules_and_ios_filtering(self):
        rules, skipped = converter.convert_rules(
            "payload:\n  - DOMAIN-KEYWORD,google\n  - IP-CIDR,1.2.3.0/24,no-resolve\n"
            "  - IP-CIDR6,2001:db8::/32,no-resolve\n  - IP-ASN,123,no-resolve\n"
            "  - PROCESS-NAME,chrome.exe\n  - DOMAIN-KEYWORD,google\n")
        self.assertEqual(skipped, 1)
        self.assertEqual(rules, ["DOMAIN-KEYWORD,google", "IP-CIDR,1.2.3.0/24,no-resolve",
                                 "IP-CIDR6,2001:db8::/32,no-resolve", "IP-ASN,123,no-resolve"])

    def test_bare_ip_addresses(self):
        self.assertEqual(converter.convert_rules("payload:\n  - 1.2.3.0/24\n  - 2001:db8::/32\n")[0],
                         ["IP-CIDR,1.2.3.0/24", "IP-CIDR6,2001:db8::/32"])

    def test_comments_are_not_counted_as_rules(self):
        self.assertEqual(converter.convert_rules("# Add personal rules here\n\n"), ([], 0))

    def test_invalid_input_fails_instead_of_silently_losing_rules(self):
        for text in ("<html>error</html>", "payload:\n  - '*.example.com'\n",
                     "payload:\n  - PROCESS-PATH,/bin/test\n", "payload: {}\n"):
            with self.subTest(text=text), self.assertRaises((ValueError, TypeError)):
                converter.convert_rules(text)

    def test_config_preserves_policies_and_unrelated_sections(self):
        config = ("[Proxy]\nprivate-node = unchanged\n[Remote Rule]\n"
                  "https://example.org/input.yaml, policy=AI, tag=Test, enabled=true, type=domain\n"
                  "[MITM]\nenable = false\n")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / "cache"
            cache.mkdir()
            (cache / converter.hashlib.sha256(b"https://example.org/input.yaml").hexdigest()).write_text(
                "payload:\n  - DOMAIN,example.com\n")
            with patch.object(converter, "urlopen", side_effect=AssertionError("unexpected network")):
                output, counts = converter.build(config, root / "rules", "https://example.org/rules", cache)
                rebuilt, _ = converter.build(output, root / "rules", "https://example.org/rules", cache)
        self.assertEqual(counts, {"Test": 1})
        self.assertEqual(output, rebuilt)
        self.assertIn("policy=AI, tag=Test, enabled=true", output)
        self.assertNotIn("type=domain", output)
        self.assertEqual(config.split("[Remote Rule]")[0], output.split("[Remote Rule]")[0])
        self.assertEqual(config.split("[MITM]")[1], output.split("[MITM]")[1])


if __name__ == "__main__":
    unittest.main()
