"""Optional official MCP SDK v1 transport; no SDK imports on core code paths."""
from __future__ import annotations
import asyncio
import json
import re
from importlib.metadata import PackageNotFoundError, version

def require_mcp_sdk():
    """Reject unsupported server SDKs before importing their incompatible API."""
    try:
        installed = version("mcp")
    except PackageNotFoundError as error:
        raise ImportError("MCP server requires mcp>=1.26,<2 in a separate Python environment; JSON/Python tools need no MCP SDK.") from error
    match = re.fullmatch(r"1\.(\d+)(?:\.\d+)?(?:\.post\d+)?(?:\+[A-Za-z0-9.-]+)?", installed)
    if match is None or int(match[1]) < 26:
        raise ImportError(f"Unsupported MCP SDK {installed}: this server requires mcp>=1.26,<2. Use a separate interpreter; keep the host's SDK unchanged.")
    return installed

def mcp_sdk_supported():
    try:
        require_mcp_sdk()
        return True
    except ImportError:
        return False

async def serve(runtime):
    require_mcp_sdk()
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import CallToolResult, TextContent, Tool
    except ImportError as error:
        raise ImportError("MCP transport requires mcp>=1.26,<2 in this Python environment") from error

    server = Server("novel_os_mcp")

    @server.list_tools()
    async def list_tools():
        return [Tool(**definition) for definition in runtime.tools()]

    @server.call_tool()
    async def call_tool(name, arguments):
        result = await asyncio.to_thread(runtime.call, name, arguments)
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=True))],
                              structuredContent=result, isError=not result["ok"])

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())
