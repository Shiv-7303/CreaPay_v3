import pytest
from app import create_app, db
from app.models.user import User
from app.models.brand import Brand
from app.models.deal import Deal
from app.models.invoice import Invoice
from datetime import datetime
import bcrypt
import io

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
def pro_client(client, app):
    with app.app_context():
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name='Test Pro',
            email='testpro@example.com',
            password_hash=hashed,
            plan='pro'
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
    client.post('/auth/login', data={
        'email': 'testpro@example.com',
        'password': 'password123'
    })
    
    return client, user_id

def test_logo_upload(pro_client, app):
    client, user_id = pro_client
    
    # Mock file upload
    data = {
        'logo': (io.BytesIO(b"fake_image_data"), 'testlogo.png')
    }
    
    res = client.post('/auth/settings/logo-upload', data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    assert 'logo_url' in res.json
    
    with app.app_context():
        u = User.query.get(user_id)
        assert u.logo_url is not None
        assert 'testlogo.png' in u.logo_url or 'logo_' in u.logo_url

def test_invoice_regenerate(pro_client, app):
    client, user_id = pro_client
    
    # Create deal to get an invoice
    res = client.post('/deals/create', json={
        'brand_name': 'Regen Brand',
        'amount': '5000',
        'content_type': 'post'
    })
    deal_id = res.json['id']
    
    with app.app_context():
        invoice = Invoice.query.filter_by(deal_id=deal_id).first()
        old_url = invoice.pdf_url
        old_time = invoice.generated_at
    
    res = client.post(f'/invoices/{deal_id}/regenerate')
    assert res.status_code == 200
    assert res.json['status'] == 'regenerated'
    
    with app.app_context():
        invoice = Invoice.query.filter_by(deal_id=deal_id).first()
        # Mock storage means URL might just change based on timestamp, but let's check generated_at
        assert invoice.generated_at > old_time
