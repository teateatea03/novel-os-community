#!/usr/bin/env python3
"""Probe an OpenAI-compatible endpoint without printing secrets or raw responses."""
import argparse, datetime as dt, json, os, subprocess, sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def load(path):
    return json.loads(Path(path).read_text())


def post(url, payload, auth_env=None, timeout=45):
    headers = {"Content-Type": "application/json"}
    if auth_env:
        value = os.environ.get(auth_env)
        if value:
            headers["Authorization"] = f"Bearer {value}"
    req = Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode()), None
    except HTTPError as e:
        return e.code, None, f"http_{e.code}"
    except (URLError, TimeoutError, ValueError) as e:
        return None, None, type(e).__name__


def host_state_probe(state_path=None, graph_root=None, reality_state=None):
    results={}
    if state_path:
        cmd=[sys.executable,'<SKILLS_ROOT>/immersive-interactive-fiction/scripts/interactive_state.py','validate','--state',state_path]
        p=subprocess.run(cmd,capture_output=True,text=True); results['interactive_state']={'passed':p.returncode==0}
    if graph_root:
        cmd=[sys.executable,'<SKILLS_ROOT>/knowledge-relationship-graph/scripts/relationship_graph.py','validate','--root',graph_root]
        p=subprocess.run(cmd,capture_output=True,text=True); results['graph_validate']={'passed':p.returncode==0}
    if reality_state:
        cmd=[sys.executable,'<SKILLS_ROOT>/novel-reality-state-engine/scripts/reality_state.py','validate','--state',reality_state]
        p=subprocess.run(cmd,capture_output=True,text=True); results['reality_gate']={'passed':p.returncode==0}
    return results


