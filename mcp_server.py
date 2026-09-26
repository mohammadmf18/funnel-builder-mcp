"""
mcp_server.py
MCP Server يعرض أدوات بناء الفنلات التسويقية للعملاء اللي يدعمون
Model Context Protocol (مثل Claude Desktop).

تشغيل محلي:
    python mcp_server.py

إعداد Claude Desktop (claude_desktop_config.json):
{
  "mcpServers": {
    "funnel-builder": {
      "command": "python",
      "args": ["/المسار-الكامل/funnel-builder-mcp/mcp_server.py"]
    }
  }
}
"""

try:
    # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _MCPServerClass
except ImportError:
    # mcp < 2.0 (FastMCP القديم)
    from mcp.server.fastmcp import FastMCP as _MCPServerClass

import schemas

mcp = _MCPServerClass("funnel-builder")


def _register_tool(tool_def):
    """يسجّل كل أداة من schemas.TOOLS كأداة MCP فعلية، بنفس الاسم والوصف."""

    func = tool_def["func"]
    func.__doc__ = tool_def["description"]
    mcp.tool(name=tool_def["name"], description=tool_def["description"])(func)


for tool_def in schemas.TOOLS:
    _register_tool(tool_def)


if __name__ == "__main__":
    mcp.run(transport="stdio")
