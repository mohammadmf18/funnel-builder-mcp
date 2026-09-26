import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest


def test_remote_bridge_and_redirect_protection(tmp_path, monkeypatch):
    import remote
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            calls.append((self.path, self.headers.get('Authorization')))
            if self.path == '/redirect':
                self.send_response(302)
                self.send_header('Location', '/must-not-follow')
                self.end_headers()
                return
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.end_headers()
            self.wfile.write(b'{"tools":[]}')
        def do_POST(self):
            calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"result":{"ok":true}}')
    server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    config = tmp_path/'connection.json'
    config.write_text(json.dumps({'url':f'http://127.0.0.1:{server.server_port}','api_key':'test-only'}))
    monkeypatch.setenv('FUNNEL_CONNECTION_FILE',str(config))
    try:
        assert remote.request('/tools') == {'tools':[]}
        assert calls[-1][1] == 'Bearer test-only'
        assert remote.request('/tools/call',{'name':'list_funnels','arguments':{}})['result']['ok']
        with pytest.raises(RuntimeError, match='302'):
            remote.request('/redirect')
        assert not any(isinstance(c,tuple) and c[0]=='/must-not-follow' for c in calls)
        config.write_text(json.dumps({'url':'http://example.com','api_key':'test-only'}))
        with pytest.raises(ValueError, match='HTTPS'):
            remote.request('/tools')
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
