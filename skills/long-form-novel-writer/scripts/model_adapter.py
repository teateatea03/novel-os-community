"""Local model-review process bridge; the host supplies an argv array, never a shell."""
from __future__ import annotations
import json
import math
import subprocess
from pathlib import Path

def review_with_adapter(command, *, role, model, prompt, max_tokens, raw_path, timeout):
    argv = json.loads(command)
    if (not isinstance(argv, list) or not argv
            or any(not isinstance(x, str) or not x or "\0" in x for x in argv)):
        raise ValueError("adapter command must be a nonempty JSON argv array")
    if not math.isfinite(timeout) or not 0 < timeout <= 600:
        raise ValueError("adapter timeout must be between 0 and 600 seconds")
    request = {"schema": "novel-os.review-request.v1", "role": role, "model": model,
               "prompt": prompt, "max_tokens": max_tokens, "may_commit_state": False}
    result = subprocess.run(argv, input=json.dumps(request, ensure_ascii=True, allow_nan=False),
                            text=True, encoding="utf-8", capture_output=True, timeout=timeout, shell=False)
    if result.returncode:
        raise ValueError("review adapter failed: " + (result.stderr or result.stdout)[-2000:])
    response = json.loads(result.stdout)
    if not isinstance(response, dict) or not isinstance(response.get("text"), str) or not response["text"].strip():
        raise ValueError("review adapter must return a JSON object containing nonempty text")
    Path(raw_path).write_text(response["text"], encoding="utf-8")
