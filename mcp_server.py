"""stdio MCP adapter using the same JSON schemas and dispatcher as the HTTP API."""
import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

import schemas
import remote

mcp = Server("funnel-builder")


@mcp.list_tools()
async def list_tools():
    if remote.enabled():
        result = await asyncio.to_thread(remote.request, '/tools')
        return [Tool(name=t['function']['name'], description=t['function']['description'], inputSchema=t['function']['parameters']) for t in result['tools']]
    return [Tool(name=t["name"], description=t["description"], inputSchema=t["parameters"]) for t in schemas.TOOLS]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict):
    if remote.enabled():
        response = await asyncio.to_thread(remote.request, '/tools/call', {'name': name, 'arguments': arguments})
        result = response['result']
    else:
        result = await asyncio.to_thread(schemas.call_tool, name, arguments)
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def main():
    async with stdio_server() as (reader, writer):
        await mcp.run(reader, writer, mcp.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
