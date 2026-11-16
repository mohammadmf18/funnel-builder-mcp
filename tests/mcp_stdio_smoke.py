"""Real MCP stdio handshake and tool invocation smoke test.

Uses the MCP Python SDK as an actual client rather than importing server functions.
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]

async def main():
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["FUNNEL_DB_PATH"] = str(Path(tmp) / "funnel-test.db")
        params = StdioServerParameters(
            command=sys.executable,
            args=[str(ROOT / "mcp_server.py")],
            env=env,
        )
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert len(names) == 15, f"Expected 15 MCP tools; found {len(names)}: {names}"
                created = await session.call_tool("create_funnel", {"name": "MCP integration smoke", "goal": "leadgen"})
                assert not created.isError, f"create_funnel failed: {created}"
                listed = await session.call_tool("list_funnels", {})
                assert not listed.isError, f"list_funnels failed: {listed}"
                output = str(listed)
                assert "MCP integration smoke" in output, f"Created funnel not found: {output}"
                print("PASS: MCP handshake, 15 tools, create_funnel, list_funnels")

if __name__ == "__main__":
    asyncio.run(main())
