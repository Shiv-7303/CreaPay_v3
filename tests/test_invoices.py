import pytest
from app import create_app, db
from app.models.user import User
from app.models.brand import Brand
from app.models.deal import Deal
from app.models.invoice import Invoice
import bcrypt
import os

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

def test_invoice_generation(auth_client, app):
    client, user_id = auth_client
    
    # Create deal, should trigger invoice generation
    response = client.post('/deals/create', json={
        'brand_name': 'Invoice Brand',
        'amount': '10000',
        'content_type': 'reel',
        'tds_applicable': True
    })
    
    assert response.status_code == 201
    deal_id = response.json['id']
    
    with app.app_context():
        invoice = Invoice.query.filter_by(deal_id=deal_id).first()
        assert invoice is not None
        assert invoice.invoice_number.startswith('CP-')
        assert invoice.gross_amount == 10000
        assert invoice.tds_amount == 1000
        assert invoice.net_amount == 9000
        
def test_invoice_whatsapp(auth_client, app):
    client, user_id = auth_client
    
    # Create deal
    res = client.post('/deals/create', json={
        'brand_name': 'Whatsapp Brand',
        'amount': '5000',
        'content_type': 'post'
    })
    deal_id = res.json['id']
    
    res = client.get(f'/invoices/{deal_id}/share/whatsapp')
    assert res.status_code == 200
    assert 'whatsapp_url' in res.json
    assert 'wa.me' in res.json['whatsapp_url']

def test_invoice_download(auth_client, app):
    client, user_id = auth_client
    
    # Create deal
    res = client.post('/deals/create', json={
        'brand_name': 'Download Brand',
        'amount': '5000',
        'content_type': 'post'
    })
    deal_id = res.json['id']
    
    # Test download
    res = client.get(f'/invoices/{deal_id}/pdf')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/pdf'
    # Check it's a valid PDF (starts with %PDF)
    assert res.data.startswith(b'%PDF')
