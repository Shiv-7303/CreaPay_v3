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

        # Add another user for testing filters
        user2 = User(
            full_name='Free User',
            email='free@example.com',
            password_hash=hashed,
            plan='free',
            is_admin=False
        )
        db.session.add(user2)

        db.session.commit()
        admin_id = admin_user.id

    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'adminpass'
    })

    return client

def test_admin_api_users_filter(admin_client):
    res = admin_client.get('/admin/api/users')
    assert res.status_code == 200
    assert len(res.json) == 2

    res_free = admin_client.get('/admin/api/users?plan=free')
    assert res_free.status_code == 200
    assert len(res_free.json) == 1
    assert res_free.json[0]['plan'] == 'free'

    res_pro = admin_client.get('/admin/api/users?plan=pro')
    assert res_pro.status_code == 200
    assert len(res_pro.json) == 1
    assert res_pro.json[0]['plan'] == 'pro'

def test_admin_api_stats(admin_client):
    res = admin_client.get('/admin/api/stats')
    assert res.status_code == 200
    assert res.json['total_signups'] == 2
    assert res.json['total_pro_users'] == 1
    assert res.json['mrr'] == 299
