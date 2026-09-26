"""stdio MCP adapter using the same JSON schemas and dispatcher as the HTTP API."""
import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

import schemas

mcp = Server("funnel-builder")


@mcp.list_tools()
async def list_tools():
    return [Tool(name=t["name"], description=t["description"], inputSchema=t["parameters"]) for t in schemas.TOOLS]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict):
    result = await asyncio.to_thread(schemas.call_tool, name, arguments)
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def main():
    async with stdio_server() as (reader, writer):
        await mcp.run(reader, writer, mcp.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
