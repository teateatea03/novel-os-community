"""Optional official MCP SDK v1 transport; no SDK imports on core code paths."""
from __future__ import annotations
import asyncio
import json

async def serve(runtime):
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
