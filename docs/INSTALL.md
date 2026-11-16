# Install AI Sales Funnel Builder Skill

## Prerequisites
Python 3.10+, pip, Git, and an MCP-compatible desktop coding assistant.

```bash
git clone https://github.com/mohammadmf18/funnel-builder-mcp.git
cd funnel-builder-mcp
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell): .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## MCP configuration
Replace both paths with absolute paths on your computer.

```json
{
  "mcpServers": {
    "funnel-builder": {
      "command": "/ABSOLUTE/PATH/funnel-builder-mcp/.venv/bin/python",
      "args": ["/ABSOLUTE/PATH/funnel-builder-mcp/mcp_server.py"],
      "env": {"FUNNEL_DB_PATH": "/ABSOLUTE/PATH/funnel-builder-mcp/funnels.db"}
    }
  }
}
```

On Windows use the Python executable inside `.venv\\Scripts\\python.exe` with escaped backslashes or forward slashes in the JSON.

For Claude Desktop, add the entry under `mcpServers` in your configuration and restart the app. For other MCP clients, use their local stdio MCP-server setup UI and point to the same executable/script.

## Agent skill
Copy `SKILL.md` into your agent's supported skills directory following that agent's current instructions. The SKILL file **does not automatically configure MCP**; install and authorize the server separately.

## Try it
Prompt: "Create a three-page lead-generation funnel for an online design course." Check the resulting funnel with `get_funnel`. Export local HTML with `publish_funnel`. Pages are **static prototypes**: forms, payment buttons, and email automation require external integrations.

## Developer checks
```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

## Data privacy
Everything is stored locally in SQLite unless you explicitly configure an external service. Back up `funnels.db`; do not commit private customer data or secrets.
