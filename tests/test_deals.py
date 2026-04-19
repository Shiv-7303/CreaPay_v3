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

def test_create_deal(auth_client, app):
    client, user_id = auth_client
    
    response = client.post('/deals/create', json={
        'brand_name': 'New Brand',
        'amount': '5000',
        'content_type': 'reel',
        'tds_applicable': True
    })
    
    assert response.status_code == 201
    data = response.json
    assert data['status'] == 'negotiating'
    assert 'brand_id' in data
    
    with app.app_context():
        deal = Deal.query.get(data['id'])
        assert deal is not None
        assert deal.amount == 5000
        assert deal.tds_applicable == True
        assert deal.brand.name == 'New Brand'
        
def test_deal_status_flow(auth_client, app):
    client, user_id = auth_client
    
    # Create deal
    res = client.post('/deals/create', json={
        'brand_name': 'Test Brand Flow',
        'amount': '1000',
        'content_type': 'post'
    })
    deal_id = res.json['id']
    
    # Invalid transition (negotiating -> paid)
    res = client.patch(f'/deals/{deal_id}/status', json={'status': 'paid'})
    assert res.status_code == 400
    
    # Valid transition (negotiating -> active)
    res = client.patch(f'/deals/{deal_id}/status', json={'status': 'active'})
    assert res.status_code == 200
    assert res.json['status'] == 'active'

def test_mark_paid(auth_client, app):
    client, user_id = auth_client
    
    res = client.post('/deals/create', json={
        'brand_name': 'Paid Brand',
        'amount': '2000',
        'content_type': 'video'
    })
    deal_id = res.json['id']
    
    res = client.post(f'/deals/{deal_id}/mark-paid')
    assert res.status_code == 200
    assert res.json['status'] == 'paid'
    
    with app.app_context():
        deal = Deal.query.get(deal_id)
        assert deal.paid_at is not None

def test_soft_delete(auth_client, app):
    client, user_id = auth_client
    
    res = client.post('/deals/create', json={
        'brand_name': 'Delete Brand',
        'amount': '1000',
        'content_type': 'story'
    })
    deal_id = res.json['id']
    
    res = client.delete(f'/deals/{deal_id}')
    assert res.status_code == 200
    
    res = client.get('/deals/')
    deals = res.json
    assert len(deals) == 0
    
    with app.app_context():
        deal = Deal.query.get(deal_id)
        assert deal.deleted_at is not None
