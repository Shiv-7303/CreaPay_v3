import pytest
from app import create_app, db
from app.models.user import User
import bcrypt

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

@pytest.fixture
def admin_client(client, app):
    with app.app_context():
        hashed = bcrypt.hashpw('adminpass'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin_user = User(
            full_name='Admin User',
            email='admin@example.com',
            password_hash=hashed,
            plan='pro',
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        admin_id = admin_user.id
        
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'adminpass'
    })
    
    return client, admin_id

@pytest.fixture
def non_admin_client(client, app):
    with app.app_context():
        hashed = bcrypt.hashpw('userpass'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        regular_user = User(
            full_name='Regular User',
            email='user@example.com',
            password_hash=hashed,
            plan='free',
            is_admin=False
        )
        db.session.add(regular_user)
        db.session.commit()
        
    client.post('/auth/login', data={
        'email': 'user@example.com',
        'password': 'userpass'
    })
    
    return client

def test_admin_panel_access_non_admin(non_admin_client):
    res = non_admin_client.get('/admin/')
    assert res.status_code == 302
    assert res.headers['Location'] == '/dashboard/'

def test_admin_api_access_non_admin(non_admin_client):
    res = non_admin_client.get('/admin/api/users')
    assert res.status_code == 403
    assert res.json['error'] == 'Admin access required'

def test_admin_panel_access_admin(admin_client):
    client, _ = admin_client
    res = client.get('/admin/')
    assert res.status_code == 302
    assert res.headers['Location'] == '/admin/analytics'

def test_admin_stats(admin_client, app):
    client, _ = admin_client
    res = client.get('/admin/api/stats')
    assert res.status_code == 200
    data = res.json
    assert 'total_signups' in data
    assert 'mrr' in data
