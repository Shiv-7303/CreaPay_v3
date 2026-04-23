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

def test_brand_report(client, app):
    with app.app_context():
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name='Test Pro',
            email='testpro@example.com',
            password_hash=hashed,
            plan='pro'
        )
        db.session.add(user)
        db.session.flush()
        
        brand1 = Brand(name="Nike", user_id=user.id)
        brand2 = Brand(name="Adidas", user_id=user.id)
        db.session.add_all([brand1, brand2])
        db.session.flush()
        
        from datetime import datetime
        d1 = Deal(user_id=user.id, brand_id=brand1.id, amount=1000, content_type='post', due_date=datetime.now(), status='paid')
        d2 = Deal(user_id=user.id, brand_id=brand1.id, amount=500, content_type='story', due_date=datetime.now(), status='active')
        d3 = Deal(user_id=user.id, brand_id=brand2.id, amount=2000, content_type='video', due_date=datetime.now(), status='paid')
        
        db.session.add_all([d1, d2, d3])
        db.session.commit()
        
    client.post('/auth/login', data={
        'email': 'testpro@example.com',
        'password': 'password123'
    })
    
    res = client.get('/dashboard/brand-report')
    assert res.status_code == 200
    
    data = res.json
    assert len(data) == 2
    
    # Check sorting and aggregations
    assert data[0]['brand'] == 'Adidas'
    assert data[0]['earned'] == 2000
    assert data[0]['pending'] == 0
    
    assert data[1]['brand'] == 'Nike'
    assert data[1]['earned'] == 1000
    assert data[1]['pending'] == 500
    assert data[1]['count'] == 2
