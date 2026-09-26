import asyncio
import inspect
import json
import os
from pathlib import Path
import sqlite3
import sys

import pytest


def test_complete_journey_and_deduplication(client, journey):
    import core
    fid, landing, optin, thanks = journey
    entry = client.get(f'/sites/{fid}/')
    assert entry.status_code == 200
    assert f'href="{optin["slug"]}.html"' in entry.text
    assert 'viewport' in entry.text
    assert 'HttpOnly' in entry.headers['set-cookie']
    response = client.get(f'/sites/{fid}/{optin["slug"]}.html')
    assert '<form' in response.text
    assert client.get(f'/sites/{fid}/funnel.js').status_code == 200
    body = {'page_id': optin['page_id'], 'email': 'Person@example.com'}
    first = client.post(f'/sites/{fid}/leads', json=body)
    assert first.status_code == 200
    assert first.json()['next_url'] == f'/sites/{fid}/{thanks["slug"]}.html'
    assert client.get(first.json()['next_url']).status_code == 200
    body['email'] = 'person@example.com'
    assert client.post(f'/sites/{fid}/leads', json=body).json() == first.json()
    assert len(core.list_leads(fid)['leads']) == 1
    stats = core.get_funnel_analytics(fid)
    assert stats['visits'] == 1  # One browser across three pages.
    assert stats['optins'] == 1
    assert stats['optin_rate'] == 1
    assert client.post('/tools/call', json={'name':'list_leads','arguments':{'funnel_id':fid}}).status_code == 401
    result = client.post('/tools/call', headers={'Authorization':'Bearer test-key'}, json={'name':'list_leads','arguments':{'funnel_id':fid}})
    assert result.json()['result']['leads'][0]['email'] == 'person@example.com'


def test_management_auth_fails_closed(client, monkeypatch):
    assert client.get('/health').status_code == 200
    assert client.get('/tools').status_code == 401
    assert client.get('/tools', headers={'Authorization':'Bearer wrong'}).status_code == 401
    assert client.get('/tools', headers={'Authorization':'Bearer test-key'}).status_code == 200
    monkeypatch.delenv('FUNNEL_API_KEY')
    assert client.get('/tools').status_code == 503
    assert client.post('/tools/call', json={'name':'create_funnel','arguments':{'name':'test'}}).status_code == 503


def test_invalid_leads_and_unpublished_pages(client, journey):
    import core
    fid, landing, optin, _ = journey
    for body in [
        {'email':'invalid','page_id':optin['page_id']},
        {'email':'person@example.com','page_id':landing['page_id']},
        {'email':'person@example.com','page_id':optin['page_id'],'value':500},
    ]:
        assert client.post(f'/sites/{fid}/leads', json=body).status_code == 422
    other = core.create_funnel('draft')['funnel_id']
    assert client.get(f'/sites/{other}/').status_code == 404
    assert client.post(f'/sites/{other}/leads', json={'email':'a@example.com','page_id':optin['page_id']}).status_code == 404
    new_page = core.add_optin_page(fid, 'unpublished', 'draft')
    assert client.get(f'/sites/{fid}/{new_page["slug"]}.html').status_code == 404
    assert client.post(f'/sites/{fid}/leads', json={'email':'a@example.com','page_id':new_page['page_id']}).status_code == 422
    assert not core.list_leads(fid)['leads']


def test_schema_required_fields_match_signatures():
    import schemas
    for tool in schemas.TOOLS:
        signature = inspect.signature(tool['func'])
        required = {name for name, param in signature.parameters.items() if param.default is inspect.Parameter.empty}
        assert set(tool['parameters'].get('required', [])) == required


@pytest.mark.parametrize('arguments', [
    {'headline':'test','price':30},
    {'headline':'test','price':-1,'benefits':['one']},
    {'headline':'test','price':30,'benefits':'not a list'},
    {'headline':'test','price':float('nan'),'benefits':[]},
    {'headline':'test','price':30,'benefits':[],'unexpected':'field'},
    {'headline':'test','price':30,'benefits':[],'currency':'<script>'},
])
def test_invalid_tool_arguments_are_rejected(journey, arguments):
    import schemas
    with pytest.raises(ValueError):
        schemas.call_tool('add_sales_page', {'funnel_id':journey[0], **arguments})


def test_page_update_validates_and_preserves_content(journey):
    import core
    fid = journey[0]
    page = core.add_sales_page(fid, 'test', ['one'], 5)
    with pytest.raises(ValueError):
        core.update_page(page['page_id'], content={'benefits':'bad'})
    with pytest.raises(ValueError):
        core.update_page(page['page_id'], content={'price':-1})
    assert core.get_funnel(fid)['pages'][-1]['content']['benefits'] == ['one']
    assert core.update_page(page['page_id'], content={'price':8})['content']['price'] == 8


