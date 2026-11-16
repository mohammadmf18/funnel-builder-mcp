"""Local stdio MCP server for AI Sales Funnel Builder."""
from mcp.server.fastmcp import FastMCP
import schemas

mcp = FastMCP("ai-sales-funnel-builder")

for tool in schemas.TOOLS:
    fn = tool["func"]
    fn.__doc__ = tool["description"]
    mcp.tool(name=tool["name"], description=tool["description"])(fn)

if __name__ == "__main__":
    mcp.run(transport="stdio")
