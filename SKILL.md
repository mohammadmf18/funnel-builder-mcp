---
name: ai-sales-funnel-builder
description: Build, edit, export, and analyze sales-funnel page drafts with the local Funnel Builder MCP server. Use when users request landing pages, opt-in pages, sales pages, checkout mockups, upsells, thank-you pages, or funnel analytics.
---
# AI Sales Funnel Builder

Turn a marketing brief into a structured, multi-page **draft** funnel through the local `funnel-builder` MCP tools.

## When to use
- A user requests a lead-generation, product-launch, webinar or course sales funnel.
- A user wants a landing page, lead-capture page, sales page, checkout *mockup*, upsell or thank-you page.
- A user wants to inspect existing funnels, export HTML, or inspect manually recorded conversion events.

## Setup
1. Install Python 3.10+ and dependencies using `python -m pip install -r requirements.txt`.
2. Register the MCP server with your agent using an absolute path to `mcp_server.py`. Example for Claude Desktop in `docs/INSTALL.md`.
3. Use the `funnel-builder` tools. The server stores funnels in a local SQLite file.

## Recommended workflow
1. Ask for the product, intended audience, offer, funnel goal, price, currency, tone, proof points and legal constraints. If absent, use clearly identified assumptions rather than inventing endorsements.
2. Choose a goal-aligned flow: lead-gen = landing → optin → thankyou; sales = landing → sales → checkout → thankyou; upsell optional.
3. Call `create_funnel` with a descriptive name and goal. Retain the returned funnel_id.
4. Call the appropriate `add_*_page` tools using that funnel_id. Draft compelling, accurate, non-deceptive headlines and CTAs. Only claim outcomes or urgency if substantiated.
5. Call `get_funnel` to check ordering, copy, prices and currency. Use `update_page` for corrections.
6. Call `publish_funnel` to **export local static HTML**. Explain that deployment to the internet is separate.
7. Use `get_funnel_analytics` only when events have been recorded via `record_event`. Do not imply live tracking or real revenue.

## Tool selection
- `create_funnel`, `list_funnels`, `get_funnel`, `delete_funnel`: lifecycle (confirm before destructive deletion).
- `add_landing_page`: headline, supporting copy, primary CTA.
- `add_optin_page`: lead-capture design **only**; email form is not connected to a backend.
- `add_sales_page`: benefits, offer price and currency.
- `add_checkout_page`: **checkout page mockup, not a payment processor**.
- `add_upsell_page`: post-purchase offer mockup.
- `add_thankyou_page`: confirmation design.
- `connect_email_sequence`: stores proposed email content; **does not send emails**.
- `record_event`: manually records event data; **not an automatic analytics pixel**.
- `get_funnel_analytics`: summarizes recorded events.
- `publish_funnel`: writes HTML to `generated_sites/<funnel_id>/`.

## Safety and limitations
Never ask for or embed card details, passwords, secret API keys or customer lists in funnel HTML. Do not claim a functional payment flow, email-delivery automation, live analytics, hosting, or production readiness. Get approval before deleting. Review generated copy for applicable marketing, privacy and consumer requirements before public use.

## Example user request
"Build a lead magnet funnel for a beginner photography guide with a landing page, opt-in page and thank-you page. Use a friendly tone and make it clear the form needs backend integration."
