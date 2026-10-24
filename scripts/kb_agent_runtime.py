#!/usr/bin/env python3
"""Fresh, tool-free Codex runs with replayable evidence, not an OS read barrier.

User provider/model config is not loaded; existing auth and CLI defaults remain.
Execpolicy rules are preserved. Receipts are not signatures against an attacker who
can rewrite the runner and every evidence file under the same local account.
"""

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path


FILES = ("prompt.txt", "schema.json", "events.jsonl", "stderr.txt", "result.json")
REQUIRED_FLAGS = ("--ephemeral", "--ignore-user-config", "--output-schema", "--output-last-message", "--json")
DISABLED = ("shell_tool", "unified_exec", "apps", "browser_use", "browser_use_external",
            "computer_use", "memories", "plugins", "hooks", "multi_agent", "skill_search",
            "image_generation", "view_image", "in_app_browser")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(text):
    return json.loads(text, object_pairs_hook=_object)


def _executable(explicit=None):
    candidates = [str(explicit)] if explicit else [shutil.which("codex")]
    if not explicit and sys.platform == "darwin":
        candidates += ["/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex",
                       str(Path.home() / "Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex")]
    failures = []
    for candidate in dict.fromkeys(value for value in candidates if value):
        resolved = shutil.which(candidate) or candidate
        try:
            probe = subprocess.run([resolved, "exec", "--help"], capture_output=True,
                                   text=True, timeout=15, check=False)
            if probe.returncode == 0 and all(flag in probe.stdout for flag in REQUIRED_FLAGS):
                return str(Path(resolved).resolve())
            failures.append(f"{candidate}: missing modern exec capabilities")
        except (OSError, subprocess.SubprocessError) as error:
            failures.append(f"{candidate}: {error}")
    raise RuntimeError("No compatible Codex CLI. " + "; ".join(failures))


def _command(executable, output_dir):
    command = [executable, "exec", "--ephemeral", "--ignore-user-config", "--sandbox", "read-only",
               "--skip-git-repo-check", "--json", "--output-schema", str(output_dir / "schema.json"),
               "--output-last-message", str(output_dir / "result.json"),
               "-c", "project_doc_max_bytes=0", "-c", 'web_search="disabled"',
               "-c", 'approval_policy="never"', "-c", "suppress_unstable_features_warning=true"]
    for feature in DISABLED:
        command.extend(["--disable", feature])
    command.extend(["--enable", "skip_host_skill_discovery", "-"])
    return command


def _replay(events_path):
    identity, started, completed, finals = None, False, False, []
    metadata = {}
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = _json(line)
        if not isinstance(event, dict):
            raise ValueError("Event must be an object")
        kind = event.get("type")
        if completed:
            raise ValueError("Events after turn completion")
        if kind == "thread.started":
            if identity is not None or started:
                raise ValueError("Multiple or misplaced thread identities")
            identity = event.get("thread_id")
            if not isinstance(identity, str) or not identity.strip():
                raise ValueError("Missing real thread identity")
        elif kind == "turn.started":
            if identity is None or started:
                raise ValueError("Missing identity or multiple turns")
            started = True
        elif kind in {"item.started", "item.updated", "item.completed"}:
            item = event.get("item")
            if not started or not isinstance(item, dict):
                raise ValueError("Item outside a running turn")
            if item.get("type") not in {"reasoning", "agent_message"}:
                raise ValueError("Tool or unsupported item in tool-free run")
            if kind == "item.completed" and item.get("type") == "agent_message":
                if not isinstance(item.get("text"), str):
                    raise ValueError("Agent result text missing")
                finals.append(item["text"])
        elif kind == "turn.completed":
            if not started:
                raise ValueError("Completion without a started turn")
            completed = True
        else:
            raise ValueError(f"Failed or unsupported runtime event: {kind}")
        if "thread_id" in event and event["thread_id"] != identity:
            raise ValueError("Conflicting event identity")
        for key in ("model", "model_provider", "usage"):
            if key in event:
                metadata[key] = event[key]
    if not identity or not completed or len(finals) != 1:
        raise ValueError("Run needs one identity, completed turn and one final message")
    output = _json(finals[0])
    if not isinstance(output, dict):
        raise ValueError("Final JSON must be an object")
    return identity, output, finals[0], metadata


