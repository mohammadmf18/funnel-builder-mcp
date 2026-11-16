# AI Sales Funnel Builder — MCP Setup

## Requirements
Python 3.10+, Git, and an AI agent that supports **local stdio MCP servers**. Agensi distributes the SKILL instructions only; it does not run the MCP server.

## Install the tested source branch
```bash
git clone --branch feature/ai-sales-funnel-builder-skill https://github.com/mohammadmf18/funnel-builder-mcp.git
cd funnel-builder-mcp
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Configure a local MCP client
Copy `mcp_config.example.json` as a reference and replace all absolute paths (including the Python executable). Do not use literal placeholder paths. Paste the `mcpServers` entry into your agent's MCP configuration. In Claude Desktop restart the app after saving. For other clients follow the local stdio server configuration instructions. This config does **not** automatically install from Agensi.

## Use the skill
Connect your agent to Agensi, authorize loading the AI Sales Funnel Builder Skill, and separately connect the local Funnel Builder MCP server. Then ask:

> Create a lead-generation funnel for a beginner photography ebook, add a landing page and opt-in page, include a thank-you page, and export static HTML drafts.

Check tool calls with `get_funnel` and `publish_funnel`. The outputs are prototypes. Forms and payment links aren't live; do not collect payment details or real customer data.

## Tests for developers
```bash
python -m unittest discover -s tests -v
python tests/mcp_stdio_smoke.py
```

## Security
Keep your server local to your machine. The REST interface (if enabled) requires `FUNNEL_API_KEY` and `X-API-Key`, and should never be exposed publicly without additional hardening. Funnel data is saved in local SQLite.

Source code: https://github.com/mohammadmf18/funnel-builder-mcp
