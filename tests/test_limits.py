import pytest
from app import create_app, db
from app.models.user import User
from app.models.brand import Brand
from app.models.deal import Deal
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
def auth_client(client, app):
    with app.app_context():
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name='Test User',
            email='test@example.com',
            password_hash=hashed,
            plan='free'
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    return client, user_id

def test_free_deal_limit(auth_client, app):
    client, user_id = auth_client
    
    # We set FREE_DEAL_LIMIT = 3 in config
    
    # Create 3 deals
    for i in range(3):
        res = client.post('/deals/create', json={
            'brand_name': f'Brand {i}',
            'amount': '1000',
            'content_type': 'post'
        })
        assert res.status_code == 201
        
    # 4th deal should be blocked
    res = client.post('/deals/create', json={
        'brand_name': 'Brand 4',
        'amount': '1000',
        'content_type': 'post'
    })
    assert res.status_code == 402
    data = res.json
    assert data['upgrade_required'] == True
    assert data['limit'] == 3
    assert data['current'] == 3
