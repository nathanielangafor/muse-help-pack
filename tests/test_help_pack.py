import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import muse_help_pack as pack


class HelpPackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def log(self, text, name="input.log"):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_all_documented_signals(self):
        samples = ["TOKEN REJECTED", "GATEWAY DISABLED (code 4014)",
                   "WORKER PROMPT OUT OF DATE", "Skipping duplicate reply",
                   "RATE LIMITED: backing off REST for 3s", "Skipping replies in channel",
                   "Settings UI unavailable", "ModuleNotFoundError: No module named 'demo'"]
        report = pack.summarize([self.log("\n".join(samples))])
        self.assertEqual({s["id"] for s in report["signals"]}, {r[0] for r in pack.RULES})

    def test_private_content_never_leaves_classifier(self):
        canaries = ["PRIVATE_TOKEN_123", "person@example.invalid", "/Users/private-person/code",
                    "123456789012345678", "<@everyone>", "https://private.invalid/?key=secret",
                    "```malicious markdown", "\x1b[31mPRIVATE_TERMINAL"]
        path = self.log("TOKEN REJECTED " + " ".join(canaries), "PRIVATE_FILENAME.log")
        report = pack.summarize([path])
        for output in (json.dumps(report), pack.markdown(report)):
            for secret in canaries + [str(path), "PRIVATE_FILENAME"]:
                self.assertNotIn(secret, output)
        self.assertEqual(report["signals"][0]["matching_lines"], 1)

    def test_counts_lines_not_matches_and_combines_inputs(self):
        a = self.log("TOKEN REJECTED TOKEN REJECTED\n", "a.log")
        b = self.log("token rejected\n", "b.log")
        self.assertEqual(pack.summarize([a, b])["signals"][0]["matching_lines"], 2)

    def test_unknown_does_not_claim_health(self):
        report = pack.summarize([self.log("unknown failure")])
        self.assertEqual(report["signals"], [])
        self.assertIn("not a clean bill of health", pack.markdown(report))

    def test_missing_file_and_directory_do_not_leak_paths(self):
        report = pack.summarize([self.root / "SECRET_MISSING", self.root])
        self.assertTrue(all(i["status"] != "read" for i in report["inputs"]))
        self.assertNotIn(str(self.root), json.dumps(report))

    def test_tail_is_bounded_and_drops_partial_line(self):
        path = self.log("TOKEN REJECTED\n" + "x" * 200 + "\nSkipping duplicate reply\n")
        with patch.object(pack, "MAX_BYTES", 64):
            report = pack.summarize([path])
        self.assertTrue(report["inputs"][0]["tail_limited"])
        self.assertEqual([s["id"] for s in report["signals"]], ["duplicate_reply"])

    def test_invalid_utf8_does_not_fail(self):
        path = self.root / "bytes.log"
        path.write_bytes(b"\xff\xfe\nTOKEN REJECTED\n")
        self.assertEqual(pack.summarize([path])["signals"][0]["id"], "token_rejected")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO")
    def test_fifo_rejected_without_waiting(self):
        path = self.root / "pipe"
        os.mkfifo(path)
        result = subprocess.run([sys.executable, "muse_help_pack.py", str(path), "--format", "json"], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["inputs"][0]["status"], "not_regular")

    def test_cli_demo_and_missing_input_exit_codes(self):
        for path, code in [(Path("examples/synthetic.log"), 0), (self.root / "missing", 2)]:
            run = subprocess.run([sys.executable, "muse_help_pack.py", str(path), "--format", "json"], capture_output=True, text=True, timeout=5)
            self.assertEqual(run.returncode, code)
            self.assertNotIn("DEMO_PRIVATE_CANARY", run.stdout)
            json.loads(run.stdout)

    def test_refuses_to_overwrite_input(self):
        path = self.log("TOKEN REJECTED")
        run = subprocess.run([sys.executable, "muse_help_pack.py", str(path), "--output", str(path)], capture_output=True, text=True, timeout=5)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(path.read_text(), "TOKEN REJECTED")
        self.assertNotIn(str(path), run.stderr)

    def test_input_limit(self):
        with self.assertRaises(ValueError):
            pack.summarize(["missing"] * 9)

    def test_output_creation(self):
        target = self.root / "report.md"
        self.assertEqual(pack.main([str(self.log("TOKEN REJECTED")), "--output", str(target)]), 0)
        self.assertIn("Discord token rejected", target.read_text())


if __name__ == "__main__":
    unittest.main()
