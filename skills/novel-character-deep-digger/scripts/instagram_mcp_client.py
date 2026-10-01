#!/usr/bin/env python3
"""Call the local anonymous Instagram MCP from a research workflow.

The wrapper deliberately speaks MCP over stdio instead of calling Instaloader
itself, so the research skill exercises the same MCP tools an external agent
would use. It emits a provenance envelope suitable for artifacts/raw/*.json.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


DEFAULT_SERVER = "<WORKSPACE_ROOT>/instagram-instaloader-mcp/server.py"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_args() -> tuple[str, dict[str, Any]]:
    parser = argparse.ArgumentParser(
        description="Call the local anonymous Instagram MCP and emit JSON"
    )
    sub = parser.add_subparsers(dest="operation", required=True)

    p = sub.add_parser("profile", help="public profile metadata")
    p.add_argument("username")

    p = sub.add_parser("posts", help="newest public posts")
    p.add_argument("username")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--include-media", action="store_true")

    p = sub.add_parser("post", help="one public post or Reel")
    p.add_argument("post_url")
    p.add_argument("--no-media", action="store_true")

    p = sub.add_parser("research", help="profile plus newest public posts")
    p.add_argument("username")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--include-media", action="store_true")

    args = parser.parse_args()
    if args.operation == "profile":
        return "get_instagram_profile", {"username": args.username}
    if args.operation == "posts":
        return "get_instagram_posts", {
            "username": args.username,
            "limit": args.limit,
            "include_media": args.include_media,
        }
    if args.operation == "post":
        return "get_instagram_post", {
            "post_url": args.post_url,
            "include_media": not args.no_media,
        }
    return "research_public_profile", {
        "username": args.username,
        "limit": args.limit,
        "include_media": args.include_media,
    }


def extract_result(call_result: Any) -> Any:
    """Extract JSON text from an MCP CallToolResult."""
    content = getattr(call_result, "content", []) or []
    for item in content:
        text = getattr(item, "text", None)
        if not text:
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"ok": False, "error": "non_json_mcp_response", "message": text}
    return {"ok": False, "error": "empty_mcp_response"}


async def call_mcp(tool: str, arguments: dict[str, Any], server_path: str) -> Any:
    params = StdioServerParameters(
        command=sys.executable,
        args=[server_path, "--transport", "stdio"],
        cwd=str(Path(server_path).parent),
        env=os.environ.copy(),
    )
    async with stdio_client(params, errlog=sys.stderr) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            if tool not in names:
                return {
                    "ok": False,
                    "error": "mcp_tool_not_found",
                    "tool": tool,
                    "available_tools": sorted(names),
                }
            result = await session.call_tool(tool, arguments)
            return extract_result(result)


def main() -> int:
    tool, arguments = parse_args()
    server_path = os.getenv("INSTAGRAM_MCP_SERVER", DEFAULT_SERVER)
    captured_at = now_utc()
    envelope: dict[str, Any] = {
        "schema": "minis.instagram-mcp-capture.v1",
        "collector": {
            "name": "instagram-instaloader-mcp",
            "transport": "stdio",
            "server_path": server_path,
            "instaloader": "4.15.3",
            "anonymous": True,
        },
        "tool": tool,
        "arguments": arguments,
        "captured_at_utc": captured_at,
    }
    try:
        envelope["result"] = asyncio.run(call_mcp(tool, arguments, server_path))
    except FileNotFoundError as exc:
        envelope["result"] = {
            "ok": False,
            "error": "mcp_server_not_found",
            "message": str(exc),
            "server_path": server_path,
        }
    except Exception as exc:  # preserve an auditable failure artifact
        envelope["result"] = {
            "ok": False,
            "error": "mcp_client_error",
            "message": str(exc),
        }
    print(json.dumps(envelope, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