def probe_endpoint(base_url, model, auth_env=None, state_path=None, graph_root=None, reality_state=None):
    url = base_url.rstrip("/") + "/chat/completions"
    probes = {}
    status, data, err = post(url, {"model": model, "messages": [{"role": "user", "content": "Reply only: probe_ok"}], "temperature": 0, "max_tokens": 32}, auth_env)
    probes["text"] = {"passed": status == 200 and isinstance(data, dict) and bool(data.get("choices")), "http_status": status, "error": err}
    status, data, err = post(url, {"model": model, "messages": [{"role": "user", "content": "Return JSON exactly with key status and value ok."}], "response_format": {"type": "json_object"}, "temperature": 0, "max_tokens": 64}, auth_env)
    json_ok = False
    if status == 200 and isinstance(data, dict) and data.get("choices"):
        content = data["choices"][0].get("message", {}).get("content", "")
        try:
            obj = json.loads(content)
            json_ok = isinstance(obj, dict) and "status" in obj
        except (TypeError, ValueError):
            pass
    probes["structured_json"] = {"passed": json_ok, "http_status": status, "error": err}
    tools = [{"type": "function", "function": {"name": "local_health_check", "description": "Report local model health", "parameters": {"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]}}}]
    status, data, err = post(url, {"model": model, "messages": [{"role": "user", "content": "Call local_health_check; do not answer with ordinary text."}], "tools": tools, "tool_choice": "required", "temperature": 0, "max_tokens": 256}, auth_env)
    result = {"passed": False, "http_status": status, "error": err}
    tool_data = None
    if status == 200 and isinstance(data, dict) and data.get("choices"):
        msg = data["choices"][0].get("message", {})
        calls = msg.get("tool_calls") or []
        if calls:
            fn = calls[0].get("function", {})
            args = fn.get("arguments", "")
            try:
                parsed = json.loads(args) if isinstance(args, str) else args
            except (TypeError, ValueError):
                parsed = None
            result["passed"] = bool(calls[0].get("id")) and bool(fn.get("name")) and isinstance(parsed, dict) and bool(parsed)
            tool_data = {"message": msg, "call": calls[0]}
            result["finish_reason"] = data["choices"][0].get("finish_reason")
            if not result["passed"]:
                result["reason"] = "empty_or_invalid_tool_arguments"
        else:
            result["reason"] = "no_native_tool_calls"
    probes["tool_call"] = result
    host = host_state_probe(state_path, graph_root, reality_state)
    probes["state_scripts"] = {"passed": bool(host) and all(x.get("passed") for x in host.values()), "checks": host}
    multi = {"passed": False, "reason": "initial_tool_call_failed"}
    if tool_data and result["passed"]:
        messages = [
            {"role": "user", "content": "Call local_health_check; do not answer with ordinary text."},
            {"role": "assistant", "tool_calls": [tool_data["call"]]},
            {"role": "tool", "tool_call_id": tool_data["call"].get("id"), "content": json.dumps({"status": "healthy"})},
        ]
        s2, d2, e2 = post(url, {"model": model, "messages": messages + [{"role": "user", "content": "Reply only: tool_loop_ok"}], "temperature": 0, "max_tokens": 64}, auth_env)
        multi = {"passed": s2 == 200 and isinstance(d2, dict) and bool(d2.get("choices")), "http_status": s2, "error": e2}
    probes["multi_step_agent"] = multi
    return probes


def assess(probes):
    passed = lambda k: bool(probes.get(k, {}).get("passed"))
    if all(passed(k) for k in ("text", "structured_json", "tool_call", "state_scripts", "multi_step_agent")):
        level = "L5"
    elif all(passed(k) for k in ("text", "structured_json", "tool_call", "state_scripts")):
        level = "L4"
    elif passed("text") and passed("structured_json"):
        level = "L2"
    elif passed("text"):
        level = "L1"
    else:
        level = "L0"
    disabled = []
    if level in ("L0", "L1", "L2"):
        disabled += ["automatic_tool_calls", "agent_loop"]
    if level in ("L0", "L1"):
        disabled += ["structured_state", "graph_automation", "reality_gate_automation"]
    if level == "L0":
        disabled += ["text_generation"]
    return {"level": level, "passed": level in ("L4", "L5"), "disabled_features": disabled}


def tool_probe(response):
    try:
        call = response["choices"][0]["message"]["tool_calls"][0]
        fn = call.get("function", {})
        args = fn.get("arguments", "")
        obj = json.loads(args) if isinstance(args, str) else args
        ok = bool(call.get("id")) and bool(fn.get("name")) and isinstance(obj, dict) and bool(obj)
        return {"passed": ok, "reason": None if ok else "missing_tool_id_name_or_nonempty_arguments"}
    except Exception as exc:
        return {"passed": False, "reason": type(exc).__name__}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report")
    ap.add_argument("--response")
    ap.add_argument("--base-url", help="OpenAI-compatible base URL, e.g. http://127.0.0.1:1234/v1")
    ap.add_argument("--model")
    ap.add_argument("--auth-env", help="environment variable name; value is never printed")
    ap.add_argument("--out")
    ap.add_argument("--state-path", help="interactive state JSON for host probe")
    ap.add_argument("--graph-root", help="Graphify root for host probe")
    ap.add_argument("--reality-state", help="state JSON for Reality engine probe")
    args = ap.parse_args()
    if args.base_url and args.model:
        probes = probe_endpoint(args.base_url, args.model, args.auth_env, args.state_path, args.graph_root, args.reality_state)
        identity = {"active_model": args.model, "endpoint_kind": "chat_completions", "base_url": args.base_url}
    elif args.response:
        response = load(args.response)
        probes = {"text": {"passed": True}, "tool_call": tool_probe(response)}
        identity = {"active_model": "response_fixture", "endpoint_kind": "unknown"}
    elif args.report:
        report = load(args.report)
        probes = report.get("probes", {})
        identity = {"active_model": report.get("active_model", "unknown"), "endpoint_kind": report.get("endpoint_kind", "unknown")}
    else:
        ap.error("provide --base-url and --model, --report, or --response")
    result = {**identity, "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(), "probes": probes, **assess(probes)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
