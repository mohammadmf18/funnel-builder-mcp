"""Optional authenticated bridge from local stdio MCP to the hosted service."""
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def enabled():
    return bool(os.environ.get('FUNNEL_CONNECTION_FILE'))


def request(path: str, payload=None):
    config = json.loads(Path(os.environ['FUNNEL_CONNECTION_FILE']).read_text())
    url = config['url'].rstrip('/')
    parsed = urlsplit(url)
    local = parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost', '::1'}
    if (parsed.scheme != 'https' and not local) or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'', '/'}:
        raise ValueError('Hosted connection must use an HTTPS origin')
    key = config.get('api_key')
    if not isinstance(key, str) or not key:
        raise ValueError('Hosted connection is missing its management key')
    body = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    req = Request(url + path, data=body, headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    try:
        with build_opener(NoRedirect()).open(req, timeout=30) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError('Hosted response exceeded the allowed size')
            return json.loads(raw)
    except HTTPError as exc:
        # Never echo connection secrets or arbitrary proxy error pages to the model.
        if exc.code == 422:
            try:
                detail = json.loads(exc.read(65536)).get('detail', 'Invalid arguments')
            except (ValueError, AttributeError):
                detail = 'Invalid arguments'
            raise ValueError(str(detail)) from exc
        raise RuntimeError(f'Hosted funnel service returned HTTP {exc.code}') from exc
    except URLError as exc:
        raise RuntimeError('Could not reach the hosted funnel service') from exc
