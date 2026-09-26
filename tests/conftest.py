import pytest


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setenv('FUNNEL_DB_PATH', str(tmp_path / 'funnels.db'))
    monkeypatch.setenv('FUNNEL_OUTPUT_DIR', str(tmp_path / 'sites'))
    monkeypatch.setenv('FUNNEL_API_KEY', 'test-key')
    import db
    monkeypatch.setattr(db, 'DB_PATH', str(tmp_path / 'funnels.db'))
    db.init_db()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from api_server import app
    with TestClient(app) as client:
        yield client


@pytest.fixture
def journey():
    import core
    fid = core.create_funnel('فنل تجريبي')['funnel_id']
    landing = core.add_landing_page(fid, 'مرحبًا')
    optin = core.add_optin_page(fid, 'سجّل', 'أخبار المنتج')
    thanks = core.add_thankyou_page(fid, message='تم التسجيل')
    core.publish_funnel(fid)
    return fid, landing, optin, thanks
