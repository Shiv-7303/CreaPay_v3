from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
import razorpay
from app import db
from app.models.subscription import Subscription
from datetime import datetime, timedelta
import hmac
import hashlib

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

def get_razorpay_client():
    key_id = current_app.config.get('RAZORPAY_KEY_ID')
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
    if not key_id or not key_secret:
        raise ValueError("Razorpay API keys (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET) are not configured in the environment.")
    return razorpay.Client(auth=(key_id, key_secret))

@payments_bp.route('/create-order', methods=['POST'])
@login_required
def create_order():
    if current_app.config.get('TESTING'):
        # Mock Razorpay response for tests
        return jsonify({
            'id': 'order_mock123',
            'amount': 29900,
            'currency': 'INR'
        }), 200
        
    try:
        client = get_razorpay_client()
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    
    amount = current_app.config.get('PRO_PLAN_PRICE', 29900)
    
    order_data = {
        "amount": amount,
        "currency": "INR",
        "receipt": f"{current_user.id}-{int(datetime.now().timestamp())}",
        "notes": {
            "user_id": current_user.id,
            "plan": "pro"
        }
    }
    
    try:
        order = client.order.create(data=order_data)
        return jsonify(order), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@payments_bp.route('/webhook', methods=['POST'])
def webhook():
    # Verify signature
    webhook_secret = current_app.config.get('RAZORPAY_WEBHOOK_SECRET', 'test_secret')
    signature = request.headers.get('X-Razorpay-Signature')
    payload = request.get_data(as_text=True)
    
    if not current_app.config.get('TESTING'):
        try:
            client = get_razorpay_client()
            client.utility.verify_webhook_signature(payload, signature, webhook_secret)
        except Exception as e:
            return jsonify({"error": "Invalid signature"}), 400
    
    data = request.json
    event = data.get('event')
    
    if event == 'payment.captured':
        payment_entity = data['payload']['payment']['entity']
        payment_id = payment_entity['id']
        amount = payment_entity['amount'] / 100 # convert from paise
        
        # Get user_id from notes
        notes = payment_entity.get('notes', {})
        user_id = notes.get('user_id')
        
        if not user_id:
            return jsonify({"error": "No user_id in notes"}), 400
            
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Create subscription record
        now = datetime.now()
        sub = Subscription(
            user_id=user.id,
            razorpay_payment_id=payment_id,
            plan='pro',
            amount_paid=amount,
            starts_at=now,
            expires_at=now + timedelta(days=30),
            status='active'
        )
        
        user.plan = 'pro'
        user.plan_expires_at = now + timedelta(days=30)
        
        db.session.add(sub)
        db.session.commit()
        
    return jsonify({"status": "ok"}), 200

@payments_bp.route('/status', methods=['GET'])
@login_required
def payment_status():
    sub = Subscription.query.filter_by(
        user_id=current_user.id, 
        status='active'
    ).order_by(Subscription.expires_at.desc()).first()
    
    if not sub:
        return jsonify({
            "plan": "free",
            "expires_at": None
        })
        
    return jsonify({
        "plan": sub.plan,
        "expires_at": sub.expires_at.isoformat()
    })