def validate_run(output_dir):
    """Rebuild identity/result from raw events; never trust a claimed pass."""
    directory = Path(output_dir).resolve()
    try:
        for name in (*FILES, "receipt.json"):
            path = directory / name
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Missing or linked run file: {name}")
        receipt = _json((directory / "receipt.json").read_text(encoding="utf-8"))
        if not isinstance(receipt, dict) or receipt.get("schemaVersion") != 1:
            raise ValueError("Unknown runtime receipt")
        if type(receipt.get("returncode")) is not int or receipt["returncode"] != 0 or receipt.get("error"):
            raise ValueError(receipt.get("error") or f"Runtime exited with code {receipt.get('returncode')}")
        if receipt.get("fileSha256") != {name: _sha(directory / name) for name in FILES}:
            raise ValueError("Runtime evidence was changed")
        invocation = receipt.get("invocation", {})
        executable = invocation.get("executable")
        if not isinstance(executable, str) or not executable:
            raise ValueError("Missing executable identity")
        if invocation.get("argv") != _command(executable, directory):
            raise ValueError("Invocation was not a fresh restricted exec")
        if invocation.get("initialCwdEntries") != [] or not invocation.get("temporaryCwd"):
            raise ValueError("Run did not use a fresh empty working directory")
        identity, output, final, metadata = _replay(directory / "events.jsonl")
        if (directory / "result.json").read_text(encoding="utf-8").strip() != final.strip():
            raise ValueError("Saved final result differs from actual runtime event")
        if receipt.get("agentId") != identity or receipt.get("runtimeMetadata") != metadata:
            raise ValueError("Receipt identity or runtime metadata differs from events")
        return {"status": "completed", "agentId": identity, "output": output,
                "runtimeMetadata": metadata, "receiptPath": str(directory / "receipt.json")}
    except (OSError, ValueError, TypeError, AttributeError) as error:
        return {"status": "runtime_error", "agentId": None, "output": None, "error": str(error)}


def run_agent(prompt, output_dir, output_schema, *, executable=None, timeout=300):
    """Run one new session. Existing auth is preserved; no config or secret reads."""
    directory = Path(output_dir).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        return {"status": "runtime_error", "agentId": None, "output": None,
                "error": "Run output directory must be empty; evidence cannot be overwritten"}
    if not isinstance(prompt, str) or not isinstance(output_schema, dict):
        return {"status": "runtime_error", "agentId": None, "output": None,
                "error": "Prompt must be a string and output schema an object"}
    (directory / "prompt.txt").write_text(prompt, encoding="utf-8")
    _write(directory / "schema.json", output_schema)
    for name in ("events.jsonl", "stderr.txt", "result.json"):
        (directory / name).write_bytes(b"")
    receipt = {"schemaVersion": 1, "returncode": None, "agentId": None,
               "runtimeMetadata": {}, "invocation": {}, "error": None}
    try:
        selected = _executable(executable)
        command = _command(selected, directory)
        with tempfile.TemporaryDirectory(prefix="kb-agent-empty-") as cwd:
            receipt["invocation"] = {"executable": selected, "argv": command,
                                     "temporaryCwd": cwd, "initialCwdEntries": os.listdir(cwd),
                                     "timeoutSeconds": timeout,
                                     "stdinFile": "prompt.txt", "history": "fresh-exec"}
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, cwd=cwd, start_new_session=os.name == "posix")
            try:
                stdout, stderr = process.communicate(prompt.encode("utf-8"), timeout=timeout)
            except subprocess.TimeoutExpired:
                receipt["error"] = f"Agent timed out after {timeout} seconds"
                if os.name == "posix":
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    process.kill()
                stdout, stderr = process.communicate()
            (directory / "events.jsonl").write_bytes(stdout)
            (directory / "stderr.txt").write_bytes(stderr)
            receipt["returncode"] = process.returncode
        if receipt["returncode"] != 0 and not receipt["error"]:
            receipt["error"] = f"Codex exited with code {receipt['returncode']}"
        identity, _, _, metadata = _replay(directory / "events.jsonl")
        receipt.update(agentId=identity, runtimeMetadata=metadata)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        receipt["error"] = receipt["error"] or str(error)
    receipt["fileSha256"] = {name: _sha(directory / name) for name in FILES}
    _write(directory / "receipt.json", receipt)
    return validate_run(directory)
