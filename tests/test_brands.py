import pytest
from app import create_app, db
from app.models.user import User
from app.models.brand import Brand

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
    import bcrypt
    
    with app.app_context():
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name='Test User',
            email='test@example.com',
            password_hash=hashed
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    return client, user_id

def test_brand_search_empty(auth_client, app):
    client, user_id = auth_client
    response = client.get('/api/brands/search?q=')
    assert response.status_code == 200
    assert response.json == []

def test_brand_name_validation(auth_client, app):
    client, user_id = auth_client
    
    # Test empty name
    res = client.post('/deals/create', json={
        'brand_name': '   ',
        'amount': '5000',
        'content_type': 'post'
    })
    assert res.status_code == 400
    assert 'required' in res.json['error']
    
    # Test long name
    res = client.post('/deals/create', json={
        'brand_name': 'a' * 256,
        'amount': '5000',
        'content_type': 'post'
    })
    assert res.status_code == 400
    assert 'exceed' in res.json['error']

def test_brand_search_results(auth_client, app):
    client, user_id = auth_client
    
    with app.app_context():
        # User needs to be fetched in this session
        u = User.query.get(user_id)
        brand1 = Brand(name="Nike", user_id=u.id)
        brand2 = Brand(name="Nintendo", user_id=u.id)
        brand3 = Brand(name="Adidas", user_id=u.id)
        db.session.add_all([brand1, brand2, brand3])
        db.session.commit()
        
    response = client.get('/api/brands/search?q=ni')
    assert response.status_code == 200
    results = response.json
    assert len(results) == 2
    names = [r['name'] for r in results]
    assert "Nike" in names
    assert "Nintendo" in names
    assert "Adidas" not in names
