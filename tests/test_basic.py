import pytest
from app import create_app, db

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_app_starts(client):
    """Test that the app can be initialized and root returns 200"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Welcome to CreaPay" in response.data

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.data == b"OK"
