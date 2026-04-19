import pytest
from app import create_app, db
from app.models.user import User
from app.models.brand import Brand
from app.models.deal import Deal
from app.models.invoice import Invoice
from datetime import datetime
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

def test_export_csv(client, app):
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
        
        brand = Brand(name="Export Brand", user_id=user.id)
        db.session.add(brand)
        db.session.commit()
        
        deal = Deal(
            user_id=user.id,
            brand_id=brand.id,
            amount=10000,
            content_type='post',
            tds_applicable=True,
            due_date=datetime.now().date()
        )
        db.session.add(deal)
        db.session.flush()
        
        invoice = Invoice(
            deal_id=deal.id,
            user_id=user.id,
            invoice_number='CP-1234',
            gross_amount=10000,
            tds_amount=1000,
            net_amount=9000
        )
        db.session.add(invoice)
        db.session.commit()
        
    client.post('/auth/login', data={
        'email': 'testpro@example.com',
        'password': 'password123'
    })
    
    res = client.get('/dashboard/export-csv')
    assert res.status_code == 200
    assert res.headers['Content-type'] == 'text/csv'
    
    csv_content = res.data.decode('utf-8')
    assert 'Brand,Amount (₹),TDS (₹),Net Amount (₹),Status,Content Type,Due Date,Created Date,Invoice Number' in csv_content
    assert 'Export Brand,10000.00,1000.00,9000.00,negotiating,post' in csv_content
    assert 'CP-1234' in csv_content
