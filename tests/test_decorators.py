import pytest
from app import create_app, db
from app.models.user import User
import bcrypt
from flask import jsonify

@pytest.fixture
def app():
    app = create_app('testing')
    
    # Add a test route
    from app.utils.decorators import pro_required
    from flask_login import login_required
    
    @app.route('/test-pro')
    @login_required
    @pro_required
    def test_pro():
        return jsonify({'success': True})
        
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def setup_user(app, client, plan):
    with app.app_context():
        hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            full_name=f'Test {plan}',
            email=f'test{plan}@example.com',
            password_hash=hashed,
            plan=plan
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
    client.post('/auth/login', data={
        'email': f'test{plan}@example.com',
        'password': 'password123'
    })
    
    return user_id

def test_pro_required_free_user(client, app):
    setup_user(app, client, 'free')
    
    res = client.get('/test-pro')
    assert res.status_code == 403
    assert res.json['upgrade_required'] == True

def test_pro_required_pro_user(client, app):
    setup_user(app, client, 'pro')
    
    res = client.get('/test-pro')
    assert res.status_code == 200
    assert res.json['success'] == True
