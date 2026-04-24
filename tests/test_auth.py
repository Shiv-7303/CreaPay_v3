import pytest
from app import create_app, db
from app.models.user import User
import bcrypt
from datetime import datetime, timezone

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user_id(app):
    with app.app_context():
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name='Test User',
            email='test@example.com',
            password_hash=hashed,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        return user.id

def test_login_active(client, test_user_id):
    res = client.post('/auth/login', data={'email': 'test@example.com', 'password': 'password123'}, follow_redirects=True)
    assert b'Logout' in res.data or b'Welcome' in res.data or b'Dashboard' in res.data # Should be logged in

def test_login_suspended(client, app, test_user_id):
    with app.app_context():
        u = User.query.get(test_user_id)
        u.is_active = False
        db.session.commit()
    res = client.post('/auth/login', data={'email': 'test@example.com', 'password': 'password123'}, follow_redirects=True)
    assert b'This account has been suspended by the administrator.' in res.data

        
def test_register_active_fails(client, test_user_id):
    res = client.post('/auth/register', data={
        'full_name': 'Another User',
        'email': 'test@example.com',
        'password': 'newpassword123'
    }, follow_redirects=True)
    assert b'Account already exists with this email.' in res.data