def test_event_ownership_and_revenue(journey):
    import core
    other = core.create_funnel('other')['funnel_id']
    with pytest.raises(ValueError):
        core.record_event(other, 'visit', journey[1]['page_id'])
    with pytest.raises(ValueError):
        core.record_event('funnel_000000000000', 'visit')
    core.record_event(journey[0], 'purchase', value=10)
    core.record_event(journey[0], 'upsell_purchase', value=3)
    assert core.get_funnel_analytics(journey[0])['revenue'] == 13


def test_escaping_and_payment_urls(journey):
    import core
    fid = journey[0]
    payload = '<script>alert("x")</script>'
    core.update_page(journey[1]['page_id'], headline=payload, content={'subheadline':payload,'cta_text':payload})
    core.add_sales_page(fid, payload, [payload], 10)
    core.add_checkout_page(fid, payload, 10)
    core.add_upsell_page(fid, payload, 5, checkout_url='https://example.com/pay?a=1&b=2')
    result = core.publish_funnel(fid)
    for page in result['pages']:
        html = Path(page['file']).read_text()
        assert '<script>alert' not in html
        assert 'href="#"' not in html
    checkout = Path(result['pages'][-2]['file']).read_text()
    assert 'الدفع غير متاح' in checkout
    assert 'https://example.com/pay?a=1&amp;b=2' in Path(result['pages'][-1]['file']).read_text()
    for url in ['javascript:alert(1)', 'http://example.com', 'https://user:password@example.com']:
        with pytest.raises(ValueError):
            core.add_checkout_page(fid, 'product', 3, checkout_url=url)


def test_publish_scope_delete_and_empty_funnel(client, journey):
    import core, schemas
    fid = journey[0]
    with pytest.raises(ValueError):
        schemas.call_tool('publish_funnel', {'funnel_id':fid,'output_dir':'/tmp/untrusted'})
    empty = core.create_funnel('empty')['funnel_id']
    with pytest.raises(ValueError):
        core.publish_funnel(empty)
    assert core.get_funnel(empty)['status'] == 'draft'
    core.submit_lead(fid, journey[2]['page_id'], 'person@example.com', 'a'*32)
    path = core.site_root() / fid
    assert path.exists()
    core.delete_funnel(fid)
    assert not path.exists()
    assert client.get(f'/sites/{fid}/').status_code == 404
    from db import get_conn
    with get_conn() as conn:
        assert conn.execute('SELECT COUNT(*) FROM leads WHERE funnel_id = ?', (fid,)).fetchone()[0] == 0
        assert conn.execute('SELECT COUNT(*) FROM events WHERE funnel_id = ?', (fid,)).fetchone()[0] == 0


def test_email_sequence_is_explicitly_a_draft(journey):
    import schemas
    args = {'funnel_id':journey[0],'list_name':'welcome','emails':[{'subject':'Hi','body':'Welcome','delay_days':0}]}
    result = schemas.call_tool('connect_email_sequence', args)
    assert result['status'] == 'draft' and result['sending_enabled'] is False
    args['emails'][0]['delay_days'] = -1
    with pytest.raises(ValueError):
        schemas.call_tool('connect_email_sequence', args)


def test_existing_database_upgrade(tmp_path, monkeypatch):
    import db
    legacy = tmp_path / 'legacy.db'
    with sqlite3.connect(legacy) as conn:
        conn.execute('CREATE TABLE events(id TEXT PRIMARY KEY, funnel_id TEXT, page_id TEXT, event_type TEXT, value REAL, created_at TEXT)')
        conn.execute("INSERT INTO events VALUES ('evt_old','funnel_old',NULL,'visit',0,'2026-01-01')")
    monkeypatch.setattr(db, 'DB_PATH', str(legacy))
    db.init_db()
    db.init_db()
    with db.get_conn() as conn:
        assert conn.execute("SELECT visitor_id FROM events WHERE id='evt_old'").fetchone()[0] is None


def test_stdio_mcp_schema_parity_and_execution():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    import schemas
    async def exercise():
        params = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).resolve().parents[1] / 'mcp_server.py')], env=dict(os.environ))
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                listing = await session.list_tools()
                actual = {tool.name:tool.inputSchema for tool in listing.tools}
                assert actual == {tool['name']:tool['parameters'] for tool in schemas.TOOLS}
                created = await session.call_tool('create_funnel', {'name':'MCP test'})
                assert not created.isError
                fid = json.loads(created.content[0].text)['funnel_id']
                bad = await session.call_tool('add_sales_page', {'funnel_id':fid,'headline':'test','price':10})
                assert bad.isError
                added = await session.call_tool('add_sales_page', {'funnel_id':fid,'headline':'test','price':10,'benefits':['one']})
                assert not added.isError
                exported = await session.call_tool('publish_funnel', {'funnel_id':fid})
                assert not exported.isError
    asyncio.run(exercise())
