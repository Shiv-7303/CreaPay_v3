import pytest
from app import create_app, db
from app.models.user import User

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

def test_register_user(client, app):
    response = client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Dashboard' in response.data
    
    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        assert user is not None
        assert user.full_name == 'Test User'

def test_duplicate_email(client, app):
    # Register first user
    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    })
    client.post('/auth/logout')
    
    # Register second user with same email
    response = client.post('/auth/register', data={
        'full_name': 'Another User',
        'email': 'test@example.com',
        'password': 'password456'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Account already exists' in response.data

def test_login_valid(client, app):
    # Register
    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    })
    client.post('/auth/logout')
    
    # Login
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_login_invalid(client, app):
    # Register
    client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    })
    client.post('/auth/logout')
    
    # Login with wrong password
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data
