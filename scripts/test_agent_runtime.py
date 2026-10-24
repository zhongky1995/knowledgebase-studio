#!/usr/bin/env python3
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import kb_agent_runtime as runtime


SCHEMA = {"type": "object", "properties": {"decision": {"type": "string"}},
          "required": ["decision"], "additionalProperties": False}


def events(identity="real-thread-123", extra=None):
    rows = [{"type": "thread.started", "thread_id": identity}, {"type": "turn.started"}]
    rows.extend(extra or [])
    rows += [{"type": "item.completed", "item": {"id": "item_1", "type": "agent_message",
                                                 "text": '{"decision":"needs_work"}'}},
             {"type": "turn.completed", "usage": {"input_tokens": 9, "output_tokens": 5}}]
    return rows


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "run"

    def run_fake(self, rows=None, returncode=0, timeout=False):
        rows = events() if rows is None else rows
        owner = self

        class Process:
            pid = 123456

            def __init__(self, argv, **kwargs):
                owner.command, owner.options = argv, kwargs
                self.returncode = returncode
                self.calls = 0
                owner.assertEqual(list(Path(kwargs["cwd"]).iterdir()), [])
                result = Path(argv[argv.index("--output-last-message") + 1])
                result.write_text('{"decision":"needs_work"}\n', encoding="utf-8")

            def communicate(self, data=None, timeout=None):
                self.calls += 1
                if self.calls == 1:
                    owner.assertEqual(data, "Reader-only material 中文".encode())
                    if timeout is not None and owner.timeout:
                        raise subprocess.TimeoutExpired(owner.command, timeout)
                return ("\n".join(json.dumps(row) for row in rows) + "\n").encode(), b"runtime diagnostic"

            def kill(self):
                self.returncode = -9

        self.timeout = timeout
        with patch.object(runtime, "_executable", return_value="/test/codex"), \
             patch.object(runtime.subprocess, "Popen", Process), patch.object(runtime.os, "killpg"):
            return runtime.run_agent("Reader-only material 中文", self.directory, SCHEMA, timeout=1)

    def rewrite_receipt_hashes(self):
        path = self.directory / "receipt.json"
        receipt = json.loads(path.read_text())
        receipt["fileSha256"] = {name: runtime._sha(self.directory / name) for name in runtime.FILES}
        runtime._write(path, receipt)

    def test_completed_is_runtime_success_not_semantic_pass(self):
        result = self.run_fake()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["output"], {"decision": "needs_work"})
        self.assertEqual(result["agentId"], "real-thread-123")
        self.assertEqual(runtime.validate_run(self.directory), result)
        self.assertNotIn("shell", self.options)
        self.assertNotIn("env", self.options)
        self.assertNotIn("resume", self.command)
        self.assertIn("--ephemeral", self.command)
        self.assertIn("--ignore-user-config", self.command)
        self.assertNotIn("--ignore-rules", self.command)
        self.assertEqual(set(p.name for p in self.directory.iterdir()), set(runtime.FILES) | {"receipt.json"})

    def test_nonzero_exit_rejected_despite_success_events(self):
        self.assertEqual(self.run_fake(returncode=1)["status"], "runtime_error")

    def test_timeout_logs_survive(self):
        result = self.run_fake(timeout=True)
        self.assertEqual(result["status"], "runtime_error")
        self.assertTrue((self.directory / "events.jsonl").read_text())
        self.assertIn("timed out", json.loads((self.directory / "receipt.json").read_text())["error"])

    def test_tools_rejected(self):
        result = self.run_fake(rows=events(extra=[{"type": "item.completed", "item": {
            "type": "command_execution", "command": "cat secret", "exit_code": 0}}]))
        self.assertEqual(result["status"], "runtime_error")

    def test_identity_required(self):
        self.assertEqual(self.run_fake(rows=events()[1:])["status"], "runtime_error")

    def test_multiple_identities_rejected(self):
        rows = events()
        rows.insert(1, {"type": "thread.started", "thread_id": "other"})
        self.assertEqual(self.run_fake(rows=rows)["status"], "runtime_error")

    def test_turn_completion_required(self):
        self.assertEqual(self.run_fake(rows=events()[:-1])["status"], "runtime_error")

    def test_multiple_final_messages_rejected(self):
        rows = events()
        rows.insert(-1, rows[-2])
        self.assertEqual(self.run_fake(rows=rows)["status"], "runtime_error")

    def test_conflicting_event_identity_rejected(self):
        rows = events()
        rows[-1]["thread_id"] = "different-thread"
        self.assertEqual(self.run_fake(rows=rows)["status"], "runtime_error")

    def test_result_tampering_rejected_even_with_renewed_hash(self):
        self.run_fake()
        (self.directory / "result.json").write_text('{"decision":"pass"}')
        self.rewrite_receipt_hashes()
        self.assertEqual(runtime.validate_run(self.directory)["status"], "runtime_error")

    def test_events_tampering_rejected(self):
        self.run_fake()
        with (self.directory / "events.jsonl").open("a") as handle:
            handle.write('{}\n')
        self.assertEqual(runtime.validate_run(self.directory)["status"], "runtime_error")

    def test_receipt_identity_not_authoritative(self):
        self.run_fake()
        path = self.directory / "receipt.json"
        receipt = json.loads(path.read_text())
        receipt["agentId"] = "invented-reviewer"
        runtime._write(path, receipt)
        self.assertEqual(runtime.validate_run(self.directory)["status"], "runtime_error")

    def test_resumed_invocation_rejected(self):
        self.run_fake()
        path = self.directory / "receipt.json"
        receipt = json.loads(path.read_text())
        receipt["invocation"]["argv"].insert(2, "resume")
        runtime._write(path, receipt)
        self.assertEqual(runtime.validate_run(self.directory)["status"], "runtime_error")

    def test_metadata_rebuilt_from_events(self):
        self.run_fake()
        path = self.directory / "receipt.json"
        receipt = json.loads(path.read_text())
        receipt["runtimeMetadata"]["model"] = "invented-model"
        runtime._write(path, receipt)
        self.assertEqual(runtime.validate_run(self.directory)["status"], "runtime_error")

    def test_old_evidence_cannot_be_overwritten(self):
        self.run_fake()
        self.assertEqual(runtime.run_agent("x", self.directory, SCHEMA)["status"], "runtime_error")

    def test_capability_probe_rejects_old_cli(self):
        with patch.object(runtime.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "old help", "")):
            with self.assertRaises(RuntimeError):
                runtime._executable("/legacy/codex")

    def test_failure_before_launch_still_records_files(self):
        with patch.object(runtime, "_executable", side_effect=RuntimeError("CLI unavailable")):
            result = runtime.run_agent("prompt", self.directory, SCHEMA)
        self.assertEqual(result["status"], "runtime_error")
        self.assertTrue((self.directory / "receipt.json").is_file())


if __name__ == "__main__":
    unittest.main()
